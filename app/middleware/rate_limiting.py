"""
Rate limiting middleware with Redis-backed and in-memory fallback
Implements complete identity resolution: user_id → API key → client IP
"""
import asyncio
import hashlib
import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union, Protocol, TYPE_CHECKING, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

REDIS_AVAILABLE = False
_redis_module = None

# Use redis.asyncio instead of deprecated aioredis (Python 3.11 compatibility)
try:
    from redis import asyncio as _redis_module
    REDIS_AVAILABLE = True
except Exception as e:
    # Broad exception catch to handle import errors, version incompatibilities, etc.
    _redis_module = None
    pass

if TYPE_CHECKING:
    Redis = Any  # Use Any type to avoid import resolution issues

from ..security.security_logger import SecurityEventType, security_logger
from ..utils.auth import get_admin_payload

logger = logging.getLogger(__name__)


class RateLimitStorage(Protocol):
    """Protocol for rate limit storage backends"""
    async def add_request(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Add a request and return (current_count, reset_time)"""
        ...
    
    async def get_request_count(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Get current request count and reset time"""
        ...
    
    async def cleanup_expired(self):
        """Clean up expired data"""
        ...
    
    async def close(self):
        """Close storage connection"""
        ...


class RedisRateLimitStorage:
    """Redis-backed rate limit storage with atomic operations"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[Any] = None
        self._connection_lock = asyncio.Lock()
        
    async def _get_redis_client(self) -> Any:
        """Get Redis client with lazy connection"""
        if not REDIS_AVAILABLE or _redis_module is None:
            raise RuntimeError("redis.asyncio is not available")
            
        if self.redis_client is None:
            async with self._connection_lock:
                if self.redis_client is None:
                    try:
                        self.redis_client = _redis_module.from_url(
                            self.redis_url,
                            decode_responses=True,
                            retry_on_timeout=True,
                            socket_connect_timeout=5,
                            socket_timeout=5,
                            health_check_interval=30
                        )
                        # Test connection
                        await self.redis_client.ping()
                        logger.info("Redis rate limiting storage connected")
                    except Exception as e:
                        logger.error(f"Failed to connect to Redis: {e}")
                        raise
        return self.redis_client
    
    async def add_request(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Add a request using Redis sliding window with atomic operations"""
        try:
            redis = await self._get_redis_client()
            now = time.time()
            window_start = now - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()
            
            # Remove expired entries from sorted set
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Add current request with score as timestamp
            pipe.zadd(key, {str(now): now})
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Set TTL to prevent memory leaks
            pipe.expire(key, window_seconds + 10)
            
            # Execute pipeline
            results = await pipe.execute()
            
            current_count = results[2]  # Result from zcard
            reset_time = now + window_seconds
            
            return current_count, reset_time
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to basic counting
            return 1, time.time() + window_seconds
    
    async def get_request_count(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Get current request count from Redis"""
        try:
            redis = await self._get_redis_client()
            now = time.time()
            window_start = now - window_seconds
            
            # Remove expired and count current
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            
            results = await pipe.execute()
            current_count = results[1]
            reset_time = now + window_seconds
            
            return current_count, reset_time
            
        except Exception as e:
            logger.error(f"Redis count error: {e}")
            return 0, time.time() + window_seconds
    
    async def cleanup_expired(self):
        """Redis handles TTL automatically, but we can clean old keys"""
        try:
            redis = await self._get_redis_client()
            now = time.time()
            
            # Find keys with rate limit pattern
            keys = await redis.keys("ratelimit:*")
            
            if keys:
                # Clean up keys with no recent activity (older than 1 hour)
                cutoff = now - 3600
                
                for key in keys:
                    try:
                        # Remove entries older than cutoff
                        await redis.zremrangebyscore(key, 0, cutoff)
                        
                        # Remove empty keys
                        count = await redis.zcard(key)
                        if count == 0:
                            await redis.delete(key)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup key {key}: {e}")
                        
        except Exception as e:
            logger.error(f"Redis cleanup error: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


class InMemoryRateLimitStorage:
    """In-memory rate limit storage with TTL support"""
    
    def __init__(self):
        self._data: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
        
    async def add_request(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Add a request and return (current_count, reset_time)"""
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean expired entries
            while self._data[key] and self._data[key][0] <= window_start:
                self._data[key].popleft()
            
            # Add current request
            self._data[key].append(now)
            
            # Calculate reset time (start of next window)
            reset_time = now + window_seconds
            
            return len(self._data[key]), reset_time
    
    async def get_request_count(self, key: str, window_seconds: int) -> Tuple[int, float]:
        """Get current request count and reset time"""
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean expired entries
            while self._data[key] and self._data[key][0] <= window_start:
                self._data[key].popleft()
            
            reset_time = now + window_seconds
            return len(self._data[key]), reset_time

    async def cleanup_expired(self):
        """Clean up expired data"""
        async with self._lock:
            now = time.time()
            keys_to_remove = []
            
            for key, timestamps in self._data.items():
                # Keep only last 1 hour of data
                cutoff = now - 3600
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                
                if not timestamps:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._data[key]
    
    async def close(self):
        """Close in-memory storage (no-op)"""
        pass


class RateLimitConfig:
    """Rate limiting configuration with prefix-based matching"""
    
    # Authentication endpoints (per IP) - exact match for security
    AUTH_ENDPOINTS = {
        "/api/admins/token": {"limit": 5, "window": 60, "methods": ["POST"]},  # 5 login attempts per minute
        "/api/admins/current/token": {"limit": 10, "window": 60, "methods": ["GET"]},  # 10 token requests per minute
    }
    
    # Critical mutation endpoints (per identity) - prefix match for coverage
    CRITICAL_ENDPOINTS = {
        "/api/admins": {"limit": 3, "window": 60, "methods": ["POST", "PUT", "DELETE", "PATCH"]},        # 3 admin operations per minute
        "/api/users": {"limit": 15, "window": 60, "methods": ["POST", "PUT", "DELETE", "PATCH"]},   # 15 user operations per minute
        "/api/nodes": {"limit": 10, "window": 60, "methods": ["POST", "PUT", "DELETE", "PATCH"]},   # 10 node operations per minute
        "/api/services": {"limit": 10, "window": 60, "methods": ["POST", "PUT", "DELETE", "PATCH"]}, # 10 service operations per minute
    }
    
    # Read-heavy endpoints (less restrictive)
    READ_ENDPOINTS = {
        "/api/users": {"limit": 100, "window": 60, "methods": ["GET"]},        # 100 reads per minute
        "/api/nodes": {"limit": 50, "window": 60, "methods": ["GET"]},         # 50 reads per minute
        "/api/services": {"limit": 50, "window": 60, "methods": ["GET"]},     # 50 reads per minute
        "/api/admins": {"limit": 30, "window": 60, "methods": ["GET"]},       # 30 admin reads per minute
    }
    
    # Global rate limits (per IP)
    GLOBAL_LIMITS = {
        "default": {"limit": 200, "window": 60},          # 200 requests per minute
        "burst": {"limit": 30, "window": 10},             # 30 requests per 10 seconds
    }


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with Redis backend and complete identity resolution
    Priority: user_id → API key → client IP
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.config = RateLimitConfig()
        
        # Initialize storage with Redis fallback
        self.storage = self._init_storage()
        
        # Set global storage for cleanup task
        global _global_storage
        _global_storage = self.storage
    
    def _init_storage(self) -> RateLimitStorage:
        """Initialize rate limit storage with Redis fallback to in-memory"""
        redis_url = os.getenv("REDIS_URL")
        
        # Only try Redis if both URL is provided AND redis.asyncio is available
        if redis_url and REDIS_AVAILABLE and _redis_module is not None:
            try:
                logger.info(f"Initializing Redis rate limiting with URL: {redis_url[:20]}...")
                return RedisRateLimitStorage(redis_url)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis storage, falling back to in-memory: {e}")
        else:
            if redis_url and not REDIS_AVAILABLE:
                logger.warning("REDIS_URL provided but redis.asyncio not available, using in-memory rate limiting")
            elif not redis_url:
                logger.info("No REDIS_URL provided, using in-memory rate limiting")
        
        logger.info("Using in-memory rate limiting storage")
        return InMemoryRateLimitStorage()
    
    async def _cleanup_task(self):
        """Background task to clean up expired rate limit data"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self.storage.cleanup_expired()
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with X-Forwarded-For support"""
        # Check X-Forwarded-For header (set by ProxyHeadersMiddleware)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client IP
        if request.client and hasattr(request.client, 'host') and request.client.host:
            return request.client.host
        
        return "unknown"
    
    def _get_identity(self, request: Request) -> Tuple[str, str]:
        """
        Get identity for rate limiting with complete resolution chain:
        1. user_id (from authenticated admin JWT token)
        2. API key (from X-API-Key header or query param)
        3. API token (from Authorization header as fallback)
        4. client IP
        
        Returns: (identity, identity_type)
        """
        # Priority 1: Try to get admin user_id from JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = get_admin_payload(token)
                if payload and "username" in payload:
                    return f"user:{payload['username']}", "user"
            except Exception:
                # Invalid JWT, continue to next method
                pass
        
        # Priority 2: Check for API key in headers
        api_key = request.headers.get("x-api-key")
        if not api_key:
            api_key = request.headers.get("api-key")
        if not api_key:
            # Check query parameters
            api_key = request.query_params.get("api_key")
        
        if api_key and len(api_key) >= 8:
            # Use hash of API key for privacy and uniqueness
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"apikey:{key_hash}", "api_key"
        
        # Priority 3: Fallback to Bearer token as API token (not JWT)
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if len(token) >= 8:
                # Use last 8 chars of token for privacy
                token_suffix = token[-8:] if len(token) >= 8 else token
                return f"token:{token_suffix}", "api_token"
        
        # Priority 4: Final fallback to IP
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}", "ip"
    
    def _get_rate_limit_key(self, request: Request, identity: str) -> Tuple[str, Dict]:
        """Get rate limit key and config for the request with prefix-based matching"""
        path = request.url.path
        method = request.method
        
        # Check auth endpoints first (IP-based for security)
        for endpoint, config in self.config.AUTH_ENDPOINTS.items():
            if path == endpoint or (path.startswith(endpoint + "/") and endpoint != "/"):
                if "methods" not in config or method in config["methods"]:
                    client_ip = self._get_client_ip(request)
                    return f"ratelimit:auth:{endpoint}:{client_ip}", config
        
        # Check critical mutation endpoints (identity-based)
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            for endpoint, config in self.config.CRITICAL_ENDPOINTS.items():
                if path.startswith(endpoint):
                    if "methods" not in config or method in config["methods"]:
                        return f"ratelimit:critical:{endpoint}:{identity}", config
        
        # Check read endpoints (less restrictive)
        if method == "GET":
            for endpoint, config in self.config.READ_ENDPOINTS.items():
                if path.startswith(endpoint):
                    if "methods" not in config or method in config["methods"]:
                        return f"ratelimit:read:{endpoint}:{identity}", config
        
        # Global rate limit (IP-based)
        client_ip = self._get_client_ip(request)
        return f"ratelimit:global:{client_ip}", self.config.GLOBAL_LIMITS["default"]
    
    async def _check_rate_limit(self, key: str, config: Dict, request: Request) -> Optional[JSONResponse]:
        """Check rate limit and return 429 response if exceeded"""
        limit = config["limit"]
        window = config["window"]
        
        # Check current count
        current_count, reset_time = await self.storage.add_request(key, window)
        
        if current_count > limit:
            # Rate limit exceeded
            retry_after = int(reset_time - time.time())
            retry_after = max(1, retry_after)  # At least 1 second
            
            # Log security event
            client_ip = self._get_client_ip(request)
            security_logger.log_security_event(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                details={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "rate_limit_key": key,
                    "current_count": current_count,
                    "limit": limit,
                    "window_seconds": window,
                    "retry_after": retry_after
                },
                severity="WARNING",
                ip_address=client_ip
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window} seconds",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(max(0, limit - current_count)),
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )
        
        return None
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method with enhanced security"""
        # Skip rate limiting for health checks and static files only
        path = request.url.path
        if path in ["/health", "/api/health", "/docs", "/redoc", "/openapi.json"] or path.startswith("/static"):
            return await call_next(request)
        
        try:
            # Get identity with full resolution chain
            identity, identity_type = self._get_identity(request)
            
            # Get rate limit configuration with prefix matching
            rate_limit_key, config = self._get_rate_limit_key(request, identity)
            
            # Check primary rate limit
            rate_limit_response = await self._check_rate_limit(rate_limit_key, config, request)
            if rate_limit_response:
                return rate_limit_response
            
            # Always check burst protection (except for burst keys)
            if not rate_limit_key.endswith(":burst"):
                client_ip = self._get_client_ip(request)
                burst_key = f"ratelimit:burst:{client_ip}"
                burst_response = await self._check_rate_limit(
                    burst_key, 
                    self.config.GLOBAL_LIMITS["burst"], 
                    request
                )
                if burst_response:
                    return burst_response
            
            # Continue to next middleware/handler
            response = await call_next(request)
            
            # Add comprehensive rate limit headers
            try:
                current_count, reset_time = await self.storage.get_request_count(
                    rate_limit_key, config["window"]
                )
                
                response.headers["X-RateLimit-Limit"] = str(config["limit"])
                response.headers["X-RateLimit-Remaining"] = str(max(0, config["limit"] - current_count))
                response.headers["X-RateLimit-Reset"] = str(int(reset_time))
                response.headers["X-RateLimit-Identity"] = identity_type
                response.headers["X-RateLimit-Window"] = str(config["window"])
                
                # Add burst limit info if different from main limit
                if not rate_limit_key.endswith(":burst"):
                    burst_count, _ = await self.storage.get_request_count(
                        f"ratelimit:burst:{self._get_client_ip(request)}", 
                        self.config.GLOBAL_LIMITS["burst"]["window"]
                    )
                    response.headers["X-RateLimit-Burst-Remaining"] = str(
                        max(0, self.config.GLOBAL_LIMITS["burst"]["limit"] - burst_count)
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to add rate limit headers: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Don't block requests on middleware errors, but log them
            return await call_next(request)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on shutdown"""
        if hasattr(self.storage, 'close'):
            try:
                await self.storage.close()
            except Exception as e:
                logger.warning(f"Error closing rate limit storage: {e}")


# Global storage instance for cleanup task
_global_storage = None

async def start_cleanup_task():
    """Start cleanup task using global storage instance"""
    global _global_storage
    if _global_storage:
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await _global_storage.cleanup_expired()
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")


__all__ = ["RateLimitingMiddleware", "RateLimitConfig", "start_cleanup_task"]