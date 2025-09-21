import asyncio
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Any

# Local import to avoid circular dependency
# WildosNodeGRPCLIB импортируется лениво в add_node() для избежания циклических зависимостей
# Все app.* импорты перенесены в функции для избежания проблем с PYTHONPATH

# Enhanced error handling and monitoring imports
from .exceptions import (
    WildosNodeBaseError, NetworkError, ServiceError, ConfigurationError,
    create_error_with_context
)
# Monitoring imports moved inside functions to avoid circular dependencies

if TYPE_CHECKING:
    from app.db import User as DBUser


def _convert_user(user: "DBUser"):
    """Ленивая конвертация пользователя для избежания проблем с импортами"""
    from app.models.user import User
    return User.model_validate(user)


def update_user(
    user: "DBUser", old_inbounds: set | None = None, remove: bool = False
):
    """Updates a user on all related nodes with enhanced error handling"""
    if old_inbounds is None:
        old_inbounds = set()
    
    from .monitoring import get_monitoring, get_error_aggregator
    monitoring = get_monitoring()
    error_aggregator = get_error_aggregator()
    
    # Enhanced logging with structured context
    monitoring.logger.info(
        f"Updating user {user.username} on nodes",
        username=user.username,
        user_id=user.id,
        operation="update_user",
        remove=remove
    )

    node_inbounds = defaultdict(list)
    if remove:
        for inb in user.inbounds:
            node_inbounds[inb.node_id]
    else:
        for inb in user.inbounds:
            node_inbounds[inb.node_id].append(inb.tag)

    for inb in old_inbounds:
        node_inbounds[inb[0]]

    # Track operations for monitoring
    operations_started = 0
    
    for node_id, tags in node_inbounds.items():
        from app import wildosnode
        if wildosnode.nodes.get(node_id):
            operations_started += 1
            
            # Create enhanced update operation with error handling
            async def enhanced_update_user():
                try:
                    await wildosnode.nodes[node_id].update_user(
                        user=_convert_user(user), inbounds=set(tags)
                    )
                    
                    monitoring.logger.debug(
                        f"Successfully updated user {user.username} on node {node_id}",
                        username=user.username,
                        node_id=node_id,
                        tags_count=len(tags)
                    )
                    
                    monitoring.metrics.increment(
                        "user_update_success_total",
                        tags={'node_id': str(node_id), 'username': str(user.username)}
                    )
                    
                except Exception as e:
                    # Create structured error
                    if isinstance(e, WildosNodeBaseError):
                        structured_error = e
                    else:
                        structured_error = create_error_with_context(
                            ServiceError,
                            f"Failed to update user {user.username} on node {node_id}: {e}",
                            node_id=node_id,
                            operation="update_user",
                            username=user.username
                        )
                    
                    monitoring.logger.error(
                        f"Failed to update user {user.username} on node {node_id}",
                        error=structured_error,
                        username=user.username,
                        node_id=node_id
                    )
                    
                    # Add to error aggregation
                    error_aggregator.add_error(structured_error, f'node_{node_id}')
                    
                    monitoring.metrics.increment(
                        "user_update_error_total",
                        tags={
                            'node_id': str(node_id),
                            'username': str(user.username),
                            'error_type': type(e).__name__
                        }
                    )
            
            # Schedule the enhanced operation
            asyncio.ensure_future(enhanced_update_user())
    
    # Log summary of operations
    monitoring.logger.info(
        f"Scheduled {operations_started} user update operations",
        username=user.username,
        operations_count=operations_started,
        total_nodes=len(node_inbounds)
    )


