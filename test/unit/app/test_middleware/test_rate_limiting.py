"""
Unit tests for rate limiting middleware (app/middleware/rate_limiting.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

from app.middleware.rate_limiting import (
    RateLimitingMiddleware,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimitType,
    RateLimitInfo,
    get_client_identifier
)


class TestInMemoryRateLimiter:
    """Test in-memory rate limiter implementation"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter proper initialization"""
        limiter = InMemoryRateLimiter()
        
        assert limiter.requests == {}
        assert limiter.cleanup_interval == 300  # 5 minutes
        assert limiter.max_entries == 10000
    
    def test_rate_limit_within_window(self):
        """Test rate limiting within time window"""
        limiter = InMemoryRateLimiter()
        client_id = "test_client"
        limit = 5
        window = 60  # 1 minute
        
        # Make requests within limit
        for i in range(limit):
            result = limiter.is_allowed(client_id, limit, window)
            assert result.allowed == True
            assert result.remaining == limit - i - 1
        
        # Next request should be denied
        result = limiter.is_allowed(client_id, limit, window)
        assert result.allowed == False
        assert result.remaining == 0
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset after expiry"""
        limiter = InMemoryRateLimiter()
        client_id = "test_client"
        limit = 2
        window = 1  # 1 second
        
        # Exhaust limit
        limiter.is_allowed(client_id, limit, window)
        limiter.is_allowed(client_id, limit, window)
        
        result = limiter.is_allowed(client_id, limit, window)
        assert result.allowed == False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        result = limiter.is_allowed(client_id, limit, window)
        assert result.allowed == True
    
    def test_rate_limit_different_clients(self):
        """Test rate limiting for different clients"""
        limiter = InMemoryRateLimiter()
        limit = 3
        window = 60
        
        # Client 1 exhausts limit
        for i in range(limit):
            result = limiter.is_allowed("client_1", limit, window)
            assert result.allowed == True
        
        result = limiter.is_allowed("client_1", limit, window)
        assert result.allowed == False
        
        # Client 2 should still be allowed
        result = limiter.is_allowed("client_2", limit, window)
        assert result.allowed == True
    
    def test_rate_limiter_cleanup(self):
        """Test automatic cleanup of old entries"""
        limiter = InMemoryRateLimiter()
        
        # Add old entries
        old_time = time.time() - 400  # 400 seconds ago
        limiter.requests["old_client"] = {
            "requests": [old_time],
            "last_request": old_time
        }
        
        # Add recent entry
        limiter.is_allowed("new_client", 5, 60)
        
        # Trigger cleanup
        limiter._cleanup_old_entries()
        
        assert "old_client" not in limiter.requests
        assert "new_client" in limiter.requests
    
    def test_rate_limiter_max_entries_protection(self):
        """Test protection against memory exhaustion"""
        limiter = InMemoryRateLimiter()
        limiter.max_entries = 5  # Small limit for testing
        
        # Add entries up to limit
        for i in range(5):
            limiter.is_allowed(f"client_{i}", 10, 60)
        
        # Adding more should trigger cleanup
        limiter.is_allowed("overflow_client", 10, 60)
        
        # Should still have entries but not more than max + some buffer
        assert len(limiter.requests) <= limiter.max_entries + 1


class TestRedisRateLimiter:
    """Test Redis-based rate limiter"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.incr.return_value = 1
        redis_mock.expire.return_value = True
        return redis_mock
    
    @pytest.mark.asyncio
    async def test_redis_rate_limiter_allowed(self, mock_redis):
        """Test Redis rate limiter allows requests within limit"""
        limiter = RedisRateLimiter(mock_redis)
        mock_redis.get.return_value = "2"  # Current count
        
        result = await limiter.is_allowed_async("test_client", 5, 60)
        
        assert result.allowed == True
        assert result.remaining == 3
        mock_redis.incr.assert_called()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limiter_denied(self, mock_redis):
        """Test Redis rate limiter denies requests over limit"""
        limiter = RedisRateLimiter(mock_redis)
        mock_redis.get.return_value = "5"  # At limit
        
        result = await limiter.is_allowed_async("test_client", 5, 60)
        
        assert result.allowed == False
        assert result.remaining == 0
        mock_redis.incr.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limiter_first_request(self, mock_redis):
        """Test Redis rate limiter first request for client"""
        limiter = RedisRateLimiter(mock_redis)
        mock_redis.get.return_value = None  # No existing entry
        mock_redis.incr.return_value = 1
        
        result = await limiter.is_allowed_async("new_client", 5, 60)
        
        assert result.allowed == True
        assert result.remaining == 4
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limiter_connection_error(self, mock_redis):
        """Test Redis rate limiter handles connection errors gracefully"""
        limiter = RedisRateLimiter(mock_redis)
        mock_redis.get.side_effect = Exception("Redis connection error")
        
        # Should fall back to allowing request
        result = await limiter.is_allowed_async("test_client", 5, 60)
        
        assert result.allowed == True  # Fail open


