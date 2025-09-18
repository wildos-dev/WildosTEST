"""
System monitoring utilities for disk space and resource management
"""
import shutil
import logging
import asyncio
from typing import Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DiskSpaceMonitor:
    """Monitor disk space and prevent operations when disk is full"""
    
    def __init__(self, min_free_gb: float = 1.0, warning_threshold: int = 85):
        self.min_free_gb = min_free_gb
        self.warning_threshold = warning_threshold
    
    def check_disk_space(self, path: str = "/") -> Tuple[bool, dict]:
        """
        Check available disk space
        
        Returns:
            Tuple[bool, dict]: (is_safe, disk_info)
        """
        try:
            total, used, free = shutil.disk_usage(path)
            
            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100
            
            disk_info = {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "usage_percent": round(usage_percent, 1),
                "path": path,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if it's safe to proceed
            is_safe = free_gb >= self.min_free_gb and usage_percent < 95
            
            if usage_percent > self.warning_threshold:
                logger.warning(
                    f"High disk usage: {usage_percent:.1f}% used, "
                    f"{free_gb:.2f}GB free on {path}"
                )
            
            if not is_safe:
                logger.error(
                    f"Critical disk space: {free_gb:.2f}GB free, "
                    f"{usage_percent:.1f}% used on {path}"
                )
            
            return is_safe, disk_info
            
        except Exception as e:
            logger.error(f"Error checking disk space for {path}: {e}")
            return False, {"error": str(e), "path": path}
    
    def ensure_disk_space(self, path: str = "/") -> bool:
        """
        Ensure sufficient disk space, raise exception if not available
        
        Raises:
            RuntimeError: If insufficient disk space
        """
        is_safe, disk_info = self.check_disk_space(path)
        
        if not is_safe:
            if "error" in disk_info:
                raise RuntimeError(f"Cannot check disk space: {disk_info['error']}")
            else:
                raise RuntimeError(
                    f"Insufficient disk space: {disk_info['free_gb']:.2f}GB free, "
                    f"{disk_info['usage_percent']:.1f}% used. "
                    f"Minimum required: {self.min_free_gb}GB free"
                )
        
        return True


class ResourceMonitor:
    """Monitor system resources and log status"""
    
    def __init__(self):
        self.disk_monitor = DiskSpaceMonitor()
    
    async def periodic_check(self, interval_seconds: int = 300):
        """Run periodic system checks"""
        logger.info(f"Starting periodic resource monitoring every {interval_seconds}s")
        
        while True:
            try:
                # Check disk space
                is_safe, disk_info = self.disk_monitor.check_disk_space()
                
                if is_safe:
                    logger.info(
                        f"System healthy: {disk_info['usage_percent']:.1f}% disk used, "
                        f"{disk_info['free_gb']:.2f}GB free"
                    )
                else:
                    logger.error(
                        f"System at risk: {disk_info['usage_percent']:.1f}% disk used, "
                        f"{disk_info['free_gb']:.2f}GB free"
                    )
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in periodic resource check: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error


# Global disk monitor instance
disk_monitor = DiskSpaceMonitor()


def check_disk_space_before_operation(path: str = "/"):
    """
    Decorator to check disk space before executing database operations
    
    Usage:
        @check_disk_space_before_operation()
        def my_database_function():
            # Your database operation here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            disk_monitor.ensure_disk_space(path)
            return func(*args, **kwargs)
        return wrapper
    return decorator


async def check_disk_space_async(path: str = "/") -> Tuple[bool, dict]:
    """Async version of disk space check"""
    return disk_monitor.check_disk_space(path)


__all__ = [
    "DiskSpaceMonitor",
    "ResourceMonitor", 
    "disk_monitor",
    "check_disk_space_before_operation",
    "check_disk_space_async"
]