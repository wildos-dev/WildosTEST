"""
Comprehensive unit tests for error handling system.

Tests:
- WildosNodeBaseError hierarchy и inheritance
- Error context creation и structured data
- Error classification (NetworkError, ServiceError, etc.)
- Exception mapping и translation from gRPC/network errors
- Error severity и category assignment
- Recovery strategy recommendations
- User message generation
"""

import time
import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase

from grpclib import GRPCError, Status
from grpclib.exceptions import StreamTerminatedError

from app.wildosnode.exceptions import (
    # Base classes
    WildosNodeBaseError, ErrorContext, ErrorSeverity, ErrorCategory, RecoveryStrategy,
    
    # Network errors
    NetworkError, ConnectionError, ConnectionTimeoutError, NetworkUnstableError,
    ContainerNetworkError,
    
    # Service errors
    ServiceError, ServiceUnavailableError, ServiceDegradedError, ConfigurationError,
    AuthenticationError, AuthorizationError, ResourceError, TimeoutError,
    DataIntegrityError, ContainerRestartError, CircuitBreakerError,
    
    # Classification functions
    classify_grpc_error, classify_network_error, classify_ssl_error,
    create_error_with_context, map_grpc_status_to_error
)


class TestErrorContext(TestCase):
    """Test ErrorContext data structure"""
    
    def test_error_context_initialization(self):
        """Test ErrorContext initializes with defaults"""
        context = ErrorContext()
        
        self.assertIsNone(context.node_id)
        self.assertIsNone(context.operation)
        self.assertEqual(context.attempt_number, 1)
        self.assertIsInstance(context.timestamp, float)
        self.assertIsNone(context.duration_ms)
        self.assertEqual(context.recovery_attempts, 0)
        self.assertIsInstance(context.metadata, dict)
    
    def test_error_context_with_parameters(self):
        """Test ErrorContext with provided parameters"""
        context = ErrorContext(
            node_id=1,
            operation="test_operation",
            attempt_number=3,
            duration_ms=150,
            remote_address="192.168.1.100",
            remote_port=443,
            service_name="wildos_service",
            method_name="FetchUsers"
        )
        
        self.assertEqual(context.node_id, 1)
        self.assertEqual(context.operation, "test_operation")
        self.assertEqual(context.attempt_number, 3)
        self.assertEqual(context.duration_ms, 150)
        self.assertEqual(context.remote_address, "192.168.1.100")
        self.assertEqual(context.remote_port, 443)
        self.assertEqual(context.service_name, "wildos_service")
        self.assertEqual(context.method_name, "FetchUsers")
    
    def test_add_metadata(self):
        """Test adding custom metadata"""
        context = ErrorContext()
        
        context.add_metadata("custom_key", "custom_value")
        context.add_metadata("retry_count", 3)
        
        self.assertEqual(context.metadata["custom_key"], "custom_value")
        self.assertEqual(context.metadata["retry_count"], 3)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        context = ErrorContext(
            node_id=1,
            operation="test_op",
            remote_address="192.168.1.1"
        )
        context.add_metadata("test_key", "test_value")
        
        context_dict = context.to_dict()
        
        self.assertIsInstance(context_dict, dict)
        self.assertEqual(context_dict["node_id"], 1)
        self.assertEqual(context_dict["operation"], "test_op")
        self.assertEqual(context_dict["remote_address"], "192.168.1.1")
        self.assertEqual(context_dict["metadata"]["test_key"], "test_value")


