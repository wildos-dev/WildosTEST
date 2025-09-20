"""
Comprehensive unit tests for recovery mechanisms.

Tests:
- RecoveryState management и lifecycle
- RecoveryStrategy implementations (Retry, Reconnection, Fallback, Degradation)
- RecoveryManager coordination и orchestration
- FallbackCache functionality и TTL handling
- Health monitoring и status reporting
- Recovery mode transitions и adaptive behavior
- Integration with error classification system
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from unittest import IsolatedAsyncioTestCase
from collections import deque

from app.wildosnode.recovery import (
    # Core classes
    RecoveryState, RecoveryMode, HealthStatus, FallbackData, RecoveryManager,
    
    # Strategy classes
    RecoveryStrategy, RetryStrategy, ReconnectionStrategy, FallbackStrategy,
    DegradationStrategy, FallbackCache,
    
    # Utility functions
    with_recovery, get_recovery_manager,
    
    # Constants
    RECOVERY_STATE_CACHE_SIZE, RECOVERY_STATE_TTL,
    FALLBACK_CACHE_SIZE, FALLBACK_CACHE_TTL,
    HEALTH_CHECK_INTERVAL, HEALTH_CHECK_TIMEOUT
)
from app.wildosnode.exceptions import (
    WildosNodeBaseError, NetworkError, ServiceError, TimeoutError,
    ConnectionError, ServiceUnavailableError, ErrorContext, ErrorSeverity
)


class TestRecoveryState(IsolatedAsyncioTestCase):
    """Test RecoveryState functionality"""
    
    async def asyncSetUp(self):
        self.recovery_state = RecoveryState("test_component")
    
    def test_recovery_state_initialization(self):
        """Test RecoveryState initializes correctly"""
        self.assertEqual(self.recovery_state.component_name, "test_component")
        self.assertEqual(self.recovery_state.consecutive_failures, 0)
        self.assertEqual(self.recovery_state.consecutive_successes, 0)
        self.assertEqual(self.recovery_state.recovery_attempts, 0)
        self.assertEqual(self.recovery_state.current_mode, RecoveryMode.NORMAL)
        self.assertEqual(self.recovery_state.health_status, HealthStatus.HEALTHY)
        self.assertEqual(self.recovery_state.total_failures, 0)
        self.assertEqual(self.recovery_state.total_recoveries, 0)
        self.assertIsNone(self.recovery_state.last_error)
        self.assertIsInstance(self.recovery_state.metadata, dict)
    
    def test_update_success(self):
        """Test recovery state updates on success"""
        # Start with some failures
        self.recovery_state.consecutive_failures = 5
        self.recovery_state.health_status = HealthStatus.UNHEALTHY
        
        # Record success
        self.recovery_state.update_success()
        
        self.assertEqual(self.recovery_state.consecutive_failures, 0)
        self.assertEqual(self.recovery_state.consecutive_successes, 1)
        self.assertIsNotNone(self.recovery_state.last_success_time)
        
        # Test health status improvement
        for _ in range(2):  # Need 3 consecutive successes to go from UNHEALTHY to DEGRADED
            self.recovery_state.update_success()
        
        self.assertEqual(self.recovery_state.health_status, HealthStatus.DEGRADED)
        
        # Need 5 total consecutive successes to go from DEGRADED to HEALTHY
        for _ in range(2):
            self.recovery_state.update_success()
        
        self.assertEqual(self.recovery_state.health_status, HealthStatus.HEALTHY)
        self.assertEqual(self.recovery_state.current_mode, RecoveryMode.NORMAL)
    
    def test_update_failure(self):
        """Test recovery state updates on failure"""
        error = NetworkError("test network error")
        
        # Record failure
        self.recovery_state.update_failure(error)
        
        self.assertEqual(self.recovery_state.consecutive_failures, 1)
        self.assertEqual(self.recovery_state.consecutive_successes, 0)
        self.assertEqual(self.recovery_state.total_failures, 1)
        self.assertEqual(self.recovery_state.last_error, error)
        self.assertIsNotNone(self.recovery_state.last_failure_time)
        
        # Test health status degradation
        for _ in range(2):  # Need 3 consecutive failures for UNHEALTHY
            self.recovery_state.update_failure(error)
        
        self.assertEqual(self.recovery_state.health_status, HealthStatus.UNHEALTHY)
        self.assertEqual(self.recovery_state.current_mode, RecoveryMode.DEGRADED)
        
        # More failures trigger emergency mode
        for _ in range(2):  # Need 5 total for EMERGENCY
            self.recovery_state.update_failure(error)
        
        self.assertEqual(self.recovery_state.current_mode, RecoveryMode.EMERGENCY)
        
        # Even more failures trigger offline mode
        for _ in range(5):  # Need 10 total for OFFLINE
            self.recovery_state.update_failure(error)
        
        self.assertEqual(self.recovery_state.current_mode, RecoveryMode.OFFLINE)
    
    @patch('app.wildosnode.recovery.time.time')
    def test_should_attempt_recovery(self, mock_time):
        """Test recovery attempt rate limiting"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Fresh state should allow recovery
        self.assertTrue(self.recovery_state.should_attempt_recovery())
        
        # Set in OFFLINE mode
        self.recovery_state.current_mode = RecoveryMode.OFFLINE
        self.assertFalse(self.recovery_state.should_attempt_recovery())
        
        # Reset to normal mode but with recent failure
        self.recovery_state.current_mode = RecoveryMode.NORMAL
        self.recovery_state.last_failure_time = current_time - 1.0  # 1 second ago
        self.recovery_state.recovery_attempts = 2
        
        # Should not allow recovery too soon (need 2^2 = 4 seconds)
        self.assertFalse(self.recovery_state.should_attempt_recovery())
        
        # Advance time past required interval
        mock_time.return_value = current_time + 5.0
        self.assertTrue(self.recovery_state.should_attempt_recovery())
    
    def test_to_dict(self):
        """Test recovery state dictionary conversion"""
        error = ServiceError("test error")
        self.recovery_state.update_failure(error)
        self.recovery_state.metadata["custom_key"] = "custom_value"
        
        state_dict = self.recovery_state.to_dict()
        
        self.assertEqual(state_dict["component_name"], "test_component")
        self.assertEqual(state_dict["consecutive_failures"], 1)
        self.assertEqual(state_dict["total_failures"], 1)
        self.assertEqual(state_dict["current_mode"], RecoveryMode.NORMAL.value)
        self.assertEqual(state_dict["health_status"], HealthStatus.DEGRADED.value)
        self.assertEqual(state_dict["last_error_type"], "ServiceError")
        self.assertEqual(state_dict["metadata"]["custom_key"], "custom_value")


