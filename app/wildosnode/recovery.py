"""
Enhanced recovery mechanisms for gRPC client operations.

This module provides sophisticated recovery strategies specifically designed
for Docker VPS environments with improved error handling, state recovery,
and graceful degradation capabilities.
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, List, Optional, Callable, Any, Union, Awaitable, TypeVar
from weakref import WeakSet

from .exceptions import (
    WildosNodeBaseError, ErrorContext, ErrorSeverity, ErrorCategory, 
    RecoveryStrategy as RecoveryStrategyEnum,
    NetworkError, ServiceError, TimeoutError, AuthenticationError, ConfigurationError,
    classify_grpc_error, classify_network_error, classify_ssl_error,
    create_error_with_context, ServiceUnavailableError, ConnectionError,
    ContainerRestartError, NetworkUnstableError, CircuitBreakerError
)

# Import with lazy loading to avoid circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grpclib import GRPCError
    from grpclib.exceptions import StreamTerminatedError

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Recovery Configuration Constants
RECOVERY_STATE_CACHE_SIZE = 1000
RECOVERY_STATE_TTL = 3600.0  # 1 hour
FALLBACK_CACHE_SIZE = 500
FALLBACK_CACHE_TTL = 300.0   # 5 minutes
HEALTH_CHECK_INTERVAL = 30.0  # 30 seconds
HEALTH_CHECK_TIMEOUT = 5.0    # 5 seconds


class RecoveryMode(Enum):
    """Recovery operation modes"""
    NORMAL = "normal"           # Normal operation mode
    DEGRADED = "degraded"       # Degraded performance mode
    EMERGENCY = "emergency"     # Emergency/minimal functionality mode
    OFFLINE = "offline"         # Offline/cached data only mode


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class RecoveryState:
    """State information for recovery operations"""
    component_name: str
    last_success_time: float = field(default_factory=time.time)
    last_failure_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    recovery_attempts: int = 0
    current_mode: RecoveryMode = RecoveryMode.NORMAL
    health_status: HealthStatus = HealthStatus.HEALTHY
    
    # Recovery metrics
    total_failures: int = 0
    total_recoveries: int = 0
    average_recovery_time: float = 0.0
    
    # Context information
    last_error: Optional[WildosNodeBaseError] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_success(self):
        """Update state after successful operation"""
        self.last_success_time = time.time()
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        
        # Upgrade health status
        if self.health_status == HealthStatus.UNHEALTHY and self.consecutive_successes >= 3:
            self.health_status = HealthStatus.DEGRADED
        elif self.health_status == HealthStatus.DEGRADED and self.consecutive_successes >= 5:
            self.health_status = HealthStatus.HEALTHY
            self.current_mode = RecoveryMode.NORMAL
    
    def update_failure(self, error: WildosNodeBaseError):
        """Update state after failed operation"""
        self.last_failure_time = time.time()
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_error = error
        
        # Downgrade health status
        if self.consecutive_failures >= 3:
            self.health_status = HealthStatus.UNHEALTHY
            self.current_mode = RecoveryMode.DEGRADED
        elif self.consecutive_failures >= 5:
            self.current_mode = RecoveryMode.EMERGENCY
        elif self.consecutive_failures >= 10:
            self.current_mode = RecoveryMode.OFFLINE
        elif self.consecutive_failures >= 1:
            self.health_status = HealthStatus.DEGRADED
    
    def should_attempt_recovery(self) -> bool:
        """Determine if recovery should be attempted"""
        if self.current_mode == RecoveryMode.OFFLINE:
            return False
        
        # Rate limit recovery attempts
        if self.last_failure_time:
            time_since_failure = time.time() - self.last_failure_time
            min_interval = min(60.0, 2.0 ** self.recovery_attempts)
            return time_since_failure >= min_interval
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/monitoring"""
        return {
            'component_name': self.component_name,
            'last_success_time': self.last_success_time,
            'last_failure_time': self.last_failure_time,
            'consecutive_failures': self.consecutive_failures,
            'consecutive_successes': self.consecutive_successes,
            'recovery_attempts': self.recovery_attempts,
            'current_mode': self.current_mode.value,
            'health_status': self.health_status.value,
            'total_failures': self.total_failures,
            'total_recoveries': self.total_recoveries,
            'average_recovery_time': self.average_recovery_time,
            'last_error_type': type(self.last_error).__name__ if self.last_error else None,
            'metadata': self.metadata
        }


