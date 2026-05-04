# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Candlepin integration for mTLS-based authentication.

This package provides Candlepin consumer identity certificate support,
enabling AAP controller instances to authenticate analytics uploads using
mTLS instead of service account credentials.
"""

import logging
import requests

from django.conf import settings

from .client import CandlepinClient
from .lifecycle import (
    get_candlepin_ca,
    get_candlepin_url,
    get_proxy_url,
    get_renewal_days,
    is_cert_valid,
    parse_cert,
    run_candlepin_lifecycle,
)

logger = logging.getLogger('awx.main.utils.candlepin')


def _fetch_candlepin_cert_from_db():
    """Read cert PEM, key PEM, and consumer UUID from AWX conf_settings.

    Returns (cert_pem, key_pem, consumer_uuid) if valid certificate data exists,
    or (None, None, None) if placeholder/unregistered data.
    Best-effort: failures are logged as warnings and never propagate.
    """
    try:
        consumer_uuid = getattr(settings, 'CANDLEPIN_CONSUMER_UUID', '')
        cert_pem = getattr(settings, 'CANDLEPIN_CERT_PEM', '')
        key_pem = getattr(settings, 'CANDLEPIN_KEY_PEM', '')

        # Check if we have valid data
        if not consumer_uuid or not cert_pem or not key_pem:
            return None, None, None

        return cert_pem, key_pem, consumer_uuid
    except Exception as e:
        logger.warning(f'Could not fetch Candlepin lifecycle data from settings: {e}')
        return None, None, None


def _save_candlepin_cert_to_db(cert_pem, key_pem):
    """Persist a renewed Candlepin identity cert and key to AWX conf_settings.

    Returns:
        bool: True if save succeeded, False on any error.
    """
    from awx.conf.models import Setting

    try:
        # Parse certificate to extract metadata
        try:
            cert_info = parse_cert(cert_pem)
            serial_number = cert_info.get('serial', '')
            expires_at = cert_info.get('not_after', None)
        except Exception as e:
            logger.warning(f'Could not parse certificate metadata: {e}')
            serial_number = ''
            expires_at = None

        # Update conf_settings
        Setting.objects.update_or_create(key='CANDLEPIN_CERT_PEM', defaults={'value': cert_pem})
        Setting.objects.update_or_create(key='CANDLEPIN_KEY_PEM', defaults={'value': key_pem})
        Setting.objects.update_or_create(key='CANDLEPIN_SERIAL_NUMBER', defaults={'value': serial_number})
        if expires_at:
            Setting.objects.update_or_create(key='CANDLEPIN_EXPIRES_AT', defaults={'value': expires_at})

        logger.info('Renewed Candlepin cert and key saved to conf_settings.')
        return True
    except Exception as e:
        logger.error(f'Could not save renewed Candlepin cert to conf_settings: {e}')
        return False


def _discover_org(candlepin_url, username, password):
    """Discover org key via GET /users/{username}/owners.

    Returns:
        str: Organization key if found, None on any failure.
    """
    try:
        url = f"{candlepin_url}/users/{username}/owners"
        candlepin_ca = get_candlepin_ca()
        verify = candlepin_ca if candlepin_ca else True

        resp = requests.get(url, auth=(username, password), verify=verify, timeout=30)
        resp.raise_for_status()

        owners = resp.json()
        if not owners:
            logger.warning(f'No organizations found for user {username}')
            return None

        # Pick the first org, but warn if multiple exist
        if len(owners) > 1:
            logger.warning(f'User {username} has access to {len(owners)} organizations. Using first: {owners[0]}')
        first_org = owners[0]
        org = first_org.get('key')
        if not org:
            logger.warning(f'Organization key missing in first org entry for user {username}')
            return None

        return org
    except requests.exceptions.RequestException as e:
        logger.warning(f'Failed to discover organization for user {username}: {e}')
        return None
    except Exception as e:
        logger.warning(f'Unexpected error discovering organization for user {username}: {e}')
        return None


def _fetch_registration_credentials_from_db():
    """Read Candlepin registration credentials from AWX settings.

    Tries several options to retrieve the Candlepin credentials (set by AWX when the
    customer configures their Red Hat subscription), and to discover the org (org
    key for the Candlepin /consumers endpoint), and INSTALL_UUID (used as the
    consumer's aap.instance_uuid fact).

    Returns (username, password, org, install_uuid), any of which may be None
    if the corresponding setting is not configured.
    """
    candlepin_url = get_candlepin_url()
    try:
        # Try multiple credential sources in priority order
        username = getattr(settings, 'REDHAT_USERNAME', None)
        password = getattr(settings, 'REDHAT_PASSWORD', None)

        if not (username and password):
            username = getattr(settings, 'SUBSCRIPTIONS_USERNAME', None)
            password = getattr(settings, 'SUBSCRIPTIONS_PASSWORD', None)

        if not (username and password):
            username = getattr(settings, 'SUBSCRIPTIONS_CLIENT_ID', None)
            password = getattr(settings, 'SUBSCRIPTIONS_CLIENT_SECRET', None)

        install_uuid = getattr(settings, 'INSTALL_UUID', None)

        # Organization discovery requires SUBSCRIPTIONS credentials specifically
        subs_username = getattr(settings, 'SUBSCRIPTIONS_USERNAME', None)
        subs_password = getattr(settings, 'SUBSCRIPTIONS_PASSWORD', None)
        org = _discover_org(candlepin_url, subs_username, subs_password) if subs_username and subs_password else None

        return username, password, org, install_uuid
    except Exception as e:
        logger.warning(f'Could not fetch Candlepin registration credentials from settings: {e}')
        return None, None, None, None


def resolve_registration_credentials(username_override=None, password_override=None, org_override=None):
    """Resolve Candlepin registration credentials with optional overrides.

    Fetches credentials from database settings and merges with any provided overrides.
    Validates that all required fields are present.

    Args:
        username_override: Optional username to use instead of database value
        password_override: Optional password to use instead of database value
        org_override: Optional org to use instead of auto-discovered value

    Returns:
        Tuple (username, password, org, install_uuid) if all required fields present,
        or (None, None, None, None, error_messages) if validation fails.
        error_messages is a list of strings describing missing values.
    """
    db_username, db_password, db_org, db_install_uuid = _fetch_registration_credentials_from_db()

    username = username_override or db_username
    password = password_override or db_password
    org = org_override or db_org

    # Validate all required fields are present
    missing = []
    if not username:
        missing.append('username (provide --username or set REDHAT_USERNAME in database)')
    if not password:
        missing.append('password (provide password or set REDHAT_PASSWORD in database)')
    if not org:
        missing.append('org (provide --org or ensure SUBSCRIPTIONS_USERNAME/PASSWORD are configured for auto-discovery)')

    if missing:
        return None, None, None, None, missing

    return username, password, org, db_install_uuid, None


def _save_candlepin_registration_to_db(cert_pem, key_pem, consumer_uuid):
    """Persist a new Candlepin consumer registration (cert, key, UUID) to AWX conf_settings.

    Returns:
        bool: True if save succeeded, False on any error.
    """
    from awx.conf.models import Setting

    try:
        # Parse certificate to extract metadata
        try:
            cert_info = parse_cert(cert_pem)
            serial_number = cert_info.get('serial', '')
            expires_at = cert_info.get('not_after', None)
        except Exception as e:
            logger.warning(f'Could not parse certificate metadata: {e}')
            serial_number = ''
            expires_at = None

        # Update conf_settings with all registration data
        Setting.objects.update_or_create(key='CANDLEPIN_CONSUMER_UUID', defaults={'value': consumer_uuid})
        Setting.objects.update_or_create(key='CANDLEPIN_CERT_PEM', defaults={'value': cert_pem})
        Setting.objects.update_or_create(key='CANDLEPIN_KEY_PEM', defaults={'value': key_pem})
        Setting.objects.update_or_create(key='CANDLEPIN_SERIAL_NUMBER', defaults={'value': serial_number})
        if expires_at:
            Setting.objects.update_or_create(key='CANDLEPIN_EXPIRES_AT', defaults={'value': expires_at})

        logger.info(f'Candlepin consumer registration saved to conf_settings (uuid={consumer_uuid}).')
        return True
    except Exception as e:
        logger.error(f'Could not save Candlepin registration to conf_settings: {e}')
        return False


def _register_candlepin_consumer():
    """Register a new Candlepin consumer using credentials from AWX settings.

    Called when no identity cert exists in the DB.

    Reads the Candlepin credentials and the org key and then calls
    POST /consumers on Candlepin to obtain an identity certificate.
    On success the cert, key, and consumer UUID are persisted to conf_settings.

    Returns (cert_pem, key_pem, consumer_uuid) on success, (None, None, None) on
    any failure.  Best-effort: logs errors but never propagates.
    """
    username, password, org, install_uuid = _fetch_registration_credentials_from_db()

    if not username or not password:
        logger.warning('Candlepin registration is enabled but credentials are not set; skipping registration.')
        return None, None, None

    if not org:
        logger.warning('Candlepin registration is enabled but subscription org is not available; skipping registration.')
        return None, None, None

    candlepin_url = get_candlepin_url()
    candlepin_ca = get_candlepin_ca()
    proxy = get_proxy_url()
    client = CandlepinClient(base_url=candlepin_url, candlepin_ca=candlepin_ca, proxy=proxy)

    try:
        cert_pem, key_pem, consumer_uuid = client.register_consumer(username, password, org, install_uuid)
    except Exception as e:
        logger.error(f'Candlepin consumer registration failed: {e}')
        return None, None, None

    if not _save_candlepin_registration_to_db(cert_pem, key_pem, consumer_uuid):
        logger.error('Candlepin consumer registration succeeded but failed to save to database.')
        return None, None, None
    return cert_pem, key_pem, consumer_uuid


def _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid):
    """Orchestrate Candlepin check-in and proactive cert renewal.

    Returns the (possibly renewed) (cert_pem, key_pem) tuple. If renewal fails, the
    original cert is returned so the caller can still attempt mTLS (which
    will then fall back to service-account auth via the existing SSLError
    handler).
    """
    if not consumer_uuid:
        logger.warning('Candlepin lifecycle is enabled but consumer UUID is not set; skipping check-in and renewal.')
        return cert_pem, key_pem

    candlepin_url = get_candlepin_url()
    renewal_days = get_renewal_days()
    candlepin_ca = get_candlepin_ca()
    proxy = get_proxy_url()

    try:
        new_cert_pem, new_key_pem = run_candlepin_lifecycle(
            cert_pem,
            key_pem,
            consumer_uuid,
            candlepin_url=candlepin_url,
            renewal_days=renewal_days,
            candlepin_ca=candlepin_ca,
            proxy=proxy,
        )
        if (new_cert_pem, new_key_pem) != (cert_pem, key_pem):
            if not _save_candlepin_cert_to_db(new_cert_pem, new_key_pem):
                logger.warning('Renewed certificate will be used for this request, but failed to persist to database for future use.')
        return new_cert_pem, new_key_pem
    except Exception as e:
        logger.error(f'Candlepin lifecycle (check-in / renewal) failed: {e}; will attempt mTLS with existing cert')
        return cert_pem, key_pem


def get_or_generate_candlepin_certificate():
    """
    Get or generate Candlepin certificate for analytics authentication.

    This function provides certificate-based authentication for analytics uploads.
    It will:
    1. Check for existing certificate in conf_settings
    2. If missing, attempt to register with Candlepin (credentials from settings)
    3. If exists, check for renewal needs and refresh if needed
    4. Return the certificate and key as PEM strings

    Returns:
        Tuple (cert_pem, key_pem) as strings if certificate is available, (None, None) otherwise.

    Note:
        Credentials for registration are retrieved from Django settings internally
        (REDHAT_USERNAME/PASSWORD, SUBSCRIPTIONS_USERNAME/PASSWORD, or
        SUBSCRIPTIONS_CLIENT_ID/CLIENT_SECRET in priority order).
    """
    cert_pem, key_pem, consumer_uuid = _fetch_candlepin_cert_from_db()

    # If no certificate exists, attempt registration
    if not cert_pem or not key_pem:
        logger.info('No Candlepin certificate found, attempting registration')
        cert_pem, key_pem, consumer_uuid = _register_candlepin_consumer()

        if not cert_pem or not key_pem:
            logger.debug('Candlepin certificate registration failed or not configured')
            return None, None

    # Run lifecycle (check-in and renewal if needed)
    if consumer_uuid:
        cert_pem, key_pem = _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid)

    # Validate certificate is still usable
    if not is_cert_valid(cert_pem):
        logger.warning('Candlepin certificate is not valid (expired or not yet valid)')
        return None, None

    # Return raw PEM strings - caller will create temp files if needed
    return cert_pem, key_pem


__all__ = [
    'get_or_generate_candlepin_certificate',
    'resolve_registration_credentials',
]
