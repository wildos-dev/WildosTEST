"""
Testing utility functions for WildOS VPN
"""
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock


def create_test_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create test configuration with optional overrides"""
    base_config = {
        "database_url": "sqlite:///:memory:",
        "secret_key": "test-secret-key",
        "jwt_secret_key": "test-jwt-secret",
        "debug": True,
        "testing": True,
        "cors_allowed_origins": ["http://localhost:3000"],
        "cors_allow_credentials": False
    }
    
    if overrides:
        base_config.update(overrides)
    
    return base_config


def create_temp_config_file(config: Dict[str, Any]) -> str:
    """Create temporary configuration file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        return f.name


def cleanup_temp_file(file_path: str) -> None:
    """Clean up temporary file"""
    if os.path.exists(file_path):
        os.unlink(file_path)


async def wait_for_condition(
    condition_func, 
    timeout: float = 10.0, 
    interval: float = 0.1
) -> bool:
    """Wait for a condition to become true"""
    start_time = asyncio.get_event_loop().time()
    while True:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        
        if asyncio.get_event_loop().time() - start_time > timeout:
            return False
        
        await asyncio.sleep(interval)


def create_mock_grpc_response(data: Dict[str, Any]) -> MagicMock:
    """Create mock gRPC response"""
    mock_response = MagicMock()
    for key, value in data.items():
        setattr(mock_response, key, value)
    return mock_response


def create_mock_database_session():
    """Create mock database session"""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.execute = MagicMock()
    session.scalar = MagicMock()
    return session


class AsyncMockManager:
    """Manager for async mocks"""
    
    def __init__(self):
        self.mocks = []
    
    def create_async_mock(self, return_value=None, side_effect=None):
        """Create and track async mock"""
        mock = AsyncMock(return_value=return_value, side_effect=side_effect)
        self.mocks.append(mock)
        return mock
    
    def reset_all_mocks(self):
        """Reset all tracked mocks"""
        for mock in self.mocks:
            mock.reset_mock()
    
    def assert_all_called(self):
        """Assert all mocks were called"""
        for mock in self.mocks:
            mock.assert_called()


def create_test_jwt_token(payload: Dict[str, Any]) -> str:
    """Create test JWT token (mock implementation)"""
    import base64
    import json
    
    header = {"alg": "HS256", "typ": "JWT"}
    
    # Encode header and payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Mock signature (not cryptographically secure, only for testing)
    signature = "test_signature"
    
    return f"{header_encoded}.{payload_encoded}.{signature}"


def assert_grpc_call_made(mock_stub, method_name: str, expected_request=None):
    """Assert that a gRPC method was called"""
    method_mock = getattr(mock_stub, method_name)
    method_mock.assert_called()
    
    if expected_request is not None:
        method_mock.assert_called_with(expected_request)


def assert_api_response_format(response_data: Dict[str, Any], expected_fields: list):
    """Assert that API response has expected format"""
    for field in expected_fields:
        assert field in response_data, f"Expected field '{field}' not found in response"


class TestMetrics:
    """Utility for tracking test metrics"""
    
    def __init__(self):
        self.call_counts = {}
        self.execution_times = {}
    
    def track_call(self, function_name: str):
        """Track function call"""
        self.call_counts[function_name] = self.call_counts.get(function_name, 0) + 1
    
    def track_execution_time(self, function_name: str, execution_time: float):
        """Track execution time"""
        if function_name not in self.execution_times:
            self.execution_times[function_name] = []
        self.execution_times[function_name].append(execution_time)
    
    def get_average_execution_time(self, function_name: str) -> float:
        """Get average execution time for function"""
        times = self.execution_times.get(function_name, [])
        return sum(times) / len(times) if times else 0.0
    
    def reset(self):
        """Reset all metrics"""
        self.call_counts.clear()
        self.execution_times.clear()