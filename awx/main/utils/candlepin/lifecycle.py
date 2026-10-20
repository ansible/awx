"""
Candlepin certificate lifecycle helpers.

is_cert_valid   — quick parseable/non-expired guard used at ship time
parse_cert      — extract metadata from a PEM cert string
needs_renewal   — check whether a cert is within the renewal window
run_candlepin_lifecycle — orchestrate check-in + proactive renewal per gather run
"""

import os
from datetime import datetime, timezone

from cryptography import x509
from django.conf import settings

import logging

logger = logging.getLogger('awx.main.utils.candlepin')

from .client import CandlepinClient

# ---------------------------------------------------------------------------
# Certificate helpers
# ---------------------------------------------------------------------------


def parse_cert(pem_text):
    """Parse a PEM certificate and return a metadata dict.

    Returns a dict with keys: serial, cn, issuer_cn, issuer_org,
    not_before, not_after, days_remaining, validity_days.

    Raises ``ValueError`` if the PEM cannot be parsed.
    """
    data = pem_text.encode('utf-8') if isinstance(pem_text, str) else pem_text
    try:
        cert = x509.load_pem_x509_certificate(data)
    except Exception as e:
        raise ValueError(f'Could not parse PEM certificate: {e}') from e

    expiry = cert.not_valid_after_utc
    remaining = expiry - datetime.now(timezone.utc)

    subject = {attr.oid._name: attr.value for attr in cert.subject}
    issuer = {attr.oid._name: attr.value for attr in cert.issuer}

    return {
        'serial': str(cert.serial_number),
        'cn': subject.get('commonName', 'unknown'),
        'issuer_cn': issuer.get('commonName', 'unknown'),
        'issuer_org': issuer.get('organizationName', 'unknown'),
        'not_before': cert.not_valid_before_utc.isoformat(),
        'not_after': expiry.isoformat(),
        'days_remaining': remaining.days,
        'validity_days': (expiry - cert.not_valid_before_utc).days,
    }


def is_cert_valid(cert_pem: str) -> bool:
    """Return True if cert_pem is parseable, already valid, and not yet expired.

    Logs a warning (suitable for operator visibility) when the cert is not yet
    valid, expired, or unparseable, then returns False so the caller can fall
    back to service-account authentication.
    """
    try:
        info = parse_cert(cert_pem)
        now = datetime.now(timezone.utc)
        not_before = datetime.fromisoformat(info['not_before'])
        if now < not_before:
            logger.warning(f'Candlepin cert is not yet valid (not_before={info["not_before"]}); falling back to service account auth')
            return False
        if info['days_remaining'] < 0:
            logger.warning(f'Candlepin cert expired at {info["not_after"]}; falling back to service account auth')
            return False
        return True
    except ValueError as e:
        logger.warning(f'Could not parse Candlepin cert: {e}')
        return False


def needs_renewal(pem_text, days_before_expiry):
    """Return True if the cert expires within ``days_before_expiry`` days.

    Also returns True if the cert is already expired (days_remaining < 0).
    Raises ``ValueError`` if the PEM cannot be parsed.
    """
    info = parse_cert(pem_text)
    return info['days_remaining'] <= days_before_expiry


# ---------------------------------------------------------------------------
# Lifecycle orchestration
# ---------------------------------------------------------------------------


