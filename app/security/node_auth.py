"""
Node authentication and authorization for production deployments
"""
import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from collections import OrderedDict
import threading
import time
from queue import Queue
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..db import crud
from ..utils.logging_config import system_monitor_logger

logger = logging.getLogger(__name__)


class NodeAuthManager:
    """Manages authentication and authorization for wildosnode instances"""
    
    def __init__(self):
        self.token_expiry_hours = 24 * 7  # 7 days
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        
        # Cache configuration
        self._cache_ttl_seconds = 600  # 10 минут
        self._cache_maxsize = 10000
        self._token_cache = OrderedDict()  # key=(node_id, token_hash) -> {token_id, expires_at, is_active, cache_until}
        self._cache_lock = threading.Lock()
        
        # Performance improvements: bounded queue with deduplication
        self._bgq = Queue(maxsize=1000)  # Prevent memory leaks
        self._pending_updates = {}  # token_id -> (node_id, last_update_time) for deduplication
        self._pending_lock = threading.Lock()
        self._batch_interval = 30  # seconds
        self._bg_thread = threading.Thread(target=self._bg_worker, daemon=True)
        self._bg_thread.start()
    
    def generate_node_token(self, node_id: int, db: Session) -> str:
        """
        Generate secure authentication token for a node
        
        Args:
            node_id: Node identifier
            db: Database session
            
        Returns:
            str: Secure authentication token
        """
        # Generate cryptographically secure token
        token_bytes = secrets.token_bytes(32)
        token = secrets.token_urlsafe(32)
        
        # Create token hash for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store token in database
        token_data = {
            "node_id": node_id,
            "token_hash": token_hash,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours),
            "is_active": True,
            "last_used": None,
            "usage_count": 0
        }
        
        crud.store_node_token(db, token_data)
        
        system_monitor_logger.info(f"Generated authentication token for node {node_id}")
        return token
    
    def _cache_get(self, key):
        """Get value from cache with TTL check"""
        with self._cache_lock:
            if key not in self._token_cache:
                return None
            
            value = self._token_cache[key]
            now = time.time()
            
            # Check TTL
            if now > value['cache_until']:
                del self._token_cache[key]
                return None
            
            # Move to end for LRU
            self._token_cache.move_to_end(key)
            return value
    
    def _cache_set(self, key, value):
        """Set value in cache with LRU eviction"""
        with self._cache_lock:
            # Add cache_until timestamp
            value['cache_until'] = time.time() + self._cache_ttl_seconds
            
            # Remove if already exists
            if key in self._token_cache:
                del self._token_cache[key]
            
            # Add to end
            self._token_cache[key] = value
            
            # Evict oldest if over size limit
            while len(self._token_cache) > self._cache_maxsize:
                self._token_cache.popitem(last=False)
    
    def _cache_evict(self, key):
        """Remove specific key from cache"""
        with self._cache_lock:
            self._token_cache.pop(key, None)
    
    def _invalidate_node(self, node_id: int):
        """Remove all cache entries for a node"""
        with self._cache_lock:
            keys_to_remove = [k for k in self._token_cache.keys() if k[0] == node_id]
            for key in keys_to_remove:
                del self._token_cache[key]
    
    def _schedule_usage_update(self, token_id: int, node_id: int):
        """Schedule background usage update with deduplication"""
        current_time = time.time()
        
        with self._pending_lock:
            # Check if we already have a recent update for this token
            if token_id in self._pending_updates:
                last_update = self._pending_updates[token_id][1]
                # Skip if updated recently (within batch interval)
                if current_time - last_update < self._batch_interval:
                    return
            
            # Update or add to pending updates
            self._pending_updates[token_id] = (node_id, current_time)
        
        try:
            self._bgq.put_nowait(('update_usage', token_id, node_id))
        except:
            # Queue full, clean up pending updates
            with self._pending_lock:
                self._pending_updates.pop(token_id, None)
    
    def _bg_worker(self):
        """Background worker for processing batched updates"""
        from ..dependencies import get_db
        
        batch_updates = {}  # token_id -> node_id
        last_batch_time = time.time()
        
        while True:
            try:
                # Try to get task from queue with timeout
                try:
                    task = self._bgq.get(timeout=1.0)
                    if task:
                        action, token_id, node_id = task
                        if action == 'update_usage':
                            batch_updates[token_id] = node_id
                except:
                    # Queue timeout, continue to check batch processing
                    pass
                
                current_time = time.time()
                
                # Process batch if we have updates and enough time has passed
                if batch_updates and (current_time - last_batch_time >= self._batch_interval):
                    # Get a fresh database session with proper cleanup
                    db_gen = get_db()
                    db = next(db_gen)
                    
                    try:
                        # Process all updates in batch
                        updated_tokens = []
                        cleared_nodes = set()
                        
                        for token_id, node_id in batch_updates.items():
                            try:
                                crud.update_token_usage(db, token_id)
                                updated_tokens.append(token_id)
                                cleared_nodes.add(node_id)
                            except Exception as e:
                                logger.debug(f"Failed to update token {token_id}: {e}")
                        
                        # Clear failed attempts for unique nodes
                        for node_id in cleared_nodes:
                            try:
                                self._clear_failed_attempts(node_id, db)
                            except Exception as e:
                                logger.debug(f"Failed to clear attempts for node {node_id}: {e}")
                        
                        # Clean up pending updates for processed tokens
                        with self._pending_lock:
                            for token_id in updated_tokens:
                                self._pending_updates.pop(token_id, None)
                        
                        if updated_tokens:
                            logger.debug(f"Batch updated {len(updated_tokens)} tokens")
                        
                    except Exception as e:
                        logger.error(f"Batch update failed: {e}")
                    finally:
                        # Properly close the database session
                        try:
                            db.close()
                        except:
                            pass
                        try:
                            db_gen.close()
                        except:
                            pass
                    
                    # Reset batch
                    batch_updates.clear()
                    last_batch_time = current_time
                
            except Exception as e:
                logger.error(f"Background worker error: {e}")
                # Continue processing
    
    def validate_node_token(self, token: str, node_id: int, db: Session) -> bool:
        """
        Validate node authentication token with caching
        
        Args:
            token: Authentication token
            node_id: Node identifier  
            db: Database session
            
        Returns:
            bool: True if token is valid
        """
        try:
            # Hash the provided token
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            cache_key = (node_id, token_hash)
            
            # Check cache first
            cached_token = self._cache_get(cache_key)
            if cached_token:
                # Check if cached token is still valid
                now = datetime.now(timezone.utc)
                if (cached_token['expires_at'] > now and 
                    cached_token['is_active']):
                    
                    # SECURITY FIX: Always check lockout status, even for cached tokens
                    if self._is_node_locked_out(node_id, db):
                        system_monitor_logger.warning(f"Cached token rejected: Node {node_id} is locked out")
                        return False
                    
                    # Schedule background usage update
                    self._schedule_usage_update(cached_token['token_id'], node_id)
                    
                    system_monitor_logger.debug(f"Cache hit: authenticated node {node_id}")
                    return True
                else:
                    # Cached token is invalid, remove from cache
                    self._cache_evict(cache_key)
            
            # Cache miss or invalid cached token - check database
            # Check if node is locked out
            if self._is_node_locked_out(node_id, db):
                system_monitor_logger.warning(f"Node {node_id} is locked out due to failed authentication attempts")
                return False
            
            # Retrieve token from database
            stored_token = crud.get_node_token(db, node_id, token_hash)
            
            if not stored_token:
                self._record_failed_attempt(node_id, db, "Invalid token")
                return False
            
            # Check if token is expired  
            expires_at = getattr(stored_token, 'expires_at', None)
            now = datetime.now(timezone.utc)
            if expires_at and expires_at < now:
                self._record_failed_attempt(node_id, db, "Expired token")
                token_id = getattr(stored_token, 'id', None)
                if token_id:
                    crud.deactivate_node_token(db, token_id)
                return False
            
            # Check if token is active
            is_active = getattr(stored_token, 'is_active', False)
            if not is_active:
                self._record_failed_attempt(node_id, db, "Inactive token")
                return False
            
            # Token is valid - cache it and update usage statistics
            token_id = getattr(stored_token, 'id', None)
            
            # Cache the valid token
            cache_value = {
                'token_id': token_id,
                'expires_at': expires_at,
                'is_active': is_active
            }
            self._cache_set(cache_key, cache_value)
            
            # Update usage statistics synchronously for database consistency
            if token_id:
                crud.update_token_usage(db, token_id)
                self._clear_failed_attempts(node_id, db)
            
            system_monitor_logger.info(f"Successfully authenticated node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating token for node {node_id}: {e}")
            self._record_failed_attempt(node_id, db, f"Validation error: {str(e)}")
            return False
    
    def revoke_node_token(self, node_id: int, token: str, db: Session) -> bool:
        """Revoke a specific node token"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = crud.deactivate_node_token_by_hash(db, node_id, token_hash)
            
            if result:
                # Invalidate cache entry
                cache_key = (node_id, token_hash)
                self._cache_evict(cache_key)
                system_monitor_logger.info(f"Revoked token for node {node_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error revoking token for node {node_id}: {e}")
            return False
    
    def revoke_all_node_tokens(self, node_id: int, db: Session) -> bool:
        """Revoke all tokens for a node"""
        try:
            result = crud.deactivate_all_node_tokens(db, node_id)
            
            if result:
                # Invalidate all cache entries for this node
                self._invalidate_node(node_id)
                
            system_monitor_logger.info(f"Revoked all tokens for node {node_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error revoking all tokens for node {node_id}: {e}")
            return False
    
    def get_node_token_info(self, node_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get information about node tokens (without revealing actual tokens)"""
        try:
            tokens = crud.get_node_tokens(db, node_id)
            
            token_info = []
            for token in tokens:
                token_info.append({
                    "id": token.id,
                    "created_at": token.created_at,
                    "expires_at": token.expires_at,
                    "is_active": token.is_active,
                    "last_used": token.last_used,
                    "usage_count": token.usage_count,
                    "is_expired": token.expires_at < datetime.now(timezone.utc)
                })
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error getting token info for node {node_id}: {e}")
            return []
    
    def generate_api_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for API requests"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_api_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature for API requests"""
        expected_signature = self.generate_api_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def _is_node_locked_out(self, node_id: int, db: Session) -> bool:
        """Check if node is locked out due to failed attempts"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.lockout_duration_minutes)
            failed_attempts = crud.get_failed_auth_attempts(db, node_id, cutoff_time)
            
            return len(failed_attempts) >= self.max_failed_attempts
            
        except Exception as e:
            logger.error(f"Error checking lockout status for node {node_id}: {e}")
            return False
    
    def _record_failed_attempt(self, node_id: int, db: Session, reason: str):
        """Record failed authentication attempt"""
        try:
            attempt_data = {
                "node_id": node_id,
                "attempted_at": datetime.now(timezone.utc),
                "reason": reason,
                "ip_address": None  # Could be added if we track source IPs
            }
            
            crud.record_failed_auth_attempt(db, attempt_data)
            
            # Check if this puts the node over the limit
            if self._is_node_locked_out(node_id, db):
                system_monitor_logger.warning(
                    f"Node {node_id} has been locked out due to {self.max_failed_attempts} "
                    f"failed authentication attempts"
                )
            
        except Exception as e:
            logger.error(f"Error recording failed attempt for node {node_id}: {e}")
    
    def _clear_failed_attempts(self, node_id: int, db: Session):
        """Clear failed authentication attempts for a node"""
        try:
            crud.clear_failed_auth_attempts(db, node_id)
        except Exception as e:
            logger.error(f"Error clearing failed attempts for node {node_id}: {e}")
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired tokens from database"""
        try:
            count = crud.cleanup_expired_tokens(db)
            if count > 0:
                system_monitor_logger.info(f"Cleaned up {count} expired tokens")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    def get_security_summary(self, db: Session) -> Dict[str, Any]:
        """Get security summary for monitoring"""
        try:
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(hours=24)
            
            summary = {
                "active_tokens": crud.count_active_tokens(db),
                "expired_tokens": crud.count_expired_tokens(db),
                "failed_attempts_24h": crud.count_failed_attempts_since(db, cutoff_time),
                "locked_out_nodes": crud.count_locked_out_nodes(db, self.max_failed_attempts, self.lockout_duration_minutes),
                "last_cleanup": crud.get_last_token_cleanup(db)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating security summary: {e}")
            return {}


# Global node auth manager instance
node_auth = NodeAuthManager()


def require_node_auth(token: str, node_id: int, db: Session):
    """
    Dependency for requiring node authentication
    Raises HTTPException if authentication fails
    """
    if not node_auth.validate_node_token(token, node_id, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired node authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


__all__ = ["NodeAuthManager", "node_auth", "require_node_auth"]