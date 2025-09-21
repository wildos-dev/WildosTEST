import asyncio
import logging
import os
from typing import Annotated
from datetime import datetime
from fastapi import Depends, Request

import sqlalchemy
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Body, Query, WebSocket

from ..exceptions import (
    node_not_found_error, ConflictError, 
    ValidationError, ServerError, ServiceUnavailableError,
    ForbiddenError, BadRequestError
)
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page
from sqlalchemy import select
from starlette.websockets import WebSocketDisconnect

from app import wildosnode
from app.wildosnode.grpc_client import (
    GRPC_FAST_TIMEOUT,
    GRPC_SLOW_TIMEOUT, 
    GRPC_PORT_ACTION_TIMEOUT,
    GRPC_STREAM_TIMEOUT
)
from app.db import crud, get_tls_certificate
from app.db.models import Node
from app.dependencies import (
    DBDep,
    SudoAdminDep,
    EndDateDep,
    StartDateDep,
    get_admin,
    get_node_auth,
)
from app.models.node import (
    NodeCreate,
    NodeModify,
    NodeResponse,
    NodeSettings,
    NodeStatus,
    NodeConnectionBackend,
    BackendConfig,
    BackendStats,
    HostSystemMetrics,
    ContainerLog,
    ContainerFile,
    PortInfo,
    PortActionRequest,
    PortActionResponse,
    ContainerRestartResponse,
    AllBackendsStatsResponse,
    PeakEvent,
    PeakEventCreate,
)
from app.models.system import TrafficUsageSeries
from app.middleware.validation import StrictNodeCreateRequest
from app.middleware.proxy_headers import get_client_ip
from app.security.security_logger import SecurityEventType, security_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nodes", tags=["Node"])


def _extract_ws_token(websocket: WebSocket) -> tuple[str | None, str | None]:
    """
    Extract authentication token from WebSocket handshake.
    
    Security Enhancement: Only supports secure Sec-WebSocket-Protocol header method.
    Supports both 'bearer.<token>' and 'bearer <token>' formats in Sec-WebSocket-Protocol.
    
    Returns:
        tuple: (token, selected_subprotocol) where selected_subprotocol is used for handshake
    """
    # Check for deprecated authentication methods and log security warnings
    query_token = websocket.query_params.get('token')
    if query_token:
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "event": "deprecated_websocket_auth_attempt",
                "method": "query_parameter",
                "reason": "Query parameter authentication is deprecated due to security risks",
                "client_ip": websocket.client.host if websocket.client else "unknown"
            },
            severity="WARNING",
            ip_address=websocket.client.host if websocket.client else None
        )
        
    auth_header = websocket.headers.get('authorization', '')
    if auth_header.lower().startswith('bearer ') and len(auth_header) > 7:
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "event": "deprecated_websocket_auth_attempt", 
                "method": "authorization_header",
                "reason": "Authorization header authentication is deprecated due to security risks",
                "client_ip": websocket.client.host if websocket.client else "unknown"
            },
            severity="WARNING",
            ip_address=websocket.client.host if websocket.client else None
        )
    
    # ONLY secure method: Check Sec-WebSocket-Protocol header for secure token transmission
    proto_header = websocket.headers.get('sec-websocket-protocol', '')
    if proto_header:
        for raw_proto in proto_header.split(','):
            proto = raw_proto.strip().strip('"\'')
            proto_lower = proto.lower()
            
            # Support both 'bearer.<token>' and 'bearer <token>' formats
            if proto_lower.startswith('bearer.') and len(proto) > 7:
                token = proto[7:]  # Extract token after 'bearer.'
                return token, proto
            elif proto_lower.startswith('bearer ') and len(proto) > 7:
                token = proto[7:]  # Extract token after 'bearer '
                return token, proto
        
    return None, None


@router.get("", response_model=Page[NodeResponse])
def get_nodes(
    db: DBDep,
    admin: SudoAdminDep,
    status: list[NodeStatus] = Query(None),
    name: str = Query(None),
):
    query = select(Node)

    if name:
        query = query.where(Node.name.ilike(f"%{name}%"))

    if status:
        query = query.where(Node.status.in_(status))

    return paginate(db, query)


