"""
Authentication middleware for grpclib server
Since grpclib doesn't support interceptors like standard grpc library,
we implement authentication at the service method level.
"""
import asyncio
import hashlib
import logging
import functools
from typing import Optional, Callable, Any, TypeVar, ParamSpec, Awaitable
from datetime import datetime, timezone

from grpclib import GRPCError, Status
from grpclib.server import Stream

logger = logging.getLogger(__name__)


class NodeTokenValidator:
    """
    Validates node authentication tokens for gRPC requests.
    This is a lightweight version that doesn't depend on the full panel database.
    """
    
    def __init__(self):
        # In production, these should come from environment variables or config
        self.token_cache = {}  # Simple in-memory cache for validated tokens
        self.cache_ttl = 300  # 5 minutes cache TTL
        
    def extract_token_from_metadata(self, metadata) -> Optional[str]:
        """Extract Bearer token from gRPC metadata"""
        if not metadata:
            return None
            
        for key, value in metadata:
            if key.lower() == 'authorization':
                if value.startswith('Bearer '):
                    return value[7:]  # Remove 'Bearer ' prefix
                elif value.startswith('bearer '):
                    return value[7:]  # Handle lowercase 'bearer'
                else:
                    # Direct token without Bearer prefix
                    return value
        return None
    
    def validate_token_format(self, token: str) -> bool:
        """Basic token format validation"""
        if not token:
            return False
        
        # Token should be base64-like string of reasonable length
        if len(token) < 20 or len(token) > 100:
            return False
            
        # Basic character validation (base64 URL-safe characters)
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        if not all(c in allowed_chars for c in token):
            return False
            
        return True
    
    def hash_token(self, token: str) -> str:
        """Create hash of token for caching/logging without exposing actual token"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]  # Short hash for logging
    
    async def validate_token(self, token: str, node_id: Optional[int] = None) -> bool:
        """
        Validate authentication token.
        
        Args:
            token: Authentication token
            node_id: Optional node ID for additional validation
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.validate_token_format(token):
            logger.warning(f"Invalid token format: {self.hash_token(token)}")
            return False
        
        token_hash = self.hash_token(token)
        
        # Check cache first
        cache_key = f"{token_hash}:{node_id}" if node_id else token_hash
        if cache_key in self.token_cache:
            cache_entry = self.token_cache[cache_key]
            # Check if cache entry is still valid
            if datetime.now(timezone.utc).timestamp() < cache_entry['expires_at']:
                logger.debug(f"Token validated from cache: {token_hash}")
                return cache_entry['valid']
            else:
                # Remove expired cache entry
                del self.token_cache[cache_key]
        
        # TODO: In a real implementation, you would validate against the database
        # For now, we'll implement a basic validation that accepts properly formatted tokens
        # In production, this should connect to the panel database and validate using NodeAuthManager
        
        # Basic validation - accept any properly formatted token for now
        # This is a security risk and should be replaced with proper database validation
        is_valid = self.validate_token_format(token)
        
        # Cache the result
        self.token_cache[cache_key] = {
            'valid': is_valid,
            'expires_at': datetime.now(timezone.utc).timestamp() + self.cache_ttl
        }
        
        if is_valid:
            logger.info(f"Token validated successfully: {token_hash}")
        else:
            logger.warning(f"Token validation failed: {token_hash}")
            
        return is_valid
    
    def clear_cache(self):
        """Clear token cache"""
        self.token_cache.clear()
        logger.info("Token cache cleared")


# Global token validator instance
_token_validator = NodeTokenValidator()

# Type variables for decorator typing
P = ParamSpec('P')
T = TypeVar('T')