class TestWildosNodeBaseError(TestCase):
    """Test base error class functionality"""
    
    def test_base_error_initialization(self):
        """Test base error initializes correctly"""
        error = WildosNodeBaseError("Test error message")
        
        self.assertEqual(error.message, "Test error message")
        self.assertIsInstance(error.context, ErrorContext)
        self.assertIsNone(error.cause)
        self.assertEqual(error.recovery_strategies, [RecoveryStrategy.RETRY])
        self.assertIsInstance(error.occurred_at, float)
    
    def test_base_error_with_context(self):
        """Test base error with custom context"""
        context = ErrorContext(node_id=1, operation="test_operation")
        error = WildosNodeBaseError("Test error", context=context)
        
        self.assertEqual(error.context, context)
        self.assertEqual(error.context.node_id, 1)
    
    def test_base_error_with_cause(self):
        """Test base error with cause exception"""
        original_error = ValueError("Original error")
        error = WildosNodeBaseError("Wrapped error", cause=original_error)
        
        self.assertEqual(error.cause, original_error)
        self.assertEqual(error.__cause__, original_error)
    
    def test_base_error_to_dict(self):
        """Test base error dictionary conversion"""
        context = ErrorContext(node_id=1)
        original_error = ValueError("Original")
        error = WildosNodeBaseError(
            "Test error",
            context=context,
            cause=original_error,
            recovery_strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.RECONNECT]
        )
        
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict["error_type"], "WildosNodeBaseError")
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["category"], "service")  # Default category
        self.assertEqual(error_dict["severity"], "medium")  # Default severity
        self.assertTrue(error_dict["retryable"])
        self.assertEqual(len(error_dict["recovery_strategies"]), 2)
        self.assertEqual(error_dict["cause_type"], "ValueError")
        self.assertEqual(error_dict["cause_message"], "Original")
    
    def test_should_retry(self):
        """Test retry recommendation logic"""
        # Retryable error
        retryable_error = WildosNodeBaseError("Retryable error")
        self.assertTrue(retryable_error.should_retry())
        
        # Non-retryable error
        non_retryable_error = WildosNodeBaseError(
            "Non-retryable error",
            recovery_strategies=[RecoveryStrategy.ESCALATE]
        )
        non_retryable_error.retryable = False
        self.assertFalse(non_retryable_error.should_retry())
    
    def test_should_circuit_break(self):
        """Test circuit breaker recommendation logic"""
        # Error that should trigger circuit breaker
        cb_error = WildosNodeBaseError(
            "Circuit breaker error",
            recovery_strategies=[RecoveryStrategy.CIRCUIT_BREAK]
        )
        self.assertTrue(cb_error.should_circuit_break())
        
        # Error that should not trigger circuit breaker
        normal_error = WildosNodeBaseError("Normal error")
        self.assertFalse(normal_error.should_circuit_break())
    
    def test_get_recommended_delay(self):
        """Test recommended delay calculation"""
        # First attempt
        error = WildosNodeBaseError("Test error")
        delay = error.get_recommended_delay()
        self.assertGreaterEqual(delay, 1.0)
        self.assertLessEqual(delay, 1.5)  # Base delay with jitter
        
        # Third attempt (exponential backoff)
        error.context.attempt_number = 3
        delay = error.get_recommended_delay()
        self.assertGreaterEqual(delay, 2.0)  # Should be higher due to backoff


class TestNetworkErrors(TestCase):
    """Test network-related error classes"""
    
    def test_network_error_properties(self):
        """Test NetworkError class properties"""
        error = NetworkError("Network connection failed")
        
        self.assertEqual(error.category, ErrorCategory.NETWORK)
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertIn(RecoveryStrategy.RETRY, error.recovery_strategies)
        self.assertIn(RecoveryStrategy.RECONNECT, error.recovery_strategies)
        self.assertTrue(error.retryable)
    
    def test_connection_error_properties(self):
        """Test ConnectionError class properties"""
        error = ConnectionError("Connection establishment failed")
        
        self.assertEqual(error.category, ErrorCategory.NETWORK)
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertIn(RecoveryStrategy.RECONNECT, error.recovery_strategies)
        self.assertIn(RecoveryStrategy.RETRY, error.recovery_strategies)
    
    def test_connection_timeout_error(self):
        """Test ConnectionTimeoutError class"""
        error = ConnectionTimeoutError("Connection timeout")
        
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertTrue(error.retryable)
    
    def test_network_unstable_error(self):
        """Test NetworkUnstableError class"""
        error = NetworkUnstableError("Network instability detected")
        
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertIn(RecoveryStrategy.CIRCUIT_BREAK, error.recovery_strategies)
    
    def test_container_network_error(self):
        """Test ContainerNetworkError class"""
        error = ContainerNetworkError("Inter-container communication failed")
        
        self.assertIn(RecoveryStrategy.ESCALATE, error.recovery_strategies)