@router.post("", response_model=NodeResponse)
async def add_node(
    new_node: StrictNodeCreateRequest, 
    db: DBDep, 
    admin: SudoAdminDep,
    request: Request
):
    """Create a new node with enhanced security validation"""
    client_ip = get_client_ip(request)
    
    # Log node creation attempt
    security_logger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        details={
            "operation": "create_node",
            "target_node": new_node.name,
            "created_by": admin.username,
            "node_address": new_node.address,
            "node_port": new_node.port
        },
        severity="INFO",
        ip_address=client_ip,
        user_id=admin.id
    )
    
    try:
        # Convert strict request to NodeCreate model  
        node_create = NodeCreate.model_validate({
            "name": new_node.name,
            "address": new_node.address,
            "port": new_node.port,
            "usage_coefficient": new_node.usage_coefficient
        })
        
        db_node = crud.create_node(db, node_create)
        
    except IntegrityError:
        db.rollback()
        
        # Log failed creation attempt
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "node_creation_failed",
                "reason": "Node already exists",
                "attempted_name": new_node.name,
                "created_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        raise ConflictError(
            f'Node "{new_node.name}" already exists'
        )
    
    certificate = get_tls_certificate(db)
    await wildosnode.operations.add_node(db_node, certificate)
    
    # Log successful creation
    security_logger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        details={
            "operation": "node_created",
            "new_node_id": db_node.id,
            "new_node_name": db_node.name,
            "created_by": admin.username
        },
        severity="INFO",
        ip_address=client_ip,
        user_id=admin.id
    )

    logger.info("New node `%s` added", db_node.name)
    return db_node


@router.get("/settings", response_model=NodeSettings)
def get_node_settings(db: DBDep, admin: SudoAdminDep):
    tls = crud.get_tls_certificate(db)

    return NodeSettings(certificate=str(tls.certificate) if tls and hasattr(tls, 'certificate') and tls.certificate is not None else "")


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(node_id: int, db: DBDep, admin: SudoAdminDep):
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        raise node_not_found_error()

    return db_node


@router.websocket("/{node_id}/{backend}/logs")
async def node_logs(
    node_id: int,
    backend: str,
    websocket: WebSocket,
    db: DBDep,
    include_buffer: bool = True,
):
    # Extract token using secure Sec-WebSocket-Protocol method only
    token, selected_subprotocol = _extract_ws_token(websocket)
    admin = get_admin(db, token or "")

    if not admin or not admin.is_sudo:
        return await websocket.close(reason="You're not allowed", code=4403)

    if not wildosnode.nodes.get(node_id):
        return await websocket.close(reason="Node not found", code=4404)

    # Accept WebSocket connection with proper subprotocol if present
    if selected_subprotocol:
        await websocket.accept(subprotocol=selected_subprotocol)
    else:
        await websocket.accept()
        
    try:
        async for line in wildosnode.nodes[node_id].get_logs(
            name=backend, include_buffer=include_buffer
        ):
            try:
                await websocket.send_text(line or "")
            except WebSocketDisconnect:
                break
    finally:
        await websocket.close()


@router.put("/{node_id}", response_model=NodeResponse)
async def modify_node(
    node_id: int, modified_node: NodeModify, db: DBDep, admin: SudoAdminDep
):
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        raise node_not_found_error()

    db_node = crud.update_node(db, db_node, modified_node)

    await wildosnode.operations.remove_node(int(getattr(db_node, 'id', 0)))
    if db_node is not None and getattr(db_node, 'status', None) != NodeStatus.disabled:
        certificate = get_tls_certificate(db)
        await wildosnode.operations.add_node(db_node, certificate)

    logger.info("Node `%s` modified", db_node.name)
    return db_node


@router.delete("/{node_id}")
async def remove_node(node_id: int, db: DBDep, admin: SudoAdminDep):
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        raise node_not_found_error()

    crud.remove_node(db, db_node)
    await wildosnode.operations.remove_node(int(getattr(db_node, 'id', 0)))

    logger.info(f"Node `%s` deleted", db_node.name)
    return {}


