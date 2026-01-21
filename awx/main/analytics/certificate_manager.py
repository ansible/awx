"""
Certificate Manager for AWX Analytics Authentication

Handles Candlepin consumer registration and certificate lifecycle management
for authenticated analytics metrics upload.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('awx.main.analytics.certificates')


class CandlepinCertificateManager:
    """Manages AAP client certificate generation and renewal via Candlepin"""
    
    def __init__(self):
        self.candlepin_url = getattr(settings, 'AWX_ANALYTICS_CANDLEPIN_URL', 
                                   "https://subscription.rhsm.redhat.com/candlepin")
        self.cert_cache_key = "aap_client_certificate"
        self.consumer_cache_key = "aap_consumer_info"
        self.cert_dir = getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_DIR',
                               os.path.join(settings.BASE_DIR, 'var', 'lib', 'awx', 'certificates'))
        
    def get_or_generate_client_certificate(self, username: str, password: str) -> Tuple[Optional[str], Optional[str]]:
        """Get existing certificate or generate new one using Candlepin basic auth"""
        try:
            # Check for valid cached certificate
            cert_path, key_path = self._get_cached_certificate()
            if cert_path and key_path and self._is_certificate_valid(cert_path):
                logger.debug("Using cached client certificate")
                return cert_path, key_path
            
            # Generate new certificate
            logger.info("Generating new client certificate via Candlepin")
            return self._generate_new_certificate(username, password)
            
        except Exception as e:
            logger.error(f"Certificate generation failed: {e}")
            return None, None
    
    def _generate_new_certificate(self, username: str, password: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate new certificate using Candlepin consumer registration"""
        try:
            # Register consumer with Candlepin
            consumer_info = self._register_consumer(username, password)
            if not consumer_info:
                return None, None
            
            # Extract certificate from consumer registration
            cert_data = consumer_info.get('idCert', {})
            cert_pem = cert_data.get('cert')
            key_pem = cert_data.get('key')
            
            if not cert_pem or not key_pem:
                logger.error("No certificate data returned from Candlepin")
                return None, None
            
            # Store certificate files securely
            cert_path, key_path = self._store_certificate_files(cert_pem, key_pem)
            
            # Cache certificate info and consumer data
            self._cache_certificate_info(cert_path, key_path, consumer_info)
            
            logger.info(f"Successfully generated client certificate with consumer UUID: {consumer_info.get('uuid')}")
            return cert_path, key_path
            
        except Exception as e:
            logger.error(f"Failed to generate new certificate: {e}")
            return None, None
    
    def _register_consumer(self, username: str, password: str) -> Optional[dict]:
        """Register AAP consumer with Candlepin using basic authentication"""
        try:
            consumer_data = {
                "name": f"aap-analytics-{str(settings.SYSTEM_UUID)[:8]}",
                "type": {"label": "system", "manifest": False},
                "facts": {
                    "system.name": "AAP Analytics Consumer",
                    "system.type": "aap-controller", 
                    "aap.instance_uuid": str(settings.SYSTEM_UUID),
                    "aap.auth_method": "certificate_auth",
                    "system.certificate_version": "3.2",
                    "uname.machine": "x86_64"
                },
                "capabilities": [
                    {"name": "cores"},
                    {"name": "ram"},
                    {"name": "cert_v3"},
                    {"name": "analytics_auth"}
                ],
                "contentTags": ["aap", "analytics"]
            }
            
            response = requests.post(
                f"{self.candlepin_url}/consumers",
                json=consumer_data,
                auth=(username, password),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                verify=False,  # Production Candlepin uses self-signed certs
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Candlepin consumer registration failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Consumer registration error: {e}")
            return None
    
    def _store_certificate_files(self, cert_pem: str, key_pem: str) -> Tuple[str, str]:
        """Store certificate files securely in AWX data directory"""
        # Ensure certificate directory exists with secure permissions
        os.makedirs(self.cert_dir, mode=0o700, exist_ok=True)
        
        cert_path = os.path.join(self.cert_dir, 'aap-analytics-client.crt')
        key_path = os.path.join(self.cert_dir, 'aap-analytics-client.key')
        
        # Write certificate files with secure permissions
        with open(cert_path, 'w') as f:
            f.write(cert_pem)
        os.chmod(cert_path, 0o644)
        
        with open(key_path, 'w') as f:
            f.write(key_pem)
        os.chmod(key_path, 0o600)
        
        logger.debug(f"Certificate stored at: {cert_path}")
        logger.debug(f"Private key stored at: {key_path}")
        
        return cert_path, key_path
    
    def _get_cached_certificate(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve cached certificate paths if available"""
        cert_info = cache.get(self.cert_cache_key)
        if cert_info:
            cert_path = cert_info.get('cert_path')
            key_path = cert_info.get('key_path')
            if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
                return cert_path, key_path
        return None, None
    
    def _is_certificate_valid(self, cert_path: str) -> bool:
        """Check if certificate is valid and not expired"""
        try:
            # Try to import cryptography, fall back to openssl command if unavailable
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                
                with open(cert_path, 'rb') as f:
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                
                # Check if certificate expires within next 7 days
                renewal_threshold = getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_RENEWAL_THRESHOLD_DAYS', 7)
                expiry_threshold = datetime.utcnow() + timedelta(days=renewal_threshold)
                
                if cert.not_valid_after <= expiry_threshold:
                    logger.info(f"Certificate expires soon: {cert.not_valid_after}")
                    return False
                
                return True
                
            except ImportError:
                # Fallback to openssl command if cryptography not available
                import subprocess
                result = subprocess.run([
                    'openssl', 'x509', '-in', cert_path, '-noout', '-checkend', str(7 * 24 * 60 * 60)
                ], capture_output=True, text=True)
                
                # openssl checkend returns 0 if certificate is valid for specified time
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return False
    
    def _cache_certificate_info(self, cert_path: str, key_path: str, consumer_info: dict):
        """Cache certificate and consumer information"""
        cert_info = {
            'cert_path': cert_path,
            'key_path': key_path,
            'generated_at': datetime.utcnow().isoformat(),
            'consumer_uuid': consumer_info.get('uuid'),
            'consumer_name': consumer_info.get('name')
        }
        
        # Cache for 30 days (certificates are valid for 365 days)
        cache.set(self.cert_cache_key, cert_info, timeout=30*24*60*60)
        cache.set(self.consumer_cache_key, consumer_info, timeout=30*24*60*60)
    
    def _should_renew_certificate(self) -> bool:
        """Check if certificate should be renewed"""
        cert_path, _ = self._get_cached_certificate()
        if not cert_path:
            logger.debug("No cached certificate found, renewal needed")
            return True
        
        if not os.path.exists(cert_path):
            logger.debug("Certificate file missing, renewal needed")
            return True
            
        is_valid = self._is_certificate_valid(cert_path)
        if not is_valid:
            logger.info("Certificate validation failed or expiry approaching, renewal needed")
        return not is_valid
    
    def get_certificate_info(self) -> dict:
        """Get detailed certificate information for monitoring"""
        try:
            cert_path, key_path = self._get_cached_certificate()
            if not cert_path or not key_path:
                return {
                    "status": "missing",
                    "message": "No certificate found",
                    "needs_renewal": True
                }
            
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                return {
                    "status": "missing_files",
                    "message": "Certificate files not found on disk",
                    "needs_renewal": True,
                    "cert_path": cert_path,
                    "key_path": key_path
                }
            
            # Get certificate details
            cert_info = {
                "status": "unknown",
                "cert_path": cert_path,
                "key_path": key_path,
                "needs_renewal": self._should_renew_certificate()
            }
            
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                
                with open(cert_path, 'rb') as f:
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                
                # Extract certificate details
                renewal_threshold = getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_RENEWAL_THRESHOLD_DAYS', 7)
                expiry_threshold = datetime.utcnow() + timedelta(days=renewal_threshold)
                
                cert_info.update({
                    "status": "valid" if cert.not_valid_after > expiry_threshold else "expiring_soon",
                    "subject": cert.subject.rfc4514_string(),
                    "issuer": cert.issuer.rfc4514_string(),
                    "not_valid_before": cert.not_valid_before.isoformat(),
                    "not_valid_after": cert.not_valid_after.isoformat(),
                    "days_until_expiry": (cert.not_valid_after - datetime.utcnow()).days,
                    "serial_number": str(cert.serial_number)
                })
                
                if cert.not_valid_after <= datetime.utcnow():
                    cert_info["status"] = "expired"
                elif cert.not_valid_after <= expiry_threshold:
                    cert_info["status"] = "expiring_soon"
                    
            except ImportError:
                # Fallback without cryptography library
                cert_info["message"] = "Certificate details unavailable (cryptography library not found)"
                
            # Add cached consumer info if available
            consumer_info = cache.get(self.consumer_cache_key)
            if consumer_info:
                cert_info.update({
                    "consumer_uuid": consumer_info.get('uuid'),
                    "consumer_name": consumer_info.get('name'),
                    "organization": consumer_info.get('owner', {}).get('key')
                })
            
            return cert_info
            
        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return {
                "status": "error",
                "message": str(e),
                "needs_renewal": True
            }
    
    def force_certificate_renewal(self, username: str, password: str) -> bool:
        """Force certificate renewal regardless of current status"""
        logger.info("Forcing certificate renewal")
        try:
            # Clear existing cache
            cache.delete(self.cert_cache_key)
            cache.delete(self.consumer_cache_key)
            
            # Generate new certificate
            cert_path, key_path = self._generate_new_certificate(username, password)
            
            if cert_path and key_path:
                logger.info("Forced certificate renewal successful")
                return True
            else:
                logger.error("Forced certificate renewal failed")
                return False
                
        except Exception as e:
            logger.error(f"Forced certificate renewal error: {e}")
            return False


# Global certificate manager instance
certificate_manager = CandlepinCertificateManager()


def get_or_generate_client_certificate(username: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Public interface for certificate management
    
    Returns:
        Tuple of (cert_path, key_path) if successful, (None, None) if failed
    """
    # Check if certificate authentication is enabled
    if not getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_AUTH_ENABLED', True):
        logger.debug("Certificate authentication disabled via settings")
        return None, None
    
    return certificate_manager.get_or_generate_client_certificate(username, password)


def get_certificate_info() -> dict:
    """
    Get detailed certificate information for monitoring and status
    
    Returns:
        Dict with certificate status, expiry, consumer info, and file paths
    """
    return certificate_manager.get_certificate_info()


def force_certificate_renewal(username: str, password: str) -> bool:
    """
    Force certificate renewal regardless of current status
    
    Args:
        username: Red Hat username for authentication
        password: Red Hat password for authentication
    
    Returns:
        True if renewal successful, False otherwise
    """
    return certificate_manager.force_certificate_renewal(username, password)


def check_certificate_health() -> dict:
    """
    Health check for analytics certificate status (simplified interface)
    
    Returns:
        Dict with basic health status for monitoring systems
    """
    cert_info = certificate_manager.get_certificate_info()
    
    # Simplify status for health check interface
    status_mapping = {
        "valid": "healthy",
        "expiring_soon": "warning",
        "expired": "critical",
        "missing": "critical",
        "missing_files": "critical",
        "error": "critical",
        "unknown": "warning"
    }
    
    return {
        "status": status_mapping.get(cert_info.get("status", "unknown"), "warning"),
        "message": cert_info.get("message", f"Certificate status: {cert_info.get('status', 'unknown')}"),
        "needs_renewal": cert_info.get("needs_renewal", True),
        "days_until_expiry": cert_info.get("days_until_expiry"),
        "cert_path": cert_info.get("cert_path")
    }