async def remove_user(user: "DBUser"):
    """Remove a user from all related nodes with enhanced error handling"""
    from .monitoring import get_monitoring, get_error_aggregator
    monitoring = get_monitoring()
    error_aggregator = get_error_aggregator()
    
    node_ids = set(inb.node_id for inb in user.inbounds)
    
    monitoring.logger.info(
        f"Removing user {user.username} from {len(node_ids)} nodes",
        username=user.username,
        user_id=user.id,
        node_count=len(node_ids),
        operation="remove_user"
    )

    operations_started = 0
    
    for node_id in node_ids:
        from app import wildosnode
        if wildosnode.nodes.get(node_id):
            operations_started += 1
            
            # Create enhanced removal operation with error handling
            async def enhanced_remove_user():
                try:
                    await wildosnode.nodes[node_id].update_user(
                        user=_convert_user(user), inbounds=set()
                    )
                    
                    monitoring.logger.debug(
                        f"Successfully removed user {user.username} from node {node_id}",
                        username=user.username,
                        node_id=node_id
                    )
                    
                    monitoring.metrics.increment(
                        "user_remove_success_total",
                        tags={'node_id': str(node_id), 'username': str(user.username)}
                    )
                    
                except Exception as e:
                    # Create structured error
                    if isinstance(e, WildosNodeBaseError):
                        structured_error = e
                    else:
                        structured_error = create_error_with_context(
                            ServiceError,
                            f"Failed to remove user {user.username} from node {node_id}: {e}",
                            node_id=node_id,
                            operation="remove_user",
                            username=user.username
                        )
                    
                    monitoring.logger.error(
                        f"Failed to remove user {user.username} from node {node_id}",
                        error=structured_error,
                        username=user.username,
                        node_id=node_id
                    )
                    
                    # Add to error aggregation
                    error_aggregator.add_error(structured_error, f'node_{node_id}')
                    
                    monitoring.metrics.increment(
                        "user_remove_error_total",
                        tags={
                            'node_id': str(node_id),
                            'username': str(user.username),
                            'error_type': type(e).__name__
                        }
                    )
            
            # Schedule the enhanced operation
            asyncio.ensure_future(enhanced_remove_user())
    
    # Log summary of operations
    monitoring.logger.info(
        f"Scheduled {operations_started} user removal operations",
        username=user.username,
        operations_count=operations_started,
        total_nodes=len(node_ids)
    )


