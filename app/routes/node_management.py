"""
Enhanced node management endpoints for production security
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..dependencies import SudoAdminDep, DBDep
from ..security.certificate_manager import cert_manager
from ..security.node_auth import node_auth, require_node_auth
from ..utils.logging_config import system_monitor_logger

router = APIRouter(prefix="/api/nodes", tags=["node-management"])


class NodeCertificateRequest(BaseModel):
    node_id: int
    hostname: str
    ip_address: Optional[str] = None


class NodeTokenRequest(BaseModel):
    node_id: int


class CertificateInfo(BaseModel):
    certificate: str
    private_key: str
    ca_certificate: str
    expires_at: str
    node_id: int


@router.post("/generate-certificate")
async def generate_node_certificate(
    request: NodeCertificateRequest,
    db: DBDep,
    _: SudoAdminDep
) -> CertificateInfo:
    """Generate SSL certificate for a node"""
    try:
        system_monitor_logger.info(f"Generating certificate for node {request.node_id}")
        
        # Generate node certificate
        cert_pem, key_pem = cert_manager.generate_node_certificate(
            request.node_id,
            request.hostname,
            request.ip_address
        )
        
        # Store in database
        success = cert_manager.store_node_certificate_in_db(
            db, request.node_id, cert_pem, key_pem
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store certificate in database"
            )
        
        # Get CA certificate for client verification
        ca_cert_pem = cert_manager.get_client_certificate_bundle()
        
        # Validate certificate
        cert_info = cert_manager.validate_certificate(cert_pem)
        
        return CertificateInfo(
            certificate=cert_pem,
            private_key=key_pem,
            ca_certificate=ca_cert_pem,
            expires_at=cert_info.get("not_after", "").isoformat() if cert_info.get("not_after") else "",
            node_id=request.node_id
        )
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to generate certificate for node {request.node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Certificate generation failed: {str(e)}"
        )


@router.get("/ca-certificate")
async def get_ca_certificate(_: SudoAdminDep) -> Dict[str, str]:
    """Get CA certificate for node verification"""
    try:
        ca_cert_pem = cert_manager.get_client_certificate_bundle()
        
        # Validate CA certificate
        cert_info = cert_manager.validate_certificate(ca_cert_pem)
        
        return {
            "ca_certificate": ca_cert_pem,
            "expires_at": cert_info.get("not_after", "").isoformat() if cert_info.get("not_after") else "",
            "is_valid": cert_info.get("valid", False)
        }
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to get CA certificate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CA certificate"
        )


@router.post("/generate-token")
async def generate_node_token(
    request: NodeTokenRequest,
    db: DBDep,
    _: SudoAdminDep
) -> Dict[str, str]:
    """Generate authentication token for a node"""
    try:
        token = node_auth.generate_node_token(request.node_id, db)
        
        return {
            "token": token,
            "node_id": str(request.node_id),
            "expires_in_hours": str(node_auth.token_expiry_hours)
        }
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to generate token for node {request.node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token"
        )


@router.get("/{node_id}/tokens")
async def get_node_tokens(
    node_id: int,
    db: DBDep,
    _: SudoAdminDep
) -> List[Dict[str, Any]]:
    """Get information about node tokens"""
    try:
        tokens = node_auth.get_node_token_info(node_id, db)
        return tokens
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to get tokens for node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token information"
        )


@router.delete("/{node_id}/tokens")
async def revoke_all_node_tokens(
    node_id: int,
    db: DBDep,
    _: SudoAdminDep
) -> Dict[str, str]:
    """Revoke all tokens for a node"""
    try:
        success = node_auth.revoke_all_node_tokens(node_id, db)
        
        if success:
            return {"message": f"All tokens revoked for node {node_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke tokens"
            )
            
    except Exception as e:
        system_monitor_logger.error(f"Failed to revoke tokens for node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke tokens"
        )


@router.get("/security/summary")
async def get_security_summary(
    db: DBDep,
    _: SudoAdminDep
) -> Dict[str, Any]:
    """Get security summary for monitoring"""
    try:
        summary = node_auth.get_security_summary(db)
        return summary
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to get security summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security summary"
        )


@router.post("/security/cleanup")
async def cleanup_expired_tokens(
    db: DBDep,
    _: SudoAdminDep
) -> Dict[str, Any]:
    """Manually cleanup expired tokens"""
    try:
        count = node_auth.cleanup_expired_tokens(db)
        
        return {
            "message": f"Cleaned up {count} expired tokens",
            "tokens_removed": count
        }
        
    except Exception as e:
        system_monitor_logger.error(f"Failed to cleanup expired tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired tokens"
        )


# Secure endpoint for nodes to validate their own tokens
@router.post("/validate-token")
async def validate_node_token(
    token: str,
    node_id: int,
    db: DBDep
) -> Dict[str, bool]:
    """Validate node token (used by nodes themselves)"""
    try:
        is_valid = node_auth.validate_node_token(token, node_id, db)
        
        return {"valid": is_valid}
        
    except Exception as e:
        system_monitor_logger.error(f"Error validating token for node {node_id}: {e}")
        return {"valid": False}


__all__ = ["router"]