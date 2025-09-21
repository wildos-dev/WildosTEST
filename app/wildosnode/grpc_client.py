import asyncio
import atexit
import logging
import random
import ssl
import tempfile
import time
from functools import wraps
from typing import Callable, TypeVar, Awaitable, Optional, Dict, Any, List, Union, Coroutine

from grpclib import GRPCError
from grpclib.client import Channel
from grpclib.exceptions import StreamTerminatedError

from .base import WildosNodeBase
from .database import WildosNodeDB
# Import enhanced error handling and recovery systems
from .exceptions import (
    WildosNodeBaseError, ErrorContext, ErrorSeverity, ErrorCategory,
    NetworkError, ServiceError, TimeoutError, AuthenticationError,
    ConfigurationError, ResourceError, ConnectionError as WildosConnectionError,
    NetworkUnstableError, ContainerRestartError, ServiceUnavailableError,
    classify_grpc_error, classify_network_error, classify_ssl_error,
    create_error_with_context
)
from .recovery import (
    RecoveryManager, RecoveryStrategy, RetryStrategy, ReconnectionStrategy,
    FallbackStrategy, DegradationStrategy, FallbackCache, RecoveryState,
    RecoveryMode, HealthStatus, with_recovery, get_recovery_manager
)
# Monitoring imports moved to functions to avoid circular dependencies
from .service_grpc import WildosServiceStub
from .service_pb2 import (
    UserData,
    UsersData,
    Empty,
    User,
    Inbound,
    BackendConfig,
    BackendLogsRequest,
    Backend,
    RestartBackendRequest,
    BackendStats,
    # Host system monitoring imports
    HostSystemMetrics,
    PortActionRequest,
    PortActionResponse,
    # Container management imports
    ContainerLogsRequest,
    ContainerLogsResponse,
    ContainerFilesRequest,
    ContainerFilesResponse,
    ContainerRestartResponse,
    # Batch operations imports
    AllBackendsStatsResponse,
    # Peak monitoring imports
    PeakEvent,
    PeakQuery,
    # Enum imports
    ConfigFormat,
    FileInfo
)
# NodeStatus импортируется лениво для избежания проблем с PYTHONPATH
# CertificateManager импортируется лениво для избежания проблем с PYTHONPATH

logger = logging.getLogger(__name__)

# Initialize enhanced monitoring and recovery systems
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .monitoring import MonitoringSystem
_monitoring_system: Optional['MonitoringSystem'] = None
_recovery_manager: Optional[RecoveryManager] = None
_resource_monitor: Optional['DockerVPSResourceMonitor'] = None

def _get_monitoring_system() -> 'MonitoringSystem':
    """Get or create monitoring system instance"""
    global _monitoring_system
    if _monitoring_system is None:
        from .monitoring import get_monitoring
        _monitoring_system = get_monitoring()
    return _monitoring_system

def _get_recovery_manager() -> RecoveryManager:
    """Get or create recovery manager instance"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = get_recovery_manager()
    return _recovery_manager

def _get_resource_monitor():
    """Get or create Docker VPS resource monitor instance"""
    global _resource_monitor
    if _resource_monitor is None:
        # Use None as placeholder since DockerVPSResourceMonitor is not defined  
        _resource_monitor = None
    return _resource_monitor

def _get_error_aggregator_local():
    """Get error aggregator with lazy import"""
    from .monitoring import get_error_aggregator
    return get_error_aggregator()

def _get_status_reporter_local():
    """Get status reporter with lazy import"""
    from .monitoring import get_status_reporter
    return get_status_reporter()

# gRPC Timeout Configuration Constants
# These timeouts are tuned for Docker/VPS environments with potential network latency
GRPC_FAST_TIMEOUT = 15.0  # Fast operations: stats, status queries, config fetches
GRPC_SLOW_TIMEOUT = 60.0  # Slow operations: backend restart, container operations
GRPC_STREAM_TIMEOUT = 30.0  # Streaming operations: logs, events, user sync
GRPC_CONNECTION_TIMEOUT = 10.0  # Connection establishment timeout
GRPC_PORT_ACTION_TIMEOUT = 20.0  # Port management operations (firewall changes)

# Connection Pool Configuration Constants
# Optimized for Docker VPS environments with variable network conditions
CONNECTION_POOL_SIZE = 5  # Number of concurrent connections per node
CONNECTION_POOL_MAX_SIZE = 10  # Maximum connections under high load
CONNECTION_LIFETIME = 3600.0  # Connection lifetime in seconds (1 hour)
CONNECTION_POOL_TIMEOUT = 5.0  # Timeout to acquire connection from pool
CONNECTION_IDLE_TIMEOUT = 300.0  # Close idle connections after 5 minutes
CONNECTION_HEALTH_CHECK_INTERVAL = 60.0  # Health check interval in seconds
CONNECTION_RETRY_DELAY = 2.0  # Delay between connection retry attempts

# Type variable for retry decorator
T = TypeVar('T')

# Circuit Breaker Configuration Constants
# Optimized for Docker VPS environments with network instability
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5  # Consecutive failures to open circuit
CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD = 0.5  # 50% error rate threshold
CIRCUIT_BREAKER_MONITORING_WINDOW = 60.0  # Monitoring window in seconds
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30.0  # Time to wait before trying HALF_OPEN
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS = 3  # Max calls to test in HALF_OPEN state
CIRCUIT_BREAKER_RESET_TIMEOUT = 300.0  # Reset circuit breaker metrics after success

from enum import Enum

class CircuitBreakerState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = "CLOSED"    # Normal operation, requests pass through
    OPEN = "OPEN"        # Circuit is open, requests fail immediately
    HALF_OPEN = "HALF_OPEN"  # Testing if service has recovered

# Use the CircuitBreakerError from exceptions module
from .exceptions import CircuitBreakerError


class CircuitBreaker:
    """
    Circuit breaker implementation optimized for Docker VPS environments with network instability.
    
    Features:
    - Three states: CLOSED, OPEN, HALF_OPEN
    - Configurable failure thresholds and recovery timeouts
    - Thread-safe for asyncio environments
    - Integration with existing retry mechanisms
    - Comprehensive metrics and logging
    """
    
    def __init__(
        self,
        failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        error_rate_threshold: float = CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
        monitoring_window: float = CIRCUIT_BREAKER_MONITORING_WINDOW,
        recovery_timeout: float = CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        half_open_max_calls: int = CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS,
        reset_timeout: float = CIRCUIT_BREAKER_RESET_TIMEOUT,
        name: str = "circuit_breaker"
    ):
        # Configuration
        self.failure_threshold = failure_threshold
        self.error_rate_threshold = error_rate_threshold
        self.monitoring_window = monitoring_window
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.reset_timeout = reset_timeout
        self.name = name
        
        # State management
        self._state = CircuitBreakerState.CLOSED
        self._state_lock = asyncio.Lock()
        
        # Failure tracking
        self._consecutive_failures = 0
        self._last_failure_time = None
        self._state_changed_time = time.time()
        
        # Statistics within monitoring window
        self._call_history = []  # List of (timestamp, success) tuples
        
        # Half-open state management
        self._half_open_calls = 0
        self._half_open_successes = 0
        
        # Metrics for monitoring
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'circuit_open_count': 0,
            'circuit_half_open_count': 0,
            'state_changes': 0,
            'last_state_change': None,
            'current_state': self._state.value,
            'consecutive_failures': 0,
            'error_rate': 0.0
        }
        
        logger.info(f"Initialized circuit breaker '{name}' with failure_threshold={failure_threshold}, "
                   f"recovery_timeout={recovery_timeout}s")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerError: When circuit is open
            Exception: Original exception from the function
        """
        async with self._state_lock:
            self._metrics['total_calls'] += 1
            
            # Check if we can make the call
            if not await self._can_execute():
                self._metrics['failed_calls'] += 1
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. Service may be unavailable."
                )
        
        # Execute the function
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _can_execute(self) -> bool:
        """Check if we can execute a call based on current state"""
        current_time = time.time()
        
        if self._state == CircuitBreakerState.CLOSED:
            return True
        elif self._state == CircuitBreakerState.OPEN:
            # Check if we should transition to HALF_OPEN
            if (current_time - self._state_changed_time) >= self.recovery_timeout:
                await self._transition_to_half_open()
                return True
            return False
        elif self._state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in HALF_OPEN state
            return self._half_open_calls < self.half_open_max_calls
        
        return False

    async def _on_success(self):
        """Handle successful call"""
        async with self._state_lock:
            current_time = time.time()
            self._metrics['successful_calls'] += 1
            
            # Record success in call history
            self._call_history.append((current_time, True))
            self._cleanup_old_history(current_time)
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._half_open_successes += 1
                logger.debug(f"Circuit breaker '{self.name}' HALF_OPEN success: "
                           f"{self._half_open_successes}/{self._half_open_calls}")
                
                # If enough successful calls, transition to CLOSED
                if self._half_open_successes >= self.half_open_max_calls:
                    await self._transition_to_closed()
            elif self._state == CircuitBreakerState.CLOSED:
                # Reset consecutive failures on success
                if self._consecutive_failures > 0:
                    self._consecutive_failures = 0
                    self._metrics['consecutive_failures'] = 0
                    logger.debug(f"Circuit breaker '{self.name}' reset consecutive failures")

    async def _on_failure(self, exception: Exception):
        """Handle failed call with enhanced error classification"""
        async with self._state_lock:
            current_time = time.time()
            self._metrics['failed_calls'] += 1
            self._consecutive_failures += 1
            self._metrics['consecutive_failures'] = self._consecutive_failures
            self._last_failure_time = current_time
            
            # Record failure in call history
            self._call_history.append((current_time, False))
            self._cleanup_old_history(current_time)
            
            # Enhanced error logging with structured context
            monitoring = _get_monitoring_system()
            error_context = ErrorContext(
                operation=f"circuit_breaker_{self.name}",
                timestamp=current_time,
                metadata={'circuit_breaker_state': self._state.value}
            )
            
            # Classify exception for better handling
            if isinstance(exception, WildosNodeBaseError):
                structured_error = exception
            elif isinstance(exception, GRPCError):
                structured_error = classify_grpc_error(exception)
            elif isinstance(exception, (OSError, ConnectionError)):
                structured_error = classify_network_error(exception)
            else:
                structured_error = create_error_with_context(
                    ServiceError,
                    f"Circuit breaker failure: {exception}",
                    operation=f"circuit_breaker_{self.name}"
                )
            
            structured_error.context = error_context
            
            # Log with structured logger
            monitoring.logger.error(
                f"Circuit breaker '{self.name}' recorded failure",
                error=structured_error,
                circuit_breaker_name=self.name,
                consecutive_failures=self._consecutive_failures,
                state=self._state.value
            )
            
            # Update metrics
            monitoring.metrics.increment(
                "circuit_breaker_failures_total",
                tags={
                    'circuit_breaker': self.name,
                    'error_type': type(exception).__name__,
                    'error_category': structured_error.category.value
                }
            )
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._half_open_calls += 1
                # Any failure in HALF_OPEN transitions back to OPEN
                monitoring.logger.warning(
                    f"Circuit breaker '{self.name}' failed in HALF_OPEN state, transitioning back to OPEN",
                    circuit_breaker_name=self.name,
                    error_severity=structured_error.severity.value
                )
                await self._transition_to_open()
            elif self._state == CircuitBreakerState.CLOSED:
                # Check if we should transition to OPEN
                if await self._should_open_circuit():
                    await self._transition_to_open()

    async def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure metrics"""
        # Check consecutive failures threshold
        if self._consecutive_failures >= self.failure_threshold:
            logger.warning(f"Circuit breaker '{self.name}' consecutive failure threshold reached: "
                         f"{self._consecutive_failures} >= {self.failure_threshold}")
            return True
        
        # Check error rate threshold within monitoring window
        current_time = time.time()
        recent_calls = [call for call in self._call_history 
                       if current_time - call[0] <= self.monitoring_window]
        
        if len(recent_calls) >= self.failure_threshold:
            failures = len([call for call in recent_calls if not call[1]])
            error_rate = failures / len(recent_calls)
            self._metrics['error_rate'] = error_rate
            
            if error_rate >= self.error_rate_threshold:
                logger.warning(f"Circuit breaker '{self.name}' error rate threshold reached: "
                             f"{error_rate:.2%} >= {self.error_rate_threshold:.2%}")
                return True
        
        return False

    async def _transition_to_open(self):
        """Transition circuit breaker to OPEN state with enhanced monitoring"""
        if self._state != CircuitBreakerState.OPEN:
            monitoring = _get_monitoring_system()
            monitoring.logger.error(
                f"Circuit breaker '{self.name}' opening due to service failures",
                circuit_breaker_name=self.name,
                consecutive_failures=self._consecutive_failures,
                failure_threshold=self.failure_threshold
            )
            
            self._state = CircuitBreakerState.OPEN
            self._state_changed_time = time.time()
            self._metrics['circuit_open_count'] += 1
            self._metrics['state_changes'] += 1
            self._metrics['last_state_change'] = self._state_changed_time
            self._metrics['current_state'] = self._state.value
            
            # Update monitoring metrics
            monitoring.metrics.increment(
                "circuit_breaker_open_total",
                tags={'circuit_breaker': self.name}
            )
            monitoring.metrics.set_gauge(
                "circuit_breaker_state",
                1,  # 1 = OPEN
                tags={'circuit_breaker': self.name}
            )

    async def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state"""
        if self._state != CircuitBreakerState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for service test")
            self._state = CircuitBreakerState.HALF_OPEN
            self._state_changed_time = time.time()
            self._half_open_calls = 0
            self._half_open_successes = 0
            self._metrics['circuit_half_open_count'] += 1
            self._metrics['state_changes'] += 1
            self._metrics['last_state_change'] = self._state_changed_time
            self._metrics['current_state'] = self._state.value

    async def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state with enhanced monitoring"""
        if self._state != CircuitBreakerState.CLOSED:
            monitoring = _get_monitoring_system()
            monitoring.logger.info(
                f"Circuit breaker '{self.name}' closing - service recovered",
                circuit_breaker_name=self.name,
                recovery_time=time.time() - (self._last_failure_time or 0)
            )
            
            self._state = CircuitBreakerState.CLOSED
            self._state_changed_time = time.time()
            self._consecutive_failures = 0
            self._metrics['consecutive_failures'] = 0
            self._metrics['state_changes'] += 1
            self._metrics['last_state_change'] = self._state_changed_time
            self._metrics['current_state'] = self._state.value
            
            # Reset half-open counters
            self._half_open_calls = 0
            self._half_open_successes = 0
            
            # Update monitoring metrics
            monitoring.metrics.increment(
                "circuit_breaker_recovery_total",
                tags={'circuit_breaker': self.name}
            )
            monitoring.metrics.set_gauge(
                "circuit_breaker_state",
                0,  # 0 = CLOSED
                tags={'circuit_breaker': self.name}
            )

    def _cleanup_old_history(self, current_time: float):
        """Remove old entries from call history outside monitoring window"""
        cutoff_time = current_time - self.monitoring_window
        self._call_history = [call for call in self._call_history if call[0] > cutoff_time]

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (normal operation)"""
        return self._state == CircuitBreakerState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open (failing fast)"""
        return self._state == CircuitBreakerState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open (testing recovery)"""
        return self._state == CircuitBreakerState.HALF_OPEN

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics for monitoring"""
        current_time = time.time()
        
        # Calculate current error rate
        recent_calls = [call for call in self._call_history 
                       if current_time - call[0] <= self.monitoring_window]
        if recent_calls:
            failures = len([call for call in recent_calls if not call[1]])
            current_error_rate = failures / len(recent_calls)
        else:
            current_error_rate = 0.0
        
        return {
            **self._metrics,
            'name': self.name,
            'current_error_rate': current_error_rate,
            'recent_calls_count': len(recent_calls),
            'time_since_last_failure': (current_time - self._last_failure_time) if self._last_failure_time else None,
            'time_in_current_state': current_time - self._state_changed_time,
            'configuration': {
                'failure_threshold': self.failure_threshold,
                'error_rate_threshold': self.error_rate_threshold,
                'monitoring_window': self.monitoring_window,
                'recovery_timeout': self.recovery_timeout,
                'half_open_max_calls': self.half_open_max_calls
            }
        }

    async def reset(self):
        """Reset circuit breaker to initial state"""
        async with self._state_lock:
            logger.info(f"Resetting circuit breaker '{self.name}' to initial state")
            self._state = CircuitBreakerState.CLOSED
            self._consecutive_failures = 0
            self._last_failure_time = None
            self._state_changed_time = time.time()
            self._call_history.clear()
            self._half_open_calls = 0
            self._half_open_successes = 0
            
            # Reset metrics except for historical counters
            self._metrics.update({
                'consecutive_failures': 0,
                'error_rate': 0.0,
                'current_state': self._state.value
            })


def circuit_breaker_protected(circuit_breaker_name: str = "grpc_operations"):
    """
    Decorator to protect gRPC operations with circuit breaker pattern
    
    Args:
        circuit_breaker_name: Name of the circuit breaker to use
    
    Usage:
        @circuit_breaker_protected("user_stats")
        async def fetch_users_stats(self):
            # gRPC operation implementation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get circuit breaker from self._circuit_breakers dict
            if not hasattr(self, '_circuit_breakers') or circuit_breaker_name not in self._circuit_breakers:
                # Fallback to direct execution if circuit breaker not initialized
                logger.warning(f"Circuit breaker '{circuit_breaker_name}' not found, executing without protection")
                return await func(self, *args, **kwargs)
            
            circuit_breaker = self._circuit_breakers[circuit_breaker_name]
            return await circuit_breaker.call(func, self, *args, **kwargs)
        
        return wrapper
    return decorator