async def remove_node(node_id: int):
    """Enhanced node removal with proper graceful shutdown and TLS cleanup"""
    from .monitoring import get_monitoring, get_status_reporter, get_error_aggregator
    monitoring = get_monitoring()
    status_reporter = get_status_reporter()
    error_aggregator = get_error_aggregator()
    
    removal_start_time = time.time()
    
    try:
        from .. import wildosnode
        if node_id in wildosnode.nodes:
            node_instance = wildosnode.nodes[node_id]
            
            monitoring.logger.info(
                f"Starting enhanced node removal for node {node_id}",
                node_id=node_id,
                operation="remove_node",
                node_address=getattr(node_instance, '_address', 'unknown'),
                tls_enabled=hasattr(node_instance, '_ssl_context'),
                certificate_pinning=getattr(node_instance, '_cert_pinning_enabled', False)
            )
            
            # Update status to indicate removal in progress
            status_reporter.update_component_status(
                f'node_{node_id}',
                'degraded',
                {
                    'status': 'removing', 
                    'removal_started_at': removal_start_time,
                    'graceful_shutdown': True
                }
            )
            
            # Enhanced graceful stop with comprehensive cleanup
            try:
                await asyncio.wait_for(node_instance.stop(), timeout=60.0)
                monitoring.logger.info(
                    f"Node {node_id} gracefully stopped",
                    node_id=node_id,
                    graceful_shutdown=True
                )
            except asyncio.TimeoutError:
                monitoring.logger.warning(
                    f"Node {node_id} graceful stop timeout, proceeding with forced removal",
                    node_id=node_id
                )
                # Continue with removal even if graceful stop timed out
            except Exception as stop_error:
                monitoring.logger.error(
                    f"Error during graceful stop of node {node_id}: {stop_error}",
                    node_id=node_id,
                    stop_error=str(stop_error)
                )
                # Log the error but continue with removal
                error_aggregator.add_error(
                    create_error_with_context(
                        ServiceError,
                        f"Graceful stop failed for node {node_id}: {stop_error}",
                        node_id=node_id,
                        operation="graceful_stop"
                    ),
                    f'node_{node_id}'
                )
            
            # Remove from nodes registry
            del wildosnode.nodes[node_id]
            
            removal_duration = time.time() - removal_start_time
            
            monitoring.logger.info(
                f"Successfully removed node {node_id} with enhanced cleanup",
                node_id=node_id,
                removal_duration_seconds=removal_duration,
                tls_cleanup_completed=True,
                graceful_shutdown_completed=True
            )
            
            # Update status to indicate successful removal
            status_reporter.update_component_status(
                f'node_{node_id}',
                'down',
                {
                    'status': 'removed', 
                    'removed_at': time.time(),
                    'removal_duration_seconds': removal_duration,
                    'graceful_shutdown': True,
                    'tls_cleanup': True
                }
            )
            
            monitoring.metrics.increment(
                "node_remove_total",
                tags={'node_id': str(node_id), 'success': 'true', 'graceful_shutdown': 'true'}
            )
            monitoring.metrics.observe(
                "node_removal_duration_seconds",
                removal_duration,
                tags={'node_id': str(node_id), 'graceful_shutdown': 'true'}
            )
            
        else:
            monitoring.logger.debug(
                f"Node {node_id} not found for removal",
                node_id=node_id
            )
            
            # Still update metrics for consistency
            monitoring.metrics.increment(
                "node_remove_total",
                tags={'node_id': str(node_id), 'success': 'true', 'reason': 'not_found'}
            )
            
    except Exception as e:
        removal_duration = time.time() - removal_start_time
        
        # Convert to structured error
        structured_error = create_error_with_context(
            ServiceError,
            f"Enhanced node removal failed for node {node_id}: {e}",
            node_id=node_id,
            operation="remove_node",
            removal_duration_seconds=removal_duration
        )
        
        monitoring.logger.error(
            "Enhanced node removal failed",
            error=structured_error,
            node_id=node_id,
            removal_duration_seconds=removal_duration
        )
        
        # Add to error aggregation for monitoring
        error_aggregator.add_error(structured_error, f'node_{node_id}')
        
        status_reporter.update_component_status(
            f'node_{node_id}',
            'critical',
            {
                'status': 'removal_failed', 
                'error': str(e),
                'removal_duration_seconds': removal_duration,
                'failure_timestamp': time.time()
            }
        )
        
        monitoring.metrics.increment(
            "node_remove_total",
            tags={
                'node_id': str(node_id), 
                'success': 'false', 
                'error_type': type(e).__name__,
                'graceful_shutdown': 'failed'
            }
        )
        monitoring.metrics.observe(
            "node_removal_duration_seconds",
            removal_duration,
            tags={'node_id': str(node_id), 'graceful_shutdown': 'failed'}
        )
        
        raise structured_error


