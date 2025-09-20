"""
Configuration and fixtures for wildosnode unit tests.

Provides comprehensive fixtures for testing gRPC client components:
- Mock monitoring systems
- Mock recovery managers  
- Mock certificate managers
- Mock connection pools
- Mock error scenarios
- Test data factories
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional

from app.wildosnode.exceptions import (
    ErrorContext, NetworkError, ServiceError, TimeoutError,
    ConnectionError, CircuitBreakerError
)


@pytest.fixture
def mock_monitoring_system():
    """Mock monitoring system with logger and metrics"""
    mock_system = MagicMock()
    
    # Mock logger
    mock_logger = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_system.logger = mock_logger
    
    # Mock metrics
    mock_metrics = MagicMock()
    mock_metrics.increment = MagicMock()
    mock_metrics.set_gauge = MagicMock()
    mock_metrics.observe = MagicMock()
    mock_system.metrics = mock_metrics
    
    # Mock health status
    mock_system.get_health_status.return_value = {
        'status': 'healthy',
        'error_rate_percent': 0.0,
        'avg_response_time_ms': 50.0
    }
    
    return mock_system


@pytest.fixture
def mock_recovery_manager():
    """Mock recovery manager for testing recovery mechanisms"""
    mock_manager = MagicMock()
    
    # Mock recovery state
    mock_state = MagicMock()
    mock_state.component_name = "test_component"
    mock_state.consecutive_failures = 0
    mock_state.consecutive_successes = 0
    mock_state.health_status = "healthy"
    mock_state.current_mode = "normal"
    mock_state.should_attempt_recovery.return_value = True
    
    mock_manager.get_recovery_state.return_value = mock_state
    mock_manager.record_success = AsyncMock()
    mock_manager.record_failure = AsyncMock()
    mock_manager.execute_with_recovery = AsyncMock()
    
    return mock_manager


@pytest.fixture
def mock_certificate_manager():
    """Mock certificate manager for SSL/TLS testing"""
    mock_manager = MagicMock()
    
    # Mock certificate data
    mock_manager.get_panel_client_certificate.return_value = (
        "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----",
        "-----BEGIN PRIVATE KEY-----\nMOCK_KEY\n-----END PRIVATE KEY-----"
    )
    mock_manager.get_client_certificate_bundle.return_value = (
        "-----BEGIN CERTIFICATE-----\nMOCK_CA_CERT\n-----END CERTIFICATE-----"
    )
    
    return mock_manager


@pytest.fixture
def mock_node_status():
    """Mock node status for testing status management"""
    mock_status = MagicMock()
    mock_status.healthy = "healthy"
    mock_status.unhealthy = "unhealthy"
    mock_status.degraded = "degraded"
    mock_status.offline = "offline"
    return mock_status


@pytest.fixture
def mock_grpc_stub():
    """Mock gRPC service stub with all required methods"""
    mock_stub = AsyncMock()
    
    # User management methods
    mock_stub.SyncUsers = AsyncMock()
    mock_stub.RepopulateUsers = AsyncMock()
    mock_stub.FetchUsersStats = AsyncMock()
    
    # Backend management methods
    mock_stub.FetchBackends = AsyncMock()
    mock_stub.FetchBackendConfig = AsyncMock()
    mock_stub.RestartBackend = AsyncMock()
    mock_stub.GetBackendStats = AsyncMock()
    mock_stub.StreamBackendLogs = AsyncMock()
    
    # System monitoring methods
    mock_stub.GetHostSystemMetrics = AsyncMock()
    mock_stub.OpenHostPort = AsyncMock()
    mock_stub.CloseHostPort = AsyncMock()
    
    # Container management methods
    mock_stub.GetContainerLogs = AsyncMock()
    mock_stub.GetContainerFiles = AsyncMock()
    mock_stub.RestartContainer = AsyncMock()
    
    # Monitoring methods
    mock_stub.StreamPeakEvents = AsyncMock()
    mock_stub.FetchPeakEvents = AsyncMock()
    mock_stub.GetAllBackendsStats = AsyncMock()
    
    return mock_stub


@pytest.fixture
def mock_grpc_channel():
    """Mock gRPC channel for connection testing"""
    mock_channel = AsyncMock()
    mock_channel.close = AsyncMock()
    return mock_channel


@pytest.fixture
def error_context_factory():
    """Factory for creating error contexts"""
    def create_context(
        node_id: Optional[int] = None,
        operation: Optional[str] = None,
        attempt_number: int = 1,
        **kwargs
    ) -> ErrorContext:
        context = ErrorContext(
            node_id=node_id,
            operation=operation,
            attempt_number=attempt_number,
            timestamp=time.time()
        )
        
        for key, value in kwargs.items():
            setattr(context, key, value)
        
        return context
    
    return create_context


@pytest.fixture
def network_error_factory(error_context_factory):
    """Factory for creating network errors"""
    def create_network_error(
        message: str = "Network error",
        node_id: Optional[int] = None,
        operation: Optional[str] = None,
        **context_kwargs
    ) -> NetworkError:
        context = error_context_factory(
            node_id=node_id,
            operation=operation,
            **context_kwargs
        )
        return NetworkError(message, context=context)
    
    return create_network_error


@pytest.fixture
def service_error_factory(error_context_factory):
    """Factory for creating service errors"""
    def create_service_error(
        message: str = "Service error",
        node_id: Optional[int] = None,
        operation: Optional[str] = None,
        **context_kwargs
    ) -> ServiceError:
        context = error_context_factory(
            node_id=node_id,
            operation=operation,
            **context_kwargs
        )
        return ServiceError(message, context=context)
    
    return create_service_error


@pytest.fixture
def circuit_breaker_config():
    """Configuration for circuit breaker testing"""
    return {
        'failure_threshold': 3,
        'error_rate_threshold': 0.5,
        'monitoring_window': 60.0,
        'recovery_timeout': 5.0,
        'half_open_max_calls': 2,
        'reset_timeout': 300.0
    }


@pytest.fixture
def connection_pool_config():
    """Configuration for connection pool testing"""
    return {
        'pool_size': 3,
        'max_pool_size': 5,
        'connection_lifetime': 3600.0,
        'health_check_interval': 30.0,
        'idle_timeout': 300.0
    }


@pytest.fixture
def grpc_timeouts():
    """gRPC timeout configurations"""
    return {
        'fast_timeout': 15.0,
        'slow_timeout': 60.0,
        'stream_timeout': 30.0,
        'connection_timeout': 10.0
    }


@pytest.fixture
def mock_ssl_context():
    """Mock SSL context for secure connections"""
    import ssl
    mock_context = MagicMock(spec=ssl.SSLContext)
    mock_context.check_hostname = True
    mock_context.verify_mode = ssl.CERT_REQUIRED
    mock_context.load_cert_chain = MagicMock()
    return mock_context


@pytest.fixture
def mock_temp_file():
    """Mock temporary file for certificate testing"""
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_cert_file"
    mock_file.close = MagicMock()
    return mock_file


@pytest.fixture
def async_test_timeout():
    """Timeout for async tests"""
    return 10.0  # 10 seconds


@pytest.fixture
def test_node_config():
    """Test node configuration"""
    return {
        'node_id': 1,
        'address': 'test.example.com',
        'port': 443,
        'ssl_key': 'test_ssl_key',
        'ssl_cert': 'test_ssl_cert',
        'auth_token': 'test_auth_token',
        'usage_coefficient': 1
    }


@pytest.fixture
def mock_protobuf_messages():
    """Mock protobuf message objects"""
    from app.wildosnode.service_pb2 import (
        Empty, Backend, BackendsResponse, User, UserData,
        BackendConfig, BackendStats, HostSystemMetrics
    )
    
    # Mock backend
    mock_backend = Backend(name="test_backend", type="test")
    
    # Mock user
    mock_user = User(id=1, username="testuser", key="testkey")
    
    # Mock backend config
    mock_config = BackendConfig(
        configuration='{"test": "config"}',
        config_format=1
    )
    
    # Mock backend stats
    mock_stats = BackendStats(running=True)
    
    # Mock host metrics
    mock_metrics = HostSystemMetrics(
        cpu_usage=50.0,
        memory_usage=1024000000,
        memory_total=8192000000,
        disk_usage=50000000000,
        disk_total=100000000000
    )
    
    return {
        'empty': Empty(),
        'backend': mock_backend,
        'backends_response': BackendsResponse(backends=[mock_backend]),
        'user': mock_user,
        'user_data': UserData(user=mock_user, inbounds=[]),
        'backend_config': mock_config,
        'backend_stats': mock_stats,
        'host_metrics': mock_metrics
    }


@pytest.fixture
def mock_streaming_response():
    """Mock streaming response for gRPC streaming tests"""
    async def mock_stream():
        from app.wildosnode.service_pb2 import LogLine
        
        # Yield some mock log lines
        yield LogLine(line="Log line 1")
        yield LogLine(line="Log line 2")
        yield LogLine(line="Log line 3")
    
    return mock_stream


@pytest.fixture
def performance_test_config():
    """Configuration for performance testing"""
    return {
        'concurrent_requests': 10,
        'request_timeout': 5.0,
        'test_duration': 30.0,
        'max_latency_ms': 1000.0,
        'min_success_rate': 0.95
    }


@pytest.fixture(autouse=True)
def clean_global_state():
    """Clean global state before each test"""
    # Reset any global variables that might affect tests
    yield
    # Cleanup after test if needed


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class MockAsyncContextManager:
    """Helper class for mocking async context managers"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.fixture
def mock_async_context_manager():
    """Factory for creating mock async context managers"""
    return MockAsyncContextManager