class TestServiceErrors(TestCase):
    """Test service-related error classes"""
    
    def test_service_error_properties(self):
        """Test ServiceError class properties"""
        error = ServiceError("Service operation failed")
        
        self.assertEqual(error.category, ErrorCategory.SERVICE)
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertTrue(error.retryable)
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError class"""
        error = ServiceUnavailableError("Service is unavailable")
        
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertIn(RecoveryStrategy.CIRCUIT_BREAK, error.recovery_strategies)
    
    def test_configuration_error(self):
        """Test ConfigurationError class"""
        error = ConfigurationError("Invalid configuration")
        
        self.assertEqual(error.category, ErrorCategory.CONFIGURATION)
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertFalse(error.retryable)  # Config errors usually not retryable
    
    def test_authentication_error(self):
        """Test AuthenticationError class"""
        error = AuthenticationError("Authentication failed")
        
        self.assertEqual(error.category, ErrorCategory.AUTHENTICATION)
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertFalse(error.retryable)
    
    def test_timeout_error(self):
        """Test TimeoutError class"""
        error = TimeoutError("Operation timed out")
        
        self.assertEqual(error.category, ErrorCategory.TIMEOUT)
        self.assertTrue(error.retryable)
    
    def test_circuit_breaker_error(self):
        """Test CircuitBreakerError class"""
        error = CircuitBreakerError("Circuit breaker is open")
        
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertFalse(error.retryable)  # Circuit breaker errors should not retry immediately


class TestErrorClassification(TestCase):
    """Test error classification functions"""
    
    def test_map_grpc_status_to_error(self):
        """Test mapping gRPC status codes to error types"""
        # Test various gRPC status mappings
        test_cases = [
            (Status.UNAVAILABLE, ServiceUnavailableError),
            (Status.DEADLINE_EXCEEDED, TimeoutError),
            (Status.UNAUTHENTICATED, AuthenticationError),
            (Status.PERMISSION_DENIED, AuthorizationError),
            (Status.RESOURCE_EXHAUSTED, ResourceError),
            (Status.INVALID_ARGUMENT, ConfigurationError),
            (Status.FAILED_PRECONDITION, ConfigurationError),
            (Status.INTERNAL, ServiceError),  # Default fallback
        ]
        
        for status, expected_error_type in test_cases:
            with self.subTest(status=status):
                error_type = map_grpc_status_to_error(status)
                self.assertEqual(error_type, expected_error_type)
    
    def test_classify_grpc_error(self):
        """Test gRPC error classification"""
        grpc_error = GRPCError(Status.UNAVAILABLE, "Service unavailable")
        
        classified_error = classify_grpc_error(grpc_error)
        
        self.assertIsInstance(classified_error, ServiceUnavailableError)
        self.assertIn("Service unavailable", str(classified_error))
        self.assertEqual(classified_error.cause, grpc_error)
    
    def test_classify_network_error(self):
        """Test network error classification"""
        # Test various network errors
        test_cases = [
            (OSError("Connection refused"), ConnectionError),
            (OSError("Network unreachable"), NetworkError),
            (OSError("Operation timed out"), ConnectionTimeoutError),
            (OSError("Connection reset"), NetworkUnstableError),
            (ConnectionRefusedError("Connection refused"), ConnectionError),
            (TimeoutError("Socket timeout"), ConnectionTimeoutError),
            (OSError("Unknown network error"), NetworkError),  # Default fallback
        ]
        
        for original_error, expected_error_type in test_cases:
            with self.subTest(original_error=original_error):
                classified_error = classify_network_error(original_error)
                self.assertIsInstance(classified_error, expected_error_type)
                self.assertEqual(classified_error.cause, original_error)
    
    def test_classify_ssl_error(self):
        """Test SSL error classification"""
        import ssl
        
        # Test SSL certificate verification error
        ssl_error = ssl.SSLCertVerificationError("Certificate verification failed")
        classified_error = classify_ssl_error(ssl_error)
        
        self.assertIsInstance(classified_error, AuthenticationError)
        self.assertEqual(classified_error.cause, ssl_error)
        
        # Test generic SSL error
        generic_ssl_error = ssl.SSLError("SSL handshake failed")
        classified_error = classify_ssl_error(generic_ssl_error)
        
        self.assertIsInstance(classified_error, NetworkError)
    
    def test_create_error_with_context(self):
        """Test error creation with context"""
        error = create_error_with_context(
            NetworkError,
            "Network connection failed",
            node_id=1,
            operation="fetch_users",
            remote_address="192.168.1.100",
            custom_field="custom_value"
        )
        
        self.assertIsInstance(error, NetworkError)
        self.assertEqual(error.message, "Network connection failed")
        self.assertEqual(error.context.node_id, 1)
        self.assertEqual(error.context.operation, "fetch_users")
        self.assertEqual(error.context.remote_address, "192.168.1.100")
        self.assertEqual(error.context.metadata["custom_field"], "custom_value")


class TestUserMessageGeneration(TestCase):
    """Test user-friendly message generation"""
    
    def test_network_error_user_messages(self):
        """Test user messages for network errors"""
        network_error = NetworkError("Low-level network failure")
        self.assertIn("Network connection issue", network_error.user_message)
        
        connection_error = ConnectionError("Connection establishment failed")
        self.assertIn("Cannot connect to remote service", connection_error.user_message)
        
        timeout_error = ConnectionTimeoutError("Connection timeout")
        self.assertIn("Connection timeout", timeout_error.user_message)
    
    def test_service_error_user_messages(self):
        """Test user messages for service errors"""
        service_error = ServiceError("Internal service error")
        self.assertIn("Service temporarily unavailable", service_error.user_message)
        
        unavailable_error = ServiceUnavailableError("Service is down")
        self.assertIn("Service is currently unavailable", unavailable_error.user_message)
        
        auth_error = AuthenticationError("Invalid credentials")
        self.assertIn("Authentication failed", auth_error.user_message)
    
    def test_configuration_error_user_messages(self):
        """Test user messages for configuration errors"""
        config_error = ConfigurationError("Invalid parameter")
        self.assertIn("Configuration issue detected", config_error.user_message)
        
        resource_error = ResourceError("Insufficient resources")
        self.assertIn("Insufficient system resources", resource_error.user_message)


class TestErrorSeverityAndRecovery(TestCase):
    """Test error severity levels and recovery strategies"""
    
    def test_severity_levels(self):
        """Test different severity levels"""
        low_severity_error = ServiceError("Minor service issue")
        low_severity_error.severity = ErrorSeverity.LOW
        
        critical_error = ServiceUnavailableError("Complete service failure")
        critical_error.severity = ErrorSeverity.CRITICAL
        
        self.assertEqual(low_severity_error.severity, ErrorSeverity.LOW)
        self.assertEqual(critical_error.severity, ErrorSeverity.CRITICAL)
    
    def test_recovery_strategy_combinations(self):
        """Test various recovery strategy combinations"""
        # Network error with multiple strategies
        network_error = NetworkUnstableError("Network instability")
        self.assertIn(RecoveryStrategy.RETRY, network_error.recovery_strategies)
        self.assertIn(RecoveryStrategy.CIRCUIT_BREAK, network_error.recovery_strategies)
        
        # Configuration error with escalation
        config_error = ConfigurationError("Invalid config")
        config_error.recovery_strategies = [RecoveryStrategy.ESCALATE]
        self.assertEqual(config_error.recovery_strategies, [RecoveryStrategy.ESCALATE])
    
    def test_category_classification(self):
        """Test error category classification"""
        network_error = NetworkError("Network issue")
        self.assertEqual(network_error.category, ErrorCategory.NETWORK)
        
        timeout_error = TimeoutError("Operation timeout")
        self.assertEqual(timeout_error.category, ErrorCategory.TIMEOUT)
        
        auth_error = AuthenticationError("Auth failure")
        self.assertEqual(auth_error.category, ErrorCategory.AUTHENTICATION)


class TestErrorChaining(TestCase):
    """Test error chaining and cause tracking"""
    
    def test_error_chaining(self):
        """Test proper error chaining"""
        original_error = ValueError("Original error")
        
        wrapped_error = NetworkError(
            "Network wrapper error",
            cause=original_error
        )
        
        self.assertEqual(wrapped_error.cause, original_error)
        self.assertEqual(wrapped_error.__cause__, original_error)
    
    def test_nested_error_chaining(self):
        """Test multiple levels of error chaining"""
        original_error = OSError("System error")
        
        network_error = NetworkError(
            "Network error",
            cause=original_error
        )
        
        service_error = ServiceError(
            "Service wrapper error",
            cause=network_error
        )
        
        self.assertEqual(service_error.cause, network_error)
        self.assertEqual(network_error.cause, original_error)
    
    def test_error_context_preservation(self):
        """Test error context is preserved through chaining"""
        original_context = ErrorContext(
            node_id=1,
            operation="test_operation",
            attempt_number=2
        )
        
        original_error = NetworkError(
            "Original network error",
            context=original_context
        )
        
        wrapped_error = ServiceError(
            "Wrapped service error",
            cause=original_error,
            context=original_context  # Same context preserved
        )
        
        self.assertEqual(wrapped_error.context, original_context)
        self.assertEqual(wrapped_error.context.node_id, 1)
        self.assertEqual(wrapped_error.context.attempt_number, 2)


class TestErrorMetadata(TestCase):
    """Test error metadata and structured information"""
    
    def test_error_metadata_collection(self):
        """Test comprehensive error metadata collection"""
        context = ErrorContext(
            node_id=5,
            operation="user_sync",
            attempt_number=3,
            duration_ms=2500,
            remote_address="10.0.0.5",
            remote_port=9443,
            service_name="wildos_node_service",
            method_name="SyncUsers",
            container_id="container_123",
            recovery_attempts=1
        )
        
        error = ServiceError(
            "User synchronization failed",
            context=context,
            recovery_strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK]
        )
        
        error_dict = error.to_dict()
        
        # Verify all metadata is preserved
        self.assertEqual(error_dict["context"]["node_id"], 5)
        self.assertEqual(error_dict["context"]["operation"], "user_sync")
        self.assertEqual(error_dict["context"]["attempt_number"], 3)
        self.assertEqual(error_dict["context"]["duration_ms"], 2500)
        self.assertEqual(error_dict["context"]["remote_address"], "10.0.0.5")
        self.assertEqual(error_dict["context"]["remote_port"], 9443)
        self.assertEqual(error_dict["context"]["service_name"], "wildos_node_service")
        self.assertEqual(error_dict["context"]["method_name"], "SyncUsers")
        self.assertEqual(error_dict["context"]["container_id"], "container_123")
        self.assertEqual(error_dict["context"]["recovery_attempts"], 1)
        
        # Verify recovery strategies
        self.assertIn("retry", error_dict["recovery_strategies"])
        self.assertIn("fallback", error_dict["recovery_strategies"])


if __name__ == '__main__':
    unittest.main()