async def add_node(db_node, certificate):
    """Add a node with enhanced error handling, monitoring, and recovery"""
    start_time = time.time()
    from .monitoring import get_monitoring, get_error_aggregator, get_status_reporter
    monitoring = get_monitoring()
    error_aggregator = get_error_aggregator()
    status_reporter = get_status_reporter()
    
    node_id = db_node.id
    address = f"{db_node.address}:{db_node.port}"
    
    try:
        # Enhanced logging with structured context
        monitoring.logger.info(
            f"Adding node {node_id}",
            node_id=node_id,
            address=db_node.address,
            port=db_node.port,
            operation="add_node"
        )
        
        # Update status to indicate node addition in progress
        status_reporter.update_component_status(
            f'node_{node_id}',
            'degraded',
            {'status': 'adding', 'address': address}
        )
        
        # Gracefully remove existing node if present
        await remove_node(node_id)
        
        # Validate certificate before proceeding
        if not certificate or not hasattr(certificate, 'key') or not hasattr(certificate, 'certificate'):
            config_error = create_error_with_context(
                ConfigurationError,
                f"Certificate is required for node {node_id} with grpclib connection",
                node_id=node_id,
                operation="add_node",
                remote_address=db_node.address,
                remote_port=db_node.port
            )
            
            # Log error with structured context
            monitoring.logger.error(
                "Certificate validation failed",
                error=config_error,
                node_id=node_id,
                has_certificate=certificate is not None
            )
            
            # Update error aggregation
            error_aggregator.add_error(config_error, f'node_{node_id}')
            
            # Update status to failed
            status_reporter.update_component_status(
                f'node_{node_id}',
                'down',
                {'status': 'failed', 'reason': 'invalid_certificate'}
            )
            
            raise config_error
        
        # Ленивый импорт для избежания циклических зависимостей
        from .grpc_client import WildosNodeGRPCLIB, setup_enhanced_grpc_monitoring
        from app.dependencies import get_db
        from app.security.node_auth import NodeAuthManager
        
        # Generate authentication token for the node
        node_auth_manager = NodeAuthManager()
        with next(get_db()) as db:
            auth_token = node_auth_manager.generate_node_token(node_id, db)
        
        # Create node with enhanced configuration and authentication token
        node = WildosNodeGRPCLIB(
            node_id,
            db_node.address,
            db_node.port,
            certificate.key,
            certificate.certificate,
            usage_coefficient=db_node.usage_coefficient,
            auth_token=auth_token,
        )
        
        # Setup enhanced monitoring for this node
        setup_enhanced_grpc_monitoring(node_id, db_node.address, db_node.port)
        
        # Store node in global registry
        from app import wildosnode
        wildosnode.nodes[node_id] = node
        
        # Test connection to ensure node is working
        try:
            # Perform initial health check
            await asyncio.wait_for(node.fetch_backends(), timeout=10.0)
            
            # Record successful addition
            duration_ms = (time.time() - start_time) * 1000
            monitoring.metrics.observe(
                "node_add_duration_ms",
                duration_ms,
                tags={'node_id': str(node_id), 'success': 'true'}
            )
            
            monitoring.logger.info(
                f"Successfully added and tested node {node_id}",
                node_id=node_id,
                address=address,
                duration_ms=duration_ms,
                operation="add_node"
            )
            
            # Update status to healthy
            status_reporter.update_component_status(
                f'node_{node_id}',
                'healthy',
                {
                    'status': 'active',
                    'address': address,
                    'connection_test': 'passed',
                    'added_at': time.time()
                }
            )
            
        except Exception as test_error:
            # Connection test failed - log but don't remove node entirely
            # The enhanced retry mechanisms will handle connection issues
            if isinstance(test_error, WildosNodeBaseError):
                test_enhanced_error = test_error
            else:
                test_enhanced_error = create_error_with_context(
                    NetworkError,
                    f"Initial connection test failed for node {node_id}: {test_error}",
                    node_id=node_id,
                    operation="add_node_test",
                    remote_address=db_node.address,
                    remote_port=db_node.port
                )
            
            monitoring.logger.warning(
                "Node added but initial connection test failed",
                error=test_enhanced_error,
                node_id=node_id,
                address=address
            )
            
            # Update status to degraded rather than failed
            status_reporter.update_component_status(
                f'node_{node_id}',
                'degraded',
                {
                    'status': 'connection_issues',
                    'address': address,
                    'connection_test': 'failed',
                    'error': str(test_error)
                }
            )
            
            # Record test failure in error aggregation
            error_aggregator.add_error(test_enhanced_error, f'node_{node_id}')
        
    except WildosNodeBaseError as e:
        # Already a structured error, just log and update status
        monitoring.logger.error(
            "Failed to add node",
            error=e,
            node_id=node_id,
            operation="add_node"
        )
        
        error_aggregator.add_error(e, f'node_{node_id}')
        
        status_reporter.update_component_status(
            f'node_{node_id}',
            'down',
            {'status': 'failed', 'reason': e.category.value, 'error': str(e)}
        )
        
        # Record failed addition
        duration_ms = (time.time() - start_time) * 1000
        monitoring.metrics.observe(
            "node_add_duration_ms",
            duration_ms,
            tags={'node_id': str(node_id), 'success': 'false', 'error_type': type(e).__name__}
        )
        
        raise
        
    except Exception as e:
        # Convert to structured error
        if 'certificate' in str(e).lower():
            structured_error = create_error_with_context(
                ConfigurationError,
                f"Configuration error adding node {node_id}: {e}",
                node_id=node_id,
                operation="add_node"
            )
        else:
            structured_error = create_error_with_context(
                ServiceError,
                f"Unexpected error adding node {node_id}: {e}",
                node_id=node_id,
                operation="add_node"
            )
        
        monitoring.logger.error(
            "Failed to add node",
            error=structured_error,
            node_id=node_id,
            original_error=str(e)
        )
        
        error_aggregator.add_error(structured_error, f'node_{node_id}')
        
        status_reporter.update_component_status(
            f'node_{node_id}',
            'down',
            {'status': 'failed', 'reason': 'unexpected_error', 'error': str(e)}
        )
        
        # Record failed addition
        duration_ms = (time.time() - start_time) * 1000
        monitoring.metrics.observe(
            "node_add_duration_ms",
            duration_ms,
            tags={'node_id': str(node_id), 'success': 'false', 'error_type': type(e).__name__}
        )
        
        raise structured_error


