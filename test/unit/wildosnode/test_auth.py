"""
Comprehensive unit tests for WildosNode authentication system.

Tests authentication components:
- NodeTokenValidator for token validation and caching
- auth_middleware decorators (require_auth, exception_handler, secure_method)
- Token format validation and security
- Authentication error handling
- Security edge cases and attack scenarios
"""

import pytest
import hashlib
import functools
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from grpclib import GRPCError, Status
from grpclib.server import Stream

from wildosnode.service.auth_middleware import (
    NodeTokenValidator, require_auth, exception_handler, secure_method,
    get_token_validator, set_token_validator
)


@pytest.fixture
def token_validator():
    """Create NodeTokenValidator instance for testing"""
    return NodeTokenValidator()


@pytest.fixture
def valid_token():
    """Sample valid token for testing"""
    return "dGVzdC10b2tlbi0xMjM0NTY3ODkw"  # base64-like token


@pytest.fixture
def invalid_token():
    """Sample invalid token for testing"""
    return "invalid-token-format!"  # Contains invalid characters


@pytest.fixture
def mock_stream():
    """Mock gRPC stream for testing"""
    stream = MagicMock(spec=Stream)
    stream.metadata = [("authorization", "Bearer valid-token")]
    return stream


class TestNodeTokenValidator:
    """Test NodeTokenValidator functionality"""
    
    def test_token_validator_initialization(self, token_validator):
        """Test NodeTokenValidator initialization"""
        assert token_validator.token_cache == {}
        assert token_validator.cache_ttl == 300  # 5 minutes
        
    def test_extract_token_from_metadata_bearer(self, token_validator):
        """Test token extraction with Bearer prefix"""
        metadata = [("authorization", "Bearer test-token-123")]
        token = token_validator.extract_token_from_metadata(metadata)
        assert token == "test-token-123"
        
    def test_extract_token_from_metadata_lowercase_bearer(self, token_validator):
        """Test token extraction with lowercase bearer prefix"""
        metadata = [("authorization", "bearer test-token-123")]
        token = token_validator.extract_token_from_metadata(metadata)
        assert token == "test-token-123"
        
    def test_extract_token_from_metadata_direct(self, token_validator):
        """Test token extraction without Bearer prefix"""
        metadata = [("authorization", "direct-token-123")]
        token = token_validator.extract_token_from_metadata(metadata)
        assert token == "direct-token-123"
        
    def test_extract_token_from_metadata_none(self, token_validator):
        """Test token extraction with no metadata"""
        token = token_validator.extract_token_from_metadata(None)
        assert token is None
        
    def test_extract_token_from_metadata_no_auth(self, token_validator):
        """Test token extraction with no authorization header"""
        metadata = [("content-type", "application/grpc")]
        token = token_validator.extract_token_from_metadata(metadata)
        assert token is None
        
    def test_validate_token_format_valid(self, token_validator, valid_token):
        """Test valid token format validation"""
        assert token_validator.validate_token_format(valid_token) is True
        
    def test_validate_token_format_invalid_characters(self, token_validator, invalid_token):
        """Test invalid token format with special characters"""
        assert token_validator.validate_token_format(invalid_token) is False
        
    def test_validate_token_format_too_short(self, token_validator):
        """Test token format validation with too short token"""
        short_token = "short"  # Less than 20 characters
        assert token_validator.validate_token_format(short_token) is False
        
    def test_validate_token_format_too_long(self, token_validator):
        """Test token format validation with too long token"""
        long_token = "a" * 101  # More than 100 characters
        assert token_validator.validate_token_format(long_token) is False
        
    def test_validate_token_format_empty(self, token_validator):
        """Test token format validation with empty token"""
        assert token_validator.validate_token_format("") is False
        assert token_validator.validate_token_format(None) is False
        
    def test_hash_token(self, token_validator):
        """Test token hashing for logging"""
        token = "test-token-123"
        token_hash = token_validator.hash_token(token)
        
        # Should be a 16-character hex string
        assert len(token_hash) == 16
        assert all(c in '0123456789abcdef' for c in token_hash)
        
        # Same token should produce same hash
        assert token_validator.hash_token(token) == token_hash
        
        # Different tokens should produce different hashes
        different_hash = token_validator.hash_token("different-token")
        assert different_hash != token_hash
        
    @pytest.mark.asyncio
    async def test_validate_token_valid_format(self, token_validator, valid_token):
        """Test token validation with valid format"""
        # Since we don't have real database validation, properly formatted tokens are accepted
        is_valid = await token_validator.validate_token(valid_token)
        assert is_valid is True
        
    @pytest.mark.asyncio
    async def test_validate_token_invalid_format(self, token_validator, invalid_token):
        """Test token validation with invalid format"""
        is_valid = await token_validator.validate_token(invalid_token)
        assert is_valid is False
        
    @pytest.mark.asyncio
    async def test_validate_token_caching(self, token_validator, valid_token):
        """Test token validation caching"""
        # First validation
        is_valid1 = await token_validator.validate_token(valid_token)
        assert is_valid1 is True
        
        # Should be cached now
        token_hash = token_validator.hash_token(valid_token)
        assert token_hash in token_validator.token_cache
        
        # Second validation should use cache
        is_valid2 = await token_validator.validate_token(valid_token)
        assert is_valid2 is True
        
    @pytest.mark.asyncio
    async def test_validate_token_with_node_id(self, token_validator, valid_token):
        """Test token validation with node ID"""
        is_valid = await token_validator.validate_token(valid_token, node_id=123)
        assert is_valid is True
        
        # Should create separate cache entry for node-specific validation
        token_hash = token_validator.hash_token(valid_token)
        cache_key = f"{token_hash}:123"
        assert cache_key in token_validator.token_cache
        
    @pytest.mark.asyncio
    async def test_validate_token_cache_expiration(self, token_validator, valid_token):
        """Test token cache expiration"""
        # Mock time to simulate cache expiration
        with patch('wildosnode.service.auth_middleware.datetime') as mock_datetime:
            # First validation - current time
            mock_datetime.now.return_value.timestamp.return_value = 1640000000
            is_valid1 = await token_validator.validate_token(valid_token)
            assert is_valid1 is True
            
            # Second validation - after cache expiration (> 300 seconds)
            mock_datetime.now.return_value.timestamp.return_value = 1640000400
            is_valid2 = await token_validator.validate_token(valid_token)
            assert is_valid2 is True
            
    def test_clear_cache(self, token_validator, valid_token):
        """Test clearing token cache"""
        # Add entry to cache
        token_validator.token_cache["test_key"] = {"valid": True, "expires_at": 1640000000}
        
        # Clear cache
        token_validator.clear_cache()
        
        assert len(token_validator.token_cache) == 0