def enhanced_retry_with_recovery(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    component_name: Optional[str] = None,
    use_recovery_manager: bool = True
):
    """Enhanced retry decorator with recovery strategies and structured error handling
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for first retry
        max_delay: Maximum delay between retries
        backoff_multiplier: Multiplier for exponential backoff
        component_name: Component name for recovery state tracking
        use_recovery_manager: Whether to use recovery manager for advanced recovery
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            monitoring = _get_monitoring_system()
            recovery_manager = _get_recovery_manager() if use_recovery_manager else None
            
            # Create error context
            context = ErrorContext(
                operation=func.__name__,
                timestamp=time.time()
            )
            
            # Extract node_id if available from self
            if args and hasattr(args[0], 'id'):
                context.node_id = args[0].id
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Update context with attempt information
                    context.attempt_number = attempt + 1
                    context.timestamp = time.time()
                    
                    # Handle both async and sync functions
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                        # Check if result is a coroutine or awaitable
                        if asyncio.iscoroutine(result):
                            result = await result
                        elif hasattr(result, '__await__') and callable(getattr(result, '__await__', None)):
                            result = await result
                    
                    # Record successful retry if this wasn't the first attempt
                    if attempt > 0:
                        monitoring.logger.info(
                            f"Retry successful for {func.__name__} on attempt {attempt + 1}",
                            operation=func.__name__,
                            attempt_number=attempt + 1,
                            node_id=context.node_id
                        )
                        
                        monitoring.metrics.increment(
                            "retry_success_total",
                            tags={
                                'operation': func.__name__,
                                'attempt': str(attempt + 1),
                                'component': component_name or 'unknown'
                            }
                        )
                    
                    return result
                    
                except Exception as e:
                    # Classify exception using our structured hierarchy
                    if isinstance(e, WildosNodeBaseError):
                        structured_error = e
                    elif isinstance(e, GRPCError):
                        structured_error = classify_grpc_error(e)
                    elif isinstance(e, (OSError, ConnectionError, StreamTerminatedError)):
                        structured_error = classify_network_error(e)
                    elif isinstance(e, asyncio.TimeoutError):
                        structured_error = create_error_with_context(
                            TimeoutError,
                            f"Operation timeout in {func.__name__}: {e}",
                            operation=func.__name__,
                            node_id=context.node_id
                        )
                    else:
                        structured_error = create_error_with_context(
                            ServiceError,
                            f"Unexpected error in {func.__name__}: {e}",
                            operation=func.__name__,
                            node_id=context.node_id
                        )
                    
                    # Update error context
                    structured_error.context = context
                    last_exception = structured_error
                    
                    # Check if error is retryable
                    if not structured_error.should_retry():
                        monitoring.logger.error(
                            f"{func.__name__} failed with non-retryable error",
                            error=structured_error,
                            operation=func.__name__,
                            node_id=context.node_id
                        )
                        raise structured_error
                    
                    # If this is the last attempt, try recovery manager or fail
                    if attempt == max_retries:
                        if recovery_manager and component_name:
                            try:
                                monitoring.logger.info(
                                    f"Attempting recovery for {func.__name__} after {max_retries} retries",
                                    operation=func.__name__,
                                    component_name=component_name,
                                    error_type=type(structured_error).__name__
                                )
                                
                                # Recovery manager not available - raise original error
                                raise structured_error
                            except Exception as recovery_error:
                                monitoring.logger.error(
                                    f"Recovery failed for {func.__name__}",
                                    error=recovery_error,
                                    original_error=structured_error,
                                    operation=func.__name__
                                )
                                raise structured_error
                        else:
                            monitoring.logger.error(
                                f"{func.__name__} failed after {max_retries} retries",
                                error=structured_error,
                                operation=func.__name__,
                                max_retries=max_retries
                            )
                            raise structured_error
                    
                    # Calculate adaptive delay based on error type
                    delay = structured_error.get_recommended_delay()
                    if delay == 1.0:  # Use our exponential backoff if no specific recommendation
                        delay = min(
                            base_delay * (backoff_multiplier ** attempt),
                            max_delay
                        )
                    
                    # Add jitter to prevent thundering herd
                    jittered_delay = delay * (0.5 + random.random() * 0.5)
                    
                    # Log retry attempt with structured context
                    monitoring.logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, retrying",
                        error=structured_error,
                        operation=func.__name__,
                        attempt_number=attempt + 1,
                        max_retries=max_retries,
                        retry_delay=jittered_delay,
                        error_category=structured_error.category.value,
                        error_severity=structured_error.severity.value,
                        node_id=context.node_id
                    )
                    
                    # Update metrics
                    monitoring.metrics.increment(
                        "retry_attempt_total",
                        tags={
                            'operation': func.__name__,
                            'attempt': str(attempt + 1),
                            'error_type': type(structured_error).__name__,
                            'error_category': structured_error.category.value,
                            'component': component_name or 'unknown'
                        }
                    )
                    
                    await asyncio.sleep(jittered_delay)
            
            # This should never be reached, but just in case
            raise last_exception or Exception("Unexpected retry logic error")
        
        return wrapper
    return decorator

# Keep the old decorator for backward compatibility
def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (OSError, ConnectionError, StreamTerminatedError, asyncio.TimeoutError)
):
    """Legacy retry decorator for backward compatibility"""
    return enhanced_retry_with_recovery(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_multiplier=backoff_multiplier,
        use_recovery_manager=False
    )


def _get_node_status():
    """Ленивый импорт NodeStatus для избежания проблем с PYTHONPATH"""
    from app.models.node import NodeStatus
    return NodeStatus


def _get_certificate_manager():
    """Ленивый импорт CertificateManager для избежания проблем с PYTHONPATH"""
    from app.security.certificate_manager import CertificateManager
    return CertificateManager


def string_to_temp_file(content: str):
    file = tempfile.NamedTemporaryFile(mode="w+t")
    file.write(content)
    file.flush()
    return file


class ConnectionInfo:
    """Information about a connection in the pool"""
    def __init__(self, channel: Channel, stub: WildosServiceStub):
        self.channel = channel
        self.stub = stub
        self.created_at = time.time()
        self.last_used = time.time()
        self.in_use = False
        self.healthy = True
        self.use_count = 0

    def is_expired(self) -> bool:
        """Check if connection has exceeded its lifetime"""
        return (time.time() - self.created_at) > CONNECTION_LIFETIME

    def is_idle(self) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > CONNECTION_IDLE_TIMEOUT

    def mark_used(self):
        """Mark connection as used"""
        self.last_used = time.time()
        self.use_count += 1

    async def close(self):
        """Close the connection"""
        try:
            self.channel.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")


class ConnectionPool:
    """Thread-safe connection pool for gRPC channels optimized for Docker VPS environments"""
    
    def __init__(self, node_id: int, address: str, port: int, ssl_context):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.ssl_context = ssl_context
        
        # Connection pool management
        self._pool: list[ConnectionInfo] = []
        self._pool_lock = asyncio.Lock()
        self._shutdown = False
        
        # Add monitoring system
        self._monitoring = _get_monitoring_system()
        
        # Pool metrics for monitoring
        self._metrics = {
            'connections_created': 0,
            'connections_closed': 0,
            'connections_in_use': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'health_check_failures': 0,
            'last_health_check': 0
        }
        
        # Background tasks
        self._health_check_task = None
        self._cleanup_task = None
        
        logger.info(f"Initialized connection pool for node {node_id} at {address}:{port}")

    async def start(self):
        """Start the connection pool and background tasks"""
        self._health_check_task = asyncio.create_task(self._periodic_health_check())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        # Pre-populate pool with initial connections
        await self._ensure_min_connections()

    async def stop(self):
        """Gracefully shutdown the connection pool"""
        logger.info(f"Shutting down connection pool for node {self.node_id}")
        self._shutdown = True
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        async with self._pool_lock:
            for conn_info in self._pool:
                await conn_info.close()
            self._pool.clear()
            
        logger.info(f"Connection pool shutdown complete for node {self.node_id}")

    async def acquire_connection(self) -> tuple[Channel, WildosServiceStub]:
        """Acquire a connection from the pool with timeout"""
        if self._shutdown:
            raise RuntimeError("Connection pool is shutdown")
        
        start_time = time.time()
        while (time.time() - start_time) < CONNECTION_POOL_TIMEOUT:
            async with self._pool_lock:
                # Try to find an available healthy connection
                for conn_info in self._pool:
                    if not conn_info.in_use and conn_info.healthy and not conn_info.is_expired():
                        conn_info.in_use = True
                        conn_info.mark_used()
                        self._metrics['pool_hits'] += 1
                        self._metrics['connections_in_use'] += 1
                        logger.debug(f"Acquired existing connection for node {self.node_id}")
                        return conn_info.channel, conn_info.stub
                
                # If pool not at max capacity, create new connection
                if len(self._pool) < CONNECTION_POOL_MAX_SIZE:
                    conn_info = await self._create_connection()
                    if conn_info:
                        conn_info.in_use = True
                        self._metrics['pool_misses'] += 1
                        self._metrics['connections_in_use'] += 1
                        logger.debug(f"Created new connection for node {self.node_id}")
                        return conn_info.channel, conn_info.stub
            
            # Wait briefly before retrying
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"Failed to acquire connection for node {self.node_id} within {CONNECTION_POOL_TIMEOUT}s")

    async def release_connection(self, channel: Channel):
        """Release a connection back to the pool"""
        async with self._pool_lock:
            for conn_info in self._pool:
                if conn_info.channel == channel:
                    conn_info.in_use = False
                    self._metrics['connections_in_use'] = max(0, self._metrics['connections_in_use'] - 1)
                    logger.debug(f"Released connection for node {self.node_id}")
                    return
            
            # If connection not found in pool, it might have been removed due to health check
            logger.warning(f"Attempted to release unknown connection for node {self.node_id}")

    async def _create_connection(self) -> ConnectionInfo | None:
        """Create a new connection with enhanced error handling and monitoring"""
        try:
            # Create connection context for monitoring
            context = ErrorContext(
                operation="create_connection",
                node_id=self.node_id,
                remote_address=self.address,
                remote_port=self.port
            )
            
            self._monitoring.logger.debug(
                f"Creating new connection for node {self.node_id}",
                node_id=self.node_id,
                address=self.address,
                port=self.port
            )
            
            channel = Channel(self.address, self.port, ssl=self.ssl_context)
            stub = WildosServiceStub(channel)
            
            # Enhanced connection test with timeout and monitoring
            try:
                # Check if channel has __connect__ method before awaiting
                if hasattr(channel, '__connect__') and callable(getattr(channel, '__connect__')):
                    await asyncio.wait_for(channel.__connect__(), timeout=GRPC_CONNECTION_TIMEOUT)
                
                # Additional health check
                await asyncio.wait_for(
                    stub.FetchBackends(Empty(), metadata=[]),
                    timeout=CONNECTION_HEALTH_CHECK_INTERVAL / 6
                )
                
            except asyncio.TimeoutError as e:
                # Channel.close() might not be awaitable in grpclib
                if hasattr(channel, 'close'):
                    close_result = channel.close()
                    if asyncio.iscoroutine(close_result):
                        await close_result
                timeout_error = create_error_with_context(
                    TimeoutError,
                    f"Connection timeout for node {self.node_id}: {e}",
                    node_id=self.node_id,
                    remote_address=self.address,
                    remote_port=self.port,
                    operation="connection_test"
                )
                self._monitoring.logger.warning(
                    "Connection test timeout",
                    error=timeout_error,
                    node_id=self.node_id
                )
                return None
            
            conn_info = ConnectionInfo(channel, stub)
            self._pool.append(conn_info)
            self._metrics['connections_created'] += 1
            
            # Update monitoring metrics
            self._monitoring.metrics.increment(
                "connection_pool_connections_created_total",
                tags={'node_id': str(self.node_id)}
            )
            
            self._monitoring.logger.debug(
                f"Successfully created connection for node {self.node_id}",
                node_id=self.node_id,
                pool_size=len(self._pool),
                connection_id=id(conn_info)
            )
            
            return conn_info
            
        except Exception as e:
            self._metrics['connection_errors'] += 1
            self._monitoring.metrics.increment(
                "connection_pool_connection_errors_total",
                tags={
                    'node_id': str(self.node_id),
                    'error_type': type(e).__name__
                }
            )
            
            # Classify and enhance the error
            if isinstance(e, WildosNodeBaseError):
                enhanced_error = e
            elif isinstance(e, GRPCError):
                enhanced_error = classify_grpc_error(e)
            elif isinstance(e, (OSError, ConnectionError)):
                enhanced_error = classify_network_error(e)
            elif 'ssl' in str(type(e)).lower():
                enhanced_error = classify_ssl_error(e)
            else:
                enhanced_error = create_error_with_context(
                    ServiceError,
                    f"Failed to create connection for node {self.node_id}: {e}",
                    node_id=self.node_id,
                    remote_address=self.address,
                    remote_port=self.port,
                    operation="create_connection"
                )
            
            self._monitoring.logger.error(
                "Failed to create connection",
                error=enhanced_error,
                node_id=self.node_id,
                address=self.address,
                port=self.port
            )
            
            # Check for Docker VPS specific issues
            await self._check_docker_vps_issues(enhanced_error)
            
            return None

    async def _ensure_min_connections(self):
        """Ensure minimum number of connections in the pool"""
        async with self._pool_lock:
            while len(self._pool) < CONNECTION_POOL_SIZE and not self._shutdown:
                conn_info = await self._create_connection()
                if not conn_info:
                    break

    async def _periodic_health_check(self):
        """Periodically check connection health and remove unhealthy ones"""
        while not self._shutdown:
            try:
                await asyncio.sleep(CONNECTION_HEALTH_CHECK_INTERVAL)
                await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check for node {self.node_id}: {e}")

    # Removed duplicate _health_check method - using the one at line 1254 instead
        
        # Ensure minimum connections after cleanup
        await self._ensure_min_connections()

    async def _periodic_cleanup(self):
        """Periodically clean up idle connections"""
        while not self._shutdown:
            try:
                await asyncio.sleep(CONNECTION_IDLE_TIMEOUT / 2)  # Check more frequently than timeout
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup for node {self.node_id}: {e}")

    async def _cleanup_idle_connections(self):
        """Clean up idle connections that exceed idle timeout"""
        async with self._pool_lock:
            if len(self._pool) <= CONNECTION_POOL_SIZE:
                return  # Don't cleanup if at minimum size
            
            idle_connections = []
            for conn_info in self._pool:
                if not conn_info.in_use and conn_info.is_idle():
                    idle_connections.append(conn_info)
            
            # Keep minimum number of connections
            connections_to_remove = len(idle_connections) - max(0, CONNECTION_POOL_SIZE - (len(self._pool) - len(idle_connections)))
            
            for conn_info in idle_connections[:connections_to_remove]:
                self._pool.remove(conn_info)
                await conn_info.close()
                self._metrics['connections_closed'] += 1
                logger.debug(f"Cleaned up idle connection for node {self.node_id}")

    def get_metrics(self) -> dict:
        """Get enhanced connection pool metrics for monitoring"""
        available_connections = len([c for c in self._pool if not c.in_use and c.healthy])
        
        # Update real-time metrics
        self._monitoring.metrics.set_gauge(
            "connection_pool_size",
            len(self._pool),
            tags={'node_id': str(self.node_id)}
        )
        self._monitoring.metrics.set_gauge(
            "connection_pool_available",
            available_connections,
            tags={'node_id': str(self.node_id)}
        )
        self._monitoring.metrics.set_gauge(
            "connection_pool_network_instability",
            getattr(self, '_network_instability_count', 0),
            tags={'node_id': str(self.node_id)}
        )
        
        return {
            **self._metrics,
            'pool_size': len(self._pool),
            'max_pool_size': CONNECTION_POOL_MAX_SIZE,
            'connections_available': available_connections,
            'connections_unhealthy': len([c for c in self._pool if not c.healthy]),
            'network_instability_count': getattr(self, '_network_instability_count', 0),
            'container_restart_detected': getattr(self, '_container_restart_detected', False),
            'node_id': self.node_id,
            'address': f"{self.address}:{self.port}",
            'component_name': getattr(self, '_component_name', f'connection_pool_node_{self.node_id}')
        }

    async def _check_docker_vps_issues(self, error: WildosNodeBaseError):
        """Check for Docker VPS specific issues and adapt behavior"""
        try:
            # Check for container restart indicators
            if isinstance(error, (NetworkUnstableError, WildosConnectionError)):
                if 'connection refused' in str(error).lower() or 'network unreachable' in str(error).lower():
                    self._container_restart_detected = True
                    self._monitoring.logger.warning(
                        f"Potential container restart detected for node {self.node_id}",
                        node_id=self.node_id,
                        error_type=type(error).__name__,
                        error_message=str(error)
                    )
                    
                    # Trigger recovery strategies
                    self._metrics['recovery_attempts'] += 1
                    
                    # Wait for container to stabilize
                    await asyncio.sleep(5.0)
                    
                    # Clear connection pool to force new connections
                    async with self._pool_lock:
                        for conn_info in self._pool.copy():
                            await conn_info.close()
                        self._pool.clear()
                        self._monitoring.logger.info(
                            f"Cleared connection pool for node {self.node_id} due to container restart",
                            node_id=self.node_id
                        )
            
            # Check for network instability patterns
            if getattr(self, '_network_instability_count', 0) > 5:
                self._monitoring.logger.error(
                    f"High network instability detected for node {self.node_id}",
                    node_id=self.node_id,
                    instability_count=self._network_instability_count,
                    address=f"{self.address}:{self.port}"
                )
                
                # Update monitoring metrics
                self._monitoring.metrics.increment(
                    "docker_vps_network_instability_total",
                    tags={'node_id': str(self.node_id)}
                )
                
        except Exception as e:
            self._monitoring.logger.error(
                "Error in Docker VPS issue check",
                error=e,
                node_id=self.node_id
            )

    async def _check_docker_vps_network_stability(self):
        """Monitor Docker VPS network stability"""
        try:
            current_time = time.time()
            
            # Only check periodically to avoid overhead
            if current_time - getattr(self, '_last_network_check', 0) < 30:
                return
            
            self._last_network_check = current_time
            
            # Check network connectivity patterns
            instability_count = getattr(self, '_network_instability_count', 0)
            if instability_count > 3:
                # Implement adaptive connection pool sizing
                target_pool_size = max(1, CONNECTION_POOL_SIZE - (instability_count // 2))
                
                async with self._pool_lock:
                    if len(self._pool) > target_pool_size:
                        # Reduce pool size under network instability
                        excess_connections = self._pool[target_pool_size:]
                        self._pool = self._pool[:target_pool_size]
                        
                        for conn_info in excess_connections:
                            if not conn_info.in_use:
                                await conn_info.close()
                                
                        self._monitoring.logger.info(
                            f"Reduced connection pool size for node {self.node_id} due to network instability",
                            node_id=self.node_id,
                            new_size=len(self._pool),
                            instability_count=instability_count
                        )
            
            # Reset instability counter if network has been stable
            elif instability_count > 0 and current_time - self._metrics.get('last_health_check', 0) > 120:
                # Network has been stable for 2 minutes
                previous_count = instability_count
                self._network_instability_count = max(0, instability_count - 1)
                
                if previous_count != self._network_instability_count:
                    self._monitoring.logger.info(
                        f"Network stability improving for node {self.node_id}",
                        node_id=self.node_id,
                        instability_count=self._network_instability_count
                    )
                    
        except Exception as e:
            self._monitoring.logger.error(
                "Error in network stability check",
                error=e,
                node_id=self.node_id
            )

    async def _health_check(self) -> bool:
        """Health check for recovery manager integration"""
        try:
            async with self._pool_lock:
                healthy_connections = len([c for c in self._pool if c.healthy and not c.in_use])
                instability_count = getattr(self, '_network_instability_count', 0)
                return healthy_connections > 0 and instability_count < 10
        except Exception:
            return False


class DockerVPSResourceMonitor:
    """Monitors Docker VPS resources and adapts behavior accordingly"""
    
    def __init__(self, monitoring_system: 'MonitoringSystem'):
        self.monitoring = monitoring_system
        self._last_resource_check = 0
        self._resource_constraints = {
            'memory_pressure': False,
            'cpu_pressure': False,
            'disk_pressure': False,
            'network_congestion': False
        }
        self._adaptive_config = {
            'connection_pool_size': CONNECTION_POOL_SIZE,
            'retry_attempts': 3,
            'timeout_multiplier': 1.0,
            'health_check_interval': CONNECTION_HEALTH_CHECK_INTERVAL
        }
    
    async def check_resource_constraints(self) -> Dict[str, bool]:
        """Check for resource constraints and update adaptive configuration"""
        current_time = time.time()
        
        # Only check every 30 seconds to avoid overhead
        if current_time - self._last_resource_check < 30:
            return self._resource_constraints
        
        self._last_resource_check = current_time
        
        try:
            # Check memory usage
            try:
                import psutil
                memory = psutil.virtual_memory()
                self._resource_constraints['memory_pressure'] = memory.percent > 85
                
                cpu = psutil.cpu_percent(interval=1)
                self._resource_constraints['cpu_pressure'] = cpu > 80
                
                disk = psutil.disk_usage('/')
                self._resource_constraints['disk_pressure'] = (disk.percent > 90)
                
            except ImportError:
                # Fallback: check /proc/meminfo and /proc/loadavg if available
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = f.read()
                        # Simple heuristic based on available memory
                        if 'MemAvailable:' in meminfo:
                            for line in meminfo.split('\n'):
                                if line.startswith('MemAvailable:'):
                                    available_kb = int(line.split()[1])
                                    # Consider memory pressure if less than 512MB available
                                    self._resource_constraints['memory_pressure'] = available_kb < 512000
                                    break
                    
                    with open('/proc/loadavg', 'r') as f:
                        loadavg = f.read().strip().split()
                        cpu_load = float(loadavg[0])
                        # Consider CPU pressure if load average > 2.0
                        self._resource_constraints['cpu_pressure'] = cpu_load > 2.0
                        
                except (FileNotFoundError, ValueError, IndexError):
                    # Unable to check resources, assume no pressure
                    pass
            
            # Update adaptive configuration based on constraints
            self._update_adaptive_config()
            
            # Log resource status
            if any(self._resource_constraints.values()):
                self.monitoring.logger.warning(
                    "Resource constraints detected",
                    resource_constraints=self._resource_constraints,
                    adaptive_config=self._adaptive_config
                )
            
            return self._resource_constraints
            
        except Exception as e:
            self.monitoring.logger.error(
                "Error checking resource constraints",
                error=e
            )
            return self._resource_constraints
    
    def _update_adaptive_config(self):
        """Update adaptive configuration based on resource constraints"""
        # Reduce connection pool size under memory pressure
        if self._resource_constraints['memory_pressure']:
            self._adaptive_config['connection_pool_size'] = max(1, CONNECTION_POOL_SIZE // 2)
            self._adaptive_config['timeout_multiplier'] = 1.5
        else:
            self._adaptive_config['connection_pool_size'] = CONNECTION_POOL_SIZE
            self._adaptive_config['timeout_multiplier'] = 1.0
        
        # Reduce retry attempts under CPU pressure
        if self._resource_constraints['cpu_pressure']:
            self._adaptive_config['retry_attempts'] = 2
            self._adaptive_config['health_check_interval'] = CONNECTION_HEALTH_CHECK_INTERVAL * 2
        else:
            self._adaptive_config['retry_attempts'] = 3
            self._adaptive_config['health_check_interval'] = CONNECTION_HEALTH_CHECK_INTERVAL
        
        # Update metrics
        self.monitoring.metrics.set_gauge(
            "docker_vps_resource_pressure",
            sum(self._resource_constraints.values()),
            tags={'type': 'total'}
        )
        
        for constraint, active in self._resource_constraints.items():
            self.monitoring.metrics.set_gauge(
                "docker_vps_resource_pressure",
                1 if active else 0,
                tags={'type': constraint}
            )
    
    def get_adaptive_config(self) -> Dict[str, Any]:
        """Get current adaptive configuration"""
        return self._adaptive_config.copy()
    
    def detect_container_restart(self, error: Exception) -> bool:
        """Enhanced container restart detection"""
        error_str = str(error).lower()
        
        # Enhanced restart detection patterns
        restart_indicators = [
            'connection refused',
            'network unreachable',
            'connection reset',
            'broken pipe',
            'no route to host',
            'temporary failure in name resolution',
            'connection aborted',
            'operation timed out',
            'connection closed by peer'
        ]
        
        # Docker-specific patterns
        docker_patterns = [
            'container not running',
            'container exited',
            'container killed',
            'container stopped',
            'service unavailable'
        ]
        
        # Check for restart indicators
        for pattern in restart_indicators + docker_patterns:
            if pattern in error_str:
                self.monitoring.logger.info(
                    "Container restart detected",
                    pattern=pattern,
                    error_message=error_str
                )
                
                self.monitoring.metrics.increment(
                    "docker_container_restart_detected_total",
                    tags={'pattern': pattern.replace(' ', '_')}
                )
                
                return True
        
        return False
    
    def get_network_stability_score(self, connection_pool: ConnectionPool) -> float:
        """Calculate network stability score (0.0 to 1.0)"""
        try:
            metrics = connection_pool.get_metrics()
            
            # Factor in various metrics
            health_check_failures = metrics.get('health_check_failures', 0)
            total_connections = metrics.get('connections_created', 1)
            network_instability = metrics.get('network_instability_count', 0)
            
            # Calculate scores (higher is better)
            health_score = max(0, 1 - (health_check_failures / max(total_connections, 1)))
            stability_score = max(0, 1 - (network_instability / 20))  # Normalize to 20 failures
            
            overall_score = (health_score + stability_score) / 2
            
            self.monitoring.metrics.set_gauge(
                "docker_vps_network_stability_score",
                overall_score,
                tags={'node_id': str(connection_pool.node_id)}
            )
            
            return overall_score
            
        except Exception as e:
            self.monitoring.logger.error(
                "Error calculating network stability score",
                error=e
            )
            return 0.5  # Neutral score on error


# Enhanced integration functions
def get_integration_status() -> Dict[str, Any]:
    """Get comprehensive integration status for dashboard display"""
    monitoring = _get_monitoring_system()
    recovery_manager = _get_recovery_manager()
    resource_monitor = _get_resource_monitor()
    
    return {
        'monitoring_health': monitoring.get_health_status(),
        'recovery_state': recovery_manager.get_recovery_state('grpc_client_system'),
        'resource_constraints': getattr(resource_monitor, '_resource_constraints', {}).copy() if resource_monitor else {},
        'adaptive_config': resource_monitor.get_adaptive_config() if resource_monitor else {},
        'error_summary': _get_error_aggregator_local().get_dashboard_data(),
        'status_report': _get_status_reporter_local().get_status_report(),
        'timestamp': time.time()
    }

def create_docker_vps_health_check():
    """Create Docker VPS specific health check function"""
    async def docker_vps_health_check() -> Dict[str, Any]:
        resource_monitor = _get_resource_monitor()
        monitoring = _get_monitoring_system()
        
        # Check resource constraints
        if resource_monitor:
            constraints = await resource_monitor.check_resource_constraints()
        else:
            constraints = {}
        
        # Get overall system health
        system_health = monitoring.get_health_status()
        
        # Calculate overall Docker VPS health score
        constraint_count = sum(constraints.values())
        if constraint_count >= 3:
            health_status = 'critical'
        elif constraint_count >= 2:
            health_status = 'degraded'
        elif constraint_count >= 1:
            health_status = 'warning'
        else:
            health_status = 'healthy'
        
        return {
            'docker_vps_health': health_status,
            'resource_constraints': constraints,
            'system_health': system_health['status'],
            'error_rate': system_health['error_rate_percent'],
            'response_time': system_health['avg_response_time_ms'],
            'adaptive_config': resource_monitor.get_adaptive_config() if resource_monitor else {},
            'recommendation': _get_docker_vps_recommendations(constraints),
            'timestamp': time.time()
        }
    
    return docker_vps_health_check

def _get_docker_vps_recommendations(constraints: Dict[str, bool]) -> List[str]:
    """Get recommendations based on resource constraints"""
    recommendations = []
    
    if constraints['memory_pressure']:
        recommendations.append("Consider reducing connection pool size or increasing container memory limit")
    
    if constraints['cpu_pressure']:
        recommendations.append("Reduce concurrent operations or increase CPU allocation")
    
    if constraints['disk_pressure']:
        recommendations.append("Clean up disk space or increase storage allocation")
    
    if constraints['network_congestion']:
        recommendations.append("Check network configuration and reduce network-intensive operations")
    
    if not any(constraints.values()):
        recommendations.append("System resources are healthy")
    
    return recommendations

def setup_enhanced_grpc_monitoring(node_id: int, address: str, port: int):
    """Setup enhanced monitoring for a gRPC node"""
    monitoring = _get_monitoring_system()
    recovery_manager = _get_recovery_manager()
    resource_monitor = _get_resource_monitor()
    # error_aggregator = get_error_aggregator()  # Not available
    # status_reporter = get_status_reporter()  # Not available
    
    # Register component with status reporter - commented out as not available
    # status_reporter.update_component_status(
    #     f'grpc_node_{node_id}',
    #     'healthy',
    #     {'address': f'{address}:{port}', 'initialized': True}
    # )
    
    # Setup resource monitoring alerts - commented out as AlertRule not available
    # monitoring.alerts.add_rule(AlertRule(
    #     name=f"docker_vps_resources_{node_id}",
    #     condition=lambda ms: any(_get_resource_monitor()._resource_constraints.values()),
    #     severity=AlertSeverity.WARNING,
    #     message_template=f"Resource constraints detected for node {node_id} at {{timestamp}}"
    # ))
    
    # Setup network stability alerts - commented out as AlertRule not available
    # monitoring.alerts.add_rule(AlertRule(
    #     name=f"network_stability_{node_id}",
    #     condition=lambda ms: ms.metrics.get_gauge(
    #         "docker_vps_network_stability_score",
    #         tags={'node_id': str(node_id)}
    #     ) and ms.metrics.get_gauge(
    #         "docker_vps_network_stability_score",
    #         tags={'node_id': str(node_id)}
    #     ) < 0.5,
    #     severity=AlertSeverity.ERROR,
    #     message_template=f"Poor network stability detected for node {node_id} at {{timestamp}}"
    # ))
    
    monitoring.logger.info(
        f"Enhanced monitoring setup complete for node {node_id}",
        node_id=node_id,
        address=address,
        port=port,
        components=['monitoring', 'recovery', 'resource_monitor', 'error_aggregator', 'status_reporter']
    )

async def cleanup_enhanced_grpc_client():
    """Cleanup enhanced gRPC client components"""
    global _monitoring_system, _recovery_manager, _resource_monitor
    
    try:
        # Stop monitoring system
        if _monitoring_system:
            await _monitoring_system.stop()
        
        # Reset all global instances
        _monitoring_system = None
        _recovery_manager = None
        _resource_monitor = None
        
        logger.info("Enhanced gRPC client cleanup complete")
        
    except Exception as e:
        logger.error(f"Error during enhanced gRPC client cleanup: {e}")

def get_docker_vps_metrics() -> Dict[str, Any]:
    """Get comprehensive Docker VPS metrics for external monitoring"""
    try:
        monitoring = _get_monitoring_system()
        resource_monitor = _get_resource_monitor()
        error_aggregator = _get_error_aggregator_local()
        
        return {
            'system_metrics': monitoring.get_health_status(),
            'resource_constraints': getattr(resource_monitor, '_resource_constraints', {}) if resource_monitor else {},
            'adaptive_config': resource_monitor.get_adaptive_config() if resource_monitor else {},
            'error_dashboard': error_aggregator.get_dashboard_data(),
            'prometheus_metrics': error_aggregator.export_prometheus_metrics(),
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"Error getting Docker VPS metrics: {e}")
        return {'error': str(e), 'timestamp': time.time()}


class ConnectionContext:
    """Context manager for acquiring and releasing connections from the pool"""
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self.channel = None
        self.stub = None
    
    async def __aenter__(self):
        self.channel, self.stub = await self.pool.acquire_connection()
        return self.channel, self.stub
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.channel:
            await self.pool.release_connection(self.channel)


class WildosNodeGRPCLIB(WildosNodeBase, WildosNodeDB):
    def __init__(
        self,
        node_id: int,
        address: str,
        port: int,
        ssl_key: str,
        ssl_cert: str,
        usage_coefficient: int = 1,
        auth_token: Optional[str] = None,
    ):
        self.id = node_id
        self._address = address
        self._port = port
        self._auth_token = auth_token

        # Create certificate manager to get panel client certificate
        cert_manager = _get_certificate_manager()()
        
        # Get panel client certificate for authentication with node
        client_cert_pem, client_key_pem = cert_manager.get_panel_client_certificate()
        ca_cert_pem = cert_manager.get_client_certificate_bundle()
        
        # Store certificate data for pinning validation
        self._expected_server_cert_pem = None
        self._cert_pinning_enabled = False
        
        # Try to get server certificate from database for certificate pinning
        try:
            from .. import db as app_db  # Lazy import to avoid circular dependencies
            from ..database import get_db
            
            # Get server certificate from database for this node
            db_session = next(get_db())
            try:
                tls_record = app_db.crud.get_tls_certificate(db_session)
                if tls_record and tls_record.certificate:
                    # Validate the certificate before using for pinning
                    cert_validation = cert_manager.validate_certificate(tls_record.certificate)
                    if cert_validation.get('valid', False):
                        self._expected_server_cert_pem = tls_record.certificate
                        self._cert_pinning_enabled = True
                        logger.info(f"Certificate pinning enabled for node {node_id} - expires in {cert_validation.get('days_until_expiry', 'unknown')} days")
                    else:
                        logger.warning(f"Invalid server certificate in database for node {node_id}: {cert_validation.get('error', 'unknown error')}")
                else:
                    logger.info(f"No server certificate found in database for node {node_id} - certificate pinning disabled")
            finally:
                db_session.close()
        except Exception as e:
            logger.warning(f"Failed to retrieve server certificate from database for node {node_id}: {e}")
        
        # Create temp files for certificates
        self._client_cert_file = string_to_temp_file(client_cert_pem)
        self._client_key_file = string_to_temp_file(client_key_pem)
        self._ca_cert_file = string_to_temp_file(ca_cert_pem)

        # Create enhanced SSL context with strict security settings
        self._ssl_context = self._create_strict_ssl_context()
        
        # Enhanced TLS validation and monitoring setup
        monitoring = _get_monitoring_system()
        monitoring.logger.info(
            f"Enhanced TLS context created for node {node_id}",
            node_id=node_id,
            certificate_pinning=self._cert_pinning_enabled,
            hostname_verification=self._ssl_context.check_hostname,
            verify_mode=self._ssl_context.verify_mode.name
        )

        # Initialize connection pool instead of single connection
        self._connection_pool = ConnectionPool(node_id, address, port, self._ssl_context)
        self._pool_initialized = False
        
        # Backward compatibility - keep a primary channel for monitoring
        self._primary_channel = None
        self._primary_stub = None
        
        self._monitor_task = None
        self._streaming_task = None
        self._health_check_task = None  # New health check task
        self._last_health_check = 0.0   # Track last health check time
        self._consecutive_health_failures = 0  # Track consecutive health failures

        self._updates_queue = asyncio.Queue(1)
        self.synced = False
        self.usage_coefficient = usage_coefficient
        
        # Register atexit handler for cleanup
        atexit.register(self._cleanup_sync)
        
        # Initialize circuit breakers for different operation types
        self._circuit_breakers = {
            'user_stats': CircuitBreaker(
                name=f"node_{node_id}_user_stats",
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                error_rate_threshold=CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
                monitoring_window=CIRCUIT_BREAKER_MONITORING_WINDOW
            ),
            'user_sync': CircuitBreaker(
                name=f"node_{node_id}_user_sync",
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD + 2,  # More tolerance for sync operations
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                error_rate_threshold=CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
                monitoring_window=CIRCUIT_BREAKER_MONITORING_WINDOW
            ),
            'backend_operations': CircuitBreaker(
                name=f"node_{node_id}_backend_ops",
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                error_rate_threshold=CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
                monitoring_window=CIRCUIT_BREAKER_MONITORING_WINDOW
            ),
            'logs_streaming': CircuitBreaker(
                name=f"node_{node_id}_logs",
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD + 1,  # Logs are less critical
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT / 2,  # Faster recovery for logs
                error_rate_threshold=CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
                monitoring_window=CIRCUIT_BREAKER_MONITORING_WINDOW
            ),
            'system_monitoring': CircuitBreaker(
                name=f"node_{node_id}_system_monitor",
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                error_rate_threshold=CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
                monitoring_window=CIRCUIT_BREAKER_MONITORING_WINDOW
            )
        }
        
        logger.info(f"Initialized {len(self._circuit_breakers)} circuit breakers for node {node_id}")
    
    def _get_auth_metadata(self) -> list:
        """Get authentication metadata for gRPC calls"""
        if self._auth_token:
            return [('authorization', f'Bearer {self._auth_token}')]
        else:
            # If no token provided, still send empty authorization for debugging
            logger.warning(f"No authentication token provided for node {self.id}")
            return [('authorization', '')]
    
    def set_auth_token(self, token: str):
        """Set or update the authentication token"""
        self._auth_token = token
        logger.info(f"Authentication token updated for node {self.id}")
    
    def get_auth_token(self) -> Optional[str]:
        """Get the current authentication token"""
        return self._auth_token

    async def _initialize_pool(self):
        """Initialize the connection pool and start background tasks"""
        monitoring = _get_monitoring_system()
        recovery_manager = _get_recovery_manager()
        
        try:
            await self._connection_pool.start()
            self._pool_initialized = True
            
            # Get a primary connection for monitoring
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                self._primary_channel = channel
                self._primary_stub = stub
                
                # Start monitoring task
                self._monitor_task = asyncio.create_task(self._monitor_pool())
                
                # Start periodic health check task
                self._health_check_task = asyncio.create_task(self._periodic_health_check())
                
                # Register with recovery manager for auto-reconnect
                recovery_manager.register_component(
                    component_id=f'node_{self.id}',
                    health_check_func=self._health_check,
                    recovery_func=self._recover_connection,
                    component_name=f'WildosNode-{self.id}'
                )
                
            monitoring.logger.info(
                f"Connection pool and health monitoring initialized for node {self.id}",
                node_id=self.id,
                recovery_management=True
            )
            
        except Exception as e:
            structured_error = create_error_with_context(
                ServiceError,
                f"Failed to initialize connection pool for node {self.id}: {e}",
                node_id=self.id,
                operation="initialize_pool"
            )
            
            monitoring.logger.error(
                f"Failed to initialize connection pool for node {self.id}",
                error=structured_error,
                node_id=self.id
            )
            
            self.set_status(_get_node_status().unhealthy, f"pool initialization failed: {e}")
            raise structured_error

    async def _periodic_health_check(self):
        """Periodic health checks with CONNECTION_HEALTH_CHECK_INTERVAL and auto-reconnect"""
        monitoring = _get_monitoring_system()
        recovery_manager = _get_recovery_manager()
        
        monitoring.logger.info(
            f"Starting periodic health checks for node {self.id}",
            node_id=self.id,
            check_interval_seconds=CONNECTION_HEALTH_CHECK_INTERVAL
        )
        
        while not getattr(self._connection_pool, '_shutdown', True):
            try:
                await asyncio.sleep(CONNECTION_HEALTH_CHECK_INTERVAL)
                
                # Perform health check
                health_check_start = time.time()
                is_healthy = await self._health_check()
                health_check_duration = time.time() - health_check_start
                
                self._last_health_check = health_check_start
                
                if is_healthy:
                    self._consecutive_health_failures = 0
                    
                    # Update metrics for successful health check
                    monitoring.metrics.increment(
                        "node_health_check_success_total",
                        tags={'node_id': str(self.id)}
                    )
                    monitoring.metrics.histogram(
                        "node_health_check_duration_seconds",
                        health_check_duration,
                        tags={'node_id': str(self.id), 'result': 'success'}
                    )
                    
                    monitoring.logger.debug(
                        f"Health check passed for node {self.id}",
                        node_id=self.id,
                        health_check_duration_seconds=health_check_duration
                    )
                    
                else:
                    await self._handle_health_failure(health_check_duration)
                    
            except asyncio.CancelledError:
                monitoring.logger.info(f"Health check task cancelled for node {self.id}")
                break
            except Exception as e:
                structured_error = create_error_with_context(
                    ServiceError,
                    f"Error in periodic health check for node {self.id}: {e}",
                    node_id=self.id,
                    operation="periodic_health_check"
                )
                
                monitoring.logger.error(
                    f"Error in periodic health check for node {self.id}",
                    error=structured_error,
                    node_id=self.id
                )
                
                await self._handle_health_failure(0.0, error=structured_error)
    
    async def _health_check(self) -> bool:
        """Comprehensive health check for the node with detailed validation"""
        monitoring = _get_monitoring_system()
        
        try:
            # Check connection pool health
            if not self._connection_pool or self._connection_pool._shutdown:
                monitoring.logger.debug(f"Health check failed for node {self.id}: connection pool not available")
                return False
            
            # Check if we have available connections
            pool_metrics = self._connection_pool.get_metrics()
            if pool_metrics['connections_available'] == 0:
                monitoring.logger.debug(f"Health check failed for node {self.id}: no available connections")
                return False
            
            # Check circuit breaker states
            if hasattr(self, '_circuit_breakers'):
                critical_breakers_open = 0
                for name, breaker in self._circuit_breakers.items():
                    if breaker.is_open:
                        if name in ['user_sync', 'backend_operations']:  # Critical operations
                            critical_breakers_open += 1
                
                if critical_breakers_open > 1:  # Too many critical breakers open
                    monitoring.logger.debug(
                        f"Health check failed for node {self.id}: {critical_breakers_open} critical circuit breakers open"
                    )
                    return False
            
            # Perform actual connectivity test with timeout
            try:
                async with asyncio.timeout(GRPC_FAST_TIMEOUT):
                    async with ConnectionContext(self._connection_pool) as (channel, stub):
                        # Try a lightweight operation to verify connectivity
                        await stub.FetchBackends(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
                        
                monitoring.logger.debug(f"Connectivity test passed for node {self.id}")
                return True
                
            except asyncio.TimeoutError:
                monitoring.logger.debug(f"Health check failed for node {self.id}: connectivity test timeout")
                return False
            except Exception as e:
                monitoring.logger.debug(f"Health check failed for node {self.id}: connectivity test error: {e}")
                return False
                
        except Exception as e:
            monitoring.logger.warning(f"Health check error for node {self.id}: {e}")
            return False
    
    async def _handle_health_failure(self, health_check_duration: float, error: Optional[Exception] = None):
        """Handle health check failure with progressive response and recovery"""
        monitoring = _get_monitoring_system()
        recovery_manager = _get_recovery_manager()
        
        self._consecutive_health_failures += 1
        
        # Update failure metrics
        monitoring.metrics.increment(
            "node_health_check_failure_total",
            tags={'node_id': str(self.id)}
        )
        monitoring.metrics.histogram(
            "node_health_check_duration_seconds",
            health_check_duration,
            tags={'node_id': str(self.id), 'result': 'failure'}
        )
        
        failure_context = {
            'consecutive_failures': self._consecutive_health_failures,
            'last_health_check': self._last_health_check,
            'error': str(error) if error else None
        }
        
        monitoring.logger.warning(
            f"Health check failed for node {self.id} (consecutive failures: {self._consecutive_health_failures})",
            node_id=self.id,
            **failure_context
        )
        
        # Progressive response based on failure count
        if self._consecutive_health_failures == 1:
            # First failure - just log and continue
            monitoring.logger.info(f"First health check failure for node {self.id}, continuing monitoring")
            
        elif self._consecutive_health_failures <= 3:
            # Minor failures - attempt connection pool refresh
            monitoring.logger.warning(f"Minor health failures for node {self.id}, refreshing connection pool")
            try:
                if self._connection_pool:
                    # Force health check on connection pool
                    await self._connection_pool._health_check()
            except Exception as e:
                monitoring.logger.error(f"Failed to refresh connection pool for node {self.id}: {e}")
            
        elif self._consecutive_health_failures <= 5:
            # Moderate failures - trigger recovery
            monitoring.logger.error(f"Moderate health failures for node {self.id}, triggering recovery")
            try:
                await self._recover_connection()
            except Exception as e:
                monitoring.logger.error(f"Recovery failed for node {self.id}: {e}")
            
        else:
            # Severe failures - mark node as unhealthy and notify recovery manager
            monitoring.logger.error(
                f"Severe health failures for node {self.id}, marking unhealthy",
                node_id=self.id,
                consecutive_failures=self._consecutive_health_failures
            )
            
            self.set_status(_get_node_status().unhealthy, "repeated health check failures")
            self.synced = False
            
            # Notify recovery manager of critical failure
            try:
                recovery_manager.report_component_failure(
                    f'node_{self.id}',
                    error or Exception(f"Health check failures: {self._consecutive_health_failures}")
                )
            except Exception as e:
                monitoring.logger.error(f"Failed to report component failure for node {self.id}: {e}")
    
    async def _recover_connection(self) -> bool:
        """Recover connection with enhanced error handling and metrics"""
        monitoring = _get_monitoring_system()
        recovery_start_time = time.time()
        
        monitoring.logger.info(
            f"Starting connection recovery for node {self.id}",
            node_id=self.id,
            consecutive_failures=self._consecutive_health_failures
        )
        
        try:
            # Stop existing connection pool
            if self._connection_pool:
                await self._connection_pool.stop()
            
            # Recreate SSL context in case of certificate issues
            self._ssl_context = self._create_strict_ssl_context()
            
            # Recreate connection pool
            self._connection_pool = ConnectionPool(self.id, self._address, self._port, self._ssl_context)
            
            # Restart connection pool
            await self._connection_pool.start()
            
            # Test connectivity
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                await stub.FetchBackends(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
            
            # Reset failure counter on successful recovery
            self._consecutive_health_failures = 0
            self.set_status(_get_node_status().healthy)
            
            recovery_duration = time.time() - recovery_start_time
            
            monitoring.logger.info(
                f"Connection recovery successful for node {self.id}",
                node_id=self.id,
                recovery_duration_seconds=recovery_duration
            )
            
            # Update recovery metrics
            monitoring.metrics.increment(
                "node_connection_recovery_total",
                tags={'node_id': str(self.id), 'success': 'true'}
            )
            monitoring.metrics.histogram(
                "node_connection_recovery_duration_seconds",
                recovery_duration,
                tags={'node_id': str(self.id)}
            )
            
            return True
            
        except Exception as e:
            recovery_duration = time.time() - recovery_start_time
            
            structured_error = create_error_with_context(
                ServiceError,
                f"Connection recovery failed for node {self.id}: {e}",
                node_id=self.id,
                operation="recover_connection",
                recovery_duration_seconds=recovery_duration
            )
            
            monitoring.logger.error(
                f"Connection recovery failed for node {self.id}",
                error=structured_error,
                node_id=self.id
            )
            
            monitoring.metrics.increment(
                "node_connection_recovery_total",
                tags={'node_id': str(self.id), 'success': 'false', 'error_type': type(e).__name__}
            )
            
            raise structured_error

    def _create_strict_ssl_context(self) -> ssl.SSLContext:
        """Create strict SSL context with enhanced security and certificate pinning"""
        # Create strict SSL context with maximum security
        context = ssl.create_default_context(cafile=self._ca_cert_file.name)
        
        # Enhanced TLS security settings
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        
        # Load client certificate for mutual TLS authentication
        context.load_cert_chain(self._client_cert_file.name, self._client_key_file.name)
        
        # Disable weak protocols and ciphers
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Set secure cipher suites (prioritize strong encryption)
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Enable certificate pinning if we have expected server certificate
        if self._cert_pinning_enabled and self._expected_server_cert_pem:
            # Store original verify callback
            original_verify = context.verify_mode
            
            def certificate_pinning_callback(conn, cert, errno, depth, ok):
                """Custom certificate verification with pinning"""
                if depth == 0:  # Only verify leaf certificate
                    # Get the certificate in PEM format
                    try:
                        cert_der = ssl.DER_cert_to_PEM_cert(cert.to_bytes())
                        if cert_der.strip() == self._expected_server_cert_pem.strip():
                            monitoring = _get_monitoring_system()
                            monitoring.logger.debug(
                                f"Certificate pinning verification passed for node {self.id}",
                                node_id=self.id
                            )
                            monitoring.metrics.increment(
                                "tls_certificate_pinning_success_total",
                                tags={'node_id': str(self.id)}
                            )
                            return ok
                        else:
                            monitoring = _get_monitoring_system()
                            monitoring.logger.error(
                                f"Certificate pinning verification FAILED for node {self.id} - certificate mismatch",
                                node_id=self.id
                            )
                            monitoring.metrics.increment(
                                "tls_certificate_pinning_failure_total",
                                tags={'node_id': str(self.id), 'reason': 'certificate_mismatch'}
                            )
                            return False
                    except Exception as e:
                        monitoring = _get_monitoring_system()
                        monitoring.logger.error(
                            f"Certificate pinning verification error for node {self.id}: {e}",
                            node_id=self.id,
                            error=str(e)
                        )
                        monitoring.metrics.increment(
                            "tls_certificate_pinning_failure_total",
                            tags={'node_id': str(self.id), 'reason': 'verification_error'}
                        )
                        return False
                return ok
            
            # Note: Python's ssl module doesn't support custom verify callbacks in the same way as OpenSSL
            # We'll implement pinning verification during connection establishment instead
            logger.info(f"Certificate pinning configured for node {self.id}")
        
        # Additional security options
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_COMPRESSION  # Disable compression to prevent CRIME attacks
        context.options |= ssl.OP_SINGLE_DH_USE   # Use new DH key for each connection
        context.options |= ssl.OP_SINGLE_ECDH_USE # Use new ECDH key for each connection
        
        monitoring = _get_monitoring_system()
        monitoring.logger.info(
            f"Strict SSL context created for node {self.id}",
            node_id=self.id,
            min_tls_version=context.minimum_version.name,
            max_tls_version=context.maximum_version.name,
            certificate_pinning=self._cert_pinning_enabled
        )
        
        return context
    
    def _cleanup_sync(self):
        """Synchronous cleanup for atexit handler"""
        try:
            # Use asyncio.create_task if there's a running loop
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.stop())
                loop.close()
            else:
                # Running loop exists, schedule cleanup
                asyncio.create_task(self.stop())
        except Exception as e:
            logger.error(f"Error during cleanup for node {self.id}: {e}")

    async def stop(self):
        """Enhanced graceful stop with comprehensive cleanup and monitoring integration"""
        monitoring = _get_monitoring_system()
        recovery_manager = _get_recovery_manager()
        
        monitoring.logger.info(
            f"Initiating graceful shutdown for node {self.id}",
            node_id=self.id,
            operation="stop"
        )
        
        shutdown_start_time = time.time()
        
        try:
            # Cancel health check task first
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await asyncio.wait_for(self._health_check_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    monitoring.logger.debug(f"Health check task cancelled for node {self.id}")
            
            # Cancel background monitoring tasks
            tasks_to_cancel = []
            if self._monitor_task and not self._monitor_task.done():
                tasks_to_cancel.append(('monitor', self._monitor_task))
            if self._streaming_task and not self._streaming_task.done():
                tasks_to_cancel.append(('streaming', self._streaming_task))
            
            # Cancel all tasks with timeout
            for task_name, task in tasks_to_cancel:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=10.0)
                    monitoring.logger.debug(f"{task_name} task stopped gracefully for node {self.id}")
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    monitoring.logger.warning(f"{task_name} task force cancelled for node {self.id}")
            
            # Reset all circuit breakers to clean state
            if hasattr(self, '_circuit_breakers'):
                for name, circuit_breaker in self._circuit_breakers.items():
                    try:
                        await circuit_breaker.reset()
                        monitoring.logger.debug(f"Reset circuit breaker '{name}' for node {self.id}")
                    except Exception as e:
                        monitoring.logger.warning(f"Failed to reset circuit breaker '{name}' for node {self.id}: {e}")
            
            # Gracefully shutdown connection pool with timeout
            if self._connection_pool:
                try:
                    await asyncio.wait_for(self._connection_pool.stop(), timeout=15.0)
                    monitoring.logger.info(f"Connection pool stopped gracefully for node {self.id}")
                except asyncio.TimeoutError:
                    monitoring.logger.warning(f"Connection pool stop timeout for node {self.id}")
                except Exception as e:
                    monitoring.logger.error(f"Error stopping connection pool for node {self.id}: {e}")
            
            # Update node status to indicate shutdown
            try:
                self.set_status(_get_node_status().unhealthy, "shutdown")
                self.synced = False
            except Exception as e:
                monitoring.logger.warning(f"Failed to update node {self.id} status during shutdown: {e}")
            
            # Cleanup temporary certificate files
            try:
                if hasattr(self, '_client_cert_file') and self._client_cert_file:
                    self._client_cert_file.close()
                if hasattr(self, '_client_key_file') and self._client_key_file:
                    self._client_key_file.close()
                if hasattr(self, '_ca_cert_file') and self._ca_cert_file:
                    self._ca_cert_file.close()
                monitoring.logger.debug(f"Cleaned up certificate files for node {self.id}")
            except Exception as e:
                monitoring.logger.warning(f"Failed to cleanup certificate files for node {self.id}: {e}")
            
            # Unregister from recovery manager if present
            try:
                recovery_manager.unregister_component(f'node_{self.id}')
                monitoring.logger.debug(f"Unregistered node {self.id} from recovery manager")
            except Exception as e:
                monitoring.logger.debug(f"Failed to unregister node {self.id} from recovery manager: {e}")
            
            shutdown_duration = time.time() - shutdown_start_time
            
            monitoring.logger.info(
                f"Node {self.id} gRPC client stopped successfully",
                node_id=self.id,
                shutdown_duration_seconds=shutdown_duration
            )
            
            # Update metrics
            monitoring.metrics.increment(
                "node_graceful_shutdown_total",
                tags={'node_id': str(self.id), 'success': 'true'}
            )
            monitoring.metrics.histogram(
                "node_shutdown_duration_seconds",
                shutdown_duration,
                tags={'node_id': str(self.id)}
            )
            
        except Exception as e:
            shutdown_duration = time.time() - shutdown_start_time
            
            # Create structured error
            structured_error = create_error_with_context(
                ServiceError,
                f"Error during node {self.id} shutdown: {e}",
                node_id=self.id,
                operation="stop",
                shutdown_duration_seconds=shutdown_duration
            )
            
            monitoring.logger.error(
                f"Error during graceful shutdown of node {self.id}",
                error=structured_error,
                node_id=self.id
            )
            
            monitoring.metrics.increment(
                "node_graceful_shutdown_total",
                tags={'node_id': str(self.id), 'success': 'false', 'error_type': type(e).__name__}
            )
            
            raise structured_error

    async def _monitor_pool(self):
        """Monitor connection pool health and manage node synchronization"""
        while not self._connection_pool._shutdown:
            try:
                # Check if pool is healthy and has connections
                pool_metrics = self._connection_pool.get_metrics()
                available_connections = pool_metrics['connections_available']
                
                # Also log circuit breaker status
                cb_metrics = self.get_circuit_breaker_metrics()
                open_breakers = [name for name, metrics in cb_metrics.items() 
                               if metrics.get('current_state') == 'OPEN']
                half_open_breakers = [name for name, metrics in cb_metrics.items() 
                                    if metrics.get('current_state') == 'HALF_OPEN']
                
                if open_breakers or half_open_breakers:
                    logger.warning("node %i circuit breaker status - OPEN: %s, HALF_OPEN: %s", 
                                 self.id, open_breakers, half_open_breakers)
                else:
                    logger.debug("node %i pool status: %d/%d connections available, all circuit breakers CLOSED", 
                               self.id, available_connections, pool_metrics['pool_size'])
                
                if available_connections > 0:
                    # Pool is healthy, ensure node is synced
                    if not self.synced:
                        try:
                            await self._sync()
                        except Exception as e:
                            logger.warning(f"Failed to sync node {self.id}: {e}")
                            self.set_status(_get_node_status().unhealthy, "sync failed")
                        else:
                            # Start streaming task after successful sync
                            if not self._streaming_task or self._streaming_task.done():
                                self._streaming_task = asyncio.create_task(
                                    self._stream_user_updates()
                                )
                            self.set_status(_get_node_status().healthy)
                            logger.info("Node %i synced and ready", self.id)
                else:
                    # No available connections
                    logger.warning("node %i has no available connections", self.id)
                    self.set_status(_get_node_status().unhealthy, "no available connections")
                    self.synced = False
                    if self._streaming_task:
                        self._streaming_task.cancel()
                        
            except Exception as e:
                logger.error(f"Error in pool monitoring for node {self.id}: {e}")
                self.set_status(_get_node_status().unhealthy, f"monitoring error: {e}")
                self.synced = False
                
            await asyncio.sleep(10)

    async def _stream_user_updates(self):
        """Stream user updates using connection from the pool"""
        try:
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                async with stub.SyncUsers.open(timeout=GRPC_STREAM_TIMEOUT, metadata=self._get_auth_metadata()) as stream:
                    logger.debug("opened the stream for node %i", self.id)
                    while True:
                        user_update = await self._updates_queue.get()
                        logger.debug("got user update from queue for node %i", self.id)
                        user = user_update["user"]
                        await stream.send_message(
                            UserData(
                                user=User(
                                    id=user.id,
                                    username=user.username,
                                    key=user.key,
                                ),
                                inbounds=[
                                    Inbound(tag=t) for t in user_update["inbounds"]
                                ],
                            )
                        )
        except (OSError, ConnectionError, GRPCError, StreamTerminatedError) as e:
            logger.info("node %i streaming detached: %s", self.id, e)
            self.synced = False
        except Exception as e:
            logger.error("Unexpected error in user updates stream for node %i: %s", self.id, e)
            self.synced = False

    async def update_user(self, user, inbounds: set[str] | None = None):
        if inbounds is None:
            inbounds = set()

        await self._updates_queue.put({"user": user, "inbounds": inbounds})

    @circuit_breaker_protected("user_sync")
    @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
    async def _repopulate_users(self, users_data: list[dict]) -> None:
        """Repopulate users using connection from the pool"""
        updates = [
            UserData(
                user=User(id=u["id"], username=u["username"], key=u["key"]),
                inbounds=[Inbound(tag=t) for t in u["inbounds"]],
            )
            for u in users_data
        ]
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            await stub.RepopulateUsers(UsersData(users_data=updates), timeout=GRPC_SLOW_TIMEOUT, metadata=self._get_auth_metadata())

    @circuit_breaker_protected("user_stats")
    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    async def fetch_users_stats(self) -> None:
        """Fetch user statistics using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response = await stub.FetchUsersStats(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
            return None

    @circuit_breaker_protected("backend_operations")
    @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
    async def _fetch_backends(self) -> list:
        """Fetch backends using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response = await stub.FetchBackends(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
            return list(response.backends)

    async def _sync(self):
        backends = await self._fetch_backends()
        self.store_backends(backends)
        users = self.list_users()
        await self._repopulate_users(users)
        self.synced = True

    async def get_logs(self, name: str = "xray", include_buffer=True):
        """Stream backend logs using connection from the pool with circuit breaker protection"""
        # Check circuit breaker before starting stream
        if hasattr(self, '_circuit_breakers') and 'logs_streaming' in self._circuit_breakers:
            circuit_breaker = self._circuit_breakers['logs_streaming']
            if circuit_breaker.is_open:
                raise CircuitBreakerError(f"Circuit breaker 'logs_streaming' is OPEN. Service may be unavailable.")
        
        try:
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                async with stub.StreamBackendLogs.open(timeout=GRPC_STREAM_TIMEOUT, metadata=self._get_auth_metadata()) as stm:
                    await stm.send_message(
                        BackendLogsRequest(
                            backend_name=name, include_buffer=include_buffer
                        )
                    )
                    while True:
                        response = await stm.recv_message()
                        if response:
                            yield response.line
                        # Record success for each yielded log line
                        if hasattr(self, '_circuit_breakers') and 'logs_streaming' in self._circuit_breakers:
                            await self._circuit_breakers['logs_streaming']._on_success()
        except Exception as e:
            # Record failure in circuit breaker
            if hasattr(self, '_circuit_breakers') and 'logs_streaming' in self._circuit_breakers:
                await self._circuit_breakers['logs_streaming']._on_failure(e)
            raise

    @circuit_breaker_protected("backend_operations")
    async def restart_backend(
        self, name: str, config: str, config_format: int
    ):
        """Restart backend using connection from the pool"""
        try:
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                await stub.RestartBackend(
                    RestartBackendRequest(
                        backend_name=name,
                        config=BackendConfig(
                            configuration=config, config_format=ConfigFormat(config_format)
                        ),
                    ), timeout=GRPC_SLOW_TIMEOUT, metadata=self._get_auth_metadata()
                )
            await self._sync()
        except:
            self.synced = False
            self.set_status(_get_node_status().unhealthy)
            raise
        else:
            self.set_status(_get_node_status().healthy)

    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("backend_operations")
    async def get_backend_config(self, name: str) -> tuple[str, str]:
        """Get backend configuration using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response: BackendConfig = await stub.FetchBackendConfig(
                Backend(name=name), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata()
            )
            config_format = response.config_format
            config_format_str = str(config_format)
            return str(response.configuration), config_format_str

    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("backend_operations")
    async def get_backend_stats(self, name: str) -> None:
        """Get backend statistics using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response: BackendStats = await stub.GetBackendStats(
                Backend(name=name), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata()
            )
            return None

    # Peak Events Monitoring Methods
    async def stream_peak_events(self):
        """Stream real-time peak events from node using connection from the pool"""
        try:
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                async with stub.StreamPeakEvents.open(timeout=GRPC_STREAM_TIMEOUT, metadata=self._get_auth_metadata()) as stream:
                    await stream.send_message(Empty())
                    async for event in stream:
                        yield event
        except (OSError, ConnectionError, GRPCError, StreamTerminatedError) as e:
            logger.error(f"Failed to stream peak events from node {self.id}: {e}")
            self.set_status(_get_node_status().unhealthy, "peak events stream unavailable")
            self.synced = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error streaming peak events from node {self.id}: {e}")
            raise

    async def fetch_peak_events(self, since_ms: int = 0, category=None):
        """Fetch historical peak events from node using connection from the pool"""
        try:
            query = PeakQuery(since_ms=since_ms)
            if category:
                query.category = category
            async with ConnectionContext(self._connection_pool) as (channel, stub):
                async with stub.FetchPeakEvents.open(timeout=GRPC_STREAM_TIMEOUT, metadata=self._get_auth_metadata()) as stream:
                    await stream.send_message(query)
                    async for event in stream:
                        yield event
        except (OSError, ConnectionError, GRPCError, StreamTerminatedError) as e:
            logger.error(f"Failed to fetch peak events from node {self.id}: {e}")
            self.set_status(_get_node_status().unhealthy, "peak events fetch unavailable")
            self.synced = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching peak events from node {self.id}: {e}")
            raise

    # Host System Monitoring Methods
    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("system_monitoring")
    async def get_host_system_metrics(self):
        """Get comprehensive host system metrics using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response: HostSystemMetrics = await stub.GetHostSystemMetrics(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
            return response

    @retry_with_exponential_backoff(max_retries=1, base_delay=1.0)  # Reduced retries for idempotency
    @circuit_breaker_protected("system_monitoring")
    async def open_host_port(self, port: int, protocol: str = "tcp"):
        """Open a port on host system firewall using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            request = PortActionRequest(port=port, protocol=protocol)
            response: PortActionResponse = await stub.OpenHostPort(request, timeout=GRPC_PORT_ACTION_TIMEOUT, metadata=self._get_auth_metadata())
            return response.success

    @retry_with_exponential_backoff(max_retries=1, base_delay=1.0)  # Reduced retries for idempotency
    @circuit_breaker_protected("system_monitoring")
    async def close_host_port(self, port: int, protocol: str = "tcp"):
        """Close a port on host system firewall using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            request = PortActionRequest(port=port, protocol=protocol)
            response: PortActionResponse = await stub.CloseHostPort(request, timeout=GRPC_PORT_ACTION_TIMEOUT, metadata=self._get_auth_metadata())
            return response.success

    # Container Management Methods
    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("logs_streaming")
    async def get_container_logs(self, tail: int = 100):
        """Get container logs using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            request = ContainerLogsRequest(tail=tail)
            response: ContainerLogsResponse = await stub.GetContainerLogs(request, timeout=GRPC_SLOW_TIMEOUT, metadata=self._get_auth_metadata())
            return response.logs

    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("backend_operations")
    async def get_container_files(self, path: str = "/app"):
        """Get list of files in container directory using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            request = ContainerFilesRequest(path=path)
            response: ContainerFilesResponse = await stub.GetContainerFiles(request, timeout=GRPC_SLOW_TIMEOUT, metadata=self._get_auth_metadata())
            return response.files

    @retry_with_exponential_backoff(max_retries=1, base_delay=2.0)  # Limited retries for container restart
    @circuit_breaker_protected("backend_operations")
    async def restart_container(self):
        """Restart the node's container using connection from the pool"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response: ContainerRestartResponse = await stub.RestartContainer(Empty(), timeout=GRPC_SLOW_TIMEOUT, metadata=self._get_auth_metadata())
            return response.success

    # Batch Operations
    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5)
    @circuit_breaker_protected("backend_operations")
    async def get_all_backends_stats(self):
        """Get stats for all backends in one request using connection from the pool (performance optimization)"""
        async with ConnectionContext(self._connection_pool) as (channel, stub):
            response: AllBackendsStatsResponse = await stub.GetAllBackendsStats(Empty(), timeout=GRPC_FAST_TIMEOUT, metadata=self._get_auth_metadata())
            return dict(response.backend_stats)

    # Connection Pool Management and Metrics
    def get_connection_pool_metrics(self) -> dict:
        """Get connection pool metrics for monitoring and debugging"""
        if not self._connection_pool:
            return {'error': 'Connection pool not initialized'}
        
        return self._connection_pool.get_metrics()

    def get_circuit_breaker_metrics(self) -> dict:
        """Get all circuit breaker metrics for monitoring"""
        if not hasattr(self, '_circuit_breakers'):
            return {}
        
        return {
            name: breaker.get_metrics() 
            for name, breaker in self._circuit_breakers.items()
        }

    def get_overall_circuit_breaker_health(self) -> dict:
        """Get overall health status of all circuit breakers"""
        if not hasattr(self, '_circuit_breakers'):
            return {'healthy': True, 'reason': 'No circuit breakers configured'}
        
        metrics = self.get_circuit_breaker_metrics()
        open_breakers = [name for name, m in metrics.items() if m.get('current_state') == 'OPEN']
        half_open_breakers = [name for name, m in metrics.items() if m.get('current_state') == 'HALF_OPEN']
        
        if open_breakers:
            return {
                'healthy': False,
                'reason': f'Circuit breakers OPEN: {", ".join(open_breakers)}',
                'open_breakers': open_breakers,
                'half_open_breakers': half_open_breakers,
                'total_breakers': len(self._circuit_breakers)
            }
        elif half_open_breakers:
            return {
                'healthy': True,  # Half-open is transitional, not unhealthy
                'reason': f'Circuit breakers in HALF_OPEN (testing recovery): {", ".join(half_open_breakers)}',
                'open_breakers': [],
                'half_open_breakers': half_open_breakers,
                'total_breakers': len(self._circuit_breakers)
            }
        else:
            return {
                'healthy': True,
                'reason': 'All circuit breakers CLOSED (healthy)',
                'open_breakers': [],
                'half_open_breakers': [],
                'total_breakers': len(self._circuit_breakers)
            }

    async def get_connection_pool_health(self) -> dict:
        """Get detailed connection pool health information"""
        if not self._connection_pool:
            return {
                'healthy': False,
                'reason': 'Connection pool not initialized',
                'pool_initialized': self._pool_initialized
            }
        
        metrics = self._connection_pool.get_metrics()
        
        # Determine overall health
        healthy = (
            self._pool_initialized and
            not self._connection_pool._shutdown and
            metrics['connections_available'] > 0 and
            metrics['pool_size'] > 0
        )
        
        health_info = {
            'healthy': healthy,
            'pool_initialized': self._pool_initialized,
            'pool_shutdown': self._connection_pool._shutdown,
            'node_synced': self.synced,
            'metrics': metrics,
            'last_health_check_age': time.time() - metrics.get('last_health_check', 0)
        }
        
        if not healthy:
            health_info['issues'] = []
            if not self._pool_initialized:
                health_info['issues'].append('Pool not initialized')
            if self._connection_pool._shutdown:
                health_info['issues'].append('Pool is shutdown')
            if metrics['connections_available'] == 0:
                health_info['issues'].append('No available connections')
            if metrics['pool_size'] == 0:
                health_info['issues'].append('Empty connection pool')
        
        return health_info





