"""
Integration test configuration and fixtures
"""
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock

from app.db.base import Base


@pytest.fixture(scope="function")
def test_db_engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest_asyncio.fixture
async def grpc_server_mock():
    """Mock gRPC server for integration tests"""
    server_mock = AsyncMock()
    server_mock.start = AsyncMock()
    server_mock.stop = AsyncMock()
    server_mock.wait_for_termination = AsyncMock()
    
    # Start the mock server
    await server_mock.start()
    
    yield server_mock
    
    # Stop the mock server
    await server_mock.stop()


@pytest.fixture
def fastapi_test_client():
    """FastAPI test client for integration tests"""
    from fastapi.testclient import TestClient
    from app.wildosvpn import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def integration_test_headers():
    """Common headers for integration tests"""
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"
    }