class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""
    
    def test_middleware_initialization(self):
        """Test middleware proper initialization"""
        app = Mock()
        middleware = RateLimitingMiddleware(
            app,
            default_limit=100,
            default_window=60,
            redis_client=None
        )
        
        assert middleware.app == app
        assert middleware.default_limit == 100
        assert middleware.default_window == 60
        assert isinstance(middleware.limiter, InMemoryRateLimiter)
    
    def test_middleware_initialization_with_redis(self):
        """Test middleware initialization with Redis"""
        app = Mock()
        redis_client = Mock()
        
        middleware = RateLimitingMiddleware(
            app,
            default_limit=100,
            default_window=60,
            redis_client=redis_client
        )
        
        assert isinstance(middleware.limiter, RedisRateLimiter)
    
    @pytest.mark.asyncio
    async def test_middleware_allowed_request(self, mock_redis):
        """Test middleware allows requests within limit"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=5, default_window=60)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        response = await middleware(request, call_next)
        
        call_next.assert_called_once_with(request)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_denied_request(self):
        """Test middleware denies requests over limit"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=1, default_window=60)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        call_next = AsyncMock()
        
        # First request should be allowed
        await middleware(request, call_next)
        
        # Second request should be denied
        response = await middleware(request, call_next)
        
        assert response.status_code == 429
        assert "rate limit exceeded" in response.body.decode().lower()
    
    @pytest.mark.asyncio
    async def test_middleware_different_rate_limits(self):
        """Test middleware applies different rate limits per endpoint"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=10, default_window=60)
        
        # Override rate limits for specific endpoints
        middleware.endpoint_limits = {
            "/api/auth/login": (3, 60),  # 3 requests per minute
            "/api/admin/*": (100, 60)    # 100 requests per minute for admin
        }
        
        # Test login endpoint with stricter limit
        request = Mock(spec=Request)
        request.url.path = "/api/auth/login"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        # Should use the stricter limit
        for i in range(3):
            response = await middleware(request, call_next)
            assert response.status_code == 200
        
        # Fourth request should be denied
        response = await middleware(request, call_next)
        assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_middleware_bypassed_endpoints(self):
        """Test middleware bypasses certain endpoints"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=1, default_window=60)
        
        # Configure bypassed endpoints
        middleware.bypassed_endpoints = ["/health", "/metrics"]
        
        request = Mock(spec=Request)
        request.url.path = "/health"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "healthy"}))
        
        # Multiple requests should all be allowed
        for i in range(5):
            response = await middleware(request, call_next)
            assert response.status_code == 200
            call_next.assert_called()
    
    @pytest.mark.asyncio
    async def test_middleware_headers_in_response(self):
        """Test middleware adds rate limit headers to response"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=5, default_window=60)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        original_response = JSONResponse({"status": "ok"})
        call_next = AsyncMock(return_value=original_response)
        
        response = await middleware(request, call_next)
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestClientIdentification:
    """Test client identification for rate limiting"""
    
    def test_get_client_identifier_ip(self):
        """Test client identification by IP address"""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        client_id = get_client_identifier(request)
        
        assert client_id == "ip:192.168.1.100"
    
    def test_get_client_identifier_api_key(self):
        """Test client identification by API key"""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {"X-API-Key": "secret_api_key_123"}
        
        client_id = get_client_identifier(request)
        
        assert client_id == "key:secret_api_key_123"
    
    def test_get_client_identifier_user_agent(self):
        """Test client identification includes user agent"""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {"User-Agent": "TestClient/1.0"}
        
        client_id = get_client_identifier(request, include_user_agent=True)
        
        assert "TestClient/1.0" in client_id
    
    def test_get_client_identifier_forwarded_ip(self):
        """Test client identification with forwarded IP"""
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}
        
        client_id = get_client_identifier(request)
        
        assert client_id == "ip:203.0.113.195"  # Should use first IP in chain


class TestRateLimitTypes:
    """Test different rate limit types and scenarios"""
    
    @pytest.mark.asyncio
    async def test_per_ip_rate_limiting(self):
        """Test per-IP rate limiting"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=2, default_window=60)
        
        # Two different IPs should have separate limits
        request1 = Mock(spec=Request)
        request1.url.path = "/api/test"
        request1.client.host = "192.168.1.1"
        request1.headers = {}
        
        request2 = Mock(spec=Request)
        request2.url.path = "/api/test"
        request2.client.host = "192.168.1.2"
        request2.headers = {}
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        # Both clients should be able to make their full quota
        for i in range(2):
            response1 = await middleware(request1, call_next)
            response2 = await middleware(request2, call_next)
            assert response1.status_code == 200
            assert response2.status_code == 200
        
        # Third request from each should be denied
        response1 = await middleware(request1, call_next)
        response2 = await middleware(request2, call_next)
        assert response1.status_code == 429
        assert response2.status_code == 429
    
    @pytest.mark.asyncio
    async def test_authenticated_user_rate_limiting(self):
        """Test rate limiting for authenticated users"""
        app = Mock()
        middleware = RateLimitingMiddleware(app, default_limit=3, default_window=60)
        
        # Authenticated user should have higher limits
        middleware.authenticated_limit = 10
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {"Authorization": "Bearer valid_token"}
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        # Should be able to make more requests than default limit
        for i in range(5):
            response = await middleware(request, call_next)
            assert response.status_code == 200


@pytest.mark.parametrize("limit,window,requests,should_pass", [
    (5, 60, 3, True),   # Within limit
    (5, 60, 5, True),   # At limit
    (5, 60, 6, False),  # Over limit
    (1, 60, 2, False),  # Small limit exceeded
])
def test_rate_limiting_scenarios(limit, window, requests, should_pass):
    """Test various rate limiting scenarios"""
    limiter = InMemoryRateLimiter()
    client_id = "test_client"
    
    results = []
    for i in range(requests):
        result = limiter.is_allowed(client_id, limit, window)
        results.append(result.allowed)
    
    if should_pass:
        assert all(results), "All requests should be allowed"
    else:
        assert not results[-1], "Last request should be denied"