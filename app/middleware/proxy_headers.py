"""
Proxy headers middleware for handling X-Forwarded-For and other proxy headers
Ensures proper client IP resolution behind reverse proxies
"""
import logging
import ipaddress
from typing import List, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to process proxy headers (X-Forwarded-For, X-Real-IP, etc.)
    and set the real client IP for rate limiting and security logging
    """
    
    def __init__(self, app, trusted_proxies: Optional[List[str]] = None):
        """
        Initialize proxy headers middleware
        
        Args:
            app: FastAPI application instance
            trusted_proxies: List of trusted proxy IP addresses/networks
                           If None, all proxies are trusted (default for internal deployments)
        """
        super().__init__(app)
        self.trusted_proxies = trusted_proxies or []
        self.trusted_networks = []
        
        # Parse trusted proxy networks
        for proxy in self.trusted_proxies:
            try:
                self.trusted_networks.append(ipaddress.ip_network(proxy, strict=False))
            except ValueError as e:
                logger.warning(f"Invalid trusted proxy network '{proxy}': {e}")
    
    def _is_trusted_proxy(self, ip: str) -> bool:
        """Check if IP is a trusted proxy"""
        if not self.trusted_networks:
            # If no trusted proxies specified, trust all (internal deployment)
            return True
        
        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in network for network in self.trusted_networks)
        except ValueError:
            return False
    
    def _extract_real_ip(self, request: Request) -> Optional[str]:
        """
        Extract real client IP from proxy headers
        Priority: X-Forwarded-For > X-Real-IP > X-Forwarded > direct connection
        """
        immediate_client = getattr(request.client, 'host', None) if request.client else None
        
        # If immediate client is not a trusted proxy, use it directly
        if immediate_client and not self._is_trusted_proxy(immediate_client):
            return immediate_client
        
        # Check X-Forwarded-For header (standard)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
            ips = [ip.strip() for ip in forwarded_for.split(',')]
            
            # Find the first non-trusted IP (the real client)
            for ip in ips:
                if ip and not self._is_trusted_proxy(ip):
                    try:
                        # Validate IP format
                        ipaddress.ip_address(ip)
                        return ip
                    except ValueError:
                        continue
        
        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get('x-real-ip')
        if real_ip and not self._is_trusted_proxy(real_ip):
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except ValueError:
                pass
        
        # Check X-Forwarded header (less common)
        forwarded = request.headers.get('x-forwarded')
        if forwarded:
            # Extract IP from "for=ip" format
            for part in forwarded.split(';'):
                if part.strip().startswith('for='):
                    ip = part.split('=')[1].strip().strip('"')
                    if ip and not self._is_trusted_proxy(ip):
                        try:
                            ipaddress.ip_address(ip)
                            return ip
                        except ValueError:
                            continue
        
        # Fallback to immediate client
        return immediate_client
    
    def _sanitize_headers(self, request: Request) -> dict:
        """Extract and sanitize important proxy headers for logging"""
        headers = {}
        
        important_headers = [
            'x-forwarded-for',
            'x-real-ip', 
            'x-forwarded',
            'x-forwarded-proto',
            'x-forwarded-host',
            'x-forwarded-port'
        ]
        
        for header in important_headers:
            value = request.headers.get(header)
            if value:
                # Sanitize header value (truncate if too long)
                headers[header] = value[:255] if len(value) > 255 else value
        
        return headers
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method"""
        try:
            # Extract real client IP
            real_ip = self._extract_real_ip(request)
            
            # Store original client info for logging
            original_client = getattr(request.client, 'host', None) if request.client else None
            
            # Set the real IP in request state for other middleware
            if real_ip:
                # Store in request state for easy access by other middleware
                request.state.real_client_ip = real_ip
                request.state.original_client_ip = original_client
                request.state.proxy_headers = self._sanitize_headers(request)
            
            # Log proxy information for debugging (only in debug mode)
            if logger.isEnabledFor(logging.DEBUG):
                proxy_info = {
                    'real_ip': real_ip,
                    'original_ip': original_client,
                    'headers': self._sanitize_headers(request)
                }
                logger.debug(f"Proxy headers processed: {proxy_info}")
        
        except Exception as e:
            # Don't block requests on proxy header processing errors
            logger.warning(f"Error processing proxy headers: {e}")
            # Set fallback values in case of error
            if not hasattr(request.state, 'real_client_ip'):
                request.state.real_client_ip = None
                request.state.original_client_ip = None
        
        return await call_next(request)


def get_client_ip(request: Request) -> str:
    """
    Utility function to get the real client IP from request
    Use this instead of request.client.host in other parts of the application
    """
    # Check if ProxyHeadersMiddleware set the real IP
    if hasattr(request.state, 'real_client_ip') and request.state.real_client_ip:
        return request.state.real_client_ip
    
    # Fallback to X-Forwarded-For header
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Final fallback to direct client
    if request.client and hasattr(request.client, 'host') and request.client.host:
        return request.client.host
    
    return 'unknown'


__all__ = ["ProxyHeadersMiddleware", "get_client_ip"]