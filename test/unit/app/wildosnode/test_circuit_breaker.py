"""
Comprehensive unit tests for CircuitBreaker class.

Tests all critical functionality:
- State transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- Failure threshold и error rate calculations
- Recovery timeout и half-open testing  
- Metrics collection и monitoring integration
- AsyncIO compatibility и thread safety
- Edge cases и error scenarios
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from unittest import IsolatedAsyncioTestCase

from app.wildosnode.grpc_client import (
    CircuitBreaker, CircuitBreakerState, 
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD,
    CIRCUIT_BREAKER_MONITORING_WINDOW,
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS
)
from app.wildosnode.exceptions import (
    CircuitBreakerError, WildosNodeBaseError, NetworkError, 
    ServiceError, ErrorContext, ErrorSeverity, ErrorCategory
)


class TestCircuitBreakerStateTransitions(IsolatedAsyncioTestCase):
    """Test circuit breaker state transitions and core functionality"""
    
    async def asyncSetUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            error_rate_threshold=0.5,
            monitoring_window=60.0,
            recovery_timeout=5.0,
            half_open_max_calls=2,
            name="test_circuit_breaker"
        )
        
    async def asyncTearDown(self):
        await self.circuit_breaker.reset()
    
    async def test_initial_state_is_closed(self):
        """Test circuit breaker starts in CLOSED state"""
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        self.assertTrue(self.circuit_breaker.is_closed)
        self.assertFalse(self.circuit_breaker.is_open)
        self.assertFalse(self.circuit_breaker.is_half_open)
    
    async def test_successful_call_in_closed_state(self):
        """Test successful function call in CLOSED state"""
        async def successful_function():
            return "success"
        
        result = await self.circuit_breaker.call(successful_function)
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['total_calls'], 1)
        self.assertEqual(metrics['successful_calls'], 1)
        self.assertEqual(metrics['failed_calls'], 0)
    
    async def test_single_failure_remains_closed(self):
        """Test single failure keeps circuit breaker CLOSED"""
        async def failing_function():
            raise ValueError("test error")
        
        with self.assertRaises(ValueError):
            await self.circuit_breaker.call(failing_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['total_calls'], 1)
        self.assertEqual(metrics['successful_calls'], 0)
        self.assertEqual(metrics['failed_calls'], 1)
        self.assertEqual(metrics['consecutive_failures'], 1)
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_consecutive_failures_trigger_open_state(self, mock_monitoring):
        """Test consecutive failures trigger transition to OPEN state"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        async def failing_function():
            raise NetworkError("network failure")
        
        # Trigger enough failures to open circuit
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(NetworkError):
                await self.circuit_breaker.call(failing_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        self.assertTrue(self.circuit_breaker.is_open)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['consecutive_failures'], self.circuit_breaker.failure_threshold)
        self.assertEqual(metrics['circuit_open_count'], 1)
        
        # Verify monitoring integration was called
        mock_monitoring_instance.logger.error.assert_called()
        mock_monitoring_instance.metrics.increment.assert_called()
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_open_state_rejects_calls_immediately(self, mock_monitoring):
        """Test OPEN state rejects calls without executing function"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        # First, trigger OPEN state
        async def failing_function():
            raise ServiceError("service failure")
        
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(ServiceError):
                await self.circuit_breaker.call(failing_function)
        
        # Verify circuit is now OPEN
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        
        # Now test that calls are rejected immediately
        call_executed = False
        async def should_not_execute():
            nonlocal call_executed
            call_executed = True
            return "should not reach here"
        
        with self.assertRaises(CircuitBreakerError) as cm:
            await self.circuit_breaker.call(should_not_execute)
        
        self.assertFalse(call_executed)
        self.assertIn("Circuit breaker", str(cm.exception))
        self.assertIn("OPEN", str(cm.exception))
    
    @patch('app.wildosnode.grpc_client.time.time')
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_open_to_half_open_transition_after_timeout(self, mock_monitoring, mock_time):
        """Test transition from OPEN to HALF_OPEN after recovery timeout"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        # Mock time to control recovery timeout
        start_time = 1000.0
        mock_time.return_value = start_time
        
        # First, trigger OPEN state
        async def failing_function():
            raise NetworkError("network failure")
        
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(NetworkError):
                await self.circuit_breaker.call(failing_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        
        # Advance time past recovery timeout
        mock_time.return_value = start_time + self.circuit_breaker.recovery_timeout + 1
        
        # Now a call should transition to HALF_OPEN
        async def test_function():
            return "test_result"
        
        result = await self.circuit_breaker.call(test_function)
        self.assertEqual(result, "test_result")
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.HALF_OPEN)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['circuit_half_open_count'], 1)
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_half_open_success_transitions_to_closed(self, mock_monitoring):
        """Test successful calls in HALF_OPEN state transition to CLOSED"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        # Manually set to HALF_OPEN state
        await self.circuit_breaker._transition_to_half_open()
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.HALF_OPEN)
        
        async def successful_function():
            return "success"
        
        # Execute successful calls up to half_open_max_calls
        for i in range(self.circuit_breaker.half_open_max_calls):
            result = await self.circuit_breaker.call(successful_function)
            self.assertEqual(result, "success")
        
        # Should now be CLOSED
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        self.assertTrue(self.circuit_breaker.is_closed)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['consecutive_failures'], 0)
        
        # Verify recovery metrics were recorded
        mock_monitoring_instance.metrics.increment.assert_called()
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_half_open_failure_transitions_back_to_open(self, mock_monitoring):
        """Test failure in HALF_OPEN state transitions back to OPEN"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        # Manually set to HALF_OPEN state
        await self.circuit_breaker._transition_to_half_open()
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.HALF_OPEN)
        
        async def failing_function():
            raise ServiceError("service failure")
        
        # Single failure should transition back to OPEN
        with self.assertRaises(ServiceError):
            await self.circuit_breaker.call(failing_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        self.assertTrue(self.circuit_breaker.is_open)
        
        # Verify transition was logged
        mock_monitoring_instance.logger.warning.assert_called()
    
    async def test_half_open_limits_concurrent_calls(self):
        """Test HALF_OPEN state limits number of concurrent calls"""
        # Manually set to HALF_OPEN state
        await self.circuit_breaker._transition_to_half_open()
        
        call_count = 0
        async def counting_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Small delay to simulate work
            return "success"
        
        # Start more calls than half_open_max_calls allows
        tasks = []
        for i in range(self.circuit_breaker.half_open_max_calls + 2):
            task = asyncio.create_task(
                self.circuit_breaker.call(counting_function)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete, some should fail with CircuitBreakerError
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successes = [r for r in results if r == "success"]
        failures = [r for r in results if isinstance(r, CircuitBreakerError)]
        
        # Should have exactly half_open_max_calls successes
        self.assertEqual(len(successes), self.circuit_breaker.half_open_max_calls)
        self.assertEqual(len(failures), 2)


class TestCircuitBreakerErrorRateThreshold(IsolatedAsyncioTestCase):
    """Test error rate threshold functionality"""
    
    async def asyncSetUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=10,  # High threshold to test error rate
            error_rate_threshold=0.6,  # 60% error rate
            monitoring_window=60.0,
            recovery_timeout=5.0,
            name="error_rate_test"
        )
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_error_rate_threshold_triggers_open_state(self, mock_monitoring):
        """Test error rate threshold triggers OPEN state"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        async def success_function():
            return "success"
        
        async def failure_function():
            raise NetworkError("network error")
        
        # Create a pattern: 4 successes, 6 failures = 60% error rate
        for i in range(4):
            await self.circuit_breaker.call(success_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        # Now add failures to hit error rate threshold
        for i in range(6):
            with self.assertRaises(NetworkError):
                await self.circuit_breaker.call(failure_function)
        
        # Should now be OPEN due to error rate
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertGreaterEqual(metrics['error_rate'], self.circuit_breaker.error_rate_threshold)
    
    async def test_error_rate_calculation_accuracy(self):
        """Test error rate calculation is accurate"""
        async def success_function():
            return "success"
        
        async def failure_function():
            raise ServiceError("service error")
        
        # Execute 5 successes and 5 failures = 50% error rate
        for i in range(5):
            await self.circuit_breaker.call(success_function)
        
        for i in range(5):
            with self.assertRaises(ServiceError):
                await self.circuit_breaker.call(failure_function)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertAlmostEqual(metrics['current_error_rate'], 0.5, places=2)
        self.assertEqual(metrics['recent_calls_count'], 10)
        
        # Should still be CLOSED since error rate (50%) < threshold (60%)
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
    
    @patch('app.wildosnode.grpc_client.time.time')
    async def test_monitoring_window_cleanup(self, mock_time):
        """Test old call history is cleaned up outside monitoring window"""
        start_time = 1000.0
        mock_time.return_value = start_time
        
        async def test_function():
            return "success"
        
        # Add some calls
        for i in range(5):
            await self.circuit_breaker.call(test_function)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['recent_calls_count'], 5)
        
        # Advance time beyond monitoring window
        mock_time.return_value = start_time + self.circuit_breaker.monitoring_window + 10
        
        # Add one more call to trigger cleanup
        await self.circuit_breaker.call(test_function)
        
        metrics = self.circuit_breaker.get_metrics()
        # Should only have the latest call
        self.assertEqual(metrics['recent_calls_count'], 1)


class TestCircuitBreakerMetrics(IsolatedAsyncioTestCase):
    """Test comprehensive metrics collection"""
    
    async def asyncSetUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=2.0,
            name="metrics_test"
        )
    
    async def test_metrics_initialization(self):
        """Test metrics are properly initialized"""
        metrics = self.circuit_breaker.get_metrics()
        
        expected_metrics = [
            'total_calls', 'successful_calls', 'failed_calls',
            'circuit_open_count', 'circuit_half_open_count',
            'state_changes', 'consecutive_failures', 'error_rate',
            'current_state', 'name', 'current_error_rate',
            'recent_calls_count', 'time_in_current_state'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
        
        self.assertEqual(metrics['name'], "metrics_test")
        self.assertEqual(metrics['current_state'], CircuitBreakerState.CLOSED.value)
        self.assertEqual(metrics['total_calls'], 0)
    
    async def test_metrics_update_on_success(self):
        """Test metrics update correctly on successful calls"""
        async def success_function():
            return "success"
        
        for i in range(3):
            await self.circuit_breaker.call(success_function)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['total_calls'], 3)
        self.assertEqual(metrics['successful_calls'], 3)
        self.assertEqual(metrics['failed_calls'], 0)
        self.assertEqual(metrics['consecutive_failures'], 0)
        self.assertEqual(metrics['current_error_rate'], 0.0)
    
    async def test_metrics_update_on_failure(self):
        """Test metrics update correctly on failed calls"""
        async def failure_function():
            raise ValueError("test error")
        
        for i in range(2):
            with self.assertRaises(ValueError):
                await self.circuit_breaker.call(failure_function)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['total_calls'], 2)
        self.assertEqual(metrics['successful_calls'], 0)
        self.assertEqual(metrics['failed_calls'], 2)
        self.assertEqual(metrics['consecutive_failures'], 2)
        self.assertEqual(metrics['current_error_rate'], 1.0)
    
    async def test_configuration_in_metrics(self):
        """Test configuration parameters are included in metrics"""
        metrics = self.circuit_breaker.get_metrics()
        
        config = metrics['configuration']
        self.assertEqual(config['failure_threshold'], self.circuit_breaker.failure_threshold)
        self.assertEqual(config['error_rate_threshold'], self.circuit_breaker.error_rate_threshold)
        self.assertEqual(config['monitoring_window'], self.circuit_breaker.monitoring_window)
        self.assertEqual(config['recovery_timeout'], self.circuit_breaker.recovery_timeout)
        self.assertEqual(config['half_open_max_calls'], self.circuit_breaker.half_open_max_calls)
    
    @patch('app.wildosnode.grpc_client.time.time')
    async def test_time_since_last_failure_metric(self, mock_time):
        """Test time since last failure is tracked correctly"""
        start_time = 1000.0
        mock_time.return_value = start_time
        
        async def failure_function():
            raise NetworkError("network error")
        
        # Trigger a failure
        with self.assertRaises(NetworkError):
            await self.circuit_breaker.call(failure_function)
        
        # Advance time
        mock_time.return_value = start_time + 30.0
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertAlmostEqual(metrics['time_since_last_failure'], 30.0, places=1)
    
    async def test_state_change_counter(self):
        """Test state change counter increments correctly"""
        initial_metrics = self.circuit_breaker.get_metrics()
        initial_state_changes = initial_metrics['state_changes']
        
        # Trigger state change to OPEN
        async def failure_function():
            raise ServiceError("service error")
        
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(ServiceError):
                await self.circuit_breaker.call(failure_function)
        
        open_metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(open_metrics['state_changes'], initial_state_changes + 1)
        self.assertEqual(open_metrics['current_state'], CircuitBreakerState.OPEN.value)
        
        # Transition to HALF_OPEN
        await self.circuit_breaker._transition_to_half_open()
        
        half_open_metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(half_open_metrics['state_changes'], initial_state_changes + 2)
        self.assertEqual(half_open_metrics['current_state'], CircuitBreakerState.HALF_OPEN.value)


class TestCircuitBreakerEdgeCases(IsolatedAsyncioTestCase):
    """Test edge cases and error scenarios"""
    
    async def asyncSetUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            name="edge_case_test"
        )
    
    async def test_exception_in_function_preserves_original_exception(self):
        """Test original exception is preserved and re-raised"""
        original_error = ValueError("original error message")
        
        async def failing_function():
            raise original_error
        
        with self.assertRaises(ValueError) as cm:
            await self.circuit_breaker.call(failing_function)
        
        self.assertEqual(cm.exception, original_error)
    
    async def test_reset_clears_all_state(self):
        """Test reset() clears all circuit breaker state"""
        # First, put circuit breaker in a non-initial state
        async def failure_function():
            raise NetworkError("network error")
        
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(NetworkError):
                await self.circuit_breaker.call(failure_function)
        
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
        
        # Reset circuit breaker
        await self.circuit_breaker.reset()
        
        # Verify all state is reset
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['consecutive_failures'], 0)
        self.assertEqual(metrics['error_rate'], 0.0)
        self.assertEqual(metrics['current_state'], CircuitBreakerState.CLOSED.value)
        
        # Verify it works normally after reset
        async def success_function():
            return "success"
        
        result = await self.circuit_breaker.call(success_function)
        self.assertEqual(result, "success")
    
    async def test_async_context_manager(self):
        """Test circuit breaker works as async context manager"""
        async with self.circuit_breaker as cb:
            self.assertIs(cb, self.circuit_breaker)
            
            async def test_function():
                return "context_test"
            
            result = await cb.call(test_function)
            self.assertEqual(result, "context_test")
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_concurrent_calls_thread_safety(self, mock_monitoring):
        """Test circuit breaker is thread-safe with concurrent calls"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        call_count = 0
        
        async def concurrent_function():
            nonlocal call_count
            await asyncio.sleep(0.01)  # Small delay to increase concurrency
            call_count += 1
            return f"result_{call_count}"
        
        # Execute many concurrent calls
        tasks = [
            asyncio.create_task(self.circuit_breaker.call(concurrent_function))
            for _ in range(50)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        self.assertEqual(len(results), 50)
        self.assertTrue(all(r.startswith("result_") for r in results))
        
        # Metrics should be consistent
        metrics = self.circuit_breaker.get_metrics()
        self.assertEqual(metrics['total_calls'], 50)
        self.assertEqual(metrics['successful_calls'], 50)
        self.assertEqual(metrics['failed_calls'], 0)
    
    async def test_zero_failure_threshold(self):
        """Test circuit breaker with zero failure threshold"""
        zero_threshold_cb = CircuitBreaker(
            failure_threshold=0,
            name="zero_threshold"
        )
        
        async def failure_function():
            raise ServiceError("service error")
        
        # Even first failure should open circuit
        with self.assertRaises(ServiceError):
            await zero_threshold_cb.call(failure_function)
        
        # Circuit should be open immediately
        self.assertEqual(zero_threshold_cb.state, CircuitBreakerState.OPEN)
    
    async def test_extremely_short_recovery_timeout(self):
        """Test circuit breaker with very short recovery timeout"""
        fast_recovery_cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.001,  # 1ms
            name="fast_recovery"
        )
        
        async def failure_function():
            raise NetworkError("network error")
        
        # Trigger OPEN state
        with self.assertRaises(NetworkError):
            await fast_recovery_cb.call(failure_function)
        
        self.assertEqual(fast_recovery_cb.state, CircuitBreakerState.OPEN)
        
        # Wait slightly longer than recovery timeout
        await asyncio.sleep(0.01)
        
        # Next call should transition to HALF_OPEN
        async def success_function():
            return "success"
        
        result = await fast_recovery_cb.call(success_function)
        self.assertEqual(result, "success")
        
        # Should be HALF_OPEN after one successful call
        # (will transition to CLOSED after half_open_max_calls)
        self.assertTrue(
            fast_recovery_cb.state in [CircuitBreakerState.HALF_OPEN, CircuitBreakerState.CLOSED]
        )


class TestCircuitBreakerMonitoringIntegration(IsolatedAsyncioTestCase):
    """Test integration with monitoring system"""
    
    async def asyncSetUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=2,
            name="monitoring_test"
        )
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_structured_error_logging(self, mock_monitoring):
        """Test structured error logging with monitoring system"""
        mock_monitoring_instance = MagicMock()
        mock_logger = MagicMock()
        mock_metrics = MagicMock()
        mock_monitoring_instance.logger = mock_logger
        mock_monitoring_instance.metrics = mock_metrics
        mock_monitoring.return_value = mock_monitoring_instance
        
        network_error = NetworkError("connection failed")
        
        async def failing_function():
            raise network_error
        
        with self.assertRaises(NetworkError):
            await self.circuit_breaker.call(failing_function)
        
        # Verify structured logging was called
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args
        
        # Check log message structure
        self.assertIn("Circuit breaker", call_args[0][0])
        self.assertIn("monitoring_test", call_args[0][0])
        
        # Check log context
        kwargs = call_args[1]
        self.assertIn('circuit_breaker_name', kwargs)
        self.assertIn('consecutive_failures', kwargs)
        self.assertIn('state', kwargs)
        
        # Verify metrics were recorded
        mock_metrics.increment.assert_called()
        metric_call = mock_metrics.increment.call_args
        self.assertEqual(metric_call[0][0], "circuit_breaker_failures_total")
        
        # Check metric tags
        tags = metric_call[1]['tags']
        self.assertEqual(tags['circuit_breaker'], 'monitoring_test')
        self.assertEqual(tags['error_type'], 'NetworkError')
        self.assertEqual(tags['error_category'], 'network')
    
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_state_transition_metrics(self, mock_monitoring):
        """Test state transition metrics are recorded"""
        mock_monitoring_instance = MagicMock()
        mock_logger = MagicMock()
        mock_metrics = MagicMock()
        mock_monitoring_instance.logger = mock_logger
        mock_monitoring_instance.metrics = mock_metrics
        mock_monitoring.return_value = mock_monitoring_instance
        
        async def failing_function():
            raise ServiceError("service failure")
        
        # Trigger state transition to OPEN
        for i in range(self.circuit_breaker.failure_threshold):
            with self.assertRaises(ServiceError):
                await self.circuit_breaker.call(failing_function)
        
        # Verify OPEN state metrics
        mock_metrics.increment.assert_any_call(
            "circuit_breaker_open_total",
            tags={'circuit_breaker': 'monitoring_test'}
        )
        mock_metrics.set_gauge.assert_any_call(
            "circuit_breaker_state",
            1,  # 1 = OPEN
            tags={'circuit_breaker': 'monitoring_test'}
        )
        
        # Transition to HALF_OPEN then CLOSED
        await self.circuit_breaker._transition_to_half_open()
        await self.circuit_breaker._transition_to_closed()
        
        # Verify CLOSED state metrics
        mock_metrics.increment.assert_any_call(
            "circuit_breaker_recovery_total",
            tags={'circuit_breaker': 'monitoring_test'}
        )
        mock_metrics.set_gauge.assert_any_call(
            "circuit_breaker_state",
            0,  # 0 = CLOSED
            tags={'circuit_breaker': 'monitoring_test'}
        )
    
    @patch('app.wildosnode.grpc_client.classify_grpc_error')
    @patch('app.wildosnode.grpc_client._get_monitoring_system')
    async def test_error_classification_integration(self, mock_monitoring, mock_classify):
        """Test integration with error classification system"""
        mock_monitoring_instance = MagicMock()
        mock_monitoring_instance.logger = MagicMock()
        mock_monitoring_instance.metrics = MagicMock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        # Mock the error classification
        classified_error = NetworkError("classified network error")
        classified_error.category = ErrorCategory.NETWORK
        classified_error.severity = ErrorSeverity.HIGH
        mock_classify.return_value = classified_error
        
        from grpclib import GRPCError, Status
        original_grpc_error = GRPCError(Status.UNAVAILABLE, "service unavailable")
        
        async def grpc_failing_function():
            raise original_grpc_error
        
        with self.assertRaises(NetworkError):
            await self.circuit_breaker.call(grpc_failing_function)
        
        # Verify error was classified
        mock_classify.assert_called_once_with(original_grpc_error)
        
        # Verify classified error was used in logging
        mock_monitoring_instance.logger.error.assert_called()
        call_kwargs = mock_monitoring_instance.logger.error.call_args[1]
        
        # Verify metrics used classified error category
        mock_monitoring_instance.metrics.increment.assert_called()
        metric_call = mock_monitoring_instance.metrics.increment.call_args
        tags = metric_call[1]['tags']
        self.assertEqual(tags['error_category'], 'network')


if __name__ == '__main__':
    unittest.main()