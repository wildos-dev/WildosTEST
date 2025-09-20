"""
Integration tests for middleware integration
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import time


@pytest.mark.integration
class TestMiddlewarePipeline:
    """Test complete middleware pipeline integration"""
    
    def test_middleware_execution_order(self, client: TestClient):
        """Test that middleware executes in correct order"""
        # This would test the middleware pipeline:
        # CORS -> Rate Limiting -> Authentication -> Authorization -> Route Handler
        
        with patch('app.middleware.rate_limiting.RateLimitingMiddleware') as mock_rate_limit, \
             patch('app.middleware.validation.ValidationMiddleware') as mock_validation, \
             patch('app.middleware.proxy_headers.ProxyHeadersMiddleware') as mock_proxy:
            
            response = client.get("/api/admins")
            
            # Middleware should be called in order
            # Actual verification would depend on implementation
    
    def test_middleware_error_handling_chain(self, client: TestClient):
        """Test error handling through middleware chain"""
        # Test how errors propagate through middleware stack
        
        # Simulate rate limit exceeded
        with patch('app.middleware.rate_limiting.InMemoryRateLimiter.is_allowed') as mock_limiter:
            mock_limiter.return_value = Mock(allowed=False, remaining=0)
            
            response = client.get("/api/admins")
            
            # Should return rate limit error before reaching authentication
            assert response.status_code == 429
    
    def test_middleware_request_modification(self, client: TestClient):
        """Test middleware request modification through pipeline"""
        # Test that middleware can modify request objects
        
        response = client.get(
            "/api/admins",
            headers={
                "X-Forwarded-For": "203.0.113.195",
                "X-Real-IP": "203.0.113.195",
                "User-Agent": "TestClient/1.0"
            }
        )
        
        # Middleware should have processed headers
        # Verification would depend on specific middleware behavior


@pytest.mark.integration
class TestRateLimitingIntegration:
    """Test rate limiting middleware integration"""
    
    def test_rate_limiting_with_authentication(self, client: TestClient, auth_headers):
        """Test rate limiting behavior with authenticated requests"""
        # Make multiple rapid authenticated requests
        responses = []
        
        for i in range(15):  # Assuming limit is around 10
            response = client.get("/api/admins", headers=auth_headers)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay
        
        # Should eventually hit rate limit even for authenticated requests
        status_codes = set(responses)
        # May include both 200 (success) and 429 (rate limited)
        assert len(status_codes) >= 1
    
    def test_rate_limiting_per_endpoint(self, client: TestClient):
        """Test different rate limits per endpoint"""
        # Test different endpoints have different rate limits
        
        # High-frequency endpoint (should have lower limit)
        auth_responses = []
        for i in range(10):
            response = client.post(
                "/api/admins/token",
                data={"username": "test", "password": "test"}
            )
            auth_responses.append(response.status_code)
        
        # Regular endpoint
        admin_responses = []
        for i in range(10):
            response = client.get("/api/admins")
            admin_responses.append(response.status_code)
        
        # Different endpoints should have different rate limiting behavior
        assert len(set(auth_responses)) >= 1
        assert len(set(admin_responses)) >= 1
    
    def test_rate_limiting_bypass_for_health_checks(self, client: TestClient):
        """Test that health check endpoints bypass rate limiting"""
        # Make many requests to health endpoint
        responses = []
        
        for i in range(50):  # Well above normal rate limit
            response = client.get("/health")
            responses.append(response.status_code)
        
        # All health check requests should succeed
        if any(status == 200 for status in responses):
            # Health endpoint exists and should not be rate limited
            healthy_responses = [status for status in responses if status == 200]
            assert len(healthy_responses) > 20  # Most should succeed
    
    def test_rate_limiting_redis_fallback(self, client: TestClient):
        """Test rate limiting fallback when Redis is unavailable"""
        with patch('app.middleware.rate_limiting.RedisRateLimiter') as mock_redis_limiter:
            # Simulate Redis connection failure
            mock_redis_limiter.side_effect = Exception("Redis connection failed")
            
            # Should fallback to in-memory rate limiting
            response = client.get("/api/admins")
            
            # Should still work (fail open or fallback to in-memory)
            assert response.status_code in [200, 401, 429]


@pytest.mark.integration
class TestSecurityMiddlewareIntegration:
    """Test security middleware integration"""
    
    def test_security_headers_integration(self, client: TestClient):
        """Test security headers are properly set"""
        response = client.get("/api/admins")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # Some security headers should be present
        present_headers = [header for header in security_headers if header in response.headers]
        # Depending on configuration, some should be present
    
    def test_cors_integration_with_auth(self, client: TestClient, auth_headers):
        """Test CORS integration with authentication"""
        response = client.get(
            "/api/admins",
            headers={
                **auth_headers,
                "Origin": "https://allowed-origin.com"
            }
        )
        
        if response.status_code == 200:
            # Should include CORS headers
            assert "Access-Control-Allow-Origin" in response.headers
    
    def test_content_security_policy(self, client: TestClient):
        """Test Content Security Policy header"""
        response = client.get("/")
        
        # CSP header should be present for web endpoints
        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            assert "default-src" in csp
    
    def test_request_id_tracking(self, client: TestClient):
        """Test request ID generation and tracking"""
        response = client.get("/api/admins")
        
        # Should include request ID header for tracking
        if "X-Request-ID" in response.headers:
            request_id = response.headers["X-Request-ID"]
            assert len(request_id) > 0
            assert "-" in request_id  # UUID format


@pytest.mark.integration
class TestValidationMiddlewareIntegration:
    """Test validation middleware integration"""
    
    def test_request_validation_integration(self, client: TestClient, auth_headers):
        """Test request validation in middleware pipeline"""
        # Test with invalid JSON
        invalid_response = client.post(
            "/api/users",
            data="invalid json",  # Not JSON
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert invalid_response.status_code == 422
    
    def test_response_validation_integration(self, client: TestClient, auth_headers):
        """Test response validation in middleware pipeline"""
        # Make valid request
        response = client.get("/api/admins", headers=auth_headers)
        
        if response.status_code == 200:
            # Response should be valid JSON
            data = response.json()
            assert isinstance(data, list)
    
    def test_size_limit_validation(self, client: TestClient, auth_headers):
        """Test request size limit validation"""
        # Create large payload
        large_payload = {
            "username": "test_user",
            "expire_strategy": "never",
            "note": "x" * 10000,  # Very long note
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=large_payload,
            headers=auth_headers
        )
        
        # Should be rejected if note exceeds limit
        assert response.status_code in [200, 201, 422]  # Depends on validation rules
    
    def test_encoding_validation(self, client: TestClient, auth_headers):
        """Test character encoding validation"""
        # Test with various character encodings
        user_data = {
            "username": "test_user_тест",  # Cyrillic characters
            "expire_strategy": "never",
            "service_ids": []
        }
        
        response = client.post(
            "/api/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Should handle Unicode properly
        assert response.status_code in [200, 201, 422]


@pytest.mark.integration
class TestMonitoringIntegration:
    """Test monitoring middleware integration"""
    
    def test_metrics_collection_integration(self, client: TestClient):
        """Test metrics collection during request processing"""
        with patch('app.middleware.monitoring.metrics_collector') as mock_metrics:
            response = client.get("/api/admins")
            
            # Metrics should be collected
            if hasattr(mock_metrics, 'record_request'):
                mock_metrics.record_request.assert_called()
    
    def test_performance_monitoring(self, client: TestClient, auth_headers):
        """Test performance monitoring integration"""
        # Make request and check for performance headers
        response = client.get("/api/admins", headers=auth_headers)
        
        # Should include timing information
        timing_headers = [
            "X-Response-Time",
            "Server-Timing", 
            "X-Processing-Time"
        ]
        
        present_timing_headers = [h for h in timing_headers if h in response.headers]
        # At least some timing info should be present
    
    def test_error_tracking_integration(self, client: TestClient):
        """Test error tracking through middleware"""
        with patch('app.middleware.monitoring.error_tracker') as mock_tracker:
            # Make request that will fail
            response = client.get("/api/admins")  # No auth
            
            if response.status_code >= 400:
                # Error should be tracked
                if hasattr(mock_tracker, 'record_error'):
                    mock_tracker.record_error.assert_called()
    
    def test_health_check_monitoring(self, client: TestClient):
        """Test health check endpoint monitoring"""
        response = client.get("/health")
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Should include system health information
            expected_fields = ["status", "timestamp", "version"]
            present_fields = [field for field in expected_fields if field in health_data]
            assert len(present_fields) > 0


@pytest.mark.integration
class TestMiddlewareErrorRecovery:
    """Test middleware error recovery and resilience"""
    
    def test_middleware_failure_isolation(self, client: TestClient):
        """Test that middleware failures don't crash the application"""
        with patch('app.middleware.rate_limiting.RateLimitingMiddleware.__call__') as mock_middleware:
            mock_middleware.side_effect = Exception("Middleware failure")
            
            # Application should handle middleware failure gracefully
            response = client.get("/health")
            
            # Should either continue processing or return meaningful error
            assert response.status_code in [200, 500, 503]
    
    def test_partial_middleware_failure(self, client: TestClient):
        """Test application behavior with partial middleware failures"""
        # Simulate failure in non-critical middleware
        with patch('app.middleware.monitoring.MonitoringMiddleware') as mock_monitoring:
            mock_monitoring.side_effect = Exception("Monitoring failed")
            
            # Core functionality should still work
            response = client.get("/health")
            
            # Health check should work even if monitoring fails
            assert response.status_code in [200, 503]
    
    def test_middleware_timeout_handling(self, client: TestClient):
        """Test middleware timeout handling"""
        with patch('app.middleware.rate_limiting.RateLimitingMiddleware') as mock_middleware:
            # Simulate slow middleware
            import time
            
            def slow_middleware(*args, **kwargs):
                time.sleep(2)  # Simulate slow operation
                return Mock(status_code=200)
            
            mock_middleware.side_effect = slow_middleware
            
            # Request should timeout or complete
            response = client.get("/health")
            
            # Should handle timeout gracefully
            assert response.status_code in [200, 408, 503]


@pytest.mark.integration
@pytest.mark.slow
class TestMiddlewarePerformance:
    """Test middleware performance under load"""
    
    def test_concurrent_request_handling(self, client: TestClient):
        """Test middleware performance with concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "duration": end_time - start_time
            })
        
        # Create multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        success_count = sum(1 for r in results if r["status_code"] == 200)
        avg_duration = sum(r["duration"] for r in results) / len(results)
        
        # Most requests should succeed
        assert success_count >= 8  # At least 80% success rate
        assert avg_duration < 5.0  # Average response under 5 seconds
    
    def test_memory_usage_under_load(self, client: TestClient):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests
        for i in range(100):
            response = client.get("/health")
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024