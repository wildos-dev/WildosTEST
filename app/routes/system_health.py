"""
System health and monitoring endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..dependencies import SudoAdminDep, DBDep
from ..exceptions import ServerError, ServiceUnavailableError, APIError
from ..utils.system_monitor import disk_monitor
from ..db.maintenance import db_maintenance, scheduled_database_cleanup
from ..utils.logging_config import system_monitor_logger
from .. import __version__

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/version")
async def get_version():
    """Get application version information"""
    return {
        "version": __version__,
        "name": "WildosVPN API",
        "description": "Unified GUI Censorship Resistant Solution Powered by Xray"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for load balancers and orchestrators"""
    try:
        # Basic readiness checks
        is_safe, disk_info = disk_monitor.check_disk_space()
        db_health = db_maintenance.check_database_health()
        
        # Simple pass/fail readiness logic
        ready = is_safe and db_health["healthy"]
        
        if ready:
            return {
                "status": "ready",
                "message": "Service is ready to accept traffic"
            }
        else:
            # Return 503 Service Unavailable if not ready
            raise ServiceUnavailableError(
                f"Service is not ready - disk_safe: {is_safe}, db_healthy: {db_health['healthy']}",
                "SERVICE_NOT_READY"
            )
    except APIError:
        # Re-raise APIError to preserve original error code and semantics
        raise
    except Exception as e:
        raise ServiceUnavailableError(
            f"Readiness check failed: {str(e)}",
            "READINESS_CHECK_FAILED"
        )


@router.get("/health")
async def system_health():
    """Get basic system health status"""
    try:
        is_safe, disk_info = disk_monitor.check_disk_space()
        db_health = db_maintenance.check_database_health()
        
        return {
            "status": "healthy" if is_safe and db_health["healthy"] else "warning",
            "disk": {
                "safe": is_safe,
                "details": {
                    "usage_percent": disk_info.get("usage_percent", 0),
                    "free_gb": disk_info.get("free_gb", 0),
                    "total_gb": disk_info.get("total_gb", 0),
                    "timestamp": disk_info.get("timestamp")
                }
            },
            "database": {
                "healthy": db_health["healthy"],
                "info": {
                    "size_mb": db_health["info"].get("size_mb", 0),
                    "last_modified": db_health["info"].get("last_modified")
                },
                "issues": db_health.get("issues", [])
            },
            "timestamp": disk_info.get("timestamp")
        }
    except Exception as e:
        raise ServerError(
            f"Health check failed: {str(e)}",
            "HEALTH_CHECK_ERROR"
        )


@router.get("/disk-info")
async def disk_info(_: SudoAdminDep):
    """Get detailed disk space information"""
    try:
        is_safe, disk_info = disk_monitor.check_disk_space()
        return {
            "safe": is_safe,
            "details": disk_info
        }
    except Exception as e:
        raise ServerError(
            f"Failed to get disk info: {str(e)}",
            "DISK_INFO_ERROR"
        )


@router.get("/database-health")
async def database_health(_: SudoAdminDep):
    """Get detailed database health information"""
    try:
        health = db_maintenance.check_database_health()
        return health
    except Exception as e:
        raise ServerError(
            f"Failed to check database health: {str(e)}",
            "DATABASE_HEALTH_ERROR"
        )


@router.post("/database-cleanup")
async def database_cleanup(db: DBDep, _: SudoAdminDep, days_to_keep: int = 30, dry_run: bool = False):
    """Manually trigger database cleanup"""
    try:
        system_monitor_logger.info(f"Manual database cleanup triggered (dry_run={dry_run}, days_to_keep={days_to_keep})")
        
        results = db_maintenance.cleanup_old_records(db, days_to_keep, dry_run)
        
        return {
            "success": True,
            "cleanup_results": results
        }
    except Exception as e:
        system_monitor_logger.error(f"Manual database cleanup failed: {e}")
        raise ServerError(
            f"Database cleanup failed: {str(e)}",
            "DATABASE_CLEANUP_ERROR"
        )


@router.post("/database-optimize")
async def database_optimize(_: SudoAdminDep):
    """Manually trigger database optimization"""
    try:
        system_monitor_logger.info("Manual database optimization triggered")
        
        results = db_maintenance.optimize_database()
        
        return {
            "success": results["success"],
            "optimization_results": results
        }
    except Exception as e:
        system_monitor_logger.error(f"Manual database optimization failed: {e}")
        raise ServerError(
            f"Database optimization failed: {str(e)}",
            "DATABASE_OPTIMIZATION_ERROR"
        )


@router.get("/monitoring-status")
async def monitoring_status(_: SudoAdminDep):
    """Get status of monitoring systems"""
    try:
        # Check if monitoring tasks are running
        disk_is_safe, disk_info = disk_monitor.check_disk_space()
        db_health = db_maintenance.check_database_health()
        
        return {
            "disk_monitoring": {
                "active": True,
                "last_check": disk_info.get("timestamp"),
                "status": "safe" if disk_is_safe else "warning"
            },
            "database_monitoring": {
                "active": True,
                "status": "healthy" if db_health["healthy"] else "issues_detected",
                "last_check": db_health["info"].get("last_modified")
            },
            "system_status": {
                "overall": "healthy" if disk_is_safe and db_health["healthy"] else "needs_attention"
            }
        }
    except Exception as e:
        raise ServerError(
            f"Failed to get monitoring status: {str(e)}",
            "MONITORING_STATUS_ERROR"
        )


__all__ = ["router"]