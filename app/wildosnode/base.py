from abc import ABC, abstractmethod
from typing import AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from .service_pb2 import PeakEvent, HostSystemMetrics, FileInfo, BackendStats
    from google.protobuf.internal.containers import RepeatedScalarFieldContainer, RepeatedCompositeFieldContainer


class WildosNodeBase(ABC):
    async def stop(self):
        """stops all operations"""

    async def update_user(
        self, user, inbounds: set[str] | None = None
    ) -> None:
        """updates a user on the node"""

    async def fetch_users_stats(self):
        """get user stats from the node"""

    async def get_logs(self, name: str, include_buffer: bool) -> AsyncGenerator[str, None]:
        """Return async generator for log lines"""
        if False:  # Make this a generator
            yield

    async def restart_backend(
        self, name: str, config: str, config_format: int
    ):
        pass

    async def get_backend_config(self, name: str) -> tuple[str, str]:
        return ("", "")

    async def get_backend_stats(self, name: str):
        pass

    @abstractmethod
    async def get_host_system_metrics(self) -> 'HostSystemMetrics':
        """Get host system metrics (CPU, RAM, disk, network, uptime)"""
        ...

    async def get_host_open_ports(self):
        """Get list of open ports on host system"""
        pass

    @abstractmethod
    async def open_host_port(self, port: int) -> bool:
        """Open a port on host system firewall"""
        ...

    @abstractmethod
    async def close_host_port(self, port: int) -> bool:
        """Close a port on host system firewall"""
        ...

    @abstractmethod
    async def get_container_logs(self, tail: int) -> 'RepeatedScalarFieldContainer[str]':
        """Get container logs"""
        ...

    @abstractmethod
    async def get_container_files(self, path: str) -> 'RepeatedCompositeFieldContainer[FileInfo]':
        """Get list of files in container directory"""
        ...

    @abstractmethod
    async def restart_container(self) -> bool:
        """Restart the node's container"""
        ...

    @abstractmethod
    async def get_all_backends_stats(self) -> dict[str, 'BackendStats']:
        """Get stats for all backends of a node in one request"""
        ...

    async def stream_peak_events(self) -> AsyncGenerator['PeakEvent', None]:
        """WebSocket endpoint for real-time peak events streaming"""
        if False:  # Make this a generator
            yield

    async def fetch_backends(self):
        """Fetch available backends"""
        pass