@router.post("/{node_id}/resync")
async def reconnect_node(node_id: int, db: DBDep, admin: SudoAdminDep, request: Request):
    """Reconnect to a node with enhanced reliability and monitoring"""
    client_ip = get_client_ip(request)
    
    # Check that node exists in database
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "reconnect_node_failed",
                "reason": "Node not found",
                "attempted_node_id": node_id,
                "requested_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        raise node_not_found_error()

    # Log reconnection attempt
    security_logger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        details={
            "operation": "reconnect_node_started",
            "target_node_id": node_id,
            "target_node_name": db_node.name,
            "target_node_address": db_node.address,
            "target_node_port": db_node.port,
            "requested_by": admin.username
        },
        severity="INFO",
        ip_address=client_ip,
        user_id=admin.id
    )

    try:
        # Get fresh TLS certificate
        certificate = get_tls_certificate(db)
        if not certificate:
            security_logger.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                details={
                    "operation": "reconnect_node_failed",
                    "reason": "TLS certificate not found",
                    "node_id": node_id,
                    "requested_by": admin.username
                },
                severity="ERROR",
                ip_address=client_ip,
                user_id=admin.id
            )
            raise ServerError("TLS certificate not configured")

        # Call the reconnect operation with enhanced error handling
        await wildosnode.operations.reconnect_node(node_id, db_node, certificate)
        
        # Log successful reconnection
        security_logger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details={
                "operation": "reconnect_node_completed",
                "node_id": node_id,
                "node_name": db_node.name,
                "requested_by": admin.username
            },
            severity="INFO",
            ip_address=client_ip,
            user_id=admin.id
        )

        logger.info("Node `%s` reconnected successfully", db_node.name)
        
        return {
            "success": True,
            "message": f"Node '{db_node.name}' reconnected successfully",
            "node_id": node_id
        }

    except ValidationError as e:
        # Handle validation errors (node configuration issues)
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "reconnect_node_failed",
                "reason": "Validation error",
                "error": str(e),
                "node_id": node_id,
                "requested_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        logger.error("Validation error during node `%s` reconnect: %s", db_node.name, str(e))
        raise ValidationError(f"Node configuration validation failed: {str(e)}")

    except ServiceUnavailableError as e:
        # Handle service unavailable errors (node unreachable)
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "reconnect_node_failed",
                "reason": "Service unavailable",
                "error": str(e),
                "node_id": node_id,
                "requested_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        logger.error("Service unavailable during node `%s` reconnect: %s", db_node.name, str(e))
        raise ServiceUnavailableError(f"Node '{db_node.name}' is unreachable", "NODE_UNREACHABLE")

    except ConflictError as e:
        # Handle conflict errors (node already connected, etc.)
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "reconnect_node_failed",
                "reason": "Conflict error",
                "error": str(e),
                "node_id": node_id,
                "requested_by": admin.username
            },
            severity="WARNING",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        logger.error("Conflict during node `%s` reconnect: %s", db_node.name, str(e))
        raise ConflictError(f"Reconnection conflict for node '{db_node.name}': {str(e)}")

    except Exception as e:
        # Handle unexpected errors
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            details={
                "operation": "reconnect_node_failed",
                "reason": "Unexpected error",
                "error": str(e),
                "error_type": type(e).__name__,
                "node_id": node_id,
                "requested_by": admin.username
            },
            severity="ERROR",
            ip_address=client_ip,
            user_id=admin.id
        )
        
        logger.error("Unexpected error during node `%s` reconnect: %s", db_node.name, str(e))
        raise ServerError(f"Failed to reconnect to node '{db_node.name}': {str(e)}")


@router.get("/{node_id}/usage", response_model=TrafficUsageSeries)
def get_usage(
    node_id: int,
    db: DBDep,
    admin: SudoAdminDep,
    start_date: StartDateDep,
    end_date: EndDateDep,
):
    """
    Get nodes usage
    """
    node = crud.get_node_by_id(db, node_id)
    if not node:
        raise node_not_found_error()

    return crud.get_node_usage(db, start_date, end_date, node)


@router.get("/{node_id}/{backend}/stats", response_model=BackendStats)
async def get_backend_stats(
    node_id: int, backend: str, db: DBDep, admin: SudoAdminDep
):
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        stats = await asyncio.wait_for(node.get_backend_stats(backend), timeout=GRPC_FAST_TIMEOUT)
    except Exception:
        raise ServerError("Backend service error")
    else:
        return BackendStats(running=stats.running if stats else False)


@router.get("/{node_id}/{backend}/config", response_model=BackendConfig)
async def get_node_xray_config(
    node_id: int, backend: str, admin: SudoAdminDep
):
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        config, config_format = await asyncio.wait_for(node.get_backend_config(name=backend), timeout=GRPC_FAST_TIMEOUT)
    except Exception:
        raise ServiceUnavailableError("Node isn't responsive", "NODE_UNRESPONSIVE")
    else:
        return {"config": config, "format": config_format}


