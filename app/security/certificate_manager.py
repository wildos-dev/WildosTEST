"""
Certificate management for secure production deployment
Handles SSL/TLS certificates for external wildosnode servers
"""
import os
import ssl
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.orm import Session

from ..db import crud
from ..utils.logging_config import system_monitor_logger

logger = logging.getLogger(__name__)


class CertificateManager:
    """Manages SSL/TLS certificates for production node communication"""
    
    def __init__(self, data_dir: str = "/var/lib/wildosvpn"):
        self.data_dir = Path(data_dir)
        self.ssl_dir = self.data_dir / "ssl"
        self._dir_created = False
        
        # Certificate files
        self.ca_cert_file = self.ssl_dir / "ca.cert"
        self.ca_key_file = self.ssl_dir / "ca.key"
        self.server_cert_file = self.ssl_dir / "server.cert"
        self.server_key_file = self.ssl_dir / "server.key"
    
    def _ensure_ssl_directory(self):
        """Ensure SSL directory exists (called lazily)"""
        if not self._dir_created:
            try:
                self.ssl_dir.mkdir(parents=True, exist_ok=True)
                self._dir_created = True
            except (OSError, PermissionError):
                # If we can't create the directory, operations will fail gracefully
                self._dir_created = False
    
    def generate_ca_certificate(self, force_regenerate: bool = False) -> Tuple[str, str]:
        """
        Generate Certificate Authority (CA) certificate and key
        
        Returns:
            Tuple[str, str]: (cert_pem, key_pem)
        """
        if not force_regenerate and self.ca_cert_file.exists() and self.ca_key_file.exists():
            system_monitor_logger.info("CA certificate already exists, loading existing")
            return self._load_certificate_files(self.ca_cert_file, self.ca_key_file)
        
        system_monitor_logger.info("Generating new CA certificate")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WildosVPN"),
            x509.NameAttribute(NameOID.COMMON_NAME, "WildosVPN CA"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("wildosvpn-ca"),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=False,
                key_encipherment=False,
                key_agreement=False,
                data_encipherment=False,
                content_commitment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).sign(private_key, hashes.SHA256())
        
        # Serialize to PEM
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Save to files
        self._save_certificate_files(cert_pem, key_pem, self.ca_cert_file, self.ca_key_file)
        
        system_monitor_logger.info("CA certificate generated successfully")
        return cert_pem, key_pem
    
    def generate_node_certificate(
        self, 
        node_id: int, 
        hostname: str, 
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate certificate for a specific node
        
        Args:
            node_id: Unique node identifier
            hostname: Node hostname or domain
            ip_address: Optional IP address for SAN
            
        Returns:
            Tuple[str, str]: (cert_pem, key_pem)
        """
        system_monitor_logger.info(f"Generating certificate for node {node_id} ({hostname})")
        
        # Load CA certificate and key
        ca_cert_pem, ca_key_pem = self.get_ca_certificate()
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem.encode('utf-8'))
        ca_key = serialization.load_pem_private_key(
            ca_key_pem.encode('utf-8'), 
            password=None
        )
        
        # Generate private key for node
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WildosVPN"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"wildosnode-{node_id}"),
        ])
        
        # Build SAN list
        san_list = [
            x509.DNSName(hostname),
            x509.DNSName(f"wildosnode-{node_id}"),
            x509.DNSName("localhost"),
        ]
        
        if ip_address:
            try:
                import ipaddress
                san_list.append(x509.IPAddress(ipaddress.ip_address(ip_address)))
            except ValueError:
                logger.warning(f"Invalid IP address provided: {ip_address}")
        
        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)  # 1 year
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=False,
                crl_sign=False,
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                data_encipherment=False,
                content_commitment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        ).sign(ca_key, hashes.SHA256())
        
        # Serialize to PEM
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        system_monitor_logger.info(f"Certificate generated for node {node_id}")
        return cert_pem, key_pem
    
    def generate_panel_client_certificate(self) -> Tuple[str, str]:
        """
        Generate client certificate for panel to authenticate with nodes
        
        Returns:
            Tuple[str, str]: (cert_pem, key_pem)
        """
        system_monitor_logger.info("Generating client certificate for panel")
        
        # Load CA certificate and key
        ca_cert_pem, ca_key_pem = self.get_ca_certificate()
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem.encode('utf-8'))
        ca_key = serialization.load_pem_private_key(
            ca_key_pem.encode('utf-8'), 
            password=None
        )
        
        # Generate private key for panel client
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create subject for panel client
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WildosVPN"),
            x509.NameAttribute(NameOID.COMMON_NAME, "wildosvpn-panel"),
        ])
        
        # Build SAN list for panel
        san_list = [
            x509.DNSName("wildosvpn-panel"),
            x509.DNSName("localhost"),
        ]
        
        # Create certificate for panel client
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)  # 1 year
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                data_encipherment=False,
                content_commitment=False,
                encipher_only=False,
                decipher_only=False,
                key_cert_sign=False,
                crl_sign=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        ).sign(ca_key, hashes.SHA256())
        
        # Serialize to PEM
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Save panel client certificate to files
        client_cert_file = self.ssl_dir / "client.cert"
        client_key_file = self.ssl_dir / "client.key"
        self._save_certificate_files(cert_pem, key_pem, client_cert_file, client_key_file)
        
        system_monitor_logger.info("Panel client certificate generated successfully")
        return cert_pem, key_pem
    
    def get_panel_client_certificate(self) -> Tuple[str, str]:
        """Get panel client certificate, generate if doesn't exist"""
        client_cert_file = self.ssl_dir / "client.cert"
        client_key_file = self.ssl_dir / "client.key"
        
        # Try to load existing certificates first (without creating directory)
        if client_cert_file.exists() and client_key_file.exists():
            try:
                return self._load_certificate_files(client_cert_file, client_key_file)
            except Exception:
                # Files corrupted, regenerate
                pass
        
        # Generate new certificates
        return self.generate_panel_client_certificate()
    
    def get_ca_certificate(self) -> Tuple[str, str]:
        """Get CA certificate, generate if doesn't exist"""
        # Try to load existing CA certificates first (without creating directory)
        if self.ca_cert_file.exists() and self.ca_key_file.exists():
            try:
                return self._load_certificate_files(self.ca_cert_file, self.ca_key_file)
            except Exception:
                # Files corrupted, regenerate
                pass
        
        # Generate new CA certificate
        return self.generate_ca_certificate()
    
    def store_node_certificate_in_db(
        self, 
        db: Session, 
        node_id: int, 
        cert_pem: str, 
        key_pem: str
    ) -> bool:
        """Store node certificate in database"""
        try:
            # Store certificate data
            node_cert_data = {
                "certificate": cert_pem,
                "private_key": key_pem,
                "created_at": datetime.now(timezone.utc),
                "expires_at": self._get_cert_expiry(cert_pem)
            }
            
            # Update node with certificate data
            crud.update_node_certificate(db, node_id, node_cert_data)
            
            system_monitor_logger.info(f"Certificate stored in database for node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store certificate for node {node_id}: {e}")
            return False
    
    def get_client_certificate_bundle(self) -> str:
        """
        Get certificate bundle for clients (CA + any intermediates)
        This is what nodes need to trust the panel's certificates
        """
        ca_cert_pem, _ = self.get_ca_certificate()
        return ca_cert_pem
    
    def validate_certificate(self, cert_pem: str) -> Dict[str, Any]:
        """Validate a certificate and return information about it"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'))
            
            return {
                "valid": True,
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "not_before": cert.not_valid_before_utc,
                "not_after": cert.not_valid_after_utc,
                "serial_number": str(cert.serial_number),
                "is_expired": datetime.now(timezone.utc) > cert.not_valid_after_utc,
                "days_until_expiry": (cert.not_valid_after_utc - datetime.now(timezone.utc)).days
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _load_certificate_files(self, cert_file: Path, key_file: Path) -> Tuple[str, str]:
        """Load certificate and key from files"""
        if not cert_file.exists() or not key_file.exists():
            raise FileNotFoundError(f"Certificate files not found: {cert_file}, {key_file}")
        
        cert_pem = cert_file.read_text()
        key_pem = key_file.read_text()
        return cert_pem, key_pem
    
    def _save_certificate_files(
        self, 
        cert_pem: str, 
        key_pem: str, 
        cert_file: Path, 
        key_file: Path
    ):
        """Save certificate and key to files with proper permissions"""
        self._ensure_ssl_directory()
        if not self._dir_created:
            raise RuntimeError("Cannot save certificates: SSL directory not accessible")
        
        cert_file.write_text(cert_pem)
        key_file.write_text(key_pem)
        
        # Set proper permissions
        cert_file.chmod(0o644)
        key_file.chmod(0o600)
        
        # Set ownership to wildosvpn user if possible
        try:
            import pwd
            uid = pwd.getpwnam('wildosvpn').pw_uid
            gid = pwd.getpwnam('wildosvpn').pw_gid
            os.chown(cert_file, uid, gid)
            os.chown(key_file, uid, gid)
        except (KeyError, PermissionError):
            # User doesn't exist or no permission to change ownership
            pass
    
    def _get_cert_expiry(self, cert_pem: str) -> datetime:
        """Extract expiry date from certificate"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'))
            return cert.not_valid_after_utc
        except Exception:
            return datetime.now(timezone.utc) + timedelta(days=365)


# Global certificate manager instance
cert_manager = CertificateManager()


__all__ = ["CertificateManager", "cert_manager"]