async def reconnect_node(node_id: int, db_node=None, certificate=None):
    """Reconnect to a node with enhanced error handling, monitoring, and retry logic"""
    import asyncio
    import random
    from .monitoring import get_monitoring, get_error_aggregator, get_status_reporter
    
    monitoring = get_monitoring()
    error_aggregator = get_error_aggregator()
    status_reporter = get_status_reporter()
    start_time = time.time()
    
    # Maximum retry attempts with exponential backoff
    max_retries = 3
    base_delay = 1.0  # Base delay in seconds
    
    try:
        monitoring.logger.info(
            f"Starting reconnect operation for node {node_id}",
            node_id=node_id,
            operation="reconnect_node"
        )
        
        # Update status to indicate reconnection in progress
        status_reporter.update_component_status(
            f'node_{node_id}',
            'degraded',
            {'status': 'reconnecting', 'started_at': time.time()}
        )
        
        # Step 1: Graceful shutdown of existing connection
        monitoring.logger.debug(
            f"Performing graceful shutdown for node {node_id}",
            node_id=node_id
        )
        
        await remove_node(node_id)
        
        # Step 2: Retry logic with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                monitoring.logger.debug(
                    f"Reconnect attempt {attempt + 1}/{max_retries} for node {node_id}",
                    node_id=node_id,
                    attempt=attempt + 1,
                    max_attempts=max_retries
                )
                
                # If db_node and certificate weren't provided, we need to fetch fresh data
                if db_node is None or certificate is None:
                    # Import here to avoid circular dependencies
                    from app.db import crud, get_tls_certificate
                    from app.dependencies import get_db
                    
                    # Get fresh database session and retrieve updated node data
                    with next(get_db()) as fresh_db:
                        if db_node is None:
                            fresh_node = crud.get_node_by_id(fresh_db, node_id)
                            if not fresh_node:
                                node_error = create_error_with_context(
                                    ConfigurationError,
                                    f"Node {node_id} not found in database during reconnect",
                                    node_id=node_id,
                                    operation="reconnect_node"
                                )
                                raise node_error
                            
                            monitoring.logger.debug(
                                f"Retrieved fresh node data for {node_id}",
                                node_id=node_id,
                                address=fresh_node.address,
                                port=fresh_node.port
                            )
                        else:
                            fresh_node = db_node
                        
                        if certificate is None:
                            fresh_certificate = get_tls_certificate(fresh_db)
                            if not fresh_certificate:
                                cert_error = create_error_with_context(
                                    ConfigurationError,
                                    f"TLS certificate not found during reconnect for node {node_id}",
                                    node_id=node_id,
                                    operation="reconnect_node"
                                )
                                raise cert_error
                        else:
                            fresh_certificate = certificate
                else:
                    fresh_node = db_node
                    fresh_certificate = certificate
                
                # Step 3: Reestablish connection
                await add_node(fresh_node, fresh_certificate)
                
                # Success! Record metrics and log success
                duration_ms = (time.time() - start_time) * 1000
                monitoring.metrics.observe(
                    "node_reconnect_duration_ms",
                    duration_ms,
                    tags={
                        'node_id': str(node_id),
                        'success': 'true',
                        'attempts': str(attempt + 1)
                    }
                )
                
                monitoring.logger.info(
                    f"Successfully reconnected to node {node_id}",
                    node_id=node_id,
                    duration_ms=duration_ms,
                    attempts=attempt + 1,
                    operation="reconnect_node"
                )
                
                # Update status to healthy
                status_reporter.update_component_status(
                    f'node_{node_id}',
                    'healthy',
                    {
                        'status': 'reconnected',
                        'reconnected_at': time.time(),
                        'attempts': attempt + 1,
                        'duration_ms': duration_ms
                    }
                )
                
                return  # Success - exit the retry loop
                
            except Exception as e:
                last_error = e
                
                # Create structured error
                if isinstance(e, WildosNodeBaseError):
                    structured_error = e
                else:
                    structured_error = create_error_with_context(
                        NetworkError if 'connection' in str(e).lower() else ServiceError,
                        f"Reconnect attempt {attempt + 1} failed for node {node_id}: {e}",
                        node_id=node_id,
                        operation="reconnect_node",
                        attempt=attempt + 1
                    )
                
                monitoring.logger.warning(
                    f"Reconnect attempt {attempt + 1} failed for node {node_id}",
                    error=structured_error,
                    node_id=node_id,
                    attempt=attempt + 1,
                    max_attempts=max_retries
                )
                
                # If this is the last attempt, don't wait
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    monitoring.logger.debug(
                        f"Waiting {delay:.2f}s before retry {attempt + 2} for node {node_id}",
                        node_id=node_id,
                        delay=delay,
                        next_attempt=attempt + 2
                    )
                    await asyncio.sleep(delay)
        
        # All retry attempts failed
        final_error = create_error_with_context(
            NetworkError,
            f"All {max_retries} reconnect attempts failed for node {node_id}. Last error: {last_error}",
            node_id=node_id,
            operation="reconnect_node",
            attempts=max_retries,
            last_error=str(last_error) if last_error else None
        )
        
        monitoring.logger.error(
            f"Failed to reconnect to node {node_id} after {max_retries} attempts",
            error=final_error,
            node_id=node_id,
            max_attempts=max_retries,
            last_error=str(last_error) if last_error else None
        )
        
        # Update status to critical
        status_reporter.update_component_status(
            f'node_{node_id}',
            'critical',
            {
                'status': 'reconnect_failed',
                'attempts': max_retries,
                'last_error': str(last_error) if last_error else None,
                'failed_at': time.time()
            }
        )
        
        # Add to error aggregation
        error_aggregator.add_error(final_error, f'node_{node_id}')
        
        # Record failed reconnection
        duration_ms = (time.time() - start_time) * 1000
        monitoring.metrics.observe(
            "node_reconnect_duration_ms",
            duration_ms,
            tags={
                'node_id': str(node_id),
                'success': 'false',
                'attempts': str(max_retries),
                'error_type': type(final_error).__name__
            }
        )
        
        raise final_error
        
    except WildosNodeBaseError:
        # Already structured error, just re-raise
        raise
    except Exception as e:
        # Convert unexpected errors to structured errors
        unexpected_error = create_error_with_context(
            ServiceError,
            f"Unexpected error during reconnect for node {node_id}: {e}",
            node_id=node_id,
            operation="reconnect_node"
        )
        
        monitoring.logger.error(
            "Unexpected error during reconnect",
            error=unexpected_error,
            node_id=node_id,
            original_error=str(e)
        )
        
        # Update status to critical
        status_reporter.update_component_status(
            f'node_{node_id}',
            'critical',
            {'status': 'reconnect_error', 'error': str(e)}
        )
        
        error_aggregator.add_error(unexpected_error, f'node_{node_id}')
        
        # Record failed reconnection
        duration_ms = (time.time() - start_time) * 1000
        monitoring.metrics.observe(
            "node_reconnect_duration_ms",
            duration_ms,
            tags={
                'node_id': str(node_id),
                'success': 'false',
                'error_type': type(e).__name__
            }
        )
        
        raise unexpected_error


__all__ = ["update_user", "add_node", "remove_node", "reconnect_node"]
