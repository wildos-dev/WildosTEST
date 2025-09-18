"""
Database maintenance utilities for cleanup and optimization
"""
import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config.env import SQLALCHEMY_DATABASE_URL
from ..utils.system_monitor import disk_monitor
from ..utils.logging_config import database_logger

logger = logging.getLogger(__name__)


class DatabaseMaintenance:
    """Handle database cleanup and optimization operations"""
    
    def __init__(self, db_url: str = SQLALCHEMY_DATABASE_URL):
        self.db_url = db_url
        self.db_path = self._extract_db_path(db_url)
    
    def _extract_db_path(self, db_url: str) -> Optional[str]:
        """Extract database file path from SQLAlchemy URL"""
        if db_url.startswith("sqlite:///"):
            return db_url.replace("sqlite:///", "")
        return None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database size and usage information"""
        info = {
            "exists": False,
            "size_mb": 0,
            "path": self.db_path,
            "last_modified": None,
            "disk_usage": None
        }
        
        try:
            if self.db_path and os.path.exists(self.db_path):
                info["exists"] = True
                
                # Get file size
                size_bytes = os.path.getsize(self.db_path)
                info["size_mb"] = round(size_bytes / (1024 * 1024), 2)
                
                # Get last modified time
                mtime = os.path.getmtime(self.db_path)
                info["last_modified"] = datetime.fromtimestamp(mtime).isoformat()
                
                # Get disk usage for the directory
                is_safe, disk_info = disk_monitor.check_disk_space(os.path.dirname(self.db_path))
                info["disk_usage"] = disk_info
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info["error"] = str(e)
        
        return info
    
    def check_database_health(self) -> Dict[str, Any]:
        """Perform database health checks"""
        health = {
            "healthy": True,
            "issues": [],
            "recommendations": [],
            "info": self.get_database_info()
        }
        
        try:
            db_info = health["info"]
            
            # Check if database exists
            if not db_info["exists"]:
                health["healthy"] = False
                health["issues"].append("Database file does not exist")
                return health
            
            # Check database size
            if db_info["size_mb"] > 100:
                health["issues"].append(f"Large database size: {db_info['size_mb']}MB")
                health["recommendations"].append("Consider database cleanup")
            
            # Check disk space
            if db_info["disk_usage"]:
                usage_percent = db_info["disk_usage"].get("usage_percent", 0)
                if usage_percent > 90:
                    health["healthy"] = False
                    health["issues"].append(f"Critical disk usage: {usage_percent}%")
                elif usage_percent > 80:
                    health["issues"].append(f"High disk usage: {usage_percent}%")
                    health["recommendations"].append("Monitor disk space closely")
            
            # Test database connection
            if self.db_path:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    conn.close()
                except Exception as e:
                    health["healthy"] = False
                    health["issues"].append(f"Database connection failed: {str(e)}")
            
        except Exception as e:
            health["healthy"] = False
            health["issues"].append(f"Health check failed: {str(e)}")
        
        return health
    
    def cleanup_old_records(
        self, 
        db_session: Session, 
        days_to_keep: int = 30,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Clean up old database records"""
        
        # Check disk space before cleanup
        if not disk_monitor.ensure_disk_space():
            raise RuntimeError("Cannot perform cleanup: insufficient disk space")
        
        cleanup_results = {
            "dry_run": dry_run,
            "tables_cleaned": [],
            "records_removed": 0,
            "space_freed_mb": 0
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Define tables and their timestamp columns to clean
            tables_to_clean = [
                ("user_usage_logs", "created_time"),
                ("notification_reports", "created_at"),
                ("backend_logs", "timestamp"),
                # Add more tables as needed
            ]
            
            initial_size = self.get_database_info()["size_mb"]
            
            for table_name, timestamp_column in tables_to_clean:
                try:
                    # Count records to be deleted
                    count_query = text(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE {timestamp_column} < :cutoff_date
                    """)
                    
                    result = db_session.execute(count_query, {"cutoff_date": cutoff_date})
                    count = result.scalar()
                    
                    if count > 0:
                        if not dry_run:
                            # Delete old records
                            delete_query = text(f"""
                                DELETE FROM {table_name} 
                                WHERE {timestamp_column} < :cutoff_date
                            """)
                            db_session.execute(delete_query, {"cutoff_date": cutoff_date})
                            db_session.commit()
                        
                        cleanup_results["tables_cleaned"].append({
                            "table": table_name,
                            "records_to_remove": count
                        })
                        cleanup_results["records_removed"] += count
                        
                        database_logger.info(
                            f"{'Would remove' if dry_run else 'Removed'} {count} old records from {table_name}"
                        )
                
                except Exception as e:
                    database_logger.error(f"Error cleaning table {table_name}: {e}")
                    db_session.rollback()
            
            # Vacuum database to reclaim space (only if not dry run)
            if not dry_run and cleanup_results["records_removed"] > 0:
                self.vacuum_database()
                
                # Calculate space freed
                final_size = self.get_database_info()["size_mb"]
                cleanup_results["space_freed_mb"] = round(initial_size - final_size, 2)
            
        except Exception as e:
            database_logger.error(f"Database cleanup failed: {e}")
            db_session.rollback()
            raise
        
        return cleanup_results
    
    def vacuum_database(self) -> bool:
        """Vacuum SQLite database to reclaim space"""
        if not self.db_path:
            logger.warning("Cannot vacuum: database path not available")
            return False
        
        try:
            database_logger.info("Starting database VACUUM operation")
            
            # Check disk space before vacuum (vacuum needs temporary space)
            is_safe, disk_info = disk_monitor.check_disk_space()
            if not is_safe:
                raise RuntimeError(f"Cannot vacuum: insufficient disk space ({disk_info.get('usage_percent', 'unknown')}% used)")
            
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            
            database_logger.info("Database VACUUM completed successfully")
            return True
            
        except Exception as e:
            database_logger.error(f"Database vacuum failed: {e}")
            return False
    
    def optimize_database(self) -> Dict[str, Any]:
        """Perform comprehensive database optimization"""
        optimization_results = {
            "success": True,
            "operations": [],
            "errors": []
        }
        
        try:
            # Check database health first
            health = self.check_database_health()
            if not health["healthy"]:
                optimization_results["errors"].extend(health["issues"])
            
            # Vacuum database
            if self.vacuum_database():
                optimization_results["operations"].append("Database vacuumed")
            else:
                optimization_results["errors"].append("Failed to vacuum database")
            
            # Update statistics (SQLite specific)
            if self.db_path:
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.execute("ANALYZE")
                    conn.close()
                    optimization_results["operations"].append("Database statistics updated")
                except Exception as e:
                    optimization_results["errors"].append(f"Failed to update statistics: {e}")
            
        except Exception as e:
            optimization_results["success"] = False
            optimization_results["errors"].append(f"Optimization failed: {e}")
        
        return optimization_results


# Global database maintenance instance
db_maintenance = DatabaseMaintenance()


def scheduled_database_cleanup(db_session: Session, days_to_keep: int = 30):
    """
    Scheduled function to run database cleanup
    Should be called periodically (e.g., daily) by task scheduler
    """
    try:
        database_logger.info("Starting scheduled database cleanup")
        
        # Perform health check first
        health = db_maintenance.check_database_health()
        if not health["healthy"]:
            database_logger.warning(f"Database health issues detected: {health['issues']}")
        
        # Run cleanup
        results = db_maintenance.cleanup_old_records(db_session, days_to_keep)
        
        if results["records_removed"] > 0:
            database_logger.info(
                f"Cleanup completed: removed {results['records_removed']} records, "
                f"freed {results['space_freed_mb']}MB"
            )
        else:
            database_logger.info("No old records found to clean up")
        
        # Optimize database if significant cleanup was done
        if results["records_removed"] > 1000:
            optimization = db_maintenance.optimize_database()
            if optimization["success"]:
                database_logger.info("Database optimization completed")
            else:
                database_logger.warning(f"Database optimization issues: {optimization['errors']}")
    
    except Exception as e:
        database_logger.error(f"Scheduled database cleanup failed: {e}")


__all__ = [
    "DatabaseMaintenance",
    "db_maintenance", 
    "scheduled_database_cleanup"
]