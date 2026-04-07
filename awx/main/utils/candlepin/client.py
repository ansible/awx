import os
import tempfile
import uuid as _uuid_mod

from datetime import datetime, timezone

import requests

import logging
logger = logging.getLogger('awx.main.utils.candlepin')


class CandlepinClient:
    """
    Minimal Candlepin REST client for certificate lifecycle operations.

    All API calls authenticate with the consumer identity certificate (mTLS),
    matching the pattern used by subscription-manager after initial registration.

    TLS server verification is **enabled** by default (``verify_tls=True``).
    Pass ``candlepin_ca`` to verify against a specific CA bundle rather than the
    system trust store.  Verification can only be disabled by explicitly passing
    ``verify_tls=False``; this should be used only in controlled test environments
    and never in production.
    """

    DEFAULT_CANDLEPIN_URL = 'https://subscription.rhsm.redhat.com/subscription'

    def __init__(self, base_url=None, candlepin_ca=None, proxy=None, verify_tls=True):
        self.base_url = (base_url or self.DEFAULT_CANDLEPIN_URL).rstrip('/')
        if candlepin_ca:
            self.verify = candlepin_ca
        elif verify_tls:
            self.verify = True
        else:
            # Explicit opt-in required to reach this branch — never set by default.
            logger.warning('CandlepinClient: TLS verification is DISABLED (verify_tls=False). Do not use in production.')
            self.verify = False
        if proxy:
            # Use the caller-supplied URL as-is for HTTPS targets (preserves the
            # intended scheme — usually http:// so requests uses plain HTTP to reach
            # the proxy and issues CONNECT for TLS tunneling, but https:// is also
            # accepted for the rare case of an HTTPS-fronted proxy).
            # The http:// key always uses plain HTTP since non-TLS traffic never
            # needs TLS to the proxy itself.
            host = proxy.split('://', 1)[-1]
            self.proxies = {'https': proxy, 'http': f'http://{host}'}
        else:
            self.proxies = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_consumer(self, username, password, org, install_uuid=None):
        """POST /consumers?owner={org} — register a new AAP consumer with basic auth.

        Uses the customer's Red Hat subscription credentials (SUBSCRIPTIONS_USERNAME /
        SUBSCRIPTIONS_PASSWORD from AWX conf_setting) to register this controller
        instance as a Candlepin consumer and obtain an identity certificate for mTLS.

        Args:
            username:     Red Hat subscription username (from SUBSCRIPTIONS_USERNAME).
            password:     Red Hat subscription password (from SUBSCRIPTIONS_PASSWORD).
            org:          Candlepin owner/org key (from LICENSE.account_number).
            install_uuid: AWX INSTALL_UUID used as the consumer's aap.instance_uuid
                          fact; falls back to a random UUID if not provided.

        Returns:
            Tuple ``(cert_pem, key_pem, consumer_uuid)``.

        Raises:
            RuntimeError on any network or API failure.
        """
        url = f'{self.base_url}/consumers'
        instance_uuid = install_uuid or str(_uuid_mod.uuid4())
        payload = {
            'name': f'aap-{instance_uuid[:8]}',
            'type': {'label': 'aap'},
            'facts': {
                'system.certificate_version': '3.3',
                'system.name': 'aap-controller',
                'aap.instance_uuid': instance_uuid,
            },
        }
        try:
            resp = requests.post(
                url,
                params={'owner': org},
                auth=(username, password),
                json=payload,
                headers={'Content-Type': 'application/json'},
                verify=self.verify,
                proxies=self.proxies,
                timeout=120,
            )
        except Exception as e:
            raise RuntimeError(f'Candlepin register_consumer network error: {e}') from e

        if not resp.ok:
            raise RuntimeError(f'Candlepin register_consumer failed with status {resp.status_code}: {resp.text}')

        try:
            body = resp.json()
            consumer_uuid = body.get('uuid')
            id_cert = body.get('idCert', {})
            cert_pem = id_cert.get('cert')
            key_pem = id_cert.get('key')
        except Exception as e:
            raise RuntimeError(f'Candlepin register_consumer: could not parse response JSON: {e}') from e

        if not consumer_uuid or not cert_pem or not key_pem:
            raise RuntimeError('Candlepin register_consumer: response missing uuid, idCert.cert or idCert.key')

        logger.info(f'Candlepin consumer registered successfully (uuid={consumer_uuid})')
        return cert_pem, key_pem, consumer_uuid

    def checkin(self, consumer_uuid, cert_pem, key_pem):
        """PUT /consumers/{uuid} — reset inactivity timer.

        Best-effort: logs a warning on failure but never raises so that a
        transient Candlepin outage cannot abort a gather run.

        Returns True on success, False on any failure.
        """
        url = f'{self.base_url}/consumers/{consumer_uuid}'
        try:
            with self._temp_cert_files(cert_pem, key_pem) as (cert_path, key_path):
                resp = requests.put(
                    url,
                    cert=(cert_path, key_path),
                    json={'facts': {'aap.last_checkin': datetime.now(timezone.utc).isoformat()}},
                    headers={'Content-Type': 'application/json'},
                    verify=self.verify,
                    proxies=self.proxies,
                    timeout=30,
                )
            if resp.status_code in (200, 204):
                logger.info(f'Candlepin check-in successful for consumer {consumer_uuid}')
                return True
            logger.warning(f'Candlepin check-in returned unexpected status {resp.status_code} for consumer {consumer_uuid}')
            return False
        except Exception as e:
            logger.warning(f'Candlepin check-in failed for consumer {consumer_uuid}: {e}')
            return False

    def regenerate_cert(self, consumer_uuid, cert_pem, key_pem):
        """POST /consumers/{uuid} — regenerate the identity certificate.

        Returns ``(new_cert_pem, new_key_pem)`` on success.
        Raises ``RuntimeError`` on API or parsing failure so the caller can
        decide whether to fall back to service-account auth.
        """
        url = f'{self.base_url}/consumers/{consumer_uuid}'
        with self._temp_cert_files(cert_pem, key_pem) as (cert_path, key_path):
            try:
                resp = requests.post(
                    url,
                    cert=(cert_path, key_path),
                    verify=self.verify,
                    proxies=self.proxies,
                    timeout=120,
                )
            except Exception as e:
                raise RuntimeError(f'Candlepin regenerate_cert network error for consumer {consumer_uuid}: {e}') from e

        if not resp.ok:
            raise RuntimeError(f'Candlepin regenerate_cert failed with status {resp.status_code} for consumer {consumer_uuid}: {resp.text}')

        try:
            body = resp.json()
            id_cert = body.get('idCert', {})
            new_cert_pem = id_cert.get('cert')
            new_key_pem = id_cert.get('key')
        except Exception as e:
            raise RuntimeError(f'Candlepin regenerate_cert: could not parse response JSON: {e}') from e

        if not new_cert_pem or not new_key_pem:
            raise RuntimeError(f'Candlepin regenerate_cert: response did not contain idCert.cert / idCert.key for consumer {consumer_uuid}')

        logger.info(f'Candlepin cert regenerated successfully for consumer {consumer_uuid}')
        return new_cert_pem, new_key_pem

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_temp_pem(content):
        """Write PEM content to a secure temp file. Returns (fd, path)."""
        fd, path = tempfile.mkstemp(prefix='candlepin_', suffix='.pem')
        try:
            os.chmod(path, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            fd = None
        except Exception:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if os.path.exists(path):
                os.unlink(path)
            raise
        return path

    @staticmethod
    def _unlink_safe(path):
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except OSError as e:
            logger.warning(f'Could not remove temp cert file {path}: {e}')

    class _temp_cert_files:
        """Context manager: writes cert + key to secure temp files, cleans up on exit."""

        def __init__(self, cert_pem, key_pem):
            self._cert_pem = cert_pem
            self._key_pem = key_pem
            self._cert_path = None
            self._key_path = None

        def __enter__(self):
            self._cert_path = CandlepinClient._write_temp_pem(self._cert_pem)
            try:
                self._key_path = CandlepinClient._write_temp_pem(self._key_pem)
            except Exception:
                CandlepinClient._unlink_safe(self._cert_path)
                raise
            return self._cert_path, self._key_path

        def __exit__(self, *_):
            CandlepinClient._unlink_safe(self._cert_path)
            CandlepinClient._unlink_safe(self._key_path)
