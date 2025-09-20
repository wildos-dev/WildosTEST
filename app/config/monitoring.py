"""
Configuration for system monitoring and resource management
"""
from decouple import config

# Disk monitoring configuration
DISK_USAGE_THRESHOLD = config("DISK_USAGE_THRESHOLD", default=85, cast=int)
DISK_USAGE_CRITICAL = config("DISK_USAGE_CRITICAL", default=95, cast=int)
MIN_FREE_DISK_GB = config("MIN_FREE_DISK_GB", default=1.0, cast=float)

# Node connection configuration  
NODE_CONNECTION_RETRIES = config("NODE_CONNECTION_RETRIES", default=5, cast=int)
NODE_CONNECTION_TIMEOUT = config("NODE_CONNECTION_TIMEOUT", default=15, cast=int)
NODE_RETRY_DELAY = config("NODE_RETRY_DELAY", default=10, cast=int)

# Database maintenance configuration
DB_CLEANUP_DAYS_TO_KEEP = config("DB_CLEANUP_DAYS_TO_KEEP", default=30, cast=int)
DB_CLEANUP_INTERVAL_HOURS = config("DB_CLEANUP_INTERVAL_HOURS", default=24, cast=int)
DB_MAX_SIZE_MB = config("DB_MAX_SIZE_MB", default=100, cast=int)

# Logging configuration
LOG_ROTATION_MAX_BYTES = config("LOG_ROTATION_MAX_BYTES", default=10485760, cast=int)  # 10MB
LOG_ROTATION_BACKUP_COUNT = config("LOG_ROTATION_BACKUP_COUNT", default=5, cast=int)
LOG_CLEANUP_DAYS = config("LOG_CLEANUP_DAYS", default=30, cast=int)

# Resource monitoring intervals
RESOURCE_CHECK_INTERVAL = config("RESOURCE_CHECK_INTERVAL", default=300, cast=int)  # 5 minutes
DISK_CHECK_INTERVAL = config("DISK_CHECK_INTERVAL", default=3600, cast=int)  # 1 hour

# Performance monitoring
ENABLE_PERFORMANCE_MONITORING = config("ENABLE_PERFORMANCE_MONITORING", default=True, cast=bool)
PERFORMANCE_LOG_INTERVAL = config("PERFORMANCE_LOG_INTERVAL", default=600, cast=int)  # 10 minutes

__all__ = [
    "DISK_USAGE_THRESHOLD",
    "DISK_USAGE_CRITICAL", 
    "MIN_FREE_DISK_GB",
    "NODE_CONNECTION_RETRIES",
    "NODE_CONNECTION_TIMEOUT",
    "NODE_RETRY_DELAY",
    "DB_CLEANUP_DAYS_TO_KEEP",
    "DB_CLEANUP_INTERVAL_HOURS",
    "DB_MAX_SIZE_MB",
    "LOG_ROTATION_MAX_BYTES",
    "LOG_ROTATION_BACKUP_COUNT",
    "LOG_CLEANUP_DAYS",
    "RESOURCE_CHECK_INTERVAL",
    "DISK_CHECK_INTERVAL",
    "ENABLE_PERFORMANCE_MONITORING",
    "PERFORMANCE_LOG_INTERVAL"
]