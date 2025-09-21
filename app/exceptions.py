"""
Standardized exception handling and error constants for the VPN management system
"""

from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, 
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE
)

# Standard error messages
class ErrorMessages:
    # Resource not found errors
    USER_NOT_FOUND = "User not found"
    ADMIN_NOT_FOUND = "Admin not found"
    NODE_NOT_FOUND = "Node not found"
    SERVICE_NOT_FOUND = "Service not found"
    INBOUND_NOT_FOUND = "Inbound not found"
    HOST_NOT_FOUND = "Host not found"
    
    # Authentication/Authorization errors
    INVALID_CREDENTIALS = "Invalid credentials"
    UNAUTHORIZED_ACCESS = "Unauthorized access"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
    TOKEN_EXPIRED = "Token has expired"
    INVALID_TOKEN = "Invalid token"
    
    # Resource conflict errors
    USER_ALREADY_EXISTS = "User already exists"
    ADMIN_ALREADY_EXISTS = "Admin already exists"
    SERVICE_ALREADY_EXISTS = "Service already exists"
    NODE_ALREADY_EXISTS = "Node already exists"
    RESOURCE_ALREADY_EXISTS = "Resource already exists"
    
    # Validation errors
    INVALID_INPUT = "Invalid input data"
    MISSING_REQUIRED_FIELD = "Required field is missing"
    INVALID_FORMAT = "Invalid format"
    INVALID_EMAIL_FORMAT = "Invalid email format"
    INVALID_USERNAME_FORMAT = "Invalid username format"
    
    # System errors
    INTERNAL_SERVER_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    DATABASE_ERROR = "Database operation failed"
    NETWORK_ERROR = "Network operation failed"
    
    # Business logic errors
    USER_DISABLED = "User is disabled"
    USER_EXPIRED = "User subscription has expired"
    TRAFFIC_LIMIT_EXCEEDED = "Traffic limit exceeded"
    SUBSCRIPTION_NOT_ACTIVE = "Subscription is not active"
    INVALID_OPERATION = "Invalid operation"


class APIError(HTTPException):
    """Base API error class with enhanced error details"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.code = code
        self.errors = errors or []
        self.headers = headers
        
        # Create detail structure compatible with ErrorResponseSchema
        error_detail = {
            "detail": detail,
            "status_code": status_code
        }
        
        if code:
            error_detail["code"] = code
            
        if errors:
            error_detail["errors"] = errors
        
        super().__init__(status_code=status_code, detail=error_detail, headers=headers)


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, detail: str = ErrorMessages.USER_NOT_FOUND, code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(HTTP_404_NOT_FOUND, detail, code)


class ConflictError(APIError):
    """Resource conflict error"""
    def __init__(self, detail: str = ErrorMessages.RESOURCE_ALREADY_EXISTS, code: str = "RESOURCE_CONFLICT"):
        super().__init__(HTTP_409_CONFLICT, detail, code)


class ValidationError(APIError):
    """Validation error with field details"""
    def __init__(
        self, 
        detail: str = ErrorMessages.INVALID_INPUT, 
        errors: Optional[List[Dict[str, Any]]] = None,
        code: str = "VALIDATION_ERROR"
    ):
        super().__init__(HTTP_422_UNPROCESSABLE_ENTITY, detail, code, errors)


class UnauthorizedError(APIError):
    """Authentication error"""
    def __init__(
        self, 
        detail: str = ErrorMessages.INVALID_CREDENTIALS, 
        code: str = "UNAUTHORIZED",
        headers: Optional[Dict[str, str]] = None
    ):
        # Add default WWW-Authenticate header for 401 responses
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(HTTP_401_UNAUTHORIZED, detail, code, headers=headers)


class ForbiddenError(APIError):
    """Authorization error"""
    def __init__(self, detail: str = ErrorMessages.INSUFFICIENT_PERMISSIONS, code: str = "FORBIDDEN"):
        super().__init__(HTTP_403_FORBIDDEN, detail, code)


class BadRequestError(APIError):
    """Bad request error"""
    def __init__(self, detail: str = ErrorMessages.INVALID_INPUT, code: str = "BAD_REQUEST"):
        super().__init__(HTTP_400_BAD_REQUEST, detail, code)


class ServerError(APIError):
    """Internal server error"""
    def __init__(self, detail: str = ErrorMessages.INTERNAL_SERVER_ERROR, code: str = "INTERNAL_ERROR"):
        super().__init__(HTTP_500_INTERNAL_SERVER_ERROR, detail, code)


class ServiceUnavailableError(APIError):
    """Service unavailable error"""
    def __init__(self, detail: str = ErrorMessages.SERVICE_UNAVAILABLE, code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(HTTP_503_SERVICE_UNAVAILABLE, detail, code)


# Convenience functions for common errors
def user_not_found_error() -> NotFoundError:
    return NotFoundError(ErrorMessages.USER_NOT_FOUND, "USER_NOT_FOUND")

def admin_not_found_error() -> NotFoundError:
    return NotFoundError(ErrorMessages.ADMIN_NOT_FOUND, "ADMIN_NOT_FOUND")

def node_not_found_error() -> NotFoundError:
    return NotFoundError(ErrorMessages.NODE_NOT_FOUND, "NODE_NOT_FOUND")

def service_not_found_error() -> NotFoundError:
    return NotFoundError(ErrorMessages.SERVICE_NOT_FOUND, "SERVICE_NOT_FOUND")

def user_already_exists_error() -> ConflictError:
    return ConflictError(ErrorMessages.USER_ALREADY_EXISTS, "USER_ALREADY_EXISTS")

def admin_already_exists_error() -> ConflictError:
    return ConflictError(ErrorMessages.ADMIN_ALREADY_EXISTS, "ADMIN_ALREADY_EXISTS")

def invalid_credentials_error() -> UnauthorizedError:
    return UnauthorizedError(ErrorMessages.INVALID_CREDENTIALS, "INVALID_CREDENTIALS")

def insufficient_permissions_error() -> ForbiddenError:
    return ForbiddenError(ErrorMessages.INSUFFICIENT_PERMISSIONS, "INSUFFICIENT_PERMISSIONS")