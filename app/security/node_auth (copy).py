"""
Node authentication and authorization for production deployments
"""
import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "is_active": True,
            "last_used": None,
            "usage_count": 0
        }
        
        crud.store_node_token(db, token_data)
        
        system_monitor_logger.info(f"Generated authentication token for node {node_id}")
        return token
    
    def validate_node_token(self, token: str, node_id: int, db: Session) -> bool:
        """
        Validate node authentication token
        
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
            if stored_token.expires_at < datetime.utcnow():
                self._record_failed_attempt(node_id, db, "Expired token")
                crud.deactivate_node_token(db, stored_token.id)
                return False
            
            # Check if token is active
            if not stored_token.is_active:
                self._record_failed_attempt(node_id, db, "Inactive token")
                return False
            
            # Token is valid - update usage statistics
            crud.update_token_usage(db, stored_token.id)
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
                system_monitor_logger.info(f"Revoked token for node {node_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error revoking token for node {node_id}: {e}")
            return False
    
    def revoke_all_node_tokens(self, node_id: int, db: Session) -> bool:
        """Revoke all tokens for a node"""
        try:
            result = crud.deactivate_all_node_tokens(db, node_id)
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
                    "is_expired": token.expires_at < datetime.utcnow()
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
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.lockout_duration_minutes)
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
                "attempted_at": datetime.utcnow(),
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
            now = datetime.utcnow()
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