@dataclass
class FallbackData:
    """Cached fallback data for when primary services are unavailable"""
    key: str
    data: Any
    cached_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + FALLBACK_CACHE_TTL)
    source: str = "cache"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cached data has expired"""
        return time.time() > self.expires_at
    
    def is_stale(self, max_age: float = 60.0) -> bool:
        """Check if data is stale (older than max_age seconds)"""
        return (time.time() - self.cached_at) > max_age


class RecoveryStrategy(ABC):
    """Abstract base class for recovery strategies"""
    
    @abstractmethod
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        error: WildosNodeBaseError,
        context: ErrorContext,
        *args, 
        **kwargs
    ) -> T:
        """Execute recovery strategy"""
        pass
    
    @abstractmethod
    def can_handle(self, error: WildosNodeBaseError) -> bool:
        """Check if this strategy can handle the given error"""
        pass


class RetryStrategy(RecoveryStrategy):
    """Enhanced retry strategy with adaptive backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter_factor: float = 0.1
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter_factor = jitter_factor
    
    def can_handle(self, error: WildosNodeBaseError) -> bool:
        """Check if error is retryable"""
        return error.retryable and RecoveryStrategyEnum.RETRY in error.recovery_strategies
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        error: WildosNodeBaseError,
        context: ErrorContext,
        *args, 
        **kwargs
    ) -> T:
        """Execute retry strategy with adaptive backoff"""
        last_exception = error
        
        for attempt in range(self.max_retries):
            try:
                # Update context with attempt number
                if context:
                    context.attempt_number = attempt + 2  # +2 because original call was attempt 1
                    context.recovery_attempts += 1
                
                result = await func(*args, **kwargs)
                
                # Log successful recovery
                logger.info(
                    f"Retry strategy succeeded on attempt {attempt + 1} for {func.__name__}: "
                    f"recovered from {type(error).__name__}"
                )
                
                return result
                
            except Exception as e:
                # Classify the new exception
                if isinstance(e, WildosNodeBaseError):
                    last_exception = e
                else:
                    # Convert to structured exception
                    last_exception = self._classify_exception(e, context)
                
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Retry strategy failed after {self.max_retries} attempts for {func.__name__}: "
                        f"{type(last_exception).__name__}: {last_exception}"
                    )
                    raise last_exception
                
                # Calculate adaptive delay
                delay = self._calculate_delay(attempt, last_exception)
                
                logger.warning(
                    f"Retry attempt {attempt + 1} failed for {func.__name__}: "
                    f"{type(last_exception).__name__}: {last_exception}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, error: WildosNodeBaseError) -> float:
        """Calculate adaptive delay based on error type and attempt"""
        # Base exponential backoff
        base_delay = min(
            self.base_delay * (self.backoff_multiplier ** attempt),
            self.max_delay
        )
        
        # Adjust delay based on error type
        if isinstance(error, NetworkError):
            # Network errors might benefit from longer delays
            base_delay *= 1.5
        elif isinstance(error, TimeoutError):
            # Timeout errors might benefit from shorter delays initially
            base_delay *= 0.8
        elif isinstance(error, ServiceError):
            # Service errors - use standard delay
            pass
        
        # Add jitter to prevent thundering herd
        jitter = base_delay * self.jitter_factor * (random.random() - 0.5)
        delay = base_delay + jitter
        
        return max(0.1, delay)  # Minimum 100ms delay
    
    def _classify_exception(self, exception: Exception, context: ErrorContext) -> WildosNodeBaseError:
        """Classify generic exception into structured error"""
        if hasattr(exception, 'status'):  # gRPC error
            return classify_grpc_error(exception)
        elif isinstance(exception, (OSError, ConnectionError)):
            return classify_network_error(exception)
        elif 'ssl' in str(type(exception)).lower():
            return classify_ssl_error(exception)
        else:
            # Generic service error
            return create_error_with_context(
                ServiceError,
                f"Unexpected error: {exception}",
                operation=context.operation if context else None,
                node_id=context.node_id if context else None,
                original_error_type=type(exception).__name__
            )


class ReconnectionStrategy(RecoveryStrategy):
    """Strategy for re-establishing connections"""
    
    def __init__(self, connection_factory: Callable[[], Awaitable[Any]]):
        self.connection_factory = connection_factory
    
    def can_handle(self, error: WildosNodeBaseError) -> bool:
        """Check if error requires reconnection"""
        return RecoveryStrategyEnum.RECONNECT in error.recovery_strategies
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        error: WildosNodeBaseError,
        context: ErrorContext,
        *args, 
        **kwargs
    ) -> T:
        """Execute reconnection strategy"""
        logger.info(f"Attempting reconnection for {func.__name__} due to {type(error).__name__}")
        
        try:
            # Re-establish connection
            new_connection = await self.connection_factory()
            
            # Update context
            if context:
                context.recovery_attempts += 1
                context.add_metadata('reconnection_attempt', True)
            
            # Retry the operation with new connection
            result = await func(*args, **kwargs)
            
            logger.info(f"Reconnection strategy succeeded for {func.__name__}")
            return result
            
        except Exception as e:
            logger.error(f"Reconnection strategy failed for {func.__name__}: {e}")
            if isinstance(e, WildosNodeBaseError):
                raise e
            else:
                raise create_error_with_context(
                    ConnectionError,
                    f"Reconnection failed: {e}",
                    operation=context.operation if context else None,
                    node_id=context.node_id if context else None
                )