def run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid, *, candlepin_url=None, renewal_days=90, candlepin_ca=None, proxy=None):
    """Perform check-in and, if needed, proactive cert renewal.

    Called once per gather run. Returns ``(cert_pem, key_pem)`` — either
    the originals (if no renewal was needed) or the freshly regenerated pair.

    Args:
        cert_pem:        Consumer identity certificate PEM string.
        key_pem:         Consumer identity key PEM string.
        consumer_uuid:   Candlepin consumer UUID string.
        candlepin_url:   Candlepin base URL (defaults to prod).
        renewal_days:    Renew if expiry is within this many days (default 90).
        candlepin_ca:    Path to Candlepin CA cert for server verification
                         (default None → uses system trust store).
        proxy:           Optional HTTP/HTTPS proxy URL string.

    Returns:
        Tuple ``(cert_pem, key_pem)`` — possibly updated after renewal.

    Raises:
        RuntimeError if cert regeneration is attempted and fails.
    """
    client = CandlepinClient(base_url=candlepin_url, candlepin_ca=candlepin_ca, proxy=proxy)

    # Step 1: Inspect cert metadata for diagnostics and renewal decision.
    try:
        info = parse_cert(cert_pem)
    except ValueError as e:
        logger.warning(f'Candlepin lifecycle: could not parse cert, skipping lifecycle: {e}')
        return cert_pem, key_pem

    logger.info(f'Candlepin cert: serial={info["serial"]}, CN={info["cn"]}, expires={info["not_after"]}, days_remaining={info["days_remaining"]}')

    # Step 2: Check-in (best-effort, never raises).
    checkin_success = client.checkin(consumer_uuid, cert_pem, key_pem)
    if not checkin_success:
        logger.warning(
            f'Candlepin check-in failed for consumer {consumer_uuid}. '
            f'Consumer may have been deleted server-side or certificate is invalid. '
            f'Lifecycle will continue but may fail.'
        )

    # Step 3: Compare local cert serial with server's serial.
    # If they differ, the server has issued a new cert (e.g., admin regenerated it).
    consumer_data = client.get_consumer(consumer_uuid, cert_pem, key_pem)
    if not consumer_data:
        if not checkin_success:
            logger.error(
                f'Both check-in and get_consumer failed for consumer {consumer_uuid}. '
                f'Consumer was likely deleted from Candlepin server. '
                f'Re-registration may be required. Will attempt cert renewal anyway.'
            )
        else:
            logger.warning(f'Could not retrieve consumer data for {consumer_uuid} but check-in succeeded. Continuing lifecycle.')
    else:
        server_cert_pem = consumer_data.get('idCert', {}).get('cert')
        if server_cert_pem:
            try:
                server_info = parse_cert(server_cert_pem)
                server_serial = server_info['serial']
                local_serial = info['serial']

                if server_serial != local_serial:
                    logger.warning(
                        f'Candlepin cert serial mismatch: local={local_serial}, server={server_serial}. '
                        f'Server has issued a new certificate; requesting updated cert.'
                    )
                    # Fetch the new cert from the server
                    new_cert_pem, new_key_pem = client.regenerate_cert(consumer_uuid, cert_pem, key_pem)

                    try:
                        new_info = parse_cert(new_cert_pem)
                        logger.info(f'Candlepin cert updated: old serial={local_serial}, new serial={new_info["serial"]}, new expiry={new_info["not_after"]}')
                    except ValueError:
                        logger.warning('Candlepin lifecycle: could not parse updated cert for logging')

                    return new_cert_pem, new_key_pem
                else:
                    logger.debug(f'Candlepin cert serial matches server: {local_serial}')
            except ValueError as e:
                logger.warning(f'Candlepin lifecycle: could not parse server cert from get_consumer: {e}')

    # Step 4: Proactive renewal if within the renewal window (or already expired).
    if needs_renewal(cert_pem, renewal_days):
        logger.info(f'Candlepin cert expires in {info["days_remaining"]} days (threshold: {renewal_days}); requesting renewal for consumer {consumer_uuid}')
        new_cert_pem, new_key_pem = client.regenerate_cert(consumer_uuid, cert_pem, key_pem)

        try:
            new_info = parse_cert(new_cert_pem)
            logger.info(f'Candlepin cert renewed: old serial={info["serial"]}, new serial={new_info["serial"]}, new expiry={new_info["not_after"]}')
        except ValueError:
            logger.warning('Candlepin lifecycle: could not parse renewed cert for logging')

        return new_cert_pem, new_key_pem

    logger.info(f'Candlepin cert is healthy ({info["days_remaining"]} days remaining); no renewal needed')
    return cert_pem, key_pem


def get_candlepin_url():
    """Get Candlepin base URL from Django settings."""
    return settings.AWX_ANALYTICS_CANDLEPIN_URL


def get_renewal_days():
    """Get certificate renewal threshold in days from Django settings."""
    return settings.AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS


def get_candlepin_ca():
    """Get Candlepin CA certificate path from Django settings.

    Returns:
        str: Path to CA certificate file if configured and exists, None otherwise.
    """
    ca_path = settings.AWX_ANALYTICS_CANDLEPIN_CA
    if ca_path and not os.path.isfile(ca_path):
        logger.warning(f'Configured Candlepin CA certificate not found at {ca_path}, using system default CA bundle')
        return None
    return ca_path


def get_proxy_url():
    """Get proxy URL from Django settings."""
    return settings.AWX_ANALYTICS_CANDLEPIN_PROXY_URL
