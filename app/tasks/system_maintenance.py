"""
System maintenance tasks for database cleanup and monitoring
"""
import asyncio
import logging
from datetime import datetime, timedelta

from ..db import GetDB
from ..db.maintenance import scheduled_database_cleanup, db_maintenance
from ..utils.system_monitor import ResourceMonitor
from ..utils.logging_config import system_monitor_logger, setup_application_logging
from ..config.monitoring import (
    DB_CLEANUP_INTERVAL_HOURS,
    DB_CLEANUP_DAYS_TO_KEEP,
    RESOURCE_CHECK_INTERVAL
)

logger = logging.getLogger(__name__)


class SystemMaintenanceScheduler:
    """Schedule and manage system maintenance tasks"""
    
    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.cleanup_running = False
        self.monitor_running = False
    
    async def start_maintenance_tasks(self):
        """Start all maintenance tasks"""
        system_monitor_logger.info("Starting system maintenance scheduler")
        
        # Set up application logging
        setup_application_logging()
        
        # Start periodic tasks
        tasks = [
            asyncio.create_task(self._periodic_database_cleanup()),
            asyncio.create_task(self._periodic_resource_monitoring()),
            asyncio.create_task(self._periodic_health_checks())
        ]
        
        system_monitor_logger.info("All maintenance tasks started")
        
        # Wait for all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _periodic_database_cleanup(self):
        """Run database cleanup periodically"""
        interval_seconds = DB_CLEANUP_INTERVAL_HOURS * 3600
        
        while True:
            try:
                if not self.cleanup_running:
                    self.cleanup_running = True
                    
                    system_monitor_logger.info("Starting periodic database cleanup")
                    
                    with GetDB() as db:
                        scheduled_database_cleanup(db, DB_CLEANUP_DAYS_TO_KEEP)
                    
                    self.cleanup_running = False
                    system_monitor_logger.info("Periodic database cleanup completed")
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                self.cleanup_running = False
                system_monitor_logger.error(f"Error in periodic database cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _periodic_resource_monitoring(self):
        """Run resource monitoring periodically"""
        try:
            await self.resource_monitor.periodic_check(RESOURCE_CHECK_INTERVAL)
        except Exception as e:
            system_monitor_logger.error(f"Error in resource monitoring: {e}")
    
    async def _periodic_health_checks(self):
        """Run system health checks"""
        while True:
            try:
                if not self.monitor_running:
                    self.monitor_running = True
                    
                    # Check database health
                    health = db_maintenance.check_database_health()
                    
                    if not health["healthy"]:
                        system_monitor_logger.warning(
                            f"Database health issues detected: {health['issues']}"
                        )
                        
                        # Auto-optimize if needed
                        if any("Large database" in issue for issue in health["issues"]):
                            system_monitor_logger.info("Running database optimization due to size")
                            optimization = db_maintenance.optimize_database()
                            
                            if optimization["success"]:
                                system_monitor_logger.info("Database optimization completed")
                            else:
                                system_monitor_logger.error(f"Database optimization failed: {optimization['errors']}")
                    
                    self.monitor_running = False
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.monitor_running = False
                system_monitor_logger.error(f"Error in health checks: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry


# Global maintenance scheduler
maintenance_scheduler = SystemMaintenanceScheduler()


async def start_system_maintenance():
    """Start system maintenance tasks - call this from app startup"""
    try:
        system_monitor_logger.info("Initializing system maintenance")
        await maintenance_scheduler.start_maintenance_tasks()
    except Exception as e:
        system_monitor_logger.error(f"Failed to start system maintenance: {e}")


def emergency_database_cleanup():
    """Emergency database cleanup for critical disk space situations"""
    try:
        system_monitor_logger.warning("Running emergency database cleanup")
        
        with GetDB() as db:
            # More aggressive cleanup for emergency situations
            results = scheduled_database_cleanup(db, days_to_keep=7)  # Keep only 7 days
            
        # Force database optimization
        optimization = db_maintenance.optimize_database()
        
        system_monitor_logger.info(
            f"Emergency cleanup completed: {results.get('records_removed', 0)} records removed"
        )
        
        return True
        
    except Exception as e:
        system_monitor_logger.error(f"Emergency cleanup failed: {e}")
        return False


__all__ = [
    "SystemMaintenanceScheduler",
    "maintenance_scheduler",
    "start_system_maintenance", 
    "emergency_database_cleanup"
]