class FallbackStrategy(RecoveryStrategy):
    """Strategy for using cached/fallback data"""
    
    def __init__(self, fallback_cache: 'FallbackCache'):
        self.fallback_cache = fallback_cache
    
    def can_handle(self, error: WildosNodeBaseError) -> bool:
        """Check if fallback is appropriate for this error"""
        return RecoveryStrategyEnum.FALLBACK in error.recovery_strategies
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        error: WildosNodeBaseError,
        context: ErrorContext,
        *args, 
        **kwargs
    ) -> T:
        """Execute fallback strategy"""
        cache_key = self._generate_cache_key(func, args, kwargs)
        
        # Try to get cached data
        cached_data = self.fallback_cache.get(cache_key)
        if cached_data and not cached_data.is_expired():
            logger.info(
                f"Using fallback data for {func.__name__} due to {type(error).__name__}: "
                f"data age {time.time() - cached_data.cached_at:.1f}s"
            )
            
            if context:
                context.recovery_attempts += 1
                context.add_metadata('fallback_used', True)
                context.add_metadata('fallback_age', time.time() - cached_data.cached_at)
            
            return cached_data.data
        
        # No valid fallback data available
        logger.warning(f"No valid fallback data available for {func.__name__}")
        raise error
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call"""
        # Simple key generation - can be improved for specific use cases
        func_name = getattr(func, '__name__', str(func))
        args_str = str(hash(args))[:8]
        kwargs_str = str(hash(frozenset(kwargs.items())))[:8]
        return f"{func_name}:{args_str}:{kwargs_str}"


class DegradationStrategy(RecoveryStrategy):
    """Strategy for graceful service degradation"""
    
    def __init__(self, degraded_func: Optional[Callable[..., Awaitable[T]]] = None):
        self.degraded_func = degraded_func
    
    def can_handle(self, error: WildosNodeBaseError) -> bool:
        """Check if degradation is appropriate for this error"""
        return RecoveryStrategyEnum.DEGRADE in error.recovery_strategies
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        error: WildosNodeBaseError,
        context: ErrorContext,
        *args, 
        **kwargs
    ) -> T:
        """Execute degradation strategy"""
        if self.degraded_func:
            logger.info(f"Using degraded functionality for {func.__name__} due to {type(error).__name__}")
            
            if context:
                context.recovery_attempts += 1
                context.add_metadata('degraded_mode', True)
            
            return await self.degraded_func(*args, **kwargs)
        else:
            # Return minimal/empty result
            logger.warning(f"Operating in degraded mode for {func.__name__}: returning minimal result")
            
            if context:
                context.recovery_attempts += 1
                context.add_metadata('minimal_result', True)
            
            # Return appropriate empty/minimal result based on function return type
            return self._get_minimal_result(func)
    
    def _get_minimal_result(self, func: Callable) -> T:
        """Get minimal result for function when degraded"""
        # This is a simplified implementation - should be customized per function
        return None  # type: ignore


class FallbackCache:
    """Cache for fallback data with TTL and automatic cleanup"""
    
    def __init__(self, max_size: int = FALLBACK_CACHE_SIZE):
        self.max_size = max_size
        self._cache: Dict[str, FallbackData] = {}
        self._access_order = deque()
        self._lock = asyncio.Lock()
    
    async def set(self, key: str, data: Any, ttl: float = FALLBACK_CACHE_TTL, source: str = "cache") -> None:
        """Set cached data with TTL"""
        async with self._lock:
            # Remove expired entries
            await self._cleanup_expired()
            
            # Implement LRU eviction if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            # Store data
            expires_at = time.time() + ttl
            self._cache[key] = FallbackData(
                key=key,
                data=data,
                expires_at=expires_at,
                source=source
            )
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
    def get(self, key: str) -> Optional[FallbackData]:
        """Get cached data"""
        data = self._cache.get(key)
        if data and not data.is_expired():
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
                self._access_order.append(key)
            return data
        elif data:
            # Remove expired data
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        return None
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._cache.items() 
            if data.expires_at <= current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order.popleft()
            if lru_key in self._cache:
                del self._cache[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for data in self._cache.values() if data.is_expired())
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'valid_entries': total_entries - expired_entries,
            'max_size': self.max_size,
            'utilization': total_entries / self.max_size if self.max_size > 0 else 0
        }


class RecoveryManager:
    """Central manager for recovery operations and state tracking"""
    
    def __init__(self):
        self._recovery_states: Dict[str, RecoveryState] = {}
        self._fallback_cache = FallbackCache()
        self._strategies: List[RecoveryStrategy] = []
        self._health_checks: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self._lock = asyncio.Lock()
        
        # Metrics
        self._metrics = {
            'total_errors': 0,
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'fallback_usage': 0,
            'degraded_operations': 0
        }
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start background maintenance tasks"""
        if self._running:
            return
            
        self._running = True
        self._health_check_task = asyncio.create_task(self._periodic_health_checks())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("Recovery manager started")
    
    async def stop(self):
        """Stop background maintenance tasks"""
        self._running = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Recovery manager stopped")
    
    def add_strategy(self, strategy: RecoveryStrategy) -> None:
        """Add a recovery strategy"""
        self._strategies.append(strategy)
        logger.debug(f"Added recovery strategy: {type(strategy).__name__}")
    
    def register_health_check(self, component: str, check_func: Callable[[], Awaitable[bool]]) -> None:
        """Register a health check for a component"""
        self._health_checks[component] = check_func
        logger.debug(f"Registered health check for component: {component}")
    
    async def handle_error(
        self,
        func: Callable[..., Awaitable[T]],
        error: Exception,
        context: Optional[ErrorContext] = None,
        component_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> T:
        """Handle error with appropriate recovery strategy"""
        # Classify error if needed
        if not isinstance(error, WildosNodeBaseError):
            if hasattr(error, 'status'):  # gRPC error
                structured_error = classify_grpc_error(error)
            elif isinstance(error, (OSError, ConnectionError)):
                structured_error = classify_network_error(error)
            elif 'ssl' in str(type(error)).lower():
                structured_error = classify_ssl_error(error)
            else:
                structured_error = create_error_with_context(
                    ServiceError,
                    f"Unexpected error: {error}",
                    operation=context.operation if context else None,
                    node_id=context.node_id if context else None
                )
        else:
            structured_error = error
        
        # Update metrics
        self._metrics['total_errors'] += 1
        
        # Update recovery state
        if component_name:
            await self._update_recovery_state(component_name, structured_error)
        
        # Try recovery strategies
        for strategy in self._strategies:
            if strategy.can_handle(structured_error):
                try:
                    self._metrics['total_recoveries'] += 1
                    # Ensure context is not None
                    execution_context = context or ErrorContext()
                    result = await strategy.execute(func, structured_error, execution_context, *args, **kwargs)
                    self._metrics['successful_recoveries'] += 1
                    
                    # Update recovery state on success
                    if component_name:
                        await self._update_recovery_state_success(component_name)
                    
                    logger.info(f"Recovery successful using {type(strategy).__name__} for {func.__name__}")
                    return result
                    
                except Exception as recovery_error:
                    logger.warning(f"Recovery strategy {type(strategy).__name__} failed for {func.__name__}: {recovery_error}")
                    continue
        
        # No recovery strategy worked
        self._metrics['failed_recoveries'] += 1
        logger.error(f"All recovery strategies failed for {func.__name__}")
        raise structured_error
    
    async def cache_result(self, key: str, data: Any, ttl: float = FALLBACK_CACHE_TTL) -> None:
        """Cache result for future fallback use"""
        await self._fallback_cache.set(key, data, ttl, source="success")
    
    async def _update_recovery_state(self, component_name: str, error: WildosNodeBaseError) -> None:
        """Update recovery state after error"""
        async with self._lock:
            if component_name not in self._recovery_states:
                self._recovery_states[component_name] = RecoveryState(component_name)
            
            state = self._recovery_states[component_name]
            state.update_failure(error)
            
            logger.debug(f"Updated recovery state for {component_name}: {state.consecutive_failures} consecutive failures")
    
    async def _update_recovery_state_success(self, component_name: str) -> None:
        """Update recovery state after successful operation"""
        async with self._lock:
            if component_name not in self._recovery_states:
                self._recovery_states[component_name] = RecoveryState(component_name)
            
            state = self._recovery_states[component_name]
            state.update_success()
            
            logger.debug(f"Updated recovery state for {component_name}: {state.consecutive_successes} consecutive successes")
    
    async def _periodic_health_checks(self):
        """Periodic health checks for registered components"""
        while self._running:
            try:
                for component, check_func in self._health_checks.items():
                    try:
                        is_healthy = await asyncio.wait_for(check_func(), timeout=HEALTH_CHECK_TIMEOUT)
                        
                        async with self._lock:
                            if component not in self._recovery_states:
                                self._recovery_states[component] = RecoveryState(component)
                            
                            state = self._recovery_states[component]
                            if is_healthy:
                                state.health_status = HealthStatus.HEALTHY
                            else:
                                state.health_status = HealthStatus.UNHEALTHY
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"Health check timeout for component {component}")
                        async with self._lock:
                            if component in self._recovery_states:
                                self._recovery_states[component].health_status = HealthStatus.UNKNOWN
                    except Exception as e:
                        logger.error(f"Health check failed for component {component}: {e}")
                        async with self._lock:
                            if component in self._recovery_states:
                                self._recovery_states[component].health_status = HealthStatus.UNHEALTHY
                
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in periodic health checks: {e}")
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old recovery states and cache"""
        while self._running:
            try:
                current_time = time.time()
                
                # Cleanup old recovery states
                async with self._lock:
                    expired_components = [
                        component for component, state in self._recovery_states.items()
                        if (current_time - state.last_success_time) > RECOVERY_STATE_TTL
                        and (not state.last_failure_time or (current_time - state.last_failure_time) > RECOVERY_STATE_TTL)
                    ]
                    
                    for component in expired_components:
                        del self._recovery_states[component]
                        logger.debug(f"Cleaned up recovery state for expired component: {component}")
                
                # Cleanup cache
                await self._fallback_cache._cleanup_expired()
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(300)
    
    def get_recovery_state(self, component_name: str) -> Optional[RecoveryState]:
        """Get recovery state for a component"""
        return self._recovery_states.get(component_name)
    
    def get_all_recovery_states(self) -> Dict[str, RecoveryState]:
        """Get all recovery states"""
        return self._recovery_states.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get recovery manager metrics"""
        cache_stats = self._fallback_cache.get_stats()
        
        return {
            **self._metrics,
            'cache_stats': cache_stats,
            'recovery_states_count': len(self._recovery_states),
            'strategies_count': len(self._strategies),
            'health_checks_count': len(self._health_checks),
            'running': self._running
        }