def require_auth(allow_health_check: bool = True):
    """
    Decorator for gRPC service methods that require authentication.
    
    Args:
        allow_health_check: Whether to allow health check methods without auth
    """
    def decorator(method):
        @functools.wraps(method)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get method name for logging
            method_name = method.__name__
            
            # Extract self and stream from args for proper handling
            if len(args) < 2:
                raise GRPCError(Status.INTERNAL, "Invalid method signature")
            self, stream = args[0], args[1]
            
            # Allow health check methods without authentication if configured
            if allow_health_check and method_name in ('Check', 'Watch', 'HealthCheck'):
                logger.debug(f"Allowing health check method without auth: {method_name}")
                return await method(*args, **kwargs)
            
            # Extract metadata from stream
            metadata = getattr(stream, 'metadata', None)
            if not metadata:
                logger.warning(f"No metadata in request for method: {method_name}")
                raise GRPCError(
                    Status.UNAUTHENTICATED,
                    "Authentication required: missing metadata"
                )
            
            # Extract token
            token = _token_validator.extract_token_from_metadata(metadata)
            if not token:
                logger.warning(f"No authentication token in request for method: {method_name}")
                raise GRPCError(
                    Status.UNAUTHENTICATED,
                    "Authentication required: missing or invalid authorization header"
                )
            
            # Validate token
            try:
                is_valid = await _token_validator.validate_token(token)
                if not is_valid:
                    logger.warning(f"Invalid token for method: {method_name}")
                    raise GRPCError(
                        Status.UNAUTHENTICATED,
                        "Authentication failed: invalid token"
                    )
            except Exception as e:
                logger.error(f"Token validation error for method {method_name}: {e}")
                raise GRPCError(
                    Status.INTERNAL,
                    "Authentication error: token validation failed"
                )
            
            # Token is valid, proceed with the method
            logger.debug(f"Authentication successful for method: {method_name}")
            return await method(*args, **kwargs)
        
        return wrapper
    return decorator


def exception_handler(method):
    """
    Decorator to handle exceptions in gRPC service methods and prevent thread crashes.
    Maps Python exceptions to appropriate gRPC status codes.
    """
    @functools.wraps(method)
    async def wrapper(*args, **kwargs):
        method_name = method.__name__
        
        try:
            return await method(*args, **kwargs)
        except GRPCError:
            # Re-raise gRPC errors as-is
            raise
        except asyncio.CancelledError:
            # Re-raise cancellation errors
            logger.info(f"Method {method_name} was cancelled")
            raise
        except PermissionError as e:
            logger.error(f"Permission error in {method_name}: {e}")
            raise GRPCError(
                Status.PERMISSION_DENIED,
                f"Permission denied: {str(e)}"
            )
        except FileNotFoundError as e:
            logger.error(f"Resource not found in {method_name}: {e}")
            raise GRPCError(
                Status.NOT_FOUND,
                f"Resource not found: {str(e)}"
            )
        except ValueError as e:
            logger.error(f"Invalid argument in {method_name}: {e}")
            raise GRPCError(
                Status.INVALID_ARGUMENT,
                f"Invalid argument: {str(e)}"
            )
        except TimeoutError as e:
            logger.error(f"Timeout in {method_name}: {e}")
            raise GRPCError(
                Status.DEADLINE_EXCEEDED,
                f"Operation timeout: {str(e)}"
            )
        except ConnectionError as e:
            logger.error(f"Connection error in {method_name}: {e}")
            raise GRPCError(
                Status.UNAVAILABLE,
                f"Service unavailable: {str(e)}"
            )
        except Exception as e:
            # Catch all other exceptions to prevent thread crashes
            logger.error(f"Unexpected error in {method_name}: {e}", exc_info=True)
            raise GRPCError(
                Status.INTERNAL,
                f"Internal server error in {method_name}"
            )
    
    return wrapper


def secure_method(allow_health_check: bool = True):
    """
    Combined decorator that applies both authentication and exception handling.
    This is the recommended decorator for all gRPC service methods.
    """
    def decorator(method):
        # Apply exception handler first, then auth
        secured_method = require_auth(allow_health_check)(method)
        return exception_handler(secured_method)
    return decorator


def get_token_validator() -> NodeTokenValidator:
    """Get the global token validator instance"""
    return _token_validator


def set_token_validator(validator: NodeTokenValidator):
    """Set a custom token validator (useful for testing)"""
    global _token_validator
    _token_validator = validator