@router.put("/{node_id}/{backend}/config")
async def alter_node_xray_config(
    node_id: int,
    backend: str,
    admin: SudoAdminDep,
    config: Annotated[BackendConfig, Body()],
):
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        await asyncio.wait_for(
            node.restart_backend(
                name=backend,
                config=config.config,
                config_format=config.format.value,
            ),
            timeout=GRPC_SLOW_TIMEOUT,
        )
    except:
        raise ServerError("No response from the node.")
    return {}


# Host System Monitoring Endpoints
@router.get("/{node_id}/host/metrics", response_model=HostSystemMetrics)
async def get_host_system_metrics(
    node_id: int, db: DBDep, admin: SudoAdminDep
):
    """Get host system metrics (CPU, RAM, disk, network, uptime)"""
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        metrics = await asyncio.wait_for(node.get_host_system_metrics(), timeout=GRPC_FAST_TIMEOUT)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get host metrics for node {node_id}: {e}")
        raise ServerError("Failed to retrieve host system metrics")


@router.get("/{node_id}/host/ports", response_model=list[PortInfo])
async def get_host_open_ports(
    node_id: int, db: DBDep, admin: SudoAdminDep
):
    """Get list of open ports on host system"""
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        ports = await asyncio.wait_for(node.get_host_open_ports(), timeout=GRPC_FAST_TIMEOUT)
        return ports
    except Exception as e:
        logger.error(f"Failed to get open ports for node {node_id}: {e}")
        raise ServerError("Failed to retrieve open ports")


@router.post("/{node_id}/host/ports/open", response_model=PortActionResponse)
async def open_host_port(
    node_id: int, 
    port_request: PortActionRequest, 
    db: DBDep, 
    admin: SudoAdminDep
):
    """Open a port on host system firewall"""
    port = port_request.port
    
    # Validate port range (already handled by Pydantic model validation)
    # Check for critical ports that should be protected
    critical_ports = [22, 443]  # SSH, HTTPS
    db_node = crud.get_node_by_id(db, node_id)
    if db_node:
        critical_ports.append(int(getattr(db_node, 'port', 0)))  # Node's own port
    
    if port in critical_ports:
        raise ForbiddenError(
            f"Cannot modify critical port {port} - access would be compromised"
        )

    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        result = await asyncio.wait_for(node.open_host_port(port), timeout=GRPC_PORT_ACTION_TIMEOUT)
        return PortActionResponse(
            success=result if result is not None else False,
            message=f"Port {port} opened successfully" if result else f"Failed to open port {port}"
        )
    except Exception as e:
        logger.error(f"Failed to open port {port} on node {node_id}: {e}")
        raise ServerError(
            f"Error opening port {port}: {str(e)}"
        )


@router.post("/{node_id}/host/ports/close", response_model=PortActionResponse)
async def close_host_port(
    node_id: int, 
    port_request: PortActionRequest, 
    db: DBDep, 
    admin: SudoAdminDep
):
    """Close a port on host system firewall"""
    port = port_request.port
    
    # Validate port range (already handled by Pydantic model validation)
    # Check for critical ports that should be protected
    critical_ports = [22, 443]  # SSH, HTTPS
    db_node = crud.get_node_by_id(db, node_id)
    if db_node:
        critical_ports.append(int(getattr(db_node, 'port', 0)))  # Node's own port
    
    if port in critical_ports:
        raise ForbiddenError(
            f"Cannot close critical port {port} - system access would be lost"
        )

    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        result = await asyncio.wait_for(node.close_host_port(port), timeout=GRPC_PORT_ACTION_TIMEOUT)
        return PortActionResponse(
            success=result if result is not None else False,
            message=f"Port {port} closed successfully" if result else f"Failed to close port {port}"
        )
    except Exception as e:
        logger.error(f"Failed to close port {port} on node {node_id}: {e}")
        raise ServerError(
            f"Error closing port {port}: {str(e)}"
        )


# Container Management Endpoints
@router.get("/{node_id}/container/logs", response_model=list[ContainerLog])
async def get_container_logs(
    node_id: int, 
    db: DBDep, 
    admin: SudoAdminDep,
    tail: int = Query(100, description="Number of log lines to return")
):
    """Get container logs"""
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        logs = await asyncio.wait_for(node.get_container_logs(tail=tail), timeout=GRPC_STREAM_TIMEOUT)
        return logs
    except Exception as e:
        logger.error(f"Failed to get container logs for node {node_id}: {e}")
        raise ServerError("Failed to retrieve container logs")


