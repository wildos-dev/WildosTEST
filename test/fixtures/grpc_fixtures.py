"""
gRPC Testing Fixtures for WildosNode service
"""
import asyncio
import grpc
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from wildosnode.wildosnode.service.service_pb2_grpc import WildosServiceStub
from wildosnode.wildosnode.service.service_pb2 import (
    Empty, Backend, BackendsResponse, User, UserData, UsersData,
    UsersStats, BackendConfig, BackendStats, HostSystemMetrics,
    NetworkInterface, PeakEvent, PeakQuery
)


@pytest.fixture
def grpc_channel():
    """Mock gRPC channel for testing"""
    return MagicMock(spec=grpc.aio.Channel)


@pytest.fixture
def grpc_stub(grpc_channel):
    """Mock gRPC service stub"""
    return MagicMock(spec=WildosServiceStub)


@pytest.fixture
def mock_backend():
    """Sample backend data for testing"""
    return Backend(
        name="test-backend",
        type="xray",
        version="1.8.0",
        inbounds=[]
    )


@pytest.fixture
def mock_user():
    """Sample user data for testing"""
    return User(
        id=1,
        username="testuser",
        key="test-key-123"
    )


@pytest.fixture
def mock_user_data(mock_user):
    """Sample user data with inbounds for testing"""
    return UserData(
        user=mock_user,
        inbounds=[]
    )


@pytest.fixture
def mock_users_data(mock_user_data):
    """Sample users data collection for testing"""
    return UsersData(
        users_data=[mock_user_data]
    )


@pytest.fixture
def mock_backend_stats():
    """Sample backend statistics for testing"""
    return BackendStats(running=True)


@pytest.fixture
def mock_host_metrics():
    """Sample host system metrics for testing"""
    return HostSystemMetrics(
        cpu_usage=45.2,
        memory_usage=2048.0,
        memory_total=8192.0,
        disk_usage=50.0,
        disk_total=100.0,
        network_interfaces=[
            NetworkInterface(
                name="eth0",
                bytes_sent=1024,
                bytes_received=2048,
                packets_sent=10,
                packets_received=20
            )
        ],
        uptime_seconds=3600,
        load_average_1m=0.5,
        load_average_5m=0.7,
        load_average_15m=0.9
    )


@pytest.fixture
def mock_peak_event():
    """Sample peak event for testing"""
    return PeakEvent(
        node_id=1,
        category="CPU",  # PeakCategory
        metric="cpu_usage",
        value=95.0,
        threshold=90.0,
        level="CRITICAL",  # PeakLevel
        dedupe_key="cpu_95",
        context_json='{"details": "test"}',
        started_at_ms=1609459200000,
        seq=1
    )


@pytest.fixture
async def mock_grpc_server():
    """Mock gRPC server for testing"""
    server = MagicMock()
    server.start = AsyncMock()
    server.stop = AsyncMock()
    server.wait_for_termination = AsyncMock()
    return server


@pytest.fixture
async def grpc_test_client(grpc_stub):
    """Test client with mocked gRPC stub"""
    class TestGRPCClient:
        def __init__(self, stub):
            self.stub = stub
            
        async def sync_users(self, users_data):
            return await self.stub.SyncUsers(users_data)
            
        async def fetch_backends(self):
            return await self.stub.FetchBackends(Empty())
            
        async def get_host_metrics(self):
            return await self.stub.GetHostSystemMetrics(Empty())
    
    return TestGRPCClient(grpc_stub)


@pytest.fixture
def grpc_mock_responses(mock_backend, mock_host_metrics, mock_backend_stats):
    """Mock responses for gRPC calls"""
    return {
        'FetchBackends': BackendsResponse(backends=[mock_backend]),
        'GetHostSystemMetrics': mock_host_metrics,
        'GetBackendStats': mock_backend_stats,
        'SyncUsers': Empty(),
        'RepopulateUsers': Empty(),
        'RestartBackend': Empty(),
    }


@pytest.fixture
async def setup_grpc_mocks(grpc_stub, grpc_mock_responses):
    """Setup all gRPC method mocks"""
    # Configure mock responses for all gRPC methods
    grpc_stub.FetchBackends.return_value = grpc_mock_responses['FetchBackends']
    grpc_stub.GetHostSystemMetrics.return_value = grpc_mock_responses['GetHostSystemMetrics']
    grpc_stub.GetBackendStats.return_value = grpc_mock_responses['GetBackendStats']
    grpc_stub.SyncUsers.return_value = grpc_mock_responses['SyncUsers']
    grpc_stub.RepopulateUsers.return_value = grpc_mock_responses['RepopulateUsers']
    grpc_stub.RestartBackend.return_value = grpc_mock_responses['RestartBackend']
    
    return grpc_stub