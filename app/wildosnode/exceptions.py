"""
Enhanced error handling system for gRPC client operations.

This module provides a structured exception hierarchy specifically designed
for Docker VPS environments with improved error context, categorization,
and recovery mechanisms.
"""

import time
from abc import ABC
from enum import Enum
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field


class ErrorSeverity(Enum):
    """Error severity levels for prioritization and alerting"""
    LOW = "low"           # Minor issues, automatic recovery possible
    MEDIUM = "medium"     # Significant issues requiring attention
    HIGH = "high"         # Critical issues requiring immediate action
    CRITICAL = "critical" # System failure, service unavailable


class ErrorCategory(Enum):
    """Error categories for classification and metrics"""
    NETWORK = "network"
    SERVICE = "service"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    PROTOCOL = "protocol"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"                    # Simple retry with backoff
    RECONNECT = "reconnect"           # Re-establish connection
    FALLBACK = "fallback"             # Use alternative service/cache
    DEGRADE = "degrade"               # Reduce functionality gracefully
    ESCALATE = "escalate"             # Report to higher level systems
    CIRCUIT_BREAK = "circuit_break"   # Activate circuit breaker


@dataclass
class ErrorContext:
    """Enhanced error context for debugging and monitoring"""
    node_id: Optional[int] = None
    operation: Optional[str] = None
    attempt_number: int = 1
    timestamp: float = field(default_factory=time.time)
    duration_ms: Optional[int] = None
    
    # Network context
    remote_address: Optional[str] = None
    remote_port: Optional[int] = None
    local_address: Optional[str] = None
    
    # Service context
    service_name: Optional[str] = None
    method_name: Optional[str] = None
    request_id: Optional[str] = None
    
    # System context
    container_id: Optional[str] = None
    host_info: Optional[Dict[str, Any]] = None
    resource_usage: Optional[Dict[str, Any]] = None
    
    # Recovery context
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[float] = None
    successful_recoveries: int = 0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata to the error context"""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary for logging"""
        return {
            'node_id': self.node_id,
            'operation': self.operation,
            'attempt_number': self.attempt_number,
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms,
            'remote_address': self.remote_address,
            'remote_port': self.remote_port,
            'local_address': self.local_address,
            'service_name': self.service_name,
            'method_name': self.method_name,
            'request_id': self.request_id,
            'container_id': self.container_id,
            'host_info': self.host_info,
            'resource_usage': self.resource_usage,
            'recovery_attempts': self.recovery_attempts,
            'last_recovery_attempt': self.last_recovery_attempt,
            'successful_recoveries': self.successful_recoveries,
            'metadata': self.metadata
        }


class WildosNodeBaseError(Exception, ABC):
    """
    Base exception class for all wildosnode errors.
    
    Provides structured error information, recovery suggestions,
    and integration with monitoring systems.
    """
    
    category: ErrorCategory = ErrorCategory.SERVICE
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    default_recovery_strategies: List[RecoveryStrategy] = [RecoveryStrategy.RETRY]
    retryable: bool = True
    
    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        recovery_strategies: Optional[List[RecoveryStrategy]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.cause = cause
        self.recovery_strategies = recovery_strategies or self.default_recovery_strategies
        self.user_message = user_message or self._generate_user_message()
        self.occurred_at = time.time()
        
        # Chain the original exception if provided
        if cause:
            self.__cause__ = cause
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        return f"Service temporarily unavailable. Please try again later."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and monitoring"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'user_message': self.user_message,
            'category': self.category.value,
            'severity': self.severity.value,
            'retryable': self.retryable,
            'recovery_strategies': [s.value for s in self.recovery_strategies],
            'occurred_at': self.occurred_at,
            'context': self.context.to_dict() if self.context else None,
            'cause_type': type(self.cause).__name__ if self.cause else None,
            'cause_message': str(self.cause) if self.cause else None
        }
    
    def should_retry(self) -> bool:
        """Determine if this error should trigger a retry"""
        return self.retryable and RecoveryStrategy.RETRY in self.recovery_strategies
    
    def should_circuit_break(self) -> bool:
        """Determine if this error should trigger circuit breaker"""
        return RecoveryStrategy.CIRCUIT_BREAK in self.recovery_strategies
    
    def get_recommended_delay(self) -> float:
        """Get recommended delay before retry (in seconds)"""
        base_delay = 1.0
        if self.context and self.context.attempt_number > 1:
            # Exponential backoff with jitter
            backoff_delay = min(base_delay * (2 ** (self.context.attempt_number - 1)), 60.0)
            import random
            jitter = random.uniform(0.5, 1.5)
            return backoff_delay * jitter
        return base_delay