class TestAuthMiddleware:
    """Test authentication middleware decorators"""
    
    def test_require_auth_decorator_structure(self):
        """Test require_auth decorator structure"""
        @require_auth(allow_health_check=True)
        async def test_method(self, stream):
            return "success"
            
        # Verify decorator preserves function metadata
        assert hasattr(test_method, '__wrapped__')
        assert test_method.__name__ == 'test_method'
        
    @pytest.mark.asyncio
    async def test_require_auth_success(self, mock_stream):
        """Test successful authentication"""
        @require_auth(allow_health_check=False)
        async def test_method(self, stream):
            return "authenticated"
            
        # Mock token validation
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "valid-token"
            mock_validator.validate_token = AsyncMock(return_value=True)
            
            result = await test_method(MagicMock(), mock_stream)
            assert result == "authenticated"
            
    @pytest.mark.asyncio
    async def test_require_auth_no_metadata(self):
        """Test authentication with no metadata"""
        @require_auth(allow_health_check=False)
        async def test_method(self, stream):
            return "should not reach"
            
        stream = MagicMock()
        stream.metadata = None
        
        with pytest.raises(GRPCError) as exc_info:
            await test_method(MagicMock(), stream)
            
        assert exc_info.value.status == Status.UNAUTHENTICATED
        assert "missing metadata" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_require_auth_no_token(self):
        """Test authentication with no token"""
        @require_auth(allow_health_check=False)
        async def test_method(self, stream):
            return "should not reach"
            
        stream = MagicMock()
        stream.metadata = [("content-type", "application/grpc")]
        
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = None
            
            with pytest.raises(GRPCError) as exc_info:
                await test_method(MagicMock(), stream)
                
            assert exc_info.value.status == Status.UNAUTHENTICATED
            assert "missing or invalid authorization header" in str(exc_info.value)
            
    @pytest.mark.asyncio
    async def test_require_auth_invalid_token(self, mock_stream):
        """Test authentication with invalid token"""
        @require_auth(allow_health_check=False)
        async def test_method(self, stream):
            return "should not reach"
            
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "invalid-token"
            mock_validator.validate_token = AsyncMock(return_value=False)
            
            with pytest.raises(GRPCError) as exc_info:
                await test_method(MagicMock(), mock_stream)
                
            assert exc_info.value.status == Status.UNAUTHENTICATED
            assert "invalid token" in str(exc_info.value)
            
    @pytest.mark.asyncio
    async def test_require_auth_validation_exception(self, mock_stream):
        """Test authentication with validation exception"""
        @require_auth(allow_health_check=False)
        async def test_method(self, stream):
            return "should not reach"
            
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "token"
            mock_validator.validate_token = AsyncMock(side_effect=Exception("Validation error"))
            
            with pytest.raises(GRPCError) as exc_info:
                await test_method(MagicMock(), mock_stream)
                
            assert exc_info.value.status == Status.INTERNAL
            assert "token validation failed" in str(exc_info.value)
            
    @pytest.mark.asyncio
    async def test_require_auth_health_check_allowed(self):
        """Test authentication bypass for health check methods"""
        @require_auth(allow_health_check=True)
        async def Check(self, stream):
            return "health check passed"
            
        result = await Check(MagicMock(), MagicMock())
        assert result == "health check passed"
        
    @pytest.mark.asyncio
    async def test_require_auth_health_check_methods(self):
        """Test all health check method names"""
        health_methods = ['Check', 'Watch', 'HealthCheck']
        
        for method_name in health_methods:
            @require_auth(allow_health_check=True)
            async def health_method(self, stream):
                return f"{method_name} passed"
            
            # Dynamically set method name
            health_method.__name__ = method_name
            
            result = await health_method(MagicMock(), MagicMock())
            assert f"{method_name} passed" == result


