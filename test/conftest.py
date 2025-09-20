"""
Global test configuration and fixtures for WildOS VPN
"""
import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Add mock path for missing backend modules and project root
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
mock_path = os.path.join(test_dir, 'mocks')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if mock_path not in sys.path:
    sys.path.insert(0, mock_path)

# Set test environment variables
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"

# Import test fixtures
from test.fixtures.grpc_fixtures import *
from test.fixtures.data_fixtures import *


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests"""
    # Set additional test environment variables
    os.environ["DEBUG"] = "False"
    os.environ["DOCS"] = "False"
    os.environ["CORS_ALLOWED_ORIGINS"] = '["http://localhost:3000"]'
    os.environ["CORS_ALLOW_CREDENTIALS"] = "False"
    
    yield
    
    # Cleanup after tests
    test_env_vars = [
        "TESTING", "DATABASE_URL", "SECRET_KEY", "JWT_SECRET_KEY",
        "DEBUG", "DOCS", "CORS_ALLOWED_ORIGINS", "CORS_ALLOW_CREDENTIALS"
    ]
    for var in test_env_vars:
        os.environ.pop(var, None)


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    return redis_mock


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler for testing"""
    scheduler_mock = MagicMock()
    scheduler_mock.start = MagicMock()
    scheduler_mock.shutdown = MagicMock()
    scheduler_mock.add_job = MagicMock()
    scheduler_mock.remove_job = MagicMock()
    return scheduler_mock


@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    from httpx import AsyncClient
    async with AsyncClient() as client:
        yield client


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "contract: marks tests as contract tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "grpc: marks tests as gRPC related"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests as database tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require database"
    )
    config.addinivalue_line(
        "markers", "requires_grpc: marks tests that require gRPC server"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location"""
    for item in items:
        # Auto-mark based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Auto-mark gRPC tests
        if "grpc" in str(item.fspath).lower() or "grpc" in item.name.lower():
            item.add_marker(pytest.mark.grpc)
            item.add_marker(pytest.mark.requires_grpc)
        
        # Auto-mark API tests
        if "api" in str(item.fspath).lower() or "api" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # Auto-mark database tests
        if "database" in str(item.fspath).lower() or "db" in str(item.fspath).lower():
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.requires_db)