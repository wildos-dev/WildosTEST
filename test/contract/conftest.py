"""
Contract test configuration and fixtures
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import json


@pytest.fixture
def contract_test_server():
    """Mock server for contract testing"""
    server_mock = MagicMock()
    server_mock.start = MagicMock()
    server_mock.stop = MagicMock()
    server_mock.set_expected_interactions = MagicMock()
    return server_mock


@pytest.fixture
def grpc_contract_schema():
    """gRPC contract schema for validation"""
    return {
        "service": "WildosService",
        "methods": {
            "SyncUsers": {
                "input": "UserData",
                "output": "Empty",
                "streaming": {"input": True, "output": False}
            },
            "FetchBackends": {
                "input": "Empty", 
                "output": "BackendsResponse",
                "streaming": {"input": False, "output": False}
            },
            "GetHostSystemMetrics": {
                "input": "Empty",
                "output": "HostSystemMetrics", 
                "streaming": {"input": False, "output": False}
            }
        }
    }


@pytest.fixture
def api_contract_schema():
    """API contract schema for validation"""
    return {
        "endpoints": {
            "/api/users": {
                "methods": ["GET", "POST"],
                "auth_required": True,
                "schemas": {
                    "GET": {"response": "UserListResponse"},
                    "POST": {"request": "CreateUserRequest", "response": "UserResponse"}
                }
            },
            "/api/nodes": {
                "methods": ["GET", "POST"],
                "auth_required": True,
                "schemas": {
                    "GET": {"response": "NodeListResponse"},
                    "POST": {"request": "CreateNodeRequest", "response": "NodeResponse"}
                }
            }
        }
    }


@pytest.fixture
def pact_consumer():
    """Pact consumer for contract testing"""
    consumer_mock = MagicMock()
    consumer_mock.given = MagicMock(return_value=consumer_mock)
    consumer_mock.upon_receiving = MagicMock(return_value=consumer_mock)
    consumer_mock.with_request = MagicMock(return_value=consumer_mock)
    consumer_mock.will_respond_with = MagicMock(return_value=consumer_mock)
    return consumer_mock