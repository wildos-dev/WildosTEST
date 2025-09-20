"""
Middleware for disk space monitoring and early warning
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.system_monitor import disk_monitor
from ..utils.logging_config import system_monitor_logger
from ..tasks.system_maintenance import emergency_database_cleanup

logger = logging.getLogger(__name__)


class DiskSpaceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check disk space before processing requests
    Prevents operations when disk space is critically low
    """
    
    def __init__(self, app, critical_threshold: int = 95, warning_threshold: int = 85):
        super().__init__(app)
        self.critical_threshold = critical_threshold
        self.warning_threshold = warning_threshold
        self.emergency_cleanup_running = False
    
    async def dispatch(self, request: Request, call_next):
        # Skip monitoring for health checks and static files
        if request.url.path in ["/health", "/api/health"] or request.url.path.startswith("/static"):
            return await call_next(request)
        
        try:
            # Check disk space
            is_safe, disk_info = disk_monitor.check_disk_space()
            
            # If there was an error checking disk space, allow the request to proceed
            if "error" in disk_info:
                logger.warning(f"Disk space check failed: {disk_info['error']}")
                return await call_next(request)
                
            usage_percent = disk_info.get("usage_percent", 0)
            
            # Critical disk space - block all write operations
            if usage_percent >= self.critical_threshold:
                # Try emergency cleanup if not already running
                if not self.emergency_cleanup_running and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                    self.emergency_cleanup_running = True
                    try:
                        system_monitor_logger.warning("Running emergency cleanup due to critical disk space")
                        emergency_database_cleanup()
                    finally:
                        self.emergency_cleanup_running = False
                
                # Block write operations
                if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                    return JSONResponse(
                        status_code=507,  # Insufficient Storage
                        content={
                            "error": "Insufficient disk space",
                            "message": f"Disk usage at {usage_percent}%. Write operations are temporarily disabled.",
                            "disk_usage_percent": usage_percent,
                            "available_gb": disk_info.get("free_gb", 0)
                        }
                    )
            
            # Warning threshold - add headers but allow operation
            elif usage_percent >= self.warning_threshold:
                response = await call_next(request)
                response.headers["X-Disk-Warning"] = f"High disk usage: {usage_percent}%"
                response.headers["X-Disk-Available-GB"] = str(disk_info.get("free_gb", 0))
                return response
            
            # Normal operation
            return await call_next(request)
            
        except Exception as e:
            # Log error but don't block the request
            logger.error(f"Error in disk space middleware: {e}")
            return await call_next(request)


def add_disk_monitoring_headers(response, disk_info):
    """Add disk monitoring information to response headers"""
    if disk_info:
        response.headers["X-Disk-Usage-Percent"] = str(disk_info.get("usage_percent", 0))
        response.headers["X-Disk-Available-GB"] = str(disk_info.get("free_gb", 0))
        response.headers["X-Disk-Total-GB"] = str(disk_info.get("total_gb", 0))


__all__ = ["DiskSpaceMiddleware"]