# Decorator for enhanced error handling with recovery
def with_recovery(
    component_name: Optional[str] = None,
    cache_result: bool = False,
    cache_ttl: float = FALLBACK_CACHE_TTL,
    recovery_manager: Optional[RecoveryManager] = None
):
    """
    Decorator for enhanced error handling with automatic recovery
    
    Args:
        component_name: Name of the component for state tracking
        cache_result: Whether to cache successful results for fallback
        cache_ttl: TTL for cached results
        recovery_manager: Recovery manager instance (if None, uses global instance)
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Create error context
            context = ErrorContext(
                operation=func.__name__,
                timestamp=time.time()
            )
            
            # Extract node_id if available from self
            if args and hasattr(args[0], 'id'):
                context.node_id = args[0].id
            
            # Get recovery manager
            manager = recovery_manager or _get_global_recovery_manager()
            
            try:
                result = await func(*args, **kwargs)
                
                # Cache result if requested
                if cache_result and manager:
                    cache_key = f"{func.__name__}:{hash(args)}:{hash(frozenset(kwargs.items()))}"
                    await manager.cache_result(cache_key, result, cache_ttl)
                
                # Update recovery state on success
                if component_name and manager:
                    await manager._update_recovery_state_success(component_name)
                
                return result
                
            except Exception as error:
                if manager:
                    return await manager.handle_error(
                        func, error, context, component_name, *args, **kwargs
                    )
                else:
                    # Fallback to basic error handling
                    if isinstance(error, WildosNodeBaseError):
                        raise error
                    else:
                        raise create_error_with_context(
                            ServiceError,
                            f"Error in {func.__name__}: {error}",
                            operation=func.__name__
                        )
        
        return wrapper
    return decorator


# Global recovery manager instance
_global_recovery_manager: Optional[RecoveryManager] = None


def _get_global_recovery_manager() -> RecoveryManager:
    """Get or create global recovery manager instance"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager()
        
        # Add default strategies
        _global_recovery_manager.add_strategy(RetryStrategy())
        
        # Start the manager
        asyncio.create_task(_global_recovery_manager.start())
    
    return _global_recovery_manager


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance"""
    return _get_global_recovery_manager()


# Cleanup function
async def cleanup_recovery():
    """Cleanup global recovery manager"""
    global _global_recovery_manager
    if _global_recovery_manager:
        await _global_recovery_manager.stop()
        _global_recovery_manager = None