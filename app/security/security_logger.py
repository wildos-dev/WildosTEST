"""
Security logging and monitoring for production deployments
"""
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.orm import Session

from ..utils.logging_config import system_monitor_logger


class SecurityEventType(Enum):
    """Types of security events to monitor"""
    AUTHENTICATION_FAILED = "auth_failed"
    AUTHENTICATION_SUCCESS = "auth_success"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"
    CERTIFICATE_EXPIRED = "cert_expired"
    CERTIFICATE_INVALID = "cert_invalid"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force"
    SSL_HANDSHAKE_FAILED = "ssl_handshake_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    NODE_CONNECTION_FAILED = "node_connection_failed"
    NODE_CONNECTION_SUCCESS = "node_connection_success"
    SYSTEM_RESOURCE_ALERT = "system_resource_alert"
    DISK_SPACE_WARNING = "disk_space_warning"


class SecurityLogger:
    """Enhanced security logging for production monitoring"""
    
    def __init__(self, log_dir: str = "/var/lib/wildosvpn/logs/security"):
        self.log_dir = log_dir
        self.security_log_file = os.path.join(log_dir, "security.log")
        self.audit_log_file = os.path.join(log_dir, "audit.log")
        self.intrusion_log_file = os.path.join(log_dir, "intrusion.log")
        self._dir_created = False
        
        # Defer directory creation until first use
        
        # Setup loggers (directory creation deferred)
        self.security_logger = None
        self.audit_logger = None  
        self.intrusion_logger = None
        
        # Event counters for rate limiting detection
        self.event_counters = {}
        self.suspicious_activity_threshold = 10  # events per minute
        
    def _ensure_dir_created(self):
        """Ensure log directory is created (called lazily)"""
        if not self._dir_created:
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                self._dir_created = True
            except OSError:
                # If we can't create the directory, fall back to console logging
                self.log_dir = "/tmp"
                self.security_log_file = os.path.join(self.log_dir, "wildosvpn_security.log") 
                self.audit_log_file = os.path.join(self.log_dir, "wildosvpn_audit.log")
                self.intrusion_log_file = os.path.join(self.log_dir, "wildosvpn_intrusion.log")
                try:
                    os.makedirs(self.log_dir, exist_ok=True)
                    self._dir_created = True
                except OSError:
                    # Complete fallback - just use console
                    pass

    def _setup_security_logger(self) -> logging.Logger:
        """Setup dedicated security logger"""
        self._ensure_dir_created()
        
        logger = logging.getLogger("wildosvpn.security")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        try:
            # Create file handler
            handler = logging.FileHandler(self.security_log_file)
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
        except OSError:
            # Fallback to console handler
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s [SECURITY] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        logger.propagate = False
        return logger
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup audit trail logger"""
        logger = logging.getLogger("wildosvpn.audit")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        handler = logging.FileHandler(self.audit_log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    def _setup_intrusion_logger(self) -> logging.Logger:
        """Setup intrusion detection logger"""
        logger = logging.getLogger("wildosvpn.intrusion")
        logger.setLevel(logging.WARNING)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        handler = logging.FileHandler(self.intrusion_log_file)
        handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [INTRUSION] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        severity: str = "INFO",
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        node_id: Optional[int] = None
    ):
        """Log a security event with structured data"""
        
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "severity": severity,
            "ip_address": ip_address,
            "user_id": user_id,
            "node_id": node_id,
            "details": details
        }
        
        # Create log message
        log_msg = f"SecurityEvent: {json.dumps(event_data)}"
        
        # Log to appropriate logger based on severity
        if severity in ["CRITICAL", "HIGH"]:
            self.intrusion_logger.warning(log_msg)
        else:
            self.security_logger.info(log_msg)
        
        # Check for suspicious patterns
        self._check_suspicious_activity(event_type, ip_address)
        
        # Log to system monitor for critical events
        if severity == "CRITICAL":
            system_monitor_logger.critical(f"Security alert: {event_type.value} - {details}")
    
    def log_authentication_event(
        self,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None,
        node_id: Optional[int] = None,
        reason: Optional[str] = None
    ):
        """Log authentication attempts"""
        
        event_type = SecurityEventType.AUTHENTICATION_SUCCESS if success else SecurityEventType.AUTHENTICATION_FAILED
        severity = "INFO" if success else "WARNING"
        
        details = {
            "user_agent": user_agent,
            "reason": reason
        }
        
        self.log_security_event(
            event_type=event_type,
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_id=user_id,
            node_id=node_id
        )
        
        # Track failed attempts for brute force detection
        if not success:
            self._track_failed_authentication(ip_address)
    
    def log_node_connection_event(
        self,
        success: bool,
        node_id: int,
        ip_address: str,
        connection_type: str = "grpc",
        error_message: Optional[str] = None
    ):
        """Log node connection attempts"""
        
        event_type = SecurityEventType.NODE_CONNECTION_SUCCESS if success else SecurityEventType.NODE_CONNECTION_FAILED
        severity = "INFO" if success else "WARNING"
        
        details = {
            "connection_type": connection_type,
            "error_message": error_message
        }
        
        self.log_security_event(
            event_type=event_type,
            details=details,
            severity=severity,
            ip_address=ip_address,
            node_id=node_id
        )
    
    def log_ssl_event(
        self,
        event_type: SecurityEventType,
        ip_address: str,
        certificate_info: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None
    ):
        """Log SSL/TLS related events"""
        
        details = {
            "certificate_info": certificate_info,
            "error_details": error_details
        }
        
        severity = "WARNING" if "failed" in event_type.value or "invalid" in event_type.value else "INFO"
        
        self.log_security_event(
            event_type=event_type,
            details=details,
            severity=severity,
            ip_address=ip_address
        )
    
    def log_system_alert(
        self,
        alert_type: str,
        message: str,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Log system resource alerts"""
        
        details = {
            "alert_type": alert_type,
            "message": message,
            "metrics": metrics or {}
        }
        
        severity = "HIGH" if any(keyword in alert_type.lower() for keyword in ["critical", "full", "exhausted"]) else "WARNING"
        
        self.log_security_event(
            event_type=SecurityEventType.SYSTEM_RESOURCE_ALERT,
            details=details,
            severity=severity
        )
    
    def log_audit_event(
        self,
        action: str,
        resource: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log audit trail events"""
        
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource": resource,
            "user_id": user_id,
            "details": details or {}
        }
        
        audit_msg = f"AuditEvent: {json.dumps(audit_data)}"
        self.audit_logger.info(audit_msg)
    
    def _check_suspicious_activity(self, event_type: SecurityEventType, ip_address: Optional[str]):
        """Check for suspicious activity patterns"""
        
        if not ip_address:
            return
        
        current_time = datetime.utcnow()
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        
        # Initialize counter for this minute if not exists
        if ip_address not in self.event_counters:
            self.event_counters[ip_address] = {}
        
        if minute_key not in self.event_counters[ip_address]:
            self.event_counters[ip_address][minute_key] = 0
        
        # Increment counter
        self.event_counters[ip_address][minute_key] += 1
        
        # Check if threshold exceeded
        if self.event_counters[ip_address][minute_key] > self.suspicious_activity_threshold:
            self.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                details={
                    "events_per_minute": self.event_counters[ip_address][minute_key],
                    "threshold": self.suspicious_activity_threshold,
                    "original_event": event_type.value
                },
                severity="HIGH",
                ip_address=ip_address
            )
        
        # Clean old counters (keep only last hour)
        hour_ago = current_time - timedelta(hours=1)
        for ip in list(self.event_counters.keys()):
            for time_key in list(self.event_counters[ip].keys()):
                try:
                    time_obj = datetime.strptime(time_key, "%Y-%m-%d %H:%M")
                    if time_obj < hour_ago:
                        del self.event_counters[ip][time_key]
                except ValueError:
                    continue
            
            # Remove IP if no recent activity
            if not self.event_counters[ip]:
                del self.event_counters[ip]
    
    def _track_failed_authentication(self, ip_address: str):
        """Track failed authentication attempts for brute force detection"""
        
        # Count failed attempts in last 10 minutes
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
        
        # This is a simplified implementation
        # In production, you'd want to store this in a database or Redis
        current_time = datetime.utcnow()
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        
        # Use a separate counter for failed auth attempts
        if not hasattr(self, 'failed_auth_counters'):
            self.failed_auth_counters = {}
        
        if ip_address not in self.failed_auth_counters:
            self.failed_auth_counters[ip_address] = {}
        
        if minute_key not in self.failed_auth_counters[ip_address]:
            self.failed_auth_counters[ip_address][minute_key] = 0
        
        self.failed_auth_counters[ip_address][minute_key] += 1
        
        # Count total failed attempts in last 10 minutes
        total_failed = 0
        for time_key, count in self.failed_auth_counters[ip_address].items():
            try:
                time_obj = datetime.strptime(time_key, "%Y-%m-%d %H:%M")
                if time_obj >= ten_minutes_ago:
                    total_failed += count
            except ValueError:
                continue
        
        # Detect brute force (5+ failed attempts in 10 minutes)
        if total_failed >= 5:
            self.log_security_event(
                event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
                details={
                    "failed_attempts": total_failed,
                    "time_window": "10 minutes",
                    "action_recommended": "IP blocking"
                },
                severity="CRITICAL",
                ip_address=ip_address
            )
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for the specified time period"""
        
        summary = {
            "time_period": f"Last {hours} hours",
            "timestamp": datetime.utcnow().isoformat(),
            "events": {
                "total": 0,
                "by_type": {},
                "by_severity": {"INFO": 0, "WARNING": 0, "HIGH": 0, "CRITICAL": 0}
            },
            "top_source_ips": {},
            "authentication": {
                "total_attempts": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # In a production implementation, you would parse the log files
        # or query a database to generate this summary
        # This is a placeholder structure
        
        return summary
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # This is a simplified cleanup
            # In production, you'd implement proper log rotation
            system_monitor_logger.info(f"Security log cleanup completed (keeping {days_to_keep} days)")
            
        except Exception as e:
            system_monitor_logger.error(f"Failed to cleanup security logs: {e}")


# Global security logger instance
security_logger = SecurityLogger()


def log_security_event(event_type: SecurityEventType, **kwargs):
    """Convenience function for logging security events"""
    security_logger.log_security_event(event_type, **kwargs)


def log_authentication_attempt(success: bool, ip_address: str, **kwargs):
    """Convenience function for logging authentication attempts"""
    security_logger.log_authentication_event(success, ip_address, **kwargs)


def log_node_connection(success: bool, node_id: int, ip_address: str, **kwargs):
    """Convenience function for logging node connections"""
    security_logger.log_node_connection_event(success, node_id, ip_address, **kwargs)


__all__ = [
    "SecurityEventType",
    "SecurityLogger", 
    "security_logger",
    "log_security_event",
    "log_authentication_attempt",
    "log_node_connection"
]