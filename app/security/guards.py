"""
Security guards for protecting critical endpoints
"""
import logging
from typing import Optional, List, Union
from fastapi import HTTPException, status, Request, Depends
from functools import wraps
from datetime import datetime, timedelta

from ..dependencies import AdminDep, SudoAdminDep
from ..models.admin import Admin
from .security_logger import SecurityEventType, security_logger
from ..middleware.proxy_headers import get_client_ip

logger = logging.getLogger(__name__)


class SecurityGuard:
    """Security guard for endpoint protection"""
    
    def __init__(self):
        self.failed_attempts = {}  # Track failed attempts
        self.lockout_threshold = 5  # Failed attempts before lockout
        self.lockout_duration = 300  # 5 minutes lockout
    
    def _get_lockout_key(self, request: Optional[Request], admin: Optional[Admin] = None) -> str:
        """Generate lockout key for tracking failed attempts"""
        if admin:
            return f"admin:{admin.username}"
        if request:
            return f"ip:{get_client_ip(request)}"
        return "ip:unknown"
    
    def _is_locked_out(self, key: str) -> bool:
        """Check if key is currently locked out"""
        if key not in self.failed_attempts:
            return False
        
        attempts = self.failed_attempts[key]
        
        # Clean old attempts (older than lockout duration)
        cutoff = datetime.utcnow() - timedelta(seconds=self.lockout_duration)
        attempts['attempts'] = [
            attempt for attempt in attempts['attempts'] 
            if attempt > cutoff
        ]
        
        # Check if still locked out
        if len(attempts['attempts']) >= self.lockout_threshold:
            last_attempt = max(attempts['attempts'])
            if datetime.utcnow() - last_attempt < timedelta(seconds=self.lockout_duration):
                return True
        
        return False
    
    def _record_failed_attempt(self, key: str):
        """Record a failed access attempt"""
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {'attempts': []}
        
        self.failed_attempts[key]['attempts'].append(datetime.utcnow())
    
    def _clear_failed_attempts(self, key: str):
        """Clear failed attempts for successful access"""
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def require_sudo_admin(self, operation: str, resource: str):
        """Guard that requires sudo admin privileges"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request and admin from function arguments
                request = None
                admin = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    elif isinstance(arg, Admin):
                        admin = arg
                
                # Check function parameters for admin
                if 'admin' in kwargs:
                    admin = kwargs['admin']
                if 'request' in kwargs:
                    request = kwargs['request']
                
                if not admin:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Generate lockout key
                lockout_key = self._get_lockout_key(request, admin)
                
                # Check lockout
                if self._is_locked_out(lockout_key):
                    client_ip = get_client_ip(request) if request else "unknown"
                    
                    security_logger.log_security_event(
                        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                        details={
                            "operation": operation,
                            "resource": resource,
                            "reason": "Account locked due to repeated failures",
                            "username": admin.username
                        },
                        severity="HIGH",
                        ip_address=client_ip,
                        user_id=admin.id
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail="Account temporarily locked due to security policy"
                    )
                
                # Check sudo privileges
                if not admin.is_sudo:
                    self._record_failed_attempt(lockout_key)
                    client_ip = get_client_ip(request) if request else "unknown"
                    
                    security_logger.log_security_event(
                        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                        details={
                            "operation": operation,
                            "resource": resource,
                            "reason": "Insufficient privileges (sudo required)",
                            "username": admin.username,
                            "is_sudo": admin.is_sudo
                        },
                        severity="WARNING",
                        ip_address=client_ip,
                        user_id=admin.id
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Sudo admin privileges required for this operation"
                    )
                
                # Clear failed attempts on successful authorization
                self._clear_failed_attempts(lockout_key)
                
                # Log successful access
                if request:
                    client_ip = get_client_ip(request)
                    security_logger.log_security_event(
                        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
                        details={
                            "operation": operation,
                            "resource": resource,
                            "username": admin.username
                        },
                        severity="INFO",
                        ip_address=client_ip,
                        user_id=admin.id
                    )
                
                return await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_admin_access(self, operation: str, resource: str, allow_modify_access: bool = True):
        """Guard that requires admin access with optional modify_users_access check"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request and admin from function arguments
                request = None
                admin = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    elif isinstance(arg, Admin):
                        admin = arg
                
                # Check function parameters for admin
                if 'admin' in kwargs:
                    admin = kwargs['admin']
                if 'request' in kwargs:
                    request = kwargs['request']
                
                if not admin:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Generate lockout key
                lockout_key = self._get_lockout_key(request, admin)
                
                # Check lockout
                if self._is_locked_out(lockout_key):
                    client_ip = get_client_ip(request) if request else "unknown"
                    
                    security_logger.log_security_event(
                        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                        details={
                            "operation": operation,
                            "resource": resource,
                            "reason": "Account locked due to repeated failures",
                            "username": admin.username
                        },
                        severity="HIGH",
                        ip_address=client_ip,
                        user_id=admin.id
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail="Account temporarily locked due to security policy"
                    )
                
                # Check admin privileges
                if not admin.enabled:
                    self._record_failed_attempt(lockout_key)
                    client_ip = get_client_ip(request) if request else "unknown"
                    
                    security_logger.log_security_event(
                        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                        details={
                            "operation": operation,
                            "resource": resource,
                            "reason": "Admin account disabled",
                            "username": admin.username
                        },
                        severity="WARNING",
                        ip_address=client_ip,
                        user_id=admin.id
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin account is disabled"
                    )
                
                # Check modify access for user operations
                if allow_modify_access and resource == "users" and operation in ["create", "modify", "delete"]:
                    if not admin.is_sudo and not admin.modify_users_access:
                        self._record_failed_attempt(lockout_key)
                        client_ip = get_client_ip(request) if request else "unknown"
                        
                        security_logger.log_security_event(
                            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                            details={
                                "operation": operation,
                                "resource": resource,
                                "reason": "Insufficient modify_users_access permission",
                                "username": admin.username,
                                "modify_users_access": admin.modify_users_access
                            },
                            severity="WARNING",
                            ip_address=client_ip,
                            user_id=admin.id
                        )
                        
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient permissions for user modifications"
                        )
                
                # Clear failed attempts on successful authorization
                self._clear_failed_attempts(lockout_key)
                
                return await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            return wrapper
        return decorator


