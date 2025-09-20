"""
Unit test configuration and fixtures
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_database():
    """Mock database session for unit tests"""
    db_mock = MagicMock()
    db_mock.query = MagicMock()
    db_mock.add = MagicMock()
    db_mock.commit = MagicMock()
    db_mock.rollback = MagicMock()
    db_mock.close = MagicMock()
    return db_mock


@pytest.fixture
def mock_grpc_client():
    """Mock gRPC client for unit tests"""
    client_mock = AsyncMock()
    client_mock.sync_users = AsyncMock()
    client_mock.fetch_backends = AsyncMock()
    client_mock.get_host_metrics = AsyncMock()
    return client_mock


@pytest.fixture
def mock_notification_service():
    """Mock notification service for unit tests"""
    service_mock = AsyncMock()
    service_mock.send_notification = AsyncMock()
    service_mock.send_telegram_message = AsyncMock()
    service_mock.send_webhook = AsyncMock()
    return service_mock