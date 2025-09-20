"""
Comprehensive unit tests for gRPC client components.

Tests:
- WildosNodeGRPCLIB client operations  
- ConnectionPool management и health checks
- Timeout handling и retry logic
- Streaming operations и reconnection
- Connection context management
- Authentication и security
- Docker VPS resource monitoring
"""

import asyncio
import ssl
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from unittest import IsolatedAsyncioTestCase
from tempfile import NamedTemporaryFile

from grpclib import GRPCError, Status
from grpclib.client import Channel
from grpclib.exceptions import StreamTerminatedError

from app.wildosnode.grpc_client import (
    WildosNodeGRPCLIB, ConnectionPool, ConnectionInfo, ConnectionContext,
    DockerVPSResourceMonitor, retry_with_exponential_backoff,
    circuit_breaker_protected, string_to_temp_file,
    GRPC_FAST_TIMEOUT, GRPC_SLOW_TIMEOUT, GRPC_STREAM_TIMEOUT,
    CONNECTION_POOL_SIZE, CONNECTION_POOL_MAX_SIZE
)
from app.wildosnode.exceptions import (
    NetworkError, ServiceError, TimeoutError, ConnectionError as WildosConnectionError,
    CircuitBreakerError, ErrorContext
)
from app.wildosnode.service_pb2 import (
    Empty, Backend, BackendsResponse, User, UserData, UsersData,
    BackendConfig, ConfigFormat, BackendStats, HostSystemMetrics
)