class TestFallbackData(IsolatedAsyncioTestCase):
    """Test FallbackData functionality"""
    
    @patch('app.wildosnode.recovery.time.time')
    def test_fallback_data_initialization(self, mock_time):
        """Test FallbackData initializes correctly"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        data = FallbackData("test_key", {"cached": "data"})
        
        self.assertEqual(data.key, "test_key")
        self.assertEqual(data.data, {"cached": "data"})
        self.assertEqual(data.cached_at, current_time)
        self.assertEqual(data.expires_at, current_time + FALLBACK_CACHE_TTL)
        self.assertEqual(data.source, "cache")
        self.assertIsInstance(data.metadata, dict)
    
    @patch('app.wildosnode.recovery.time.time')
    def test_fallback_data_expiration(self, mock_time):
        """Test fallback data expiration checking"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        data = FallbackData("test_key", "test_data")
        
        # Fresh data should not be expired
        self.assertFalse(data.is_expired())
        
        # Advance time past expiration
        mock_time.return_value = current_time + FALLBACK_CACHE_TTL + 1
        self.assertTrue(data.is_expired())
    
    @patch('app.wildosnode.recovery.time.time')
    def test_fallback_data_staleness(self, mock_time):
        """Test fallback data staleness checking"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        data = FallbackData("test_key", "test_data")
        
        # Fresh data should not be stale
        self.assertFalse(data.is_stale(max_age=60.0))
        
        # Advance time to make data stale
        mock_time.return_value = current_time + 70.0
        self.assertTrue(data.is_stale(max_age=60.0))


class TestRetryStrategy(IsolatedAsyncioTestCase):
    """Test RetryStrategy implementation"""
    
    async def asyncSetUp(self):
        self.retry_strategy = RetryStrategy(
            max_retries=3,
            base_delay=0.1,
            max_delay=2.0,
            backoff_multiplier=2.0,
            jitter_factor=0.1
        )
    
    def test_retry_strategy_can_handle(self):
        """Test retry strategy error handling detection"""
        # Retryable error
        retryable_error = NetworkError("network error")
        self.assertTrue(self.retry_strategy.can_handle(retryable_error))
        
        # Non-retryable error
        non_retryable_error = ServiceError("non-retryable error")
        non_retryable_error.retryable = False
        self.assertFalse(self.retry_strategy.can_handle(non_retryable_error))
    
    async def test_retry_strategy_successful_execution(self):
        """Test retry strategy with eventually successful function"""
        call_count = 0
        
        async def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("temporary failure")
            return "success"
        
        error = NetworkError("initial error")
        context = ErrorContext(operation="test_operation")
        
        result = await self.retry_strategy.execute(
            eventually_successful_function, error, context
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        self.assertEqual(context.recovery_attempts, 2)  # 2 retries
    
    async def test_retry_strategy_exhausted_retries(self):
        """Test retry strategy when retries are exhausted"""
        call_count = 0
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ServiceError("persistent failure")
        
        error = ServiceError("initial error")
        context = ErrorContext()
        
        with self.assertRaises(ServiceError):
            await self.retry_strategy.execute(
                always_failing_function, error, context
            )
        
        self.assertEqual(call_count, self.retry_strategy.max_retries)
        self.assertEqual(context.recovery_attempts, self.retry_strategy.max_retries)


class TestFallbackCache(IsolatedAsyncioTestCase):
    """Test FallbackCache functionality"""
    
    async def asyncSetUp(self):
        self.cache = FallbackCache(
            max_size=5,
            default_ttl=60.0
        )
    
    @patch('app.wildosnode.recovery.time.time')
    async def test_cache_set_and_get(self, mock_time):
        """Test cache set and get operations"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Set data in cache
        await self.cache.set("test_key", {"data": "test"}, source="test_source")
        
        # Get data from cache
        data = await self.cache.get("test_key")
        
        self.assertIsNotNone(data)
        self.assertEqual(data.key, "test_key")
        self.assertEqual(data.data, {"data": "test"})
        self.assertEqual(data.source, "test_source")
    
    @patch('app.wildosnode.recovery.time.time')
    async def test_cache_expiration(self, mock_time):
        """Test cache entry expiration"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        await self.cache.set("test_key", "test_data", ttl=30.0)
        
        # Data should be available immediately
        data = await self.cache.get("test_key")
        self.assertIsNotNone(data)
        
        # Advance time past expiration
        mock_time.return_value = current_time + 35.0
        
        # Data should be expired and removed
        data = await self.cache.get("test_key")
        self.assertIsNone(data)
    
    async def test_cache_size_limit(self):
        """Test cache respects size limit"""
        # Fill cache beyond capacity
        for i in range(7):  # max_size is 5
            await self.cache.set(f"key_{i}", f"data_{i}")
        
        # Check that cache doesn't exceed max size
        self.assertLessEqual(len(self.cache._cache), self.cache.max_size)
        
        # Oldest entries should be evicted
        data = await self.cache.get("key_0")
        self.assertIsNone(data)  # Should be evicted
        
        data = await self.cache.get("key_6")
        self.assertIsNotNone(data)  # Should still be present
    
    async def test_cache_clear(self):
        """Test cache clear operation"""
        await self.cache.set("key1", "data1")
        await self.cache.set("key2", "data2")
        
        self.assertEqual(len(self.cache._cache), 2)
        
        await self.cache.clear()
        
        self.assertEqual(len(self.cache._cache), 0)
    
    async def test_cache_metrics(self):
        """Test cache metrics collection"""
        await self.cache.set("key1", "data1")
        await self.cache.get("key1")  # Hit
        await self.cache.get("key2")  # Miss
        
        metrics = await self.cache.get_metrics()
        
        self.assertEqual(metrics["cache_size"], 1)
        self.assertEqual(metrics["total_hits"], 1)
        self.assertEqual(metrics["total_misses"], 1)
        self.assertGreater(metrics["hit_rate"], 0.0)


class TestReconnectionStrategy(IsolatedAsyncioTestCase):
    """Test ReconnectionStrategy implementation"""
    
    async def asyncSetUp(self):
        self.reconnection_strategy = ReconnectionStrategy(
            max_attempts=3,
            base_delay=0.1,
            connection_timeout=5.0
        )
    
    def test_reconnection_strategy_can_handle(self):
        """Test reconnection strategy error handling detection"""
        # Connection errors
        connection_error = ConnectionError("connection failed")
        self.assertTrue(self.reconnection_strategy.can_handle(connection_error))
        
        # Network errors
        network_error = NetworkError("network unreachable")
        self.assertTrue(self.reconnection_strategy.can_handle(network_error))
        
        # Non-connection errors
        service_error = ServiceError("service error")
        self.assertFalse(self.reconnection_strategy.can_handle(service_error))
    
    async def test_reconnection_strategy_execution(self):
        """Test reconnection strategy execution"""
        attempt_count = 0
        
        async def connection_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("connection failed")
            return "connected"
        
        error = ConnectionError("initial connection error")
        context = ErrorContext()
        
        result = await self.reconnection_strategy.execute(
            connection_function, error, context
        )
        
        self.assertEqual(result, "connected")
        self.assertEqual(attempt_count, 3)


class TestFallbackStrategy(IsolatedAsyncioTestCase):
    """Test FallbackStrategy implementation"""
    
    async def asyncSetUp(self):
        self.fallback_cache = FallbackCache()
        self.fallback_strategy = FallbackStrategy(
            fallback_cache=self.fallback_cache,
            cache_key_extractor=lambda *args, **kwargs: "test_key",
            fallback_data_generator=lambda *args, **kwargs: {"fallback": "data"}
        )
    
    def test_fallback_strategy_can_handle(self):
        """Test fallback strategy error handling detection"""
        # Service unavailable
        service_error = ServiceUnavailableError("service down")
        self.assertTrue(self.fallback_strategy.can_handle(service_error))
        
        # Timeout errors
        timeout_error = TimeoutError("operation timeout")
        self.assertTrue(self.fallback_strategy.can_handle(timeout_error))
        
        # Authentication errors (shouldn't use fallback)
        from app.wildosnode.exceptions import AuthenticationError
        auth_error = AuthenticationError("auth failed")
        self.assertFalse(self.fallback_strategy.can_handle(auth_error))
    
    async def test_fallback_strategy_with_cached_data(self):
        """Test fallback strategy with cached data available"""
        # Pre-populate cache
        await self.fallback_cache.set("test_key", {"cached": "result"})
        
        async def failing_function():
            raise ServiceUnavailableError("service unavailable")
        
        error = ServiceUnavailableError("service error")
        context = ErrorContext()
        
        result = await self.fallback_strategy.execute(
            failing_function, error, context
        )
        
        self.assertEqual(result, {"cached": "result"})
    
    async def test_fallback_strategy_with_generated_data(self):
        """Test fallback strategy with generated fallback data"""
        async def failing_function():
            raise ServiceUnavailableError("service unavailable")
        
        error = ServiceUnavailableError("service error")
        context = ErrorContext()
        
        result = await self.fallback_strategy.execute(
            failing_function, error, context
        )
        
        self.assertEqual(result, {"fallback": "data"})


class TestRecoveryManager(IsolatedAsyncioTestCase):
    """Test RecoveryManager orchestration"""
    
    async def asyncSetUp(self):
        self.recovery_manager = RecoveryManager()
    
    async def asyncTearDown(self):
        await self.recovery_manager.stop()
    
    def test_recovery_manager_initialization(self):
        """Test RecoveryManager initializes correctly"""
        self.assertIsInstance(self.recovery_manager._strategies, list)
        self.assertIsInstance(self.recovery_manager._fallback_cache, FallbackCache)
        self.assertIsInstance(self.recovery_manager._recovery_states, dict)
    
    def test_register_strategy(self):
        """Test strategy registration"""
        strategy = RetryStrategy()
        initial_count = len(self.recovery_manager._strategies)
        
        self.recovery_manager.register_strategy(strategy)
        
        self.assertEqual(len(self.recovery_manager._strategies), initial_count + 1)
        self.assertIn(strategy, self.recovery_manager._strategies)
    
    def test_get_recovery_state(self):
        """Test recovery state retrieval"""
        state = self.recovery_manager.get_recovery_state("test_component")
        
        self.assertIsInstance(state, RecoveryState)
        self.assertEqual(state.component_name, "test_component")
        
        # Same component should return same state
        state2 = self.recovery_manager.get_recovery_state("test_component")
        self.assertIs(state, state2)
    
    async def test_execute_with_recovery(self):
        """Test function execution with recovery"""
        call_count = 0
        
        async def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("temporary failure")
            return "success"
        
        result = await self.recovery_manager.execute_with_recovery(
            eventually_successful_function,
            component_name="test_component"
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        
        # Check recovery state was updated
        state = self.recovery_manager.get_recovery_state("test_component")
        self.assertGreater(state.consecutive_successes, 0)
    
    async def test_record_success(self):
        """Test success recording"""
        component_name = "test_component"
        
        await self.recovery_manager.record_success(component_name)
        
        state = self.recovery_manager.get_recovery_state(component_name)
        self.assertEqual(state.consecutive_successes, 1)
        self.assertEqual(state.consecutive_failures, 0)
    
    async def test_record_failure(self):
        """Test failure recording"""
        component_name = "test_component"
        error = NetworkError("test error")
        
        await self.recovery_manager.record_failure(component_name, error)
        
        state = self.recovery_manager.get_recovery_state(component_name)
        self.assertEqual(state.consecutive_failures, 1)
        self.assertEqual(state.last_error, error)
    
    async def test_health_monitoring(self):
        """Test health monitoring functionality"""
        # Start health monitoring
        await self.recovery_manager.start_health_monitoring()
        
        # Register a health check function
        health_check_called = False
        
        async def test_health_check():
            nonlocal health_check_called
            health_check_called = True
            return {"status": "healthy"}
        
        self.recovery_manager.register_health_check("test_component", test_health_check)
        
        # Wait for health check to be called
        await asyncio.sleep(0.1)
        
        self.assertTrue(health_check_called)
    
    def test_get_system_health(self):
        """Test system health aggregation"""
        # Create some recovery states with different health statuses
        state1 = self.recovery_manager.get_recovery_state("component1")
        state1.health_status = HealthStatus.HEALTHY
        
        state2 = self.recovery_manager.get_recovery_state("component2")
        state2.health_status = HealthStatus.DEGRADED
        
        state3 = self.recovery_manager.get_recovery_state("component3")
        state3.health_status = HealthStatus.UNHEALTHY
        
        health = self.recovery_manager.get_system_health()
        
        self.assertIn("overall_status", health)
        self.assertIn("component_count", health)
        self.assertIn("healthy_components", health)
        self.assertIn("degraded_components", health)
        self.assertIn("unhealthy_components", health)
        
        self.assertEqual(health["healthy_components"], 1)
        self.assertEqual(health["degraded_components"], 1)
        self.assertEqual(health["unhealthy_components"], 1)


class TestWithRecoveryDecorator(IsolatedAsyncioTestCase):
    """Test with_recovery decorator"""
    
    async def test_with_recovery_decorator_success(self):
        """Test with_recovery decorator with successful function"""
        @with_recovery(component_name="test_component")
        async def successful_function():
            return "success"
        
        result = await successful_function()
        self.assertEqual(result, "success")
    
    async def test_with_recovery_decorator_with_retries(self):
        """Test with_recovery decorator with retries"""
        call_count = 0
        
        @with_recovery(component_name="test_component")
        async def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("temporary failure")
            return "success"
        
        result = await eventually_successful_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)


class TestRecoveryIntegration(IsolatedAsyncioTestCase):
    """Integration tests for recovery system"""
    
    async def asyncSetUp(self):
        self.recovery_manager = RecoveryManager()
    
    async def asyncTearDown(self):
        await self.recovery_manager.stop()
    
    async def test_full_recovery_cycle(self):
        """Test complete recovery cycle from failure to recovery"""
        component_name = "integration_test_component"
        failure_count = 0
        
        async def simulated_service():
            nonlocal failure_count
            failure_count += 1
            
            # Fail first few attempts
            if failure_count <= 3:
                raise ServiceUnavailableError(f"Service failure #{failure_count}")
            
            # Then succeed
            return f"Success after {failure_count} attempts"
        
        # Execute with recovery - should eventually succeed
        result = await self.recovery_manager.execute_with_recovery(
            simulated_service,
            component_name=component_name
        )
        
        self.assertIn("Success", result)
        
        # Check recovery state reflects the journey
        state = self.recovery_manager.get_recovery_state(component_name)
        self.assertGreater(state.total_failures, 0)
        self.assertGreater(state.consecutive_successes, 0)
        self.assertEqual(state.health_status, HealthStatus.HEALTHY)
    
    async def test_recovery_mode_transitions(self):
        """Test recovery mode transitions under stress"""
        component_name = "mode_transition_test"
        
        # Simulate multiple failures to trigger mode changes
        for i in range(15):  # Enough to trigger OFFLINE mode
            error = NetworkError(f"Failure #{i}")
            await self.recovery_manager.record_failure(component_name, error)
        
        state = self.recovery_manager.get_recovery_state(component_name)
        self.assertEqual(state.current_mode, RecoveryMode.OFFLINE)
        self.assertEqual(state.health_status, HealthStatus.UNHEALTHY)
        
        # Now simulate recovery
        for i in range(10):
            await self.recovery_manager.record_success(component_name)
        
        state = self.recovery_manager.get_recovery_state(component_name)
        self.assertEqual(state.current_mode, RecoveryMode.NORMAL)
        self.assertEqual(state.health_status, HealthStatus.HEALTHY)


if __name__ == '__main__':
    unittest.main()