# Network-related errors
class NetworkError(WildosNodeBaseError):
    """Base class for network-related errors"""
    category = ErrorCategory.NETWORK
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.RECONNECT]
    
    def _generate_user_message(self) -> str:
        return "Network connection issue. Checking connectivity..."


class ConnectionError(NetworkError):
    """Connection establishment failures"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RECONNECT, RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "Cannot connect to remote service. Retrying connection..."


class ConnectionTimeoutError(NetworkError):
    """Connection timeout during establishment"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.RECONNECT]
    
    def _generate_user_message(self) -> str:
        return "Connection timeout. Retrying with extended timeout..."


class NetworkUnstableError(NetworkError):
    """Network instability detected (Docker VPS specific)"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.CIRCUIT_BREAK]
    
    def _generate_user_message(self) -> str:
        return "Network instability detected. Attempting to stabilize connection..."


class ContainerNetworkError(NetworkError):
    """Inter-container communication issues"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RECONNECT, RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Container network issue detected. Investigating connectivity..."


# Service-related errors
class ServiceError(WildosNodeBaseError):
    """Base class for service-related errors"""
    category = ErrorCategory.SERVICE
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK]


class ServiceUnavailableError(ServiceError):
    """Service is temporarily unavailable"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.CIRCUIT_BREAK, RecoveryStrategy.FALLBACK]
    
    def _generate_user_message(self) -> str:
        return "Service temporarily unavailable. Please wait while we restore service..."


class ServiceOverloadedError(ServiceError):
    """Service is overloaded with requests"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.DEGRADE]
    
    def _generate_user_message(self) -> str:
        return "Service is currently busy. Please try again in a moment..."


class ServiceDegradedError(ServiceError):
    """Service is running in degraded mode"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.DEGRADE, RecoveryStrategy.FALLBACK]
    retryable = False
    
    def _generate_user_message(self) -> str:
        return "Service is running with limited functionality. Some features may be unavailable..."


class BackendError(ServiceError):
    """Backend (Xray, Hysteria2, etc.) specific errors"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Backend service issue detected. Attempting automatic recovery..."


# Timeout-related errors
class TimeoutError(WildosNodeBaseError):
    """Base class for timeout-related errors"""
    category = ErrorCategory.TIMEOUT
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY]


class OperationTimeoutError(TimeoutError):
    """Operation exceeded allowed time limit"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "Operation is taking longer than expected. Retrying with extended timeout..."


class StreamTimeoutError(TimeoutError):
    """Streaming operation timeout"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RECONNECT, RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "Data stream timeout. Re-establishing connection..."


class HealthCheckTimeoutError(TimeoutError):
    """Health check operation timeout"""
    severity = ErrorSeverity.LOW
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.DEGRADE]
    
    def _generate_user_message(self) -> str:
        return "Health check timeout. Service may be slow to respond..."


# Authentication-related errors
class AuthenticationError(WildosNodeBaseError):
    """Base class for authentication-related errors"""
    category = ErrorCategory.AUTHENTICATION
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    retryable = False


class SSLError(AuthenticationError):
    """SSL/TLS certificate or handshake errors"""
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Security certificate issue. Please contact system administrator..."