class TestExceptionHandler:
    """Test exception handler decorator"""
    
    @pytest.mark.asyncio
    async def test_exception_handler_success(self):
        """Test exception handler with successful execution"""
        @exception_handler
        async def test_method():
            return "success"
            
        result = await test_method()
        assert result == "success"
        
    @pytest.mark.asyncio
    async def test_exception_handler_grpc_error_passthrough(self):
        """Test that GRPCError is passed through unchanged"""
        @exception_handler
        async def test_method():
            raise GRPCError(Status.NOT_FOUND, "Not found")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.NOT_FOUND
        assert str(exc_info.value) == "Not found"
        
    @pytest.mark.asyncio
    async def test_exception_handler_permission_error(self):
        """Test handling of PermissionError"""
        @exception_handler
        async def test_method():
            raise PermissionError("Access denied")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.PERMISSION_DENIED
        assert "Permission denied" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_file_not_found(self):
        """Test handling of FileNotFoundError"""
        @exception_handler
        async def test_method():
            raise FileNotFoundError("File missing")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.NOT_FOUND
        assert "Resource not found" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_value_error(self):
        """Test handling of ValueError"""
        @exception_handler
        async def test_method():
            raise ValueError("Invalid value")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.INVALID_ARGUMENT
        assert "Invalid argument" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_timeout_error(self):
        """Test handling of TimeoutError"""
        @exception_handler
        async def test_method():
            raise TimeoutError("Operation timeout")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.DEADLINE_EXCEEDED
        assert "Operation timeout" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_connection_error(self):
        """Test handling of ConnectionError"""
        @exception_handler
        async def test_method():
            raise ConnectionError("Connection failed")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.UNAVAILABLE
        assert "Service unavailable" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_generic_exception(self):
        """Test handling of generic Exception"""
        @exception_handler
        async def test_method():
            raise Exception("Unexpected error")
            
        with pytest.raises(GRPCError) as exc_info:
            await test_method()
            
        assert exc_info.value.status == Status.INTERNAL
        assert "Internal server error" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_exception_handler_cancelled_error(self):
        """Test handling of asyncio.CancelledError"""
        import asyncio
        
        @exception_handler
        async def test_method():
            raise asyncio.CancelledError()
            
        # CancelledError should be re-raised, not converted to GRPCError
        with pytest.raises(asyncio.CancelledError):
            await test_method()


class TestSecureMethod:
    """Test secure_method combined decorator"""
    
    @pytest.mark.asyncio
    async def test_secure_method_success(self, mock_stream):
        """Test secure_method with successful authentication and execution"""
        @secure_method(allow_health_check=False)
        async def test_method(self, stream):
            return "secure success"
            
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "valid-token"
            mock_validator.validate_token = AsyncMock(return_value=True)
            
            result = await test_method(MagicMock(), mock_stream)
            assert result == "secure success"
            
    @pytest.mark.asyncio
    async def test_secure_method_auth_failure(self, mock_stream):
        """Test secure_method with authentication failure"""
        @secure_method(allow_health_check=False)
        async def test_method(self, stream):
            return "should not reach"
            
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "invalid-token"
            mock_validator.validate_token = AsyncMock(return_value=False)
            
            with pytest.raises(GRPCError) as exc_info:
                await test_method(MagicMock(), mock_stream)
                
            assert exc_info.value.status == Status.UNAUTHENTICATED
            
    @pytest.mark.asyncio
    async def test_secure_method_exception_handling(self, mock_stream):
        """Test secure_method exception handling after successful auth"""
        @secure_method(allow_health_check=False)
        async def test_method(self, stream):
            raise ValueError("Test error")
            
        with patch('wildosnode.service.auth_middleware._token_validator') as mock_validator:
            mock_validator.extract_token_from_metadata.return_value = "valid-token"
            mock_validator.validate_token = AsyncMock(return_value=True)
            
            with pytest.raises(GRPCError) as exc_info:
                await test_method(MagicMock(), mock_stream)
                
            assert exc_info.value.status == Status.INVALID_ARGUMENT
            
    @pytest.mark.asyncio
    async def test_secure_method_health_check_bypass(self):
        """Test secure_method health check bypass"""
        @secure_method(allow_health_check=True)
        async def Check(self, stream):
            return "health check"
            
        result = await Check(MagicMock(), MagicMock())
        assert result == "health check"