# Global security guard instance
security_guard = SecurityGuard()


# Dependency functions for FastAPI
def RequireSudoAdmin(operation: str, resource: str):
    """FastAPI dependency factory for sudo admin requirement"""
    def dependency(admin: SudoAdminDep, request: Request):
        # The SudoAdminDep already handles the sudo check, but we'll add logging
        client_ip = get_client_ip(request)
        security_logger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details={
                "operation": operation,
                "resource": resource,
                "username": admin.username,
                "access_level": "sudo"
            },
            severity="INFO",
            ip_address=client_ip,
            user_id=admin.id
        )
        return admin
    
    return Depends(dependency)


def RequireAdminAccess(operation: str, resource: str):
    """FastAPI dependency factory for admin access requirement"""
    def dependency(admin: AdminDep, request: Request):
        # Additional checks beyond basic AdminDep
        if not admin.enabled:
            client_ip = get_client_ip(request)
            security_logger.log_security_event(
                event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                details={
                    "operation": operation,
                    "resource": resource,
                    "reason": "Admin account disabled",
                    "username": admin.username
                },
                severity="WARNING",
                ip_address=client_ip,
                user_id=admin.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is disabled"
            )
        
        client_ip = get_client_ip(request)
        security_logger.log_security_event(
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details={
                "operation": operation,
                "resource": resource,
                "username": admin.username,
                "access_level": "admin"
            },
            severity="INFO",
            ip_address=client_ip,
            user_id=admin.id
        )
        return admin
    
    return Depends(dependency)


__all__ = [
    "SecurityGuard", 
    "security_guard", 
    "RequireSudoAdmin", 
    "RequireAdminAccess"
]