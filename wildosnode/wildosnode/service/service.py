"""
The grpc Service to add/update/delete users
Right now it only supports Xray but that is subject to change
"""

import json
import logging
from collections import defaultdict
from typing import Coroutine, Any

from grpclib import GRPCError, Status
from grpclib.server import Stream

# Import authentication middleware
from .auth_middleware import secure_method

from wildosnode.backends.abstract_backend import VPNBackend
from wildosnode.storage import BaseStorage
# Import service_grpc from local service directory  
from wildosnode.service.service_grpc import WildosServiceBase
# Import from local protobuf file
from wildosnode.service.service_pb2 import (
    BackendConfig as BackendConfig_pb2,
    Backend,
    BackendLogsRequest,
    RestartBackendRequest,
    BackendStats,
    # Host system monitoring
    HostSystemMetrics,
    NetworkInterface,
    PortActionRequest,
    PortActionResponse,
    # Container management
    ContainerLogsRequest,
    ContainerLogsResponse,
    ContainerFilesRequest,
    ContainerFilesResponse,
    FileInfo,
    ContainerRestartResponse,
    # Batch operations
    AllBackendsStatsResponse,
    # Peak monitoring
    PeakEvent,
    PeakQuery,
    UserData,
    UsersData,
    Empty,
    BackendsResponse,
    Inbound,
    UsersStats,
    LogLine,
)
from ..models import User as UserModel, Inbound as InboundModel
from ..monitoring import get_peak_monitor
import psutil
import os
import subprocess
import socket
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class WildosService(WildosServiceBase):
    """Add/Update/Delete users based on calls from the client"""

    def __init__(self, storage: BaseStorage, backends: dict[str, VPNBackend]):
        self._backends = backends
        self._storage = storage

    def _resolve_tag(self, inbound_tag: str) -> VPNBackend:
        for backend in self._backends.values():
            if backend.contains_tag(inbound_tag):
                return backend
        raise GRPCError(Status.NOT_FOUND, f"Backend not found for inbound tag: {inbound_tag}")

    async def _add_user(self, user: UserModel, inbounds: list[InboundModel]):
        for inbound in inbounds:
            backend = self._resolve_tag(inbound.tag)
            logger.debug("adding user `%s` to inbound `%s`", user.username, inbound.tag)
            await backend.add_user(user, inbound)

    async def _remove_user(self, user: UserModel, inbounds: list[InboundModel]):
        for inbound in inbounds:
            backend = self._resolve_tag(inbound.tag)
            logger.debug(
                "removing user `%s` from inbound `%s`", user.username, inbound.tag
            )
            await backend.remove_user(user, inbound)

    async def _update_user(self, user_data: UserData):
        pb_user = user_data.user
        user = UserModel(id=pb_user.id, username=pb_user.username, key=pb_user.key)
        storage_user = await self._storage.list_users(user.id)
        if not storage_user and len(user_data.inbounds) > 0:
            """add the user in case there isn't any currently
            and the inbounds is non-empty"""
            inbound_tags = [i.tag for i in user_data.inbounds]
            inbound_additions = await self._storage.list_inbounds(tag=inbound_tags)
            if isinstance(inbound_additions, list):
                await self._add_user(user, inbound_additions)
                await self._storage.update_user_inbounds(user, inbound_additions)
            else:
                logger.warning("Expected list of inbounds, got: %s", type(inbound_additions))
            return
        elif not user_data.inbounds and storage_user:
            """remove in case we have the user but client has sent
            us an empty list of inbounds"""
            if isinstance(storage_user, UserModel):
                await self._remove_user(storage_user, storage_user.inbounds)
                return await self._storage.remove_user(storage_user)
            else:
                logger.error("Expected UserModel, got: %s", type(storage_user))
        elif not user_data.inbounds and not storage_user:
            """we're asked to remove a user which we don't have, just pass."""
            return

        """otherwise synchronize the user with what 
        the client has sent us"""
        if not isinstance(storage_user, UserModel):
            logger.error("Expected UserModel, got: %s", type(storage_user))
            return
            
        storage_tags = {i.tag for i in storage_user.inbounds}
        new_tags = {i.tag for i in user_data.inbounds}
        added_tags = new_tags - storage_tags
        removed_tags = storage_tags - new_tags
        new_inbounds = await self._storage.list_inbounds(tag=list(new_tags))
        added_inbounds = await self._storage.list_inbounds(tag=list(added_tags))
        removed_inbounds = await self._storage.list_inbounds(tag=list(removed_tags))
        
        if isinstance(removed_inbounds, list) and isinstance(added_inbounds, list) and isinstance(new_inbounds, list):
            await self._remove_user(storage_user, removed_inbounds)
            await self._add_user(storage_user, added_inbounds)
            await self._storage.update_user_inbounds(storage_user, new_inbounds)
        else:
            logger.error("Expected list types for inbounds operations")

    @secure_method(allow_health_check=False)
    async def SyncUsers(self, stream: Stream[UserData, Empty]) -> None:
        async for user_data in stream:
            await self._update_user(user_data)

    @secure_method(allow_health_check=False)
    async def FetchBackends(
        self,
        stream: Stream[Empty, BackendsResponse],
    ) -> None:
        await stream.recv_message()
        backends = [
            Backend(
                name=name,
                type=backend.backend_type,
                version=backend.version,
                inbounds=[
                    Inbound(tag=i.tag, config=json.dumps(i.config))
                    for i in backend.list_inbounds()
                ],
            )
            for name, backend in self._backends.items()
        ]
        await stream.send_message(BackendsResponse(backends=backends))

    @secure_method(allow_health_check=False)
    async def RepopulateUsers(
        self,
        stream: Stream[UsersData, Empty],
    ) -> None:
        message = await stream.recv_message()
        if message and hasattr(message, 'users_data') and message.users_data:
            users_data = message.users_data
            for user_data in users_data:
                await self._update_user(user_data)
            user_ids = {user_data.user.id for user_data in users_data}
        else:
            user_ids = set()
        all_users = await self._storage.list_users()
        if isinstance(all_users, list):
            for storage_user in all_users:
                if storage_user.id not in user_ids:
                    await self._remove_user(storage_user, storage_user.inbounds)
                    await self._storage.remove_user(storage_user)
        else:
            logger.error("Expected list of users from storage, got: %s", type(all_users))
        await stream.send_message(Empty())

    @secure_method(allow_health_check=False)
    async def FetchUsersStats(self, stream: Stream[Empty, UsersStats]) -> None:
        await stream.recv_message()
        all_stats = defaultdict(int)

        for backend in self._backends.values():
            stats = await backend.get_usages()

            for user, usage in stats.items():
                all_stats[user] += usage

        logger.debug(all_stats)
        user_stats = [
            UsersStats.UserStats(uid=uid, usage=usage)
            for uid, usage in all_stats.items()
        ]
        await stream.send_message(UsersStats(users_stats=user_stats))

    @secure_method(allow_health_check=False)
    async def StreamBackendLogs(
        self, stream: Stream[BackendLogsRequest, LogLine]
    ) -> None:
        req = await stream.recv_message()
        if not req or not hasattr(req, 'backend_name') or req.backend_name not in self._backends:
            raise GRPCError(Status.NOT_FOUND, "Backend not found")
        async for line in self._backends[req.backend_name].get_logs(req.include_buffer):
            await stream.send_message(LogLine(line=line))

    @secure_method(allow_health_check=False)
    async def FetchBackendConfig(
        self, stream: Stream[Backend, BackendConfig_pb2]
    ) -> None:
        req = await stream.recv_message()
        if not req or not hasattr(req, 'name') or req.name not in self._backends:
            raise GRPCError(Status.NOT_FOUND, "Backend not found")
        backend = self._backends[req.name]
        config = backend.get_config()
        # Ensure config_format is properly handled
        config_format = backend.config_format
        if hasattr(config_format, 'name') and not isinstance(config_format, int):
            config_format = config_format.name
        elif isinstance(config_format, int):
            # Convert int to string representation
            config_format = str(config_format)
        else:
            # Fallback to string representation
            config_format = str(config_format)
        
        await stream.send_message(
            BackendConfig_pb2(configuration=config, config_format=config_format)
        )

    @secure_method(allow_health_check=False)
    async def RestartBackend(
        self, stream: Stream[RestartBackendRequest, Empty]
    ) -> None:
        message = await stream.recv_message()
        if not message or not hasattr(message, 'backend_name') or message.backend_name not in self._backends:
            raise GRPCError(Status.NOT_FOUND, "Backend not found")
        if not hasattr(message, 'config') or not message.config:
            raise GRPCError(Status.INVALID_ARGUMENT, "Config required")
            
        await self._backends[message.backend_name].restart(message.config.configuration)
        await stream.send_message(Empty())

    @secure_method(allow_health_check=False)
    async def GetBackendStats(self, stream: Stream[Backend, BackendStats]) -> None:
        backend = await stream.recv_message()
        if not backend or not hasattr(backend, 'name') or backend.name not in self._backends.keys():
            raise GRPCError(
                Status.NOT_FOUND,
                "Backend doesn't exist",
            )
        running = self._backends[backend.name].running
        await stream.send_message(BackendStats(running=running))

    @secure_method(allow_health_check=False)
    async def StreamPeakEvents(self, stream: Stream[Empty, PeakEvent]) -> None:
        """Stream real-time peak events to panel"""
        await stream.recv_message()  # Receive Empty message
        
        # Get peak monitor instance (with lazy initialization)
        peak_monitor = get_peak_monitor(node_id=1)  # TODO: Get actual node_id
        
        try:
            # Start monitoring if not already running
            if not peak_monitor.is_running:
                monitoring_task = peak_monitor.start()
                
            # Stream events to client
            async for event in peak_monitor.get_peak_events_stream():
                await stream.send_message(event)
                
        except Exception as e:
            logger.error(f"Error in StreamPeakEvents: {e}")
            raise GRPCError(Status.INTERNAL, f"Peak monitoring error: {e}")

    @secure_method(allow_health_check=False)
    async def FetchPeakEvents(self, stream: Stream[PeakQuery, PeakEvent]) -> None:
        """Fetch historical peak events based on query"""
        query = await stream.recv_message()
        
        # Get peak monitor instance  
        peak_monitor = get_peak_monitor(node_id=1)  # TODO: Get actual node_id
        
        try:
            # TODO: Implement historical event replay from persistent storage
            # For now, just close the stream
            if query:
                since_ms = getattr(query, 'since_ms', 0)
                category = getattr(query, 'category', None)
                logger.info(f"FetchPeakEvents query: since_ms={since_ms}, category={category}")
            else:
                logger.warning("Received None query in FetchPeakEvents")
            # Historical events would be sent here via stream.send_message()
            
        except Exception as e:
            logger.error(f"Error in FetchPeakEvents: {e}")
            raise GRPCError(Status.INTERNAL, f"Peak events fetch error: {e}")

    # Host System Monitoring Methods
    @secure_method(allow_health_check=False)
    async def GetHostSystemMetrics(self, stream: Stream[Empty, HostSystemMetrics]) -> None:
        """Get comprehensive host system metrics"""
        await stream.recv_message()  # Receive Empty message
        
        try:
            # CPU metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_total = memory.total / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            disk_total = disk.total / (1024**3)  # GB
            
            # Load average
            load_avg = psutil.getloadavg()
            
            # Network interfaces
            net_io = psutil.net_io_counters(pernic=True)
            network_interfaces = []
            for name, stats in net_io.items():
                network_interfaces.append(NetworkInterface(
                    name=name,
                    bytes_sent=stats.bytes_sent,
                    bytes_received=stats.bytes_recv,
                    packets_sent=stats.packets_sent,
                    packets_received=stats.packets_recv
                ))
            
            # Uptime
            boot_time = int(psutil.boot_time())
            current_time = int(time.time())
            uptime_seconds = current_time - boot_time
            
            metrics = HostSystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                memory_total=memory_total,
                disk_usage=disk_usage,
                disk_total=disk_total,
                network_interfaces=network_interfaces,
                uptime_seconds=uptime_seconds,
                load_average_1m=load_avg[0],
                load_average_5m=load_avg[1],
                load_average_15m=load_avg[2]
            )
            
            await stream.send_message(metrics)
            
        except Exception as e:
            logger.error(f"Error getting host system metrics: {e}")
            raise GRPCError(Status.INTERNAL, f"Host metrics error: {e}")

    @secure_method(allow_health_check=False)
    async def OpenHostPort(self, stream: Stream[PortActionRequest, PortActionResponse]) -> None:
        """Open a port on host system firewall"""
        request = await stream.recv_message()
        
        try:
            if not request or not hasattr(request, 'protocol') or not hasattr(request, 'port'):
                await stream.send_message(PortActionResponse(success=False, message="Invalid request"))
                return
                
            # Basic port opening using iptables (simplified)
            cmd = f"iptables -A INPUT -p {request.protocol} --dport {request.port} -j ACCEPT"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            success = result.returncode == 0
            message = result.stderr if not success else f"Port {request.port}/{request.protocol} opened successfully"
            
            await stream.send_message(PortActionResponse(success=success, message=message))
            
        except Exception as e:
            port_info = getattr(request, 'port', 'unknown') if request else 'unknown'
            logger.error(f"Error opening port {port_info}: {e}")
            await stream.send_message(PortActionResponse(success=False, message=str(e)))

    @secure_method(allow_health_check=False)
    async def CloseHostPort(self, stream: Stream[PortActionRequest, PortActionResponse]) -> None:
        """Close a port on host system firewall"""
        request = await stream.recv_message()
        
        try:
            if not request or not hasattr(request, 'protocol') or not hasattr(request, 'port'):
                await stream.send_message(PortActionResponse(success=False, message="Invalid request"))
                return
                
            # Basic port closing using iptables (simplified)
            cmd = f"iptables -D INPUT -p {request.protocol} --dport {request.port} -j ACCEPT"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            success = result.returncode == 0
            message = result.stderr if not success else f"Port {request.port}/{request.protocol} closed successfully"
            
            await stream.send_message(PortActionResponse(success=success, message=message))
            
        except Exception as e:
            port_info = getattr(request, 'port', 'unknown') if request else 'unknown'
            logger.error(f"Error closing port {port_info}: {e}")
            await stream.send_message(PortActionResponse(success=False, message=str(e)))

    # Container Management Methods  
    @secure_method(allow_health_check=False)
    async def GetContainerLogs(self, stream: Stream[ContainerLogsRequest, ContainerLogsResponse]) -> None:
        """Get container logs"""
        request = await stream.recv_message()
        
        try:
            # Get container logs using docker logs command
            tail_count = getattr(request, 'tail', 100) if request else 100
            cmd = f"docker logs --tail {tail_count} $(hostname)"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            logs = result.stdout.split('\n') if result.returncode == 0 else []
            
            await stream.send_message(ContainerLogsResponse(logs=logs))
            
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            await stream.send_message(ContainerLogsResponse(logs=[f"Error: {e}"]))

    @secure_method(allow_health_check=False)
    async def GetContainerFiles(self, stream: Stream[ContainerFilesRequest, ContainerFilesResponse]) -> None:
        """Get list of files in container directory"""
        request = await stream.recv_message()
        
        try:
            path_str = getattr(request, 'path', '/app') if request else '/app'
            path = Path(path_str)
            files = []
            
            if path.exists() and path.is_dir():
                for item in path.iterdir():
                    files.append(FileInfo(
                        name=item.name,
                        path=str(item),
                        is_directory=item.is_dir(),
                        size=item.stat().st_size if item.is_file() else 0,
                        modified_time=int(item.stat().st_mtime)
                    ))
            
            await stream.send_message(ContainerFilesResponse(files=files))
            
        except Exception as e:
            path_info = getattr(request, 'path', 'unknown') if request else 'unknown'
            logger.error(f"Error getting container files for {path_info}: {e}")
            await stream.send_message(ContainerFilesResponse(files=[]))

    @secure_method(allow_health_check=False)
    async def RestartContainer(self, stream: Stream[Empty, ContainerRestartResponse]) -> None:
        """Restart the node's container"""
        await stream.recv_message()  # Receive Empty message
        
        try:
            # This is tricky as we're inside the container - we'll simulate restart signal
            # In production, this would trigger an external restart mechanism
            logger.info("Container restart requested - sending termination signal")
            
            # Send a graceful shutdown signal to the current process
            # The container orchestrator should restart the container
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
            
            await stream.send_message(ContainerRestartResponse(
                success=True, 
                message="Container restart signal sent"
            ))
            
        except Exception as e:
            logger.error(f"Error restarting container: {e}")
            await stream.send_message(ContainerRestartResponse(
                success=False, 
                message=f"Restart error: {e}"
            ))

    # Batch Operations
    @secure_method(allow_health_check=False)
    async def GetAllBackendsStats(self, stream: Stream[Empty, AllBackendsStatsResponse]) -> None:
        """Get stats for all backends in one request"""
        await stream.recv_message()  # Receive Empty message
        
        try:
            backend_stats = {}
            
            for name, backend in self._backends.items():
                backend_stats[name] = BackendStats(running=backend.running)
            
            await stream.send_message(AllBackendsStatsResponse(backend_stats=backend_stats))
            
        except Exception as e:
            logger.error(f"Error getting all backend stats: {e}")
            raise GRPCError(Status.INTERNAL, f"Backend stats error: {e}")