@router.get("/{node_id}/container/files", response_model=list[ContainerFile])
async def get_container_files(
    node_id: int, 
    db: DBDep, 
    admin: SudoAdminDep,
    path: str = Query("/app", description="Path to list files from")
):
    """Get list of files in container directory"""
    # Validate path to prevent directory traversal attacks
    if ".." in path or path.startswith("/etc") or path.startswith("/root"):
        raise BadRequestError(
            "Invalid path - directory traversal and system directories are not allowed"
        )
    
    # Normalize and validate the path
    normalized_path = os.path.normpath(path)
    allowed_prefixes = ["/app", "/var", "/tmp", "/opt"]
    if not any(normalized_path.startswith(prefix) for prefix in allowed_prefixes):
        raise ForbiddenError(
            "Access denied - only specific directories are allowed"
        )
    
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        files = await asyncio.wait_for(node.get_container_files(path=normalized_path), timeout=GRPC_FAST_TIMEOUT)
        return files
    except Exception as e:
        logger.error(f"Failed to get container files for node {node_id}: {e}")
        raise ServerError("Failed to retrieve container files")


@router.post("/{node_id}/container/restart", response_model=ContainerRestartResponse)
async def restart_container(
    node_id: int, db: DBDep, admin: SudoAdminDep
):
    """Restart the node's container"""
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        result = await asyncio.wait_for(node.restart_container(), timeout=GRPC_SLOW_TIMEOUT)
        return ContainerRestartResponse(
            success=result if result is not None else False, 
            message="Container restart initiated" if result else "Failed to restart container"
        )
    except Exception as e:
        logger.error(f"Failed to restart container for node {node_id}: {e}")
        raise ServerError("Failed to restart container")


