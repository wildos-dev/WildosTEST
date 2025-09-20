"""
Enhanced input validation schemas with strict security patterns
"""
import re
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, validator, ConfigDict


# Strict validation patterns
USERNAME_PATTERN = r"^[a-zA-Z0-9._-]{3,32}$"
NODE_NAME_PATTERN = r"^[a-zA-Z0-9._-]{2,64}$"
SERVICE_NAME_PATTERN = r"^[a-zA-Z0-9._-]{2,64}$"
ADMIN_USERNAME_PATTERN = r"^[a-zA-Z0-9._-]{3,32}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
DOMAIN_PATTERN = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
IP_PATTERN = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

# Port ranges
MIN_PORT = 1024
MAX_PORT = 65535

# Data limits
MAX_DATA_LIMIT = 1024 * 1024 * 1024 * 1024  # 1TB in bytes
MAX_USAGE_DURATION = 9999 * 365 * 24 * 60 * 60  # 9999 years in seconds
MAX_NOTE_LENGTH = 500
MAX_CONFIG_LENGTH = 1024 * 1024  # 1MB for configs


class ValidatedBackendType(str, Enum):
    """Strictly validated backend types"""
    XRAY = "xray"
    HYSTERIA = "hysteria"
    NGINX = "nginx"
    TROJAN = "trojan"
    SHADOWSOCKS = "shadowsocks"


class ValidatedProtocol(str, Enum):
    """Strictly validated protocols"""
    VMESS = "vmess"
    VLESS = "vless"  
    TROJAN = "trojan"
    SHADOWSOCKS = "shadowsocks"
    HYSTERIA = "hysteria"


class ValidatedNodeStatus(str, Enum):
    """Validated node statuses"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


# Type aliases for validated fields
ValidatedUsername = Annotated[str, StringConstraints(
    pattern=USERNAME_PATTERN,
    min_length=3,
    max_length=32,
    strip_whitespace=True
)]

ValidatedNodeName = Annotated[str, StringConstraints(
    pattern=NODE_NAME_PATTERN,
    min_length=2,
    max_length=64,
    strip_whitespace=True
)]

ValidatedServiceName = Annotated[str, StringConstraints(
    pattern=SERVICE_NAME_PATTERN,
    min_length=2,
    max_length=64,
    strip_whitespace=True
)]

ValidatedAdminUsername = Annotated[str, StringConstraints(
    pattern=ADMIN_USERNAME_PATTERN,
    min_length=3,
    max_length=32,
    strip_whitespace=True
)]

ValidatedEmail = Annotated[str, StringConstraints(
    pattern=EMAIL_PATTERN,
    max_length=255,
    strip_whitespace=True
)]

ValidatedDomain = Annotated[str, StringConstraints(
    pattern=DOMAIN_PATTERN,
    max_length=255,
    strip_whitespace=True
)]

ValidatedIP = Annotated[str, StringConstraints(
    pattern=IP_PATTERN,
    strip_whitespace=True
)]

ValidatedPort = Annotated[int, Field(
    ge=MIN_PORT,
    le=MAX_PORT,
    description=f"Port must be between {MIN_PORT} and {MAX_PORT}"
)]

ValidatedDataLimit = Annotated[Optional[int], Field(
    ge=0,
    le=MAX_DATA_LIMIT,
    description=f"Data limit must be between 0 and {MAX_DATA_LIMIT} bytes"
)]

ValidatedUsageDuration = Annotated[Optional[int], Field(
    ge=1,
    le=MAX_USAGE_DURATION,
    description=f"Usage duration must be between 1 second and {MAX_USAGE_DURATION} seconds"
)]

ValidatedNote = Annotated[Optional[str], Field(
    max_length=MAX_NOTE_LENGTH,
    description=f"Note must be less than {MAX_NOTE_LENGTH} characters"
)]

ValidatedConfig = Annotated[str, Field(
    max_length=MAX_CONFIG_LENGTH,
    description=f"Config must be less than {MAX_CONFIG_LENGTH} characters"
)]


class StrictUserCreateRequest(BaseModel):
    """Strictly validated user creation request"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    username: ValidatedUsername
    expire_date: Optional[datetime] = None
    usage_duration: ValidatedUsageDuration = None
    data_limit: ValidatedDataLimit = None
    note: ValidatedNote = None
    services: List[int] = Field(default_factory=list, max_length=100)
    
    @validator('expire_date')
    def validate_expire_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("Expire date must be in the future")
        return v
    
    @validator('services')
    def validate_services(cls, v):
        if len(v) > 100:
            raise ValueError("Too many services (max 100)")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate service IDs not allowed")
        return v


