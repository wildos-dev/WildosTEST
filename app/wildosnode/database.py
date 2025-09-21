# Ленивые импорты для избежания проблем с PYTHONPATH в контейнере
from typing import TYPE_CHECKING, Dict, List, Any
import time

# Enhanced error handling and monitoring imports
from .exceptions import (
    WildosNodeBaseError, ServiceError, ConfigurationError,
    create_error_with_context
)
# Monitoring imports moved inside methods to avoid circular dependencies

if TYPE_CHECKING:
    from app.models.node import NodeStatus


class WildosNodeDB:
    """
    Enhanced mixin class for working with node database operations.
    Requires presence of id attribute. Includes structured error handling and monitoring.
    """
    id: int  # Устанавливается в дочернем классе WildosNodeGRPCLIB
    
    def _get_monitoring(self):
        """Get monitoring system for database operations"""
        from .monitoring import get_monitoring
        return get_monitoring()
    
    def _get_error_aggregator(self):
        """Get error aggregator for database operations"""
        from .monitoring import get_error_aggregator
        return get_error_aggregator()
    
    def list_users(self):
        """List users with enhanced error handling"""
        monitoring = self._get_monitoring()
        try:
            monitoring.logger.debug(f"Listing users for node {self.id}", node_id=self.id)
            
            from app.db import crud, GetDB
            with GetDB() as db:
                relations = crud.get_node_users(db, self.id)
                users = dict()
                for rel in relations:
                    if not users.get(rel[0]):
                        users[rel[0]] = dict(
                            username=rel[1], id=rel[0], key=rel[2], inbounds=[]
                        )
                    users[rel[0]]["inbounds"].append(rel[3].tag)
                
                result = list(users.values())
                monitoring.metrics.increment("db_list_users_success_total", tags={'node_id': str(self.id)})
                return result
                
        except Exception as e:
            error = create_error_with_context(
                ServiceError, f"Database error listing users for node {self.id}: {e}",
                node_id=self.id, operation="list_users"
            )
            monitoring.logger.error("Database error", error=error, node_id=self.id)
            self._get_error_aggregator().add_error(error, f'node_db_{self.id}')
            monitoring.metrics.increment("db_list_users_error_total", tags={'node_id': str(self.id)})
            raise error

    def store_backends(self, backends):
        """Store backends with enhanced error handling"""
        monitoring = self._get_monitoring()
        backend_count = len(backends) if backends else 0
        
        try:
            monitoring.logger.debug(
                f"Storing {backend_count} backends for node {self.id}",
                node_id=self.id, backend_count=backend_count
            )
            
            inbounds = [
                inbound for backend in backends for inbound in backend.inbounds
            ]
            
            from app.db import crud, GetDB
            with GetDB() as db:
                crud.ensure_node_backends(db, backends, self.id)
                crud.ensure_node_inbounds(db, inbounds, self.id)
            
            monitoring.metrics.increment("db_store_backends_success_total", tags={'node_id': str(self.id)})
            
        except Exception as e:
            error = create_error_with_context(
                ServiceError, f"Database error storing backends for node {self.id}: {e}",
                node_id=self.id, operation="store_backends", backend_count=backend_count
            )
            monitoring.logger.error("Database error", error=error, node_id=self.id)
            self._get_error_aggregator().add_error(error, f'node_db_{self.id}')
            monitoring.metrics.increment("db_store_backends_error_total", tags={'node_id': str(self.id)})
            raise error

    def set_status(self, status: "NodeStatus", message: str | None = None):
        """Set node status with enhanced error handling"""
        monitoring = self._get_monitoring()
        status_str = str(status) if status else "unknown"
        
        try:
            monitoring.logger.debug(
                f"Setting status {status_str} for node {self.id}",
                node_id=self.id, status=status_str, status_message=message
            )
            
            from app.db import crud, GetDB
            with GetDB() as db:
                crud.update_node_status(db, self.id, status, message or "")
            
            monitoring.metrics.increment("db_set_status_success_total", tags={'node_id': str(self.id), 'status': status_str})
            
            # Update status in monitoring system
            from .monitoring import get_status_reporter
            get_status_reporter().update_component_status(
                f'node_db_{self.id}',
                'healthy' if 'online' in status_str.lower() else 'degraded',
                {'database_status': status_str, 'message': message, 'last_updated': time.time()}
            )
            
        except Exception as e:
            error = create_error_with_context(
                ServiceError, f"Database error setting status for node {self.id}: {e}",
                node_id=self.id, operation="set_status", target_status=status_str
            )
            monitoring.logger.error("Database error", error=error, node_id=self.id)
            self._get_error_aggregator().add_error(error, f'node_db_{self.id}')
            monitoring.metrics.increment("db_set_status_error_total", tags={'node_id': str(self.id)})
            raise error
