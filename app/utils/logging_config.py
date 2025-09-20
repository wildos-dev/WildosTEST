"""
Improved logging configuration with rotation and monitoring
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


class RotatingSystemLogger:
    """Configure rotating logs to prevent disk space issues"""
    
    def __init__(
        self,
        log_dir: str = "/var/lib/wildosvpn/logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.log_dir = Path(log_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Directory will be created when first logger is set up
        self._dir_created = False
    
    def _ensure_log_directory(self):
        """Ensure log directory exists (called lazily)"""
        if not self._dir_created:
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                self._dir_created = True
            except (OSError, PermissionError):
                # If we can't create the directory, fall back to console logging
                self._dir_created = False
    
    def setup_logger(
        self,
        name: str,
        level: int = logging.INFO,
        filename: str | None = None
    ) -> logging.Logger:
        """
        Set up a rotating file logger
        
        Args:
            name: Logger name
            level: Logging level
            filename: Log filename (defaults to {name}.log)
        
        Returns:
            Configured logger instance
        """
        if filename is None:
            filename = f"{name}.log"
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for existing_handler in logger.handlers[:]:
            logger.removeHandler(existing_handler)
        
        # Try to create file handler, fall back to console if fails
        try:
            self._ensure_log_directory()
            if self._dir_created:
                log_file = self.log_dir / filename
                
                # Create rotating handler
                handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count
                )
                
                # Set format
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(name)s: %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        
        except (OSError, PermissionError):
            # File logging failed, just use console
            pass
        
        # Always add console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING if level > logging.WARNING else level)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove log files older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    print(f"Removed old log file: {log_file}")
                    
        except Exception as e:
            print(f"Error cleaning old logs: {e}")


# Global logger instances
system_logger_manager = RotatingSystemLogger()

# Specific loggers for different components
system_monitor_logger = system_logger_manager.setup_logger(
    "system_monitor", logging.INFO, "system_monitor.log"
)

node_connection_logger = system_logger_manager.setup_logger(
    "node_connections", logging.INFO, "node_connections.log"
)

database_logger = system_logger_manager.setup_logger(
    "database_operations", logging.WARNING, "database_operations.log"
)

grpc_logger = system_logger_manager.setup_logger(
    "grpc_connections", logging.INFO, "grpc_connections.log"
)


def setup_application_logging():
    """Set up improved logging for the entire application"""
    
    # Set up periodic log cleanup
    try:
        system_logger_manager.cleanup_old_logs()
    except Exception as e:
        print(f"Warning: Could not clean old logs: {e}")
    
    # Log startup message
    system_monitor_logger.info("Application logging system initialized")
    
    return {
        "system_monitor": system_monitor_logger,
        "node_connections": node_connection_logger,
        "database": database_logger,
        "grpc": grpc_logger
    }


__all__ = [
    "RotatingSystemLogger",
    "system_logger_manager",
    "system_monitor_logger",
    "node_connection_logger", 
    "database_logger",
    "grpc_logger",
    "setup_application_logging"
]