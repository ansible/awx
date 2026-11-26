# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import status

from awx.api.generics import APIView, Response
from awx.api.permissions import IsSystemAdmin
from awx.main.utils.candlepin import (
    _fetch_candlepin_cert_from_db,
    _register_candlepin_consumer,
    _run_candlepin_lifecycle,
    _save_candlepin_cert_to_db,
)
from awx.main.utils.candlepin.lifecycle import parse_cert

logger = logging.getLogger('awx.api.views.candlepin')


def _cert_response_data(cert_pem, key_pem, consumer_uuid):
    """Build the standard cert response dict from PEM strings."""
    cert_info = {}
    try:
        cert_info = parse_cert(cert_pem) if cert_pem else {}
    except Exception:
        pass
    return {
        'registered': bool(cert_pem and key_pem),
        'consumer_uuid': consumer_uuid or '',
        'cert_pem': cert_pem or '',
        'key_pem': key_pem or '',
        'serial_number': cert_info.get('serial', ''),
        'expires': cert_info.get('not_after', None),
        'days_remaining': cert_info.get('days_remaining', None),
    }


class CandlepinCertView(APIView):
    """Return the current Candlepin identity certificate, key, and metadata.

    Used by external services (e.g. metrics-service) to retrieve the mTLS
    credentials needed for analytics uploads to CRC without requiring direct
    access to the AWX database or SECRET_KEY.
    """

    name = _('Candlepin Identity Certificate')
    permission_classes = (IsSystemAdmin,)
    swagger_topic = 'System Configuration'
    resource_purpose = 'candlepin mTLS identity certificate for analytics uploads'

    def get(self, request, format=None):
        cert_pem, key_pem, consumer_uuid = _fetch_candlepin_cert_from_db()
        return Response(_cert_response_data(cert_pem, key_pem, consumer_uuid))


class CandlepinRegisterView(APIView):
    """Register this AAP instance as a Candlepin consumer.

    Credentials (REDHAT_USERNAME / REDHAT_PASSWORD) are read from AWX settings.
    Returns 409 if already registered; pass {"force": true} to re-register.
    The cert, key, and consumer UUID are persisted to the AWX conf_setting table
    on success.
    """

    name = _('Candlepin Register')
    permission_classes = (IsSystemAdmin,)
    swagger_topic = 'System Configuration'
    resource_purpose = 'candlepin consumer registration'

    def post(self, request, format=None):
        force = bool(request.data.get('force', False))

        existing_cert, existing_key, _ = _fetch_candlepin_cert_from_db()
        if existing_cert and existing_key and not force:
            return Response(
                {'error': 'Already registered. Use {"force": true} to re-register.'},
                status=status.HTTP_409_CONFLICT,
            )

        cert_pem, key_pem, consumer_uuid = _register_candlepin_consumer()
        if not cert_pem or not key_pem:
            return Response(
                {
                    'error': (
                        'Registration failed. Ensure REDHAT_USERNAME and REDHAT_PASSWORD '
                        'are configured in AWX settings and that the Candlepin service is reachable.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info('Candlepin registration completed via API (consumer_uuid=%s)', consumer_uuid)
        return Response(_cert_response_data(cert_pem, key_pem, consumer_uuid), status=status.HTTP_201_CREATED)


class CandlepinRenewView(APIView):
    """Check in with Candlepin and renew the identity certificate if needed.

    Performs a Candlepin check-in and conditionally renews the cert if it is
    within the renewal threshold (AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS).
    Pass {"force": true} to renew regardless of how many days remain on the cert.
    The renewed cert is persisted to the AWX conf_setting table automatically.
    Returns 400 if not yet registered (run register first).
    """

    name = _('Candlepin Renew')
    permission_classes = (IsSystemAdmin,)
    swagger_topic = 'System Configuration'
    resource_purpose = 'candlepin certificate renewal'

    def post(self, request, format=None):
        force = bool(request.data.get('force', False))

        cert_pem, key_pem, consumer_uuid = _fetch_candlepin_cert_from_db()
        if not cert_pem or not key_pem:
            return Response(
                {'error': 'No Candlepin certificate found. Run the register endpoint first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if force:
            # Bypass the renewal threshold check by passing renewal_days=0 so
            # needs_renewal() always returns True, forcing immediate renewal.
            from awx.main.utils.candlepin.lifecycle import (
                get_candlepin_ca,
                get_candlepin_url,
                get_proxy_url,
                run_candlepin_lifecycle,
            )

            new_cert_pem, new_key_pem = run_candlepin_lifecycle(
                cert_pem,
                key_pem,
                consumer_uuid,
                candlepin_url=get_candlepin_url(),
                renewal_days=0,
                candlepin_ca=get_candlepin_ca(),
                proxy=get_proxy_url(),
            )
            if (new_cert_pem, new_key_pem) != (cert_pem, key_pem):
                _save_candlepin_cert_to_db(new_cert_pem, new_key_pem)
            cert_pem, key_pem = new_cert_pem, new_key_pem
        else:
            cert_pem, key_pem = _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid)

        logger.info('Candlepin renewal completed via API (consumer_uuid=%s)', consumer_uuid)
        return Response(_cert_response_data(cert_pem, key_pem, consumer_uuid))


class CandlepinLifecycleView(APIView):
    """Single-call endpoint: register if no cert, then check in and renew if needed, return cert.

    Designed for external service integrations (e.g. metrics-service) that need
    a valid mTLS certificate without managing the register/renew steps separately.
    Returns 201 on first registration, 200 on subsequent calls.
    Returns 400 if no cert exists and registration fails (credentials not configured).
    """

    name = _('Candlepin Lifecycle')
    permission_classes = (IsSystemAdmin,)
    swagger_topic = 'System Configuration'
    resource_purpose = 'candlepin lifecycle - register if needed, renew if needed, return cert'

    def post(self, request, format=None):
        newly_registered = False

        cert_pem, key_pem, consumer_uuid = _fetch_candlepin_cert_from_db()

        if not cert_pem or not key_pem:
            cert_pem, key_pem, consumer_uuid = _register_candlepin_consumer()
            if not cert_pem or not key_pem:
                return Response(
                    {
                        'error': (
                            'No Candlepin certificate found and registration failed. '
                            'Ensure REDHAT_USERNAME and REDHAT_PASSWORD are configured in AWX settings.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            newly_registered = True
            logger.info('Candlepin consumer registered via lifecycle endpoint (consumer_uuid=%s)', consumer_uuid)

        if consumer_uuid:
            cert_pem, key_pem = _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid)

        logger.info('Candlepin lifecycle completed via API (consumer_uuid=%s)', consumer_uuid)
        return Response(
            _cert_response_data(cert_pem, key_pem, consumer_uuid),
            status=status.HTTP_201_CREATED if newly_registered else status.HTTP_200_OK,
        )