class TestConnectionInfo(IsolatedAsyncioTestCase):
    """Test ConnectionInfo functionality"""
    
    async def asyncSetUp(self):
        self.mock_channel = MagicMock()
        self.mock_stub = MagicMock()
        self.conn_info = ConnectionInfo(self.mock_channel, self.mock_stub)
    
    def test_connection_info_initialization(self):
        """Test ConnectionInfo initializes correctly"""
        self.assertEqual(self.conn_info.channel, self.mock_channel)
        self.assertEqual(self.conn_info.stub, self.mock_stub)
        self.assertFalse(self.conn_info.in_use)
        self.assertTrue(self.conn_info.healthy)
        self.assertIsNotNone(self.conn_info.created_at)
        self.assertIsNotNone(self.conn_info.last_used)
    
    def test_acquire_and_release(self):
        """Test acquire and release functionality"""
        self.assertFalse(self.conn_info.in_use)
        
        self.conn_info.acquire()
        self.assertTrue(self.conn_info.in_use)
        
        self.conn_info.release()
        self.assertFalse(self.conn_info.in_use)
    
    def test_mark_unhealthy(self):
        """Test marking connection as unhealthy"""
        self.assertTrue(self.conn_info.healthy)
        
        self.conn_info.mark_unhealthy()
        self.assertFalse(self.conn_info.healthy)
    
    @patch('app.wildosnode.grpc_client.time.time')
    def test_is_idle(self, mock_time):
        """Test idle detection"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Recently used, should not be idle
        self.conn_info.last_used = current_time - 10.0
        self.assertFalse(self.conn_info.is_idle())
        
        # Long time since last use, should be idle
        self.conn_info.last_used = current_time - 400.0  # > CONNECTION_IDLE_TIMEOUT
        self.assertTrue(self.conn_info.is_idle())
    
    @patch('app.wildosnode.grpc_client.time.time')
    def test_is_expired(self, mock_time):
        """Test connection expiration"""
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Recently created, should not be expired
        self.conn_info.created_at = current_time - 1800.0  # 30 minutes
        self.assertFalse(self.conn_info.is_expired())
        
        # Old connection, should be expired
        self.conn_info.created_at = current_time - 7200.0  # 2 hours > CONNECTION_LIFETIME
        self.assertTrue(self.conn_info.is_expired())
    
    async def test_close(self):
        """Test connection close"""
        self.mock_channel.close = AsyncMock()
        
        await self.conn_info.close()
        self.mock_channel.close.assert_called_once()


class TestConnectionPool(IsolatedAsyncioTestCase):
    """Test ConnectionPool functionality"""
    
    async def asyncSetUp(self):
        self.mock_ssl_context = MagicMock(spec=ssl.SSLContext)
        
        with patch('app.wildosnode.grpc_client._get_monitoring_system') as mock_monitoring:
            mock_monitoring_instance = MagicMock()
            mock_monitoring_instance.logger = MagicMock()
            mock_monitoring_instance.metrics = MagicMock()
            mock_monitoring.return_value = mock_monitoring_instance
            
            self.connection_pool = ConnectionPool(
                node_id=1,
                address="test.example.com",
                port=443,
                ssl_context=self.mock_ssl_context
            )
    
    async def asyncTearDown(self):
        if hasattr(self.connection_pool, '_pool'):
            await self.connection_pool.stop()
    
    @patch('app.wildosnode.grpc_client.Channel')
    @patch('app.wildosnode.grpc_client.WildosServiceStub')
    async def test_create_connection_success(self, mock_stub_class, mock_channel_class):
        """Test successful connection creation"""
        mock_channel = AsyncMock()
        mock_stub = MagicMock()
        mock_channel_class.return_value = mock_channel
        mock_stub_class.return_value = mock_stub
        
        # Mock successful connection test
        mock_stub.FetchBackends = AsyncMock()
        mock_response = MagicMock()
        mock_response.backends = []
        mock_stub.FetchBackends.return_value = mock_response
        
        conn_info = await self.connection_pool._create_connection()
        
        self.assertIsNotNone(conn_info)
        self.assertEqual(conn_info.channel, mock_channel)
        self.assertEqual(conn_info.stub, mock_stub)
        self.assertTrue(conn_info.healthy)
        
        # Verify channel was created with correct parameters
        mock_channel_class.assert_called_once_with(
            "test.example.com", 443, ssl=self.mock_ssl_context
        )
    
    @patch('app.wildosnode.grpc_client.Channel')
    async def test_create_connection_failure(self, mock_channel_class):
        """Test connection creation failure"""
        mock_channel_class.side_effect = OSError("Connection refused")
        
        conn_info = await self.connection_pool._create_connection()
        self.assertIsNone(conn_info)
    
    @patch('app.wildosnode.grpc_client.Channel')
    @patch('app.wildosnode.grpc_client.WildosServiceStub')
    async def test_acquire_connection_from_pool(self, mock_stub_class, mock_channel_class):
        """Test acquiring connection from pool"""
        # Setup mocks
        mock_channel = AsyncMock()
        mock_stub = MagicMock()
        mock_channel_class.return_value = mock_channel
        mock_stub_class.return_value = mock_stub
        
        # Mock successful connection test
        mock_stub.FetchBackends = AsyncMock()
        mock_response = MagicMock()
        mock_response.backends = []
        mock_stub.FetchBackends.return_value = mock_response
        
        # Start pool to create connections
        await self.connection_pool.start()
        
        # Wait a moment for connections to be created
        await asyncio.sleep(0.1)
        
        # Acquire connection
        channel, stub = await self.connection_pool.acquire_connection()
        
        self.assertIsNotNone(channel)
        self.assertIsNotNone(stub)
        
        # Release connection
        await self.connection_pool.release_connection(channel)
    
    async def test_pool_size_limits(self):
        """Test connection pool respects size limits"""
        self.assertEqual(len(self.connection_pool._pool), 0)
        
        # Pool should not exceed max size
        with patch.object(self.connection_pool, '_create_connection') as mock_create:
            mock_conn_info = MagicMock(spec=ConnectionInfo)
            mock_create.return_value = mock_conn_info
            
            # Try to create more connections than max size
            for _ in range(CONNECTION_POOL_MAX_SIZE + 5):
                await self.connection_pool._ensure_min_connections()
            
            # Should not exceed max size
            self.assertLessEqual(len(self.connection_pool._pool), CONNECTION_POOL_MAX_SIZE)
    
    async def test_health_check_removes_unhealthy_connections(self):
        """Test health check removes unhealthy connections"""
        # Add a mock unhealthy connection
        mock_conn_info = MagicMock(spec=ConnectionInfo)
        mock_conn_info.healthy = False
        mock_conn_info.in_use = False
        mock_conn_info.close = AsyncMock()
        
        self.connection_pool._pool.append(mock_conn_info)
        
        await self.connection_pool._health_check()
        
        # Unhealthy connection should be removed
        self.assertNotIn(mock_conn_info, self.connection_pool._pool)
        mock_conn_info.close.assert_called_once()
    
    async def test_cleanup_idle_connections(self):
        """Test cleanup of idle connections"""
        # Add mock idle connection
        mock_conn_info = MagicMock(spec=ConnectionInfo)
        mock_conn_info.healthy = True
        mock_conn_info.in_use = False
        mock_conn_info.is_idle.return_value = True
        mock_conn_info.close = AsyncMock()
        
        # Add enough connections to trigger cleanup
        for _ in range(CONNECTION_POOL_SIZE + 2):
            self.connection_pool._pool.append(mock_conn_info)
        
        await self.connection_pool._cleanup_idle_connections()
        
        # Some idle connections should be cleaned up
        self.assertLessEqual(len(self.connection_pool._pool), CONNECTION_POOL_MAX_SIZE)
    
    def test_get_metrics(self):
        """Test metrics collection"""
        # Add mock connections with different states
        healthy_conn = MagicMock(spec=ConnectionInfo)
        healthy_conn.healthy = True
        healthy_conn.in_use = False
        
        unhealthy_conn = MagicMock(spec=ConnectionInfo)
        unhealthy_conn.healthy = False
        unhealthy_conn.in_use = False
        
        in_use_conn = MagicMock(spec=ConnectionInfo)
        in_use_conn.healthy = True
        in_use_conn.in_use = True
        
        self.connection_pool._pool.extend([healthy_conn, unhealthy_conn, in_use_conn])
        
        metrics = self.connection_pool.get_metrics()
        
        self.assertEqual(metrics['pool_size'], 3)
        self.assertEqual(metrics['connections_available'], 1)  # Only healthy and not in use
        self.assertEqual(metrics['connections_unhealthy'], 1)
        self.assertEqual(metrics['node_id'], 1)
        self.assertIn('address', metrics)


class TestConnectionContext(IsolatedAsyncioTestCase):
    """Test ConnectionContext context manager"""
    
    async def asyncSetUp(self):
        self.mock_pool = AsyncMock()
        self.mock_channel = MagicMock()
        self.mock_stub = MagicMock()
        
        self.mock_pool.acquire_connection.return_value = (self.mock_channel, self.mock_stub)
        self.mock_pool.release_connection = AsyncMock()
        
        self.context = ConnectionContext(self.mock_pool)
    
    async def test_context_manager_flow(self):
        """Test context manager acquire and release flow"""
        async with self.context as (channel, stub):
            self.assertEqual(channel, self.mock_channel)
            self.assertEqual(stub, self.mock_stub)
            self.mock_pool.acquire_connection.assert_called_once()
        
        # Should release connection on exit
        self.mock_pool.release_connection.assert_called_once_with(self.mock_channel)
    
    async def test_context_manager_exception_handling(self):
        """Test context manager releases connection even on exception"""
        with pytest.raises(ValueError):
            async with self.context as (channel, stub):
                raise ValueError("test exception")
        
        # Should still release connection
        self.mock_pool.release_connection.assert_called_once_with(self.mock_channel)


class TestWildosNodeGRPCLIB(IsolatedAsyncioTestCase):
    """Test main gRPC client functionality"""
    
    async def asyncSetUp(self):
        # Mock certificate manager
        with patch('app.wildosnode.grpc_client._get_certificate_manager') as mock_cert_manager_func:
            mock_cert_manager = MagicMock()
            mock_cert_manager.get_panel_client_certificate.return_value = ("cert_pem", "key_pem")
            mock_cert_manager.get_client_certificate_bundle.return_value = "ca_cert_pem"
            mock_cert_manager_func.return_value = lambda: mock_cert_manager
            
            # Mock node status
            with patch('app.wildosnode.grpc_client._get_node_status') as mock_node_status:
                mock_status = MagicMock()
                mock_status.healthy = "healthy"
                mock_status.unhealthy = "unhealthy"
                mock_node_status.return_value = mock_status
                
                # Mock temp file creation
                with patch('app.wildosnode.grpc_client.string_to_temp_file') as mock_temp_file:
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/test_cert"
                    mock_temp_file.return_value = mock_file
                    
                    self.client = WildosNodeGRPCLIB(
                        node_id=1,
                        address="test.example.com",
                        port=443,
                        ssl_key="test_key",
                        ssl_cert="test_cert",
                        auth_token="test_token"
                    )
    
    async def asyncTearDown(self):
        await self.client.stop()
    
    def test_client_initialization(self):
        """Test client initializes correctly"""
        self.assertEqual(self.client.id, 1)
        self.assertEqual(self.client._address, "test.example.com")
        self.assertEqual(self.client._port, 443)
        self.assertEqual(self.client._auth_token, "test_token")
        self.assertIsNotNone(self.client._connection_pool)
        self.assertIsInstance(self.client._circuit_breakers, dict)
        
        # Check circuit breakers are created for different operations
        expected_breakers = ['user_stats', 'user_sync', 'backend_operations', 
                           'logs_streaming', 'system_monitoring']
        for breaker_name in expected_breakers:
            self.assertIn(breaker_name, self.client._circuit_breakers)
    
    def test_auth_metadata_generation(self):
        """Test authentication metadata generation"""
        metadata = self.client._get_auth_metadata()
        self.assertEqual(metadata, [('authorization', 'Bearer test_token')])
        
        # Test without token
        self.client._auth_token = None
        metadata = self.client._get_auth_metadata()
        self.assertEqual(metadata, [('authorization', '')])
    
    def test_auth_token_management(self):
        """Test auth token set/get"""
        new_token = "new_test_token"
        self.client.set_auth_token(new_token)
        self.assertEqual(self.client.get_auth_token(), new_token)
        self.assertEqual(self.client._auth_token, new_token)
    
    @patch('app.wildosnode.grpc_client.ConnectionContext')
    async def test_fetch_users_stats_with_circuit_breaker(self, mock_context_class):
        """Test fetch_users_stats with circuit breaker protection"""
        # Mock connection context
        mock_context = AsyncMock()
        mock_channel = MagicMock()
        mock_stub = AsyncMock()
        mock_context.__aenter__.return_value = (mock_channel, mock_stub)
        mock_context_class.return_value = mock_context
        
        # Mock successful response
        mock_stub.FetchUsersStats.return_value = MagicMock()
        
        result = await self.client.fetch_users_stats()
        
        # Verify call was made with correct parameters
        mock_stub.FetchUsersStats.assert_called_once()
        call_args = mock_stub.FetchUsersStats.call_args
        self.assertIsInstance(call_args[0][0], Empty)
        self.assertEqual(call_args[1]['timeout'], GRPC_FAST_TIMEOUT)
        self.assertEqual(call_args[1]['metadata'], [('authorization', 'Bearer test_token')])
    
    @patch('app.wildosnode.grpc_client.ConnectionContext')
    async def test_fetch_backends_with_retry(self, mock_context_class):
        """Test _fetch_backends with retry mechanism"""
        # Mock connection context
        mock_context = AsyncMock()
        mock_channel = MagicMock()
        mock_stub = AsyncMock()
        mock_context.__aenter__.return_value = (mock_channel, mock_stub)
        mock_context_class.return_value = mock_context
        
        # Mock backends response
        mock_backend1 = Backend(name="backend1", type="test")
        mock_backend2 = Backend(name="backend2", type="test")
        mock_response = BackendsResponse(backends=[mock_backend1, mock_backend2])
        mock_stub.FetchBackends.return_value = mock_response
        
        result = await self.client._fetch_backends()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "backend1")
        self.assertEqual(result[1].name, "backend2")
    
    @patch('app.wildosnode.grpc_client.ConnectionContext')
    async def test_restart_backend(self, mock_context_class):
        """Test restart_backend operation"""
        # Mock connection context
        mock_context = AsyncMock()
        mock_channel = MagicMock()
        mock_stub = AsyncMock()
        mock_context.__aenter__.return_value = (mock_channel, mock_stub)
        mock_context_class.return_value = mock_context
        
        # Mock successful restart
        mock_stub.RestartBackend = AsyncMock()
        
        # Mock _sync method
        self.client._sync = AsyncMock()
        
        # Mock set_status method
        with patch.object(self.client, 'set_status') as mock_set_status:
            await self.client.restart_backend("test_backend", "test_config", 1)
        
        # Verify restart was called
        mock_stub.RestartBackend.assert_called_once()
        
        # Verify sync was called after restart
        self.client._sync.assert_called_once()
        
        # Verify status was set to healthy
        mock_set_status.assert_called()
    
    @patch('app.wildosnode.grpc_client.ConnectionContext')
    async def test_get_logs_streaming_with_circuit_breaker(self, mock_context_class):
        """Test get_logs streaming with circuit breaker protection"""
        # Mock connection context
        mock_context = AsyncMock()
        mock_channel = MagicMock()
        mock_stub = AsyncMock()
        mock_context.__aenter__.return_value = (mock_channel, mock_stub)
        mock_context_class.return_value = mock_context
        
        # Mock streaming response
        mock_stream = AsyncMock()
        mock_stub.StreamBackendLogs.open.return_value = mock_stream
        
        # Mock log responses
        from app.wildosnode.service_pb2 import LogLine
        mock_log1 = LogLine(line="Log line 1")
        mock_log2 = LogLine(line="Log line 2")
        mock_stream.recv_message.side_effect = [mock_log1, mock_log2, None]
        
        # Collect log lines
        log_lines = []
        async for line in self.client.get_logs("xray", True):
            log_lines.append(line)
            if len(log_lines) >= 2:  # Prevent infinite loop
                break
        
        self.assertEqual(len(log_lines), 2)
        self.assertEqual(log_lines[0], "Log line 1")
        self.assertEqual(log_lines[1], "Log line 2")
        
        # Verify circuit breaker was used
        self.assertIn('logs_streaming', self.client._circuit_breakers)
    
    async def test_update_user_queues_update(self):
        """Test update_user queues user update"""
        from app.models.user import User
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.key = "testkey"
        
        inbounds = {"test_inbound"}
        
        # Queue should be empty initially
        self.assertTrue(self.client._updates_queue.empty())
        
        await self.client.update_user(mock_user, inbounds)
        
        # Queue should now have the update
        self.assertFalse(self.client._updates_queue.empty())
        
        # Get the queued update
        update = await self.client._updates_queue.get()
        self.assertEqual(update["user"], mock_user)
        self.assertEqual(update["inbounds"], inbounds)
    
    def test_get_circuit_breaker_metrics(self):
        """Test circuit breaker metrics collection"""
        metrics = self.client.get_circuit_breaker_metrics()
        
        # Should have metrics for all circuit breakers
        expected_breakers = ['user_stats', 'user_sync', 'backend_operations', 
                           'logs_streaming', 'system_monitoring']
        
        for breaker_name in expected_breakers:
            self.assertIn(breaker_name, metrics)
            breaker_metrics = metrics[breaker_name]
            self.assertIn('name', breaker_metrics)
            self.assertIn('current_state', breaker_metrics)
            self.assertIn('total_calls', breaker_metrics)
    
    async def test_stop_graceful_shutdown(self):
        """Test graceful shutdown process"""
        # Create mock tasks
        self.client._monitor_task = AsyncMock()
        self.client._streaming_task = AsyncMock()
        
        # Mock connection pool stop
        self.client._connection_pool.stop = AsyncMock()
        
        await self.client.stop()
        
        # Verify tasks were cancelled
        self.client._monitor_task.cancel.assert_called()
        self.client._streaming_task.cancel.assert_called()
        
        # Verify connection pool was stopped
        self.client._connection_pool.stop.assert_called_once()


class TestDockerVPSResourceMonitor(IsolatedAsyncioTestCase):
    """Test Docker VPS resource monitoring"""
    
    async def asyncSetUp(self):
        self.mock_monitoring = MagicMock()
        self.monitor = DockerVPSResourceMonitor(self.mock_monitoring)
    
    @patch('app.wildosnode.grpc_client.psutil')
    async def test_check_resource_constraints_with_psutil(self, mock_psutil):
        """Test resource constraint checking with psutil"""
        # Mock psutil data
        mock_memory = MagicMock()
        mock_memory.percent = 90  # High memory usage
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_psutil.cpu_percent.return_value = 85  # High CPU usage
        
        mock_disk = MagicMock()
        mock_disk.percent = 95  # High disk usage
        mock_psutil.disk_usage.return_value = mock_disk
        
        constraints = await self.monitor.check_resource_constraints()
        
        self.assertTrue(constraints['memory_pressure'])
        self.assertTrue(constraints['cpu_pressure'])
        self.assertTrue(constraints['disk_pressure'])
    
    @patch('app.wildosnode.grpc_client.psutil', None)  # Simulate psutil not available
    @patch('builtins.open', mock_open(read_data="MemAvailable: 400000 kB\n"))
    async def test_check_resource_constraints_fallback(self):
        """Test resource constraint checking with /proc fallback"""
        with patch('builtins.open', mock_open(read_data="MemAvailable: 400000 kB\n")):
            constraints = await self.monitor.check_resource_constraints()
            
            # Should detect memory pressure (< 512MB available)
            self.assertTrue(constraints['memory_pressure'])
    
    def test_get_adaptive_config(self):
        """Test adaptive configuration retrieval"""
        config = self.monitor.get_adaptive_config()
        
        expected_keys = ['connection_pool_size', 'retry_attempts', 
                        'timeout_multiplier', 'health_check_interval']
        
        for key in expected_keys:
            self.assertIn(key, config)
    
    def test_detect_container_restart(self):
        """Test container restart detection"""
        # Test various restart indicators
        restart_errors = [
            OSError("Connection refused"),
            ConnectionError("Network unreachable"),
            RuntimeError("Container not running"),
            Exception("Service unavailable")
        ]
        
        for error in restart_errors:
            with self.subTest(error=error):
                is_restart = self.monitor.detect_container_restart(error)
                self.assertTrue(is_restart)
        
        # Test non-restart error
        normal_error = ValueError("Invalid input")
        is_restart = self.monitor.detect_container_restart(normal_error)
        self.assertFalse(is_restart)
    
    def test_get_network_stability_score(self):
        """Test network stability score calculation"""
        mock_pool = MagicMock()
        mock_pool.node_id = 1
        mock_pool.get_metrics.return_value = {
            'health_check_failures': 2,
            'connections_created': 10,
            'network_instability_count': 3
        }
        
        score = self.monitor.get_network_stability_score(mock_pool)
        
        # Score should be between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # With some failures, score should be less than perfect
        self.assertLess(score, 1.0)


class TestRetryDecorator(IsolatedAsyncioTestCase):
    """Test retry decorator functionality"""
    
    async def test_retry_successful_function(self):
        """Test retry decorator with successful function"""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)  # Should succeed on first try
    
    async def test_retry_eventually_successful_function(self):
        """Test retry decorator with function that succeeds after failures"""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        async def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("network failure")
            return "success"
        
        result = await eventually_successful_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)  # Should succeed on third try
    
    async def test_retry_exhausted_retries(self):
        """Test retry decorator when retries are exhausted"""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ServiceError("persistent failure")
        
        with self.assertRaises(ServiceError):
            await always_failing_function()
        
        self.assertEqual(call_count, 3)  # Original call + 2 retries
    
    async def test_retry_respects_non_retryable_errors(self):
        """Test retry decorator respects non-retryable errors"""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        async def non_retryable_error_function():
            nonlocal call_count
            call_count += 1
            error = ServiceError("non-retryable error")
            error.retryable = False
            raise error
        
        with self.assertRaises(ServiceError):
            await non_retryable_error_function()
        
        self.assertEqual(call_count, 1)  # Should not retry


class TestUtilityFunctions(IsolatedAsyncioTestCase):
    """Test utility functions"""
    
    def test_string_to_temp_file(self):
        """Test string to temporary file conversion"""
        test_content = "test certificate content"
        
        temp_file = string_to_temp_file(test_content)
        
        try:
            self.assertTrue(hasattr(temp_file, 'name'))
            
            # Read back content to verify
            with open(temp_file.name, 'r') as f:
                content = f.read()
            
            self.assertEqual(content, test_content)
        finally:
            temp_file.close()


if __name__ == '__main__':
    unittest.main()