class TestTokenValidatorGlobalMethods:
    """Test global token validator methods"""
    
    def test_get_token_validator(self):
        """Test getting global token validator"""
        validator = get_token_validator()
        assert isinstance(validator, NodeTokenValidator)
        
    def test_set_token_validator(self):
        """Test setting custom token validator"""
        custom_validator = NodeTokenValidator()
        custom_validator.cache_ttl = 600  # Different from default
        
        set_token_validator(custom_validator)
        
        retrieved_validator = get_token_validator()
        assert retrieved_validator is custom_validator
        assert retrieved_validator.cache_ttl == 600


class TestSecurityScenarios:
    """Test various security scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_token_injection_attack(self, token_validator):
        """Test resistance to token injection attacks"""
        malicious_tokens = [
            "'; DROP TABLE tokens; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "\x00\x01\x02\x03",  # null bytes and control characters
            "A" * 1000,  # very long token
        ]
        
        for token in malicious_tokens:
            is_valid = await token_validator.validate_token(token)
            # All should be rejected due to format validation
            assert is_valid is False
            
    def test_metadata_header_case_sensitivity(self, token_validator):
        """Test metadata header case sensitivity"""
        test_cases = [
            [("Authorization", "Bearer test-token")],
            [("authorization", "Bearer test-token")],
            [("AUTHORIZATION", "Bearer test-token")],
            [("AuthorizAtion", "Bearer test-token")],
        ]
        
        for metadata in test_cases:
            token = token_validator.extract_token_from_metadata(metadata)
            # Should handle case-insensitive header names
            assert token == "test-token"
            
    def test_token_cache_isolation(self, token_validator):
        """Test that token cache properly isolates different tokens"""
        token1 = "dGVzdC10b2tlbi0xMjM0NTY3ODkw"
        token2 = "ZGlmZmVyZW50LXRva2VuLTEyMzQ1Ng"
        
        hash1 = token_validator.hash_token(token1)
        hash2 = token_validator.hash_token(token2)
        
        # Different tokens should have different hashes
        assert hash1 != hash2
        
        # Cache entries should be separate
        token_validator.token_cache[hash1] = {"valid": True, "expires_at": 9999999999}
        token_validator.token_cache[hash2] = {"valid": False, "expires_at": 9999999999}
        
        assert len(token_validator.token_cache) == 2
        assert token_validator.token_cache[hash1]["valid"] != token_validator.token_cache[hash2]["valid"]
        
    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self, token_validator):
        """Test concurrent token validation doesn't cause race conditions"""
        import asyncio
        
        token = "dGVzdC10b2tlbi0xMjM0NTY3ODkw"
        
        # Simulate concurrent validations
        tasks = [
            token_validator.validate_token(token) 
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        assert all(result == results[0] for result in results)
        
        # Should have only one cache entry
        token_hash = token_validator.hash_token(token)
        assert token_hash in token_validator.token_cache
        
    def test_token_format_edge_cases(self, token_validator):
        """Test token format validation edge cases"""
        edge_cases = [
            ("", False),  # empty string
            (None, False),  # None
            ("a" * 20, True),  # exactly 20 chars (minimum)
            ("a" * 100, True),  # exactly 100 chars (maximum)
            ("a" * 19, False),  # one less than minimum
            ("a" * 101, False),  # one more than maximum
            ("valid-token-123_ABC", True),  # valid characters
            ("invalid token space", False),  # contains space
            ("valid_token-123", True),  # underscore and dash
            ("UPPERCASE_TOKEN123", True),  # uppercase
            ("lowercase_token123", True),  # lowercase
            ("MixedCase_Token123", True),  # mixed case
        ]
        
        for token, expected in edge_cases:
            result = token_validator.validate_token_format(token)
            assert result == expected, f"Token '{token}' validation failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])