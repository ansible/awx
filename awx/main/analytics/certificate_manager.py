"""
Certificate Manager for AWX Analytics Authentication

Manages Candlepin consumer registration and certificate lifecycle for
authenticated analytics metrics upload. Adapted from subscription-manager
patterns (identity.py, identitycertlib.py, cp_provider.py).

Lifecycle:
1. Register - POST /consumers with consumer_type=aap, store returned cert+key
2. Connect - Create ssl.SSLContext with cert+key for mTLS
3. Upload - Use mTLS connection to upload analytics to Ingress
4. Check in - Every 4 hours, call GET /consumers/{uuid} to stay alive
5. Renew - On check-in, compare cert serial, update if changed
"""

import json
import logging
import os
import ssl
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger('awx.main.analytics.certificates')


class ConsumerIdentity:
    """
    Manages certificate storage on disk.

    Adapted from subscription_manager/identity.py:37 ConsumerIdentity class.
    Stores cert.pem and key.pem in a configurable directory, with proper
    file permissions. Handles non-root operation (awx user).
    """

    def __init__(self, cert_dir=None):
        self.cert_dir = cert_dir or getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_DIR', '/var/lib/awx/pki/consumer/')

    @property
    def certpath(self):
        return os.path.join(self.cert_dir, 'cert.pem')

    @property
    def keypath(self):
        return os.path.join(self.cert_dir, 'key.pem')

    @property
    def consumer_info_path(self):
        return os.path.join(self.cert_dir, 'consumer.json')

    def exists(self):
        """Check if both certificate and key files exist on disk."""
        return os.path.exists(self.certpath) and os.path.exists(self.keypath)

    def write(self, cert_pem, key_pem):
        """
        Write certificate and key files with secure permissions.

        Adapted from subscription_manager/identity.py:111-148.
        subscription-manager already handles non-root: skips chown when
        os.getuid() != 0.
        """
        os.makedirs(self.cert_dir, mode=0o700, exist_ok=True)

        with open(self.keypath, 'w') as f:
            f.write(key_pem)
        os.chmod(self.keypath, 0o600)  # Private key: owner read+write only

        with open(self.certpath, 'w') as f:
            f.write(cert_pem)
        os.chmod(self.certpath, 0o644)  # Certificate: world readable

        logger.debug("Certificate written to %s", self.certpath)
        logger.debug("Private key written to %s", self.keypath)

    def write_consumer_info(self, consumer_data):
        """Persist consumer UUID and metadata to disk for recovery after cache loss."""
        info = {
            'uuid': consumer_data.get('uuid'),
            'name': consumer_data.get('name'),
            'owner': consumer_data.get('owner', {}).get('key'),
            'serial': consumer_data.get('idCert', {}).get('serial', {}).get('serial'),
            'registered_at': datetime.utcnow().isoformat(),
        }
        with open(self.consumer_info_path, 'w') as f:
            json.dump(info, f, indent=2)
        os.chmod(self.consumer_info_path, 0o600)

    def read_consumer_info(self):
        """Read persisted consumer info from disk."""
        if not os.path.exists(self.consumer_info_path):
            return None
        try:
            with open(self.consumer_info_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read consumer info: %s", e)
            return None

    def get_serial_number(self):
        """
        Get the serial number from the local certificate.

        Adapted from subscription_manager/identity.py ConsumerIdentity.
        """
        try:
            from cryptography import x509

            with open(self.certpath, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read())
            return cert.serial_number
        except ImportError:
            # Fall back to persisted consumer info
            info = self.read_consumer_info()
            return info.get('serial') if info else None
        except Exception as e:
            logger.error("Failed to read certificate serial: %s", e)
            return None

    def get_expiry(self):
        """Get the certificate expiry datetime."""
        try:
            from cryptography import x509

            with open(self.certpath, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read())
            return cert.not_valid_after_utc
        except ImportError:
            return None
        except Exception as e:
            logger.error("Failed to read certificate expiry: %s", e)
            return None

    def remove(self):
        """Remove certificate files from disk."""
        for path in (self.certpath, self.keypath, self.consumer_info_path):
            if os.path.exists(path):
                os.remove(path)


class CandlepinCertificateManager:
    """
    Manages AAP client certificate lifecycle via Candlepin.

    Adapted from subscription-manager patterns:
    - Registration: rhsm/connection.py registerConsumer()
    - Certificate storage: subscription_manager/identity.py ConsumerIdentity
    - Check-in/renewal: subscription_manager/identitycertlib.py IdentityUpdateAction
    - Thread safety: subscription_manager/identity.py Identity class
    """

    def __init__(self):
        self.candlepin_url = getattr(settings, 'AWX_ANALYTICS_CANDLEPIN_URL', 'https://subscription.rhsm.redhat.com/candlepin')
        self.identity = ConsumerIdentity()
        self._lock = threading.Lock()

    def get_or_generate_client_certificate(self, username, password):
        """
        Get existing certificate or generate new one using Candlepin registration.

        Returns:
            Tuple of (cert_path, key_path) if successful, (None, None) if failed
        """
        with self._lock:
            try:
                if self.identity.exists() and self._is_certificate_valid():
                    logger.debug("Using existing client certificate")
                    return self.identity.certpath, self.identity.keypath

                logger.info("Generating new client certificate via Candlepin")
                return self._register_and_store(username, password)

            except Exception as e:
                logger.error("Certificate generation failed: %s", e)
                return None, None

    def has_valid_certificate(self):
        """Check if a valid certificate exists on disk."""
        with self._lock:
            return self.identity.exists() and self._is_certificate_valid()

    def get_certificate_paths(self):
        """Return certificate and key paths if they exist."""
        if self.identity.exists():
            return self.identity.certpath, self.identity.keypath
        return None, None

    def checkin_and_renew(self):
        """
        Check in with Candlepin and renew certificate if needed.

        Adapted from subscription_manager/identitycertlib.py IdentityUpdateAction.
        Any API call to Candlepin resets the consumer's lastCheckin timestamp,
        preventing the InactiveConsumerCleanerJob from deleting the consumer.

        The check-in also compares local cert serial to server serial. If
        different, the cert was regenerated server-side and we save the new one.
        """
        with self._lock:
            consumer_info = self.identity.read_consumer_info()
            if not consumer_info or not consumer_info.get('uuid'):
                logger.debug("No consumer registered, skipping check-in")
                return False

            uuid = consumer_info['uuid']

            try:
                # GET /consumers/{uuid} -- this IS the check-in
                # Resets lastCheckin server-side (connection.py:1862)
                response = requests.get(
                    f"{self.candlepin_url}/consumers/{uuid}",
                    cert=(self.identity.certpath, self.identity.keypath),
                    headers={'Accept': 'application/json'},
                    verify=False,
                    timeout=30,
                )

                if response.status_code == 404 or response.status_code == 410:
                    # Consumer was deleted (inactive cleanup or manual)
                    logger.warning("Consumer %s no longer exists, will re-register on next upload", uuid)
                    self.identity.remove()
                    return False

                if response.status_code != 200:
                    logger.error("Check-in failed: %s %s", response.status_code, response.text)
                    return False

                server_consumer = response.json()
                logger.info("Check-in successful for consumer %s", uuid)

                # Compare cert serials for renewal
                # Adapted from identitycertlib.py:42 IdentityUpdateAction
                server_serial = server_consumer.get('idCert', {}).get('serial', {}).get('serial')
                local_serial = self.identity.get_serial_number()

                if server_serial and local_serial and server_serial != local_serial:
                    logger.info("Certificate serial changed (local=%s, server=%s), saving new certificate", local_serial, server_serial)
                    self._persist_consumer_cert(server_consumer)

                return True

            except requests.RequestException as e:
                logger.error("Check-in failed for consumer %s: %s", uuid, e)
                return False

    def force_renewal(self, username, password):
        """Force certificate renewal by re-registering with Candlepin."""
        with self._lock:
            logger.info("Forcing certificate renewal")
            self.identity.remove()
            cert_path, key_path = self._register_and_store(username, password)
            return cert_path is not None

    def get_certificate_info(self):
        """Get detailed certificate information for monitoring."""
        info = {
            'status': 'missing',
            'cert_path': self.identity.certpath,
            'key_path': self.identity.keypath,
            'certificate_auth_enabled': getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_AUTH_ENABLED', True),
        }

        consumer_info = self.identity.read_consumer_info()
        if consumer_info:
            info['consumer_uuid'] = consumer_info.get('uuid')
            info['consumer_name'] = consumer_info.get('name')
            info['organization'] = consumer_info.get('owner')
            info['registered_at'] = consumer_info.get('registered_at')

        if not self.identity.exists():
            info['message'] = 'No certificate found on disk'
            info['needs_renewal'] = True
            return info

        expiry = self.identity.get_expiry()
        if expiry:
            days_until_expiry = (expiry - datetime.utcnow()).days
            renewal_threshold = getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_RENEWAL_THRESHOLD_DAYS', 30)

            info['not_valid_after'] = expiry.isoformat()
            info['days_until_expiry'] = days_until_expiry
            info['serial_number'] = str(self.identity.get_serial_number() or '')

            if expiry <= datetime.utcnow():
                info['status'] = 'expired'
                info['needs_renewal'] = True
            elif days_until_expiry <= renewal_threshold:
                info['status'] = 'expiring_soon'
                info['needs_renewal'] = True
            else:
                info['status'] = 'valid'
                info['needs_renewal'] = False
        else:
            info['status'] = 'unknown'
            info['needs_renewal'] = False
            info['message'] = 'Certificate exists but details unavailable (cryptography library not found)'

        return info

    # -- Private methods --

    def _register_and_store(self, username, password):
        """Register with Candlepin and store the returned certificate."""
        consumer_data = self._register_consumer(username, password)
        if not consumer_data:
            return None, None

        self._persist_consumer_cert(consumer_data)
        logger.info("Registered consumer %s with UUID %s", consumer_data.get('name'), consumer_data.get('uuid'))
        return self.identity.certpath, self.identity.keypath

    def _register_consumer(self, username, password):
        """
        Register AAP consumer with Candlepin using basic authentication.

        Adapted from rhsm/connection.py:1593 UEPConnection.registerConsumer().
        POST /consumers?owner=ORG_KEY
        """
        try:
            import socket

            hostname = socket.gethostname()

            consumer_data = {
                'name': f'aap-{hostname}-{str(getattr(settings, "SYSTEM_UUID", "unknown"))[:8]}',
                'type': {'label': 'aap', 'manifest': False},
                'facts': {
                    'system.name': hostname,
                    'system.type': 'aap-controller',
                    'aap.instance_uuid': str(getattr(settings, 'SYSTEM_UUID', '')),
                    'aap.version': getattr(settings, 'VERSION', 'unknown'),
                },
            }

            response = requests.post(
                f'{self.candlepin_url}/consumers',
                json=consumer_data,
                auth=(username, password),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                verify=False,
                timeout=30,
            )

            if response.status_code in (200, 201):
                return response.json()
            else:
                logger.error("Candlepin consumer registration failed: %s %s", response.status_code, response.text)
                return None

        except Exception as e:
            logger.error("Consumer registration error: %s", e)
            return None

    def _persist_consumer_cert(self, consumer_data):
        """
        Extract and persist certificate from consumer registration response.

        Adapted from subscription_manager/managerlib.py:93 persist_consumer_cert().
        """
        cert_data = consumer_data.get('idCert', {})
        cert_pem = cert_data.get('cert')
        key_pem = cert_data.get('key')

        if not cert_pem or not key_pem:
            logger.error("No certificate data in consumer response")
            return

        self.identity.write(cert_pem, key_pem)
        self.identity.write_consumer_info(consumer_data)

    def _is_certificate_valid(self):
        """Check if the certificate exists and is not near expiry."""
        if not self.identity.exists():
            return False

        expiry = self.identity.get_expiry()
        if expiry is None:
            # Can't check expiry without cryptography library; assume valid if file exists
            return True

        renewal_threshold = getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_RENEWAL_THRESHOLD_DAYS', 30)
        threshold_date = datetime.utcnow() + timedelta(days=renewal_threshold)

        if expiry <= threshold_date:
            logger.info("Certificate expires %s (within %d-day renewal threshold)", expiry, renewal_threshold)
            return False

        return True


# Global certificate manager instance
certificate_manager = CandlepinCertificateManager()


def get_or_generate_client_certificate(username, password):
    """Public interface for certificate generation."""
    if not getattr(settings, 'AWX_ANALYTICS_CERTIFICATE_AUTH_ENABLED', True):
        logger.debug("Certificate authentication disabled via settings")
        return None, None

    return certificate_manager.get_or_generate_client_certificate(username, password)


def get_certificate_info():
    """Get detailed certificate information for monitoring and status."""
    return certificate_manager.get_certificate_info()


def force_certificate_renewal(username, password):
    """Force certificate renewal regardless of current status."""
    return certificate_manager.force_renewal(username, password)


def check_certificate_health():
    """Health check for analytics certificate status."""
    cert_info = certificate_manager.get_certificate_info()

    status_mapping = {
        'valid': 'healthy',
        'expiring_soon': 'warning',
        'expired': 'critical',
        'missing': 'critical',
        'error': 'critical',
        'unknown': 'warning',
    }

    return {
        'status': status_mapping.get(cert_info.get('status', 'unknown'), 'warning'),
        'message': cert_info.get('message', f"Certificate status: {cert_info.get('status', 'unknown')}"),
        'needs_renewal': cert_info.get('needs_renewal', True),
        'days_until_expiry': cert_info.get('days_until_expiry'),
        'cert_path': cert_info.get('cert_path'),
    }