class StrictNodeCreateRequest(BaseModel):
    """Strictly validated node creation request"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    name: ValidatedNodeName
    address: ValidatedDomain | ValidatedIP
    port: ValidatedPort = 50051
    usage_coefficient: float = Field(ge=0.0, le=10.0, default=1.0)
    
    @validator('usage_coefficient')
    def validate_usage_coefficient(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Usage coefficient must be between 0 and 10")
        return round(v, 2)  # Limit to 2 decimal places


class StrictServiceCreateRequest(BaseModel):
    """Strictly validated service creation request"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    name: ValidatedServiceName
    inbounds: List[dict] = Field(default_factory=list, max_length=50)
    
    @validator('inbounds')
    def validate_inbounds(cls, v):
        if len(v) > 50:
            raise ValueError("Too many inbounds (max 50)")
        
        for i, inbound in enumerate(v):
            # Validate required inbound fields
            if 'id' not in inbound:
                raise ValueError(f"Inbound at index {i} missing required 'id' field")
            if 'tag' not in inbound:
                raise ValueError(f"Inbound at index {i} missing required 'tag' field")
            if 'protocol' not in inbound:
                raise ValueError(f"Inbound at index {i} missing required 'protocol' field")
            
            # Validate inbound ID
            try:
                inbound_id = int(inbound['id'])
                if inbound_id <= 0:
                    raise ValueError(f"Inbound at index {i} ID must be a positive integer, got {inbound_id}")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Inbound at index {i} has invalid ID: {str(e)}")
            
            # Validate protocol
            try:
                ValidatedProtocol(inbound['protocol'])
            except ValueError:
                raise ValueError(f"Inbound at index {i} has invalid protocol: {inbound['protocol']}")
            
            # Additional security checks
            if len(str(inbound.get('tag', ''))) > 64:
                raise ValueError(f"Inbound at index {i} tag too long (max 64 characters)")
        
        # Check for duplicate inbound IDs
        inbound_ids = []
        for i, inbound in enumerate(v):
            inbound_id = int(inbound['id'])
            if inbound_id in inbound_ids:
                raise ValueError(f"Duplicate inbound ID {inbound_id} found at index {i}")
            inbound_ids.append(inbound_id)
        
        return v


class StrictAdminCreateRequest(BaseModel):
    """Strictly validated admin creation request"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    username: ValidatedAdminUsername
    password: str = Field(min_length=8, max_length=128)
    is_sudo: bool = False
    enabled: bool = True
    service_ids: List[int] = Field(default_factory=list, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password too long (max 128 characters)")
        
        # Check password complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and digit characters")
        
        return v
    
    @validator('service_ids')
    def validate_service_ids(cls, v):
        if len(v) > 100:
            raise ValueError("Too many service IDs (max 100)")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate service IDs not allowed")
        return v


class StrictConfigUpdateRequest(BaseModel):
    """Strictly validated config update request"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    config: ValidatedConfig
    format: str = Field(pattern=r"^(json|yaml|plain)$")
    
    @validator('config')
    def validate_config(cls, v):
        if not v.strip():
            raise ValueError("Config cannot be empty")
        return v


class ValidationResponse(BaseModel):
    """Standard validation error response"""
    error: str = "Validation failed"
    details: dict
    field_errors: dict = Field(default_factory=dict)


# Security validation utilities
class SecurityValidator:
    """Utility class for additional security validations"""
    
    @staticmethod
    def validate_node_id(node_id: int) -> bool:
        """Validate node ID is within reasonable bounds"""
        return 1 <= node_id <= 999999
    
    @staticmethod
    def validate_user_id(user_id: int) -> bool:
        """Validate user ID is within reasonable bounds"""
        return 1 <= user_id <= 999999999
    
    @staticmethod
    def validate_service_id(service_id: int) -> bool:
        """Validate service ID is within reasonable bounds"""
        return 1 <= service_id <= 999999
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path separators and dangerous characters
        safe_chars = re.sub(r'[^\w\-_.]', '', filename)
        # Prevent hidden files and relative paths
        if safe_chars.startswith('.') or '..' in safe_chars:
            raise ValueError("Invalid filename")
        return safe_chars[:255]  # Limit length
    
    @staticmethod
    def validate_json_size(json_str: str, max_size: int = 1024 * 1024) -> bool:
        """Validate JSON string size"""
        return len(json_str.encode('utf-8')) <= max_size


__all__ = [
    "USERNAME_PATTERN", "NODE_NAME_PATTERN", "SERVICE_NAME_PATTERN",
    "ValidatedBackendType", "ValidatedProtocol", "ValidatedNodeStatus",
    "ValidatedUsername", "ValidatedNodeName", "ValidatedServiceName",
    "ValidatedAdminUsername", "ValidatedEmail", "ValidatedDomain",
    "ValidatedIP", "ValidatedPort", "ValidatedDataLimit",
    "StrictUserCreateRequest", "StrictNodeCreateRequest", 
    "StrictServiceCreateRequest", "StrictAdminCreateRequest",
    "StrictConfigUpdateRequest", "ValidationResponse",
    "SecurityValidator"
]