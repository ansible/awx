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
            return True
        return not self._is_certificate_valid(cert_path)


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


def check_certificate_health() -> dict:
    """Health check for analytics certificate status"""
    try:
        cert_path, key_path = certificate_manager._get_cached_certificate()
        if cert_path and certificate_manager._is_certificate_valid(cert_path):
            # Try to extract expiry date for health status
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                
                with open(cert_path, 'rb') as f:
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                
                return {
                    "status": "healthy", 
                    "cert_expires": cert.not_valid_after.isoformat(),
                    "cert_path": cert_path
                }
            except ImportError:
                return {"status": "healthy", "cert_path": cert_path}
        else:
            return {"status": "warning", "message": "Certificate renewal needed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}