class CertificateExpiredError(AuthenticationError):
    """Certificate has expired"""
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Security certificate has expired. Automatic renewal in progress..."


class InvalidCredentialsError(AuthenticationError):
    """Invalid authentication credentials"""
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Authentication failed. Please verify credentials..."


# Configuration-related errors
class ConfigurationError(WildosNodeBaseError):
    """Base class for configuration-related errors"""
    category = ErrorCategory.CONFIGURATION
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    retryable = False


class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration detected"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Configuration error detected. Please check system settings..."


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing"""
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Required configuration missing. Please contact system administrator..."


class ConfigurationValidationError(ConfigurationError):
    """Configuration validation failed"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Configuration validation failed. Please verify settings..."


# Resource-related errors (Docker VPS specific)
class ResourceError(WildosNodeBaseError):
    """Base class for resource-related errors"""
    category = ErrorCategory.RESOURCE
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.DEGRADE, RecoveryStrategy.ESCALATE]


class MemoryExhaustionError(ResourceError):
    """System running out of memory"""
    severity = ErrorSeverity.CRITICAL
    default_recovery_strategies = [RecoveryStrategy.DEGRADE, RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "System memory low. Operating in reduced capacity mode..."


class DiskSpaceError(ResourceError):
    """Insufficient disk space"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.DEGRADE, RecoveryStrategy.ESCALATE]
    
    def _generate_user_message(self) -> str:
        return "Disk space low. Some features may be temporarily unavailable..."


class CPUOverloadError(ResourceError):
    """CPU overload detected"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.DEGRADE, RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "System under high load. Requests may be processed slower..."


class ContainerRestartError(ResourceError):
    """Container restart detected"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.RECONNECT, RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "Service restart detected. Re-establishing connections..."


# Protocol-related errors
class ProtocolError(WildosNodeBaseError):
    """Base class for protocol-related errors"""
    category = ErrorCategory.PROTOCOL
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.RECONNECT]


class GRPCError(ProtocolError):
    """gRPC protocol specific errors"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.RECONNECT]
    
    def _generate_user_message(self) -> str:
        return "Communication protocol issue. Retrying with different approach..."


class ProtocolVersionMismatchError(ProtocolError):
    """Protocol version mismatch between client and server"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.ESCALATE]
    retryable = False
    
    def _generate_user_message(self) -> str:
        return "Version compatibility issue. Please update the system..."


class StreamInterruptedError(ProtocolError):
    """Data stream was interrupted"""
    severity = ErrorSeverity.MEDIUM
    default_recovery_strategies = [RecoveryStrategy.RECONNECT, RecoveryStrategy.RETRY]
    
    def _generate_user_message(self) -> str:
        return "Data stream interrupted. Re-establishing connection..."


class CircuitBreakerError(ServiceError):
    """Circuit breaker is open, requests are being rejected"""
    severity = ErrorSeverity.HIGH
    default_recovery_strategies = [RecoveryStrategy.FALLBACK, RecoveryStrategy.DEGRADE]
    retryable = False
    
    def _generate_user_message(self) -> str:
        return "Service temporarily disabled due to errors. Please try again later..."


# Utility functions for error handling
def classify_grpc_error(grpc_error) -> WildosNodeBaseError:
    """
    Classify gRPC errors into our structured exception hierarchy
    
    Args:
        grpc_error: Original gRPC error
        
    Returns:
        Appropriate WildosNodeBaseError subclass
    """
    from grpclib import Status
    
    if not hasattr(grpc_error, 'status'):
        return ServiceError("Unknown gRPC error", cause=grpc_error)
    
    error_context = ErrorContext(
        operation="grpc_call",
        metadata={'grpc_status': grpc_error.status.name if hasattr(grpc_error.status, 'name') else str(grpc_error.status)}
    )
    
    status_mapping = {
        Status.UNAVAILABLE: ServiceUnavailableError(
            "Service unavailable", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.DEADLINE_EXCEEDED: OperationTimeoutError(
            "Operation timeout", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.RESOURCE_EXHAUSTED: ServiceOverloadedError(
            "Service overloaded", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.UNAUTHENTICATED: InvalidCredentialsError(
            "Authentication failed", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.PERMISSION_DENIED: InvalidCredentialsError(
            "Permission denied", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.INVALID_ARGUMENT: ConfigurationValidationError(
            "Invalid request parameters", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.FAILED_PRECONDITION: ConfigurationError(
            "Service precondition failed", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.ABORTED: StreamInterruptedError(
            "Operation aborted", 
            context=error_context, 
            cause=grpc_error
        ),
        Status.INTERNAL: BackendError(
            "Internal service error", 
            context=error_context, 
            cause=grpc_error
        ),
    }
    
    return status_mapping.get(
        grpc_error.status, 
        GRPCError(f"gRPC error: {grpc_error}", context=error_context, cause=grpc_error)
    )


def classify_network_error(network_error) -> WildosNodeBaseError:
    """
    Classify network errors into our structured exception hierarchy
    
    Args:
        network_error: Original network error
        
    Returns:
        Appropriate NetworkError subclass
    """
    error_context = ErrorContext(
        operation="network_operation",
        metadata={'original_error_type': type(network_error).__name__}
    )
    
    error_message = str(network_error).lower()
    
    if 'timeout' in error_message or 'timed out' in error_message:
        return ConnectionTimeoutError(
            f"Connection timeout: {network_error}",
            context=error_context,
            cause=network_error
        )
    elif 'connection refused' in error_message or 'connection failed' in error_message:
        return ConnectionError(
            f"Connection failed: {network_error}",
            context=error_context,
            cause=network_error
        )
    elif 'network is unreachable' in error_message or 'no route to host' in error_message:
        return NetworkUnstableError(
            f"Network unreachable: {network_error}",
            context=error_context,
            cause=network_error
        )
    else:
        return NetworkError(
            f"Network error: {network_error}",
            context=error_context,
            cause=network_error
        )


def classify_ssl_error(ssl_error) -> WildosNodeBaseError:
    """
    Classify SSL errors into our structured exception hierarchy
    
    Args:
        ssl_error: Original SSL error
        
    Returns:
        Appropriate AuthenticationError subclass
    """
    error_context = ErrorContext(
        operation="ssl_handshake",
        metadata={'original_error_type': type(ssl_error).__name__}
    )
    
    error_message = str(ssl_error).lower()
    
    if 'certificate' in error_message and 'expired' in error_message:
        return CertificateExpiredError(
            f"Certificate expired: {ssl_error}",
            context=error_context,
            cause=ssl_error
        )
    elif 'certificate' in error_message:
        return SSLError(
            f"Certificate error: {ssl_error}",
            context=error_context,
            cause=ssl_error
        )
    else:
        return SSLError(
            f"SSL error: {ssl_error}",
            context=error_context,
            cause=ssl_error
        )


# Factory function for creating errors with context
def create_error_with_context(
    error_class: type,
    message: str,
    node_id: Optional[int] = None,
    operation: Optional[str] = None,
    remote_address: Optional[str] = None,
    **kwargs
) -> WildosNodeBaseError:
    """
    Factory function for creating errors with rich context
    
    Args:
        error_class: Exception class to instantiate
        message: Error message
        node_id: Node ID where error occurred
        operation: Operation being performed
        remote_address: Remote address if applicable
        **kwargs: Additional context parameters
        
    Returns:
        Exception instance with populated context
    """
    context = ErrorContext(
        node_id=node_id,
        operation=operation,
        remote_address=remote_address
    )
    
    # Add any additional context from kwargs
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)
        else:
            context.add_metadata(key, value)
    
    return error_class(message, context=context)