# Batch Backend Stats Endpoint (for performance optimization)
@router.get("/{node_id}/backends/stats", response_model=AllBackendsStatsResponse)
async def get_all_backends_stats(
    node_id: int, db: DBDep, admin: SudoAdminDep
):
    """Get stats for all backends of a node in one request"""
    if not (node := wildosnode.nodes.get(node_id)):
        raise node_not_found_error()

    try:
        all_stats = await asyncio.wait_for(node.get_all_backends_stats(), timeout=GRPC_FAST_TIMEOUT)
        
        # Convert protobuf BackendStats to model BackendStats with safe conversion
        converted_stats = {}
        if all_stats:
            for backend_name, proto_stats in all_stats.items():
                try:
                    # Check if it's already a BackendStats model instance
                    if isinstance(proto_stats, BackendStats):
                        converted_stats[backend_name] = proto_stats
                    # Check if it's a protobuf object with 'running' attribute
                    elif hasattr(proto_stats, 'running') and hasattr(proto_stats, '__class__'):
                        # Safe protobuf to model conversion
                        running_value = getattr(proto_stats, 'running', False)
                        converted_stats[backend_name] = BackendStats(running=bool(running_value))
                    else:
                        # Fallback: create default BackendStats
                        converted_stats[backend_name] = BackendStats(running=False)
                except Exception as e:
                    logger.warning(f"Failed to convert backend stats for {backend_name}: {e}")
                    # Fallback to default stats on conversion error
                    converted_stats[backend_name] = BackendStats(running=False)
        
        return AllBackendsStatsResponse(
            backends=converted_stats,
            node_id=node_id,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get all backend stats for node {node_id}: {e}")
        raise ServerError("Failed to retrieve backend stats")


# Peak Events Monitoring Endpoints
@router.get("/{node_id}/peak/events", response_model=list[PeakEvent])
async def get_peak_events_history(
    node_id: int, 
    db: DBDep, 
    admin: SudoAdminDep,
    since_ms: int = Query(0, description="Fetch events since timestamp (milliseconds)"),
    category: str = Query(None, description="Filter by category (CPU, MEMORY, DISK, NETWORK, BACKEND)"),
    limit: int = Query(100, description="Maximum number of events to return")
):
    """Get historical peak events from database"""
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        raise node_not_found_error()

    try:
        events = crud.get_peak_events(
            db=db,
            node_id=node_id,
            since_ms=since_ms,
            category=category,
            limit=limit
        )
        
        # Convert database records to API response format
        result = []
        for event in events:
            result.append(PeakEvent(
                node_id=int(getattr(event, 'node_id', 0)),
                category=getattr(event, 'category'),
                metric=str(getattr(event, 'metric', '')),
                level=getattr(event, 'level'),
                value=float(getattr(event, 'value', 0.0)),
                threshold=float(getattr(event, 'threshold', 0.0)),
                dedupe_key=str(getattr(event, 'dedupe_key', '')),
                context_json=str(getattr(event, 'context_json', '{}')) if getattr(event, 'context_json', None) is not None else "{}",
                started_at_ms=int(getattr(event, 'started_at', datetime.now()).timestamp() * 1000) if getattr(event, 'started_at', None) is not None else 0,
                resolved_at_ms=int(getattr(event, 'resolved_at', datetime.now()).timestamp() * 1000) if getattr(event, 'resolved_at', None) is not None else None,
                seq=int(getattr(event, 'seq', 0))
            ))
        
        return result
    except Exception as e:
        logger.error(f"Failed to get peak events for node {node_id}: {e}")
        raise ServerError("Failed to retrieve peak events")


@router.websocket("/{node_id}/peak/events/stream")
async def stream_peak_events(
    websocket: WebSocket,
    node_id: int,
    db: DBDep
):
    """WebSocket endpoint for real-time peak events streaming"""
    # Extract token using secure Sec-WebSocket-Protocol method only
    token, selected_subprotocol = _extract_ws_token(websocket)
    admin = get_admin(db, token or "")

    if not admin or not admin.is_sudo:
        return await websocket.close(reason="You're not allowed", code=4403)

    if not (node := wildosnode.nodes.get(node_id)):
        return await websocket.close(reason="Node not found", code=4404)

    # Accept WebSocket connection with proper subprotocol if present
    if selected_subprotocol:
        await websocket.accept(subprotocol=selected_subprotocol)
    else:
        await websocket.accept()
    
    try:
        async for event in node.stream_peak_events():
            # Convert protobuf event to dict using correct field names
            if event is not None:
                event_dict = {
                    "node_id": getattr(event, 'node_id', 0),
                    "category": getattr(event.category, 'name', str(event.category)) if hasattr(event, 'category') else 'unknown',
                    "metric": getattr(event, 'metric', ''),
                    "level": getattr(event.level, 'name', str(event.level)) if hasattr(event, 'level') else 'unknown',
                    "value": getattr(event, 'value', 0),
                    "threshold": getattr(event, 'threshold', 0),
                    "dedupe_key": getattr(event, 'dedupe_key', ''),
                    "context_json": getattr(event, 'context_json', '{}'),
                    "started_at_ms": getattr(event, 'started_at_ms', 0),
                    "resolved_at_ms": getattr(event, 'resolved_at_ms', None),
                    "seq": getattr(event, 'seq', 0)
                }
                await websocket.send_json(event_dict)
    except WebSocketDisconnect:
        logger.info(f"Peak events WebSocket disconnected for node {node_id}")
    except Exception as e:
        logger.error(f"Error streaming peak events for node {node_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        await websocket.close()


@router.post("/{node_id}/peak/events", response_model=dict)
async def save_peak_event(
    node_id: int,
    peak_event: PeakEventCreate,
    db: DBDep,
    node_auth: Annotated[dict, Depends(get_node_auth)]
):
    """Save a peak event to the database (called by authenticated nodes)"""
    # Verify node ID matches authenticated node
    if node_auth["node_id"] != node_id:
        raise ForbiddenError("Node ID mismatch")
        
    try:
        # Convert timestamp to datetime object
        started_at = datetime.fromtimestamp(peak_event.started_at_ms / 1000)
        resolved_at = datetime.fromtimestamp(peak_event.resolved_at_ms / 1000) if peak_event.resolved_at_ms else None
        
        # Upsert peak event with deduplication
        db_peak_event = crud.upsert_peak_event(
            db=db,
            node_id=node_id,
            category=peak_event.category.value,
            metric=peak_event.metric,
            value=peak_event.value,
            threshold=peak_event.threshold,
            level=peak_event.level.value,
            dedupe_key=peak_event.dedupe_key,
            context_json=peak_event.context_json,
            started_at=started_at,
            resolved_at=resolved_at,
            seq=peak_event.seq
        )
        
        logger.info(f"Peak event saved for node {node_id}: {peak_event.category} {peak_event.metric} = {peak_event.value}%")
        return {"success": True, "event_id": db_peak_event.id}
        
    except Exception as e:
        logger.error(f"Failed to save peak event for node {node_id}: {e}")
        raise ServerError("Failed to save peak event")
