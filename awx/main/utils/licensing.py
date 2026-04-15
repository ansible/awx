# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

'''
This is intended to be a lightweight license class for verifying subscriptions, and parsing subscription data
from entitlement certificates.

The Licenser class can do the following:
 - Parse an Entitlement cert to generate license
'''

import base64
import configparser
from django.db import connection
from datetime import datetime, timezone
import collections
import copy
import io
import json
import logging
import os
import re
import requests
import tempfile
import time
import zipfile

from dateutil.parser import parse as parse_date

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509

# Django
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Shared code for the AWX platform
from awx_plugins.interfaces._temporary_private_licensing_api import detect_server_product_name

from awx.main.constants import SUBSCRIPTION_USAGE_MODEL_UNIQUE_HOSTS
from awx.main.utils.analytics_proxy import OIDCClient
from awx.main.utils.candlepin.client import CandlepinClient
from awx.main.utils.candlepin.lifecycle import (
    get_candlepin_ca,
    get_candlepin_url,
    get_proxy_url,
    get_renewal_days,
    parse_cert,
    run_candlepin_lifecycle,
)

MAX_INSTANCES = 9999999

logger = logging.getLogger(__name__)


def rhsm_config():
    path = '/etc/rhsm/rhsm.conf'
    config = configparser.ConfigParser()
    config.read(path)
    return config


def validate_entitlement_manifest(data):
    buff = io.BytesIO()
    buff.write(base64.b64decode(data))
    try:
        z = zipfile.ZipFile(buff)
    except zipfile.BadZipFile as e:
        raise ValueError(_("Invalid manifest: a subscription manifest zip file is required.")) from e
    buff = io.BytesIO()

    files = z.namelist()
    if 'consumer_export.zip' not in files or 'signature' not in files:
        raise ValueError(_("Invalid manifest: missing required files."))
    export = z.open('consumer_export.zip').read()
    sig = z.open('signature').read()
    with open('/etc/tower/candlepin-redhat-ca.crt', 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())
        key = cert.public_key()
    try:
        key.verify(sig, export, padding=padding.PKCS1v15(), algorithm=hashes.SHA256())
    except InvalidSignature as e:
        raise ValueError(_("Invalid manifest: signature verification failed.")) from e

    buff.write(export)
    z = zipfile.ZipFile(buff)
    subs = []
    for f in z.filelist:
        if f.filename.startswith('export/entitlements') and f.filename.endswith('.json'):
            subs.append(json.loads(z.open(f).read()))
    if subs:
        return subs
    raise ValueError(_("Invalid manifest: manifest contains no subscriptions."))


class OpenLicense(object):
    def validate(self):
        return dict(
            license_type='open',
            valid_key=True,
            subscription_name='OPEN',
            product_name="AWX",
        )


class Licenser(object):
    # warn when there is a month (30 days) left on the subscription
    SUBSCRIPTION_TIMEOUT = 60 * 60 * 24 * 30

    UNLICENSED_DATA = dict(
        subscription_name=None,
        sku=None,
        support_level=None,
        instance_count=0,
        license_date=0,
        license_type="UNLICENSED",
        product_name="Red Hat Ansible Automation Platform",
        valid_key=False,
    )

    def __init__(self, **kwargs):
        self._attrs = dict(
            instance_count=0,
            license_date=0,
            license_type='UNLICENSED',
        )
        self.config = rhsm_config()
        if not kwargs:
            license_setting = getattr(settings, 'LICENSE', None)
            if license_setting is not None:
                kwargs = license_setting

        if 'company_name' in kwargs:
            kwargs.pop('company_name')
        self._attrs.update(kwargs)
        if 'valid_key' in self._attrs:
            if not self._attrs['valid_key']:
                self._unset_attrs()
        else:
            self._unset_attrs()

    def _unset_attrs(self):
        self._attrs = self.UNLICENSED_DATA.copy()

    def license_from_manifest(self, manifest):
        def is_appropriate_manifest_sub(sub):
            if sub['pool']['activeSubscription'] is False:
                return False
            now = datetime.now(timezone.utc)
            if parse_date(sub['startDate']) > now:
                return False
            if parse_date(sub['endDate']) < now:
                return False
            products = sub['pool']['providedProducts']
            if any(product.get('productId') == '480' for product in products):
                return True
            return False

        def _can_aggregate(sub, license):
            # We aggregate multiple subs into a larger meta-sub, if they match
            #
            # No current sub in aggregate
            if not license:
                return True
            # Same SKU type (SER vs MCT vs others)?
            if license['sku'][0:3] != sub['pool']['productId'][0:3]:
                return False
            return True

        # Parse output for subscription metadata to build config
        license = dict()
        for sub in manifest:
            if not is_appropriate_manifest_sub(sub):
                logger.warning("Subscription %s (%s) in manifest is not active or for another product" % (sub['pool']['productName'], sub['pool']['productId']))
                continue
            if not _can_aggregate(sub, license):
                logger.warning(
                    "Subscription %s (%s) in manifest does not match other manifest subscriptions" % (sub['pool']['productName'], sub['pool']['productId'])
                )
                continue

            license.setdefault('sku', sub['pool']['productId'])
            license.setdefault('subscription_name', sub['pool']['productName'])
            license.setdefault('subscription_id', sub['pool']['subscriptionId'])
            license.setdefault('account_number', sub['pool']['accountNumber'])
            license.setdefault('pool_id', sub['pool']['id'])
            license.setdefault('product_name', sub['pool']['productName'])
            license.setdefault('valid_key', True)
            if sub['pool']['productId'].startswith('S'):
                license.setdefault('trial', True)
                license.setdefault('license_type', 'trial')
            else:
                license.setdefault('trial', False)
                license.setdefault('license_type', 'enterprise')
            license.setdefault('satellite', False)
            # Use the nearest end date
            endDate = parse_date(sub['endDate'])
            currentEndDateStr = license.get('license_date', '4102462800')  # 2100-01-01
            currentEndDate = datetime.fromtimestamp(int(currentEndDateStr), timezone.utc)
            if endDate < currentEndDate:
                license['license_date'] = endDate.strftime('%s')
            instances = sub['quantity']
            license['instance_count'] = license.get('instance_count', 0) + instances
            license['subscription_name'] = re.sub(r'[\d]* Managed Nodes', '%d Managed Nodes' % license['instance_count'], license['subscription_name'])

            license['support_level'] = ''
            license['usage'] = ''
            for attr in sub['pool'].get('productAttributes', []):
                if attr.get('name') == 'support_level':
                    license['support_level'] = attr.get('value')
                elif attr.get('name') == 'usage':
                    license['usage'] = attr.get('value')
                elif attr.get('name') == 'ph_product_name' and attr.get('value') == 'RHEL Developer':
                    license['license_type'] = 'developer'

        if not license:
            logger.error("No valid subscriptions found in manifest")
        self._attrs.update(license)
        settings.LICENSE = self._attrs
        return self._attrs

    def update(self, **kwargs):
        # Update attributes of the current license.
        if 'instance_count' in kwargs:
            kwargs['instance_count'] = int(kwargs['instance_count'])
        if 'license_date' in kwargs:
            kwargs['license_date'] = int(kwargs['license_date'])
        self._attrs.update(kwargs)

    def get_host_from_rhsm_config(self):
        try:
            host = 'https://' + str(self.config.get("server", "hostname"))
        except Exception:
            logger.exception('Cannot access rhsm.conf, make sure subscription manager is installed and configured.')
            host = None
        return host

    def validate_rh(self, user, pw, basic_auth):
        # if basic auth is True, host is read from rhsm.conf (subscription.rhsm.redhat.com)
        # if basic auth is False, host is settings.SUBSCRIPTIONS_RHSM_URL (console.redhat.com)
        # if rhsm.conf is not found, host is settings.REDHAT_CANDLEPIN_HOST (satellite server)
        if basic_auth:
            host = self.get_host_from_rhsm_config()
            if not host:
                host = getattr(settings, 'REDHAT_CANDLEPIN_HOST', None)
        else:
            host = settings.SUBSCRIPTIONS_RHSM_URL

        if not host:
            raise ValueError('Could not get host url for subscriptions')

        if not user:
            raise ValueError('subscriptions_client_id or subscriptions_username is required')

        if not pw:
            raise ValueError('subscriptions_client_secret or subscriptions_password is required')

        if host and user and pw:
            if basic_auth:
                if 'subscription.rhsm.redhat.com' in host:
                    json = self.get_rhsm_subs(host, user, pw)
                else:
                    json = self.get_satellite_subs(host, user, pw)
            else:
                json = self.get_crc_subs(host, user, pw)
            return self.generate_license_options_from_entitlements(json, is_candlepin=basic_auth)
        return []

    def get_rhsm_subs(self, host, user, pw):
        verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', True)
        json = []
        try:
            subs = requests.get('/'.join([host, 'subscription/users/{}/owners'.format(user)]), verify=verify, auth=(user, pw))
        except requests.exceptions.ConnectionError as error:
            raise error
        except OSError as error:
            raise OSError(
                'Unable to open certificate bundle {}. Check that the service is running on Red Hat Enterprise Linux.'.format(verify)
            ) from error  # noqa
        subs.raise_for_status()

        for sub in subs.json():
            resp = requests.get('/'.join([host, 'subscription/owners/{}/pools/?match=*tower*'.format(sub['key'])]), verify=verify, auth=(user, pw))
            resp.raise_for_status()
            json.extend(resp.json())
        return json

    def get_crc_subs(self, host, client_id, client_secret):
        try:
            client = OIDCClient(client_id, client_secret)
            subs = client.make_request(
                'GET',
                host,
                verify=True,
                timeout=(31, 31),
            )
        except requests.RequestException:
            logger.warning("Failed to connect to console.redhat.com using Service Account credentials. Falling back to basic auth.")
            subs = requests.request(
                'GET',
                host,
                auth=(client_id, client_secret),
                verify=True,
                timeout=(31, 31),
            )
        subs.raise_for_status()
        subs_formatted = []
        for sku in subs.json()['body']:
            sku_data = {k: v for k, v in sku.items() if k != 'subscriptions'}
            for sub in sku['subscriptions']:
                sub_data = sku_data.copy()
                sub_data['subscriptions'] = sub
                subs_formatted.append(sub_data)

        return subs_formatted

    def get_satellite_subs(self, host, user, pw):
        port = None
        try:
            verify = str(self.config.get("rhsm", "repo_ca_cert"))
            port = str(self.config.get("server", "port"))
        except Exception as e:
            logger.exception('Unable to read rhsm config to get ca_cert location. {}'.format(str(e)))
            verify = True
        if port:
            host = ':'.join([host, port])
        json = []
        try:
            orgs = requests.get('/'.join([host, 'katello/api/organizations']), verify=verify, auth=(user, pw))
        except requests.exceptions.ConnectionError as error:
            raise error
        except OSError as error:
            raise OSError(
                'Unable to open certificate bundle {}. Check that the service is running on Red Hat Enterprise Linux.'.format(verify)
            ) from error  # noqa
        orgs.raise_for_status()

        for org in orgs.json()['results']:
            resp = requests.get(
                '/'.join([host, '/katello/api/organizations/{}/subscriptions/?search=Red Hat Ansible Automation'.format(org['id'])]),
                verify=verify,
                auth=(user, pw),
            )
            resp.raise_for_status()
            results = resp.json()['results']
            if results != []:
                for sub in results:
                    # Parse output for subscription metadata to build config
                    license = dict()
                    license['productId'] = sub['product_id']
                    license['quantity'] = int(sub['quantity'])
                    license['support_level'] = sub['support_level']
                    license['usage'] = sub.get('usage')
                    license['subscription_name'] = sub['name']
                    license['subscriptionId'] = sub['subscription_id']
                    license['accountNumber'] = sub['account_number']
                    license['id'] = sub['upstream_pool_id']
                    license['endDate'] = sub['end_date']
                    license['productName'] = "Red Hat Ansible Automation"
                    license['valid_key'] = True
                    license['license_type'] = 'enterprise'
                    license['satellite'] = True
                    json.append(license)
        return json

    def is_appropriate_sub(self, sub):
        if sub['activeSubscription'] is False:
            return False
        # Products that contain Ansible Tower
        products = sub.get('providedProducts', [])
        if any(product.get('productId') == '480' for product in products):
            return True
        return False

    def is_appropriate_sat_sub(self, sub):
        if 'Red Hat Ansible Automation' not in sub['subscription_name']:
            return False
        return True

    def generate_license_options_from_entitlements(self, json, is_candlepin=False):
        from dateutil.parser import parse

        ValidSub = collections.namedtuple(
            'ValidSub', 'sku name support_level end_date trial developer_license quantity satellite subscription_id account_number usage'
        )
        valid_subs = []
        for sub in json:
            satellite = sub.get('satellite')
            if satellite:
                is_valid = self.is_appropriate_sat_sub(sub)
            elif is_candlepin:
                is_valid = self.is_appropriate_sub(sub)
            else:
                # the list of subs from console.redhat.com and subscriptions.rhsm.redhat.com are already valid based on the query params we provided
                is_valid = True
            if is_valid:
                try:
                    if is_candlepin:
                        end_date = parse(sub.get('endDate'))
                    else:
                        end_date = parse(sub['subscriptions']['endDate'])
                except Exception:
                    continue
                now = datetime.now(timezone.utc)
                now = now.replace(tzinfo=end_date.tzinfo)
                if end_date < now:
                    # If the sub has a past end date, skip it
                    continue

                developer_license = False
                support_level = sub.get('support_level', '')
                account_number = ''
                usage = sub.get('usage', '')
                if is_candlepin:
                    try:
                        quantity = int(sub['quantity'])
                    except Exception:
                        continue
                    sku = sub['productId']
                    subscription_id = sub['subscriptionId']
                    sub_name = sub['productName']
                    account_number = sub['accountNumber']
                else:
                    try:
                        # Determine total quantity based on capacity name
                        # if capacity name is Nodes, capacity quantity x subscription quantity
                        # if capacity name is Sockets, capacity quantity / 2 (minimum of 1) x subscription quantity
                        if sub['capacity']['name'] == "Nodes":
                            quantity = int(sub['capacity']['quantity']) * int(sub['subscriptions']['quantity'])
                        elif sub['capacity']['name'] == "Sockets":
                            quantity = max(int(sub['capacity']['quantity']) / 2, 1) * int(sub['subscriptions']['quantity'])
                        else:
                            continue
                    except Exception:
                        continue
                    sku = sub['sku']
                    sub_name = sub['name']
                    support_level = sub['serviceLevel']
                    subscription_id = sub['subscriptions']['number']
                    if sub.get('name') == 'RHEL Developer':
                        developer_license = True

                if quantity == -1:
                    # effectively, unlimited
                    quantity = MAX_INSTANCES
                trial = sku.startswith('S')  # i.e.,, SER/SVC

                valid_subs.append(
                    ValidSub(
                        sku,
                        sub_name,
                        support_level,
                        end_date,
                        trial,
                        developer_license,
                        quantity,
                        satellite,
                        subscription_id,
                        account_number,
                        usage,
                    )
                )

        if valid_subs:
            licenses = []
            for sub in valid_subs:
                license = self.__class__(subscription_name='Red Hat Ansible Automation Platform')
                license._attrs['instance_count'] = int(sub.quantity)
                license._attrs['sku'] = sub.sku
                license._attrs['support_level'] = sub.support_level
                license._attrs['usage'] = sub.usage
                license._attrs['license_type'] = 'enterprise'
                if sub.trial:
                    license._attrs['trial'] = True
                    license._attrs['license_type'] = 'trial'
                if sub.developer_license:
                    license._attrs['license_type'] = 'developer'
                license._attrs['instance_count'] = min(MAX_INSTANCES, license._attrs['instance_count'])
                human_instances = license._attrs['instance_count']
                if human_instances == MAX_INSTANCES:
                    human_instances = 'Unlimited'
                subscription_name = re.sub(r' \([\d]+ Managed Nodes', ' ({} Managed Nodes'.format(human_instances), sub.name)
                license._attrs['subscription_name'] = subscription_name
                license._attrs['satellite'] = satellite
                license._attrs['valid_key'] = True
                license.update(license_date=int(sub.end_date.strftime('%s')))
                license.update(subscription_id=sub.subscription_id)
                license.update(account_number=sub.account_number)
                licenses.append(license._attrs.copy())
            # sort by sku
            licenses.sort(key=lambda x: x['sku'])
            return licenses

        raise ValueError('No valid Red Hat Ansible Automation subscription could be found for this account.')  # noqa

    def validate(self):
        # Return license attributes with additional validation info.
        attrs = copy.deepcopy(self._attrs)
        type = attrs.get('license_type', 'none')

        if type == 'UNLICENSED' or False:
            attrs.update(dict(valid_key=False, compliant=False))
            return attrs
        attrs['valid_key'] = True

        from awx.main.models import Host, HostMetric, Instance

        current_instances = Host.objects.active_count()
        license_date = int(attrs.get('license_date', 0) or 0)

        subscription_model = getattr(settings, 'SUBSCRIPTION_USAGE_MODEL', '')
        if subscription_model == SUBSCRIPTION_USAGE_MODEL_UNIQUE_HOSTS:
            automated_instances = HostMetric.active_objects.count()
            first_host = HostMetric.active_objects.only('first_automation').order_by('first_automation').first()
            attrs['deleted_instances'] = HostMetric.objects.filter(deleted=True).count()
            attrs['reactivated_instances'] = HostMetric.active_objects.filter(deleted_counter__gte=1).count()
        else:
            automated_instances = 0
            first_host = HostMetric.objects.only('first_automation').order_by('first_automation').first()
            attrs['deleted_instances'] = 0
            attrs['reactivated_instances'] = 0

        if first_host:
            automated_since = int(first_host.first_automation.timestamp())
        else:
            try:
                automated_since = int(Instance.objects.order_by('id').first().created.timestamp())
            except AttributeError:
                # In the odd scenario that create_preload_data was not run, there are no hosts
                # Then we CAN end up here before any instance has registered
                automated_since = int(time.time())
        instance_count = int(attrs.get('instance_count', 0))
        attrs['current_instances'] = current_instances
        attrs['automated_instances'] = automated_instances
        attrs['automated_since'] = automated_since
        free_instances = instance_count - automated_instances
        attrs['free_instances'] = max(0, free_instances)

        current_date = int(time.time())
        time_remaining = license_date - current_date
        attrs['time_remaining'] = time_remaining
        if attrs.setdefault('trial', False):
            attrs['grace_period_remaining'] = time_remaining
        else:
            attrs['grace_period_remaining'] = (license_date + 2592000) - current_date
        attrs['compliant'] = bool(time_remaining > 0 and free_instances >= 0)
        attrs['date_warning'] = bool(time_remaining < self.SUBSCRIPTION_TIMEOUT)
        attrs['date_expired'] = bool(time_remaining <= 0)
        return attrs


def get_licenser(*args, **kwargs):
    from awx.main.utils.licensing import Licenser, OpenLicense

    try:
        if detect_server_product_name() == 'AWX':
            return OpenLicense()
        else:
            return Licenser(*args, **kwargs)
    except Exception as e:
        raise ValueError(_('Error importing License: %s') % e)


# ---------------------------------------------------------------------------
# Candlepin Integration for mTLS Authentication
# ---------------------------------------------------------------------------

# Placeholder UUID used before a real consumer is registered.
# Treat it the same as an absent UUID so we never attempt a Candlepin
# lifecycle call with a non-functional consumer identity.
CANDLEPIN_CERT_SETTING_KEY = 'CANDLEPIN_CONSUMER_CERT'
CANDLEPIN_KEY_SETTING_KEY = 'CANDLEPIN_CONSUMER_KEY'
CANDLEPIN_UUID_SETTING_KEY = 'CANDLEPIN_CONSUMER_UUID'
CANDLEPIN_UUID_PLACEHOLDER = '00000000-0000-0000-0000-000000000000'
SUBSCRIPTIONS_USERNAME_SETTING_KEY = 'SUBSCRIPTIONS_USERNAME'
SUBSCRIPTIONS_PASSWORD_SETTING_KEY = 'SUBSCRIPTIONS_PASSWORD'


def _fetch_candlepin_cert_from_db():
    """Read cert PEM, key PEM, and consumer UUID from CandlepinCertificate model.

    Returns (cert_pem, key_pem, consumer_uuid), any of which may be None if the
    model instance doesn't exist or has no valid data. Best-effort: failures are
    logged as warnings and never propagate.
    """
    from awx.main.models import CandlepinCertificate

    try:
        instance = CandlepinCertificate.get_instance()
        if not instance or not instance.has_valid_data():
            return None, None, None

        return instance.cert_pem, instance.key_pem, instance.consumer_uuid
    except Exception as e:
        logger.warning(f'Could not fetch Candlepin lifecycle data from DB: {e}')
        return None, None, None


def _save_candlepin_cert_to_db(cert_pem, key_pem):
    """Persist a renewed Candlepin identity cert and key to the CandlepinCertificate model.

    Updates the existing instance if present, creates a new one if needed.
    Best-effort: failures are logged as errors but never propagate.
    """
    from awx.main.models import CandlepinCertificate

    try:
        # Get or create the instance
        instance = CandlepinCertificate.get_or_create_instance()

        # Parse certificate to extract metadata
        try:
            cert_info = parse_cert(cert_pem)
            serial_number = cert_info.get('serial', '')
            from datetime import datetime
            expires_at = datetime.fromisoformat(cert_info['not_after']) if cert_info.get('not_after') else None
        except Exception as e:
            logger.warning(f'Could not parse certificate metadata: {e}')
            serial_number = ''
            expires_at = None

        # Update the certificate data
        instance.update_certificate(
            cert_pem=cert_pem,
            key_pem=key_pem,
            serial_number=serial_number,
            expires_at=expires_at,
        )
        logger.info('Renewed Candlepin cert and key saved to database.')
    except Exception as e:
        logger.error(f'Could not save renewed Candlepin cert to database: {e}')


def _fetch_registration_credentials_from_db():
    """Read Candlepin registration credentials from AWX settings.

    Reads SUBSCRIPTIONS_USERNAME, SUBSCRIPTIONS_PASSWORD (set by AWX when the
    customer configures their Red Hat subscription), LICENSE.account_number (org
    key for the Candlepin /consumers endpoint), and INSTALL_UUID (used as the
    consumer's aap.instance_uuid fact).

    Returns (username, password, org, install_uuid), any of which may be None
    if the corresponding row is absent or on any DB error.  Best-effort: failures
    are logged as warnings and never propagate.
    """
    keys = ['SUBSCRIPTIONS_USERNAME', 'SUBSCRIPTIONS_PASSWORD', 'LICENSE', 'INSTALL_UUID']
    try:
        placeholders = ', '.join(['%s'] * len(keys))
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT key, value FROM conf_setting WHERE key IN ({placeholders})',
                keys,
            )
            rows = {key: json.loads(value) for key, value in cursor.fetchall() if value}

        license_data = rows.get('LICENSE', {})
        org = license_data.get('account_number') if isinstance(license_data, dict) else None
        return (
            rows.get(SUBSCRIPTIONS_USERNAME_SETTING_KEY),
            rows.get(SUBSCRIPTIONS_PASSWORD_SETTING_KEY),
            org,
            rows.get('INSTALL_UUID'),
        )
    except Exception as e:
        logger.warning(f'Could not fetch Candlepin registration credentials from DB: {e}')
        return None, None, None, None


def _save_candlepin_registration_to_db(cert_pem, key_pem, consumer_uuid):
    """Persist a new Candlepin consumer registration (cert, key, UUID) to the CandlepinCertificate model.

    Updates the existing instance if present, creates a new one if needed.
    Best-effort: failures are logged as errors but never propagate.
    """
    from awx.main.models import CandlepinCertificate

    try:
        # Get or create the instance
        instance = CandlepinCertificate.get_or_create_instance()

        # Parse certificate to extract metadata
        try:
            cert_info = parse_cert(cert_pem)
            serial_number = cert_info.get('serial', '')
            from datetime import datetime
            expires_at = datetime.fromisoformat(cert_info['not_after']) if cert_info.get('not_after') else None
        except Exception as e:
            logger.warning(f'Could not parse certificate metadata: {e}')
            serial_number = ''
            expires_at = None

        # Update the certificate data with new consumer UUID
        instance.update_certificate(
            cert_pem=cert_pem,
            key_pem=key_pem,
            consumer_uuid=consumer_uuid,
            serial_number=serial_number,
            expires_at=expires_at,
        )
        logger.info(f'Candlepin consumer registration saved to database (uuid={consumer_uuid}).')
    except Exception as e:
        logger.error(f'Could not save Candlepin registration to database: {e}')


def _register_candlepin_consumer():
    """Register a new Candlepin consumer using credentials from AWX settings.

    Called when no identity cert exists in the DB.

    Reads SUBSCRIPTIONS_USERNAME / SUBSCRIPTIONS_PASSWORD and the org key from
    LICENSE.account_number, then calls POST /consumers on Candlepin to obtain an
    identity certificate.  On success the cert, key, and consumer UUID are
    persisted to the CandlepinCertificate model.

    Returns (cert_pem, key_pem, consumer_uuid) on success, (None, None, None) on
    any failure.  Best-effort: logs errors but never propagates.
    """
    username, password, org, install_uuid = _fetch_registration_credentials_from_db()

    if not username or not password:
        logger.warning(
            'Candlepin registration is enabled but SUBSCRIPTIONS_USERNAME / SUBSCRIPTIONS_PASSWORD '
            'are not set; skipping registration.'
        )
        return None, None, None

    if not org:
        logger.warning('Candlepin registration is enabled but LICENSE.account_number is not available; skipping registration.')
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

    _save_candlepin_registration_to_db(cert_pem, key_pem, consumer_uuid)
    return cert_pem, key_pem, consumer_uuid


def _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid):
    """Orchestrate Candlepin check-in and proactive cert renewal.

    Returns the (possibly renewed) (cert_pem, key_pem) tuple. If renewal fails, the
    original cert is returned so the caller can still attempt mTLS (which
    will then fall back to service-account auth via the existing SSLError
    handler).
    """
    if not consumer_uuid or consumer_uuid == CANDLEPIN_UUID_PLACEHOLDER:
        logger.warning(
            'Candlepin lifecycle is enabled but consumer UUID is not set '
            '(or still contains the placeholder value); '
            'skipping check-in and renewal.'
        )
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
            _save_candlepin_cert_to_db(new_cert_pem, new_key_pem)
        return new_cert_pem, new_key_pem
    except Exception as e:
        logger.error(f'Candlepin lifecycle (check-in / renewal) failed: {e}; will attempt mTLS with existing cert')
        return cert_pem, key_pem


def get_or_generate_candlepin_certificate(username, password):
    """
    Get or generate Candlepin certificate for analytics authentication.

    This function provides certificate-based authentication for analytics uploads.
    It will:
    1. Check for existing certificate in the CandlepinCertificate model
    2. If missing, attempt to register with Candlepin
    3. If exists, check for renewal needs
    4. Write cert/key to secure temporary files
    5. Return paths to temporary files

    Args:
        username: Red Hat subscription username (SUBSCRIPTIONS_USERNAME or REDHAT_USERNAME)
        password: Red Hat subscription password (SUBSCRIPTIONS_PASSWORD or REDHAT_PASSWORD)

    Returns:
        Tuple (cert_path, key_path) if certificate is available, (None, None) otherwise.
        The temporary files are created with secure permissions and should be cleaned up
        by the caller when no longer needed.

    Adapted from PR 16240's get_or_generate_client_certificate() but uses Django model
    instead of file-based storage.
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
    if consumer_uuid and consumer_uuid != CANDLEPIN_UUID_PLACEHOLDER:
        cert_pem, key_pem = _run_candlepin_lifecycle(cert_pem, key_pem, consumer_uuid)

    # Validate certificate is still usable
    from awx.main.utils.candlepin.lifecycle import is_cert_valid

    if not is_cert_valid(cert_pem):
        logger.warning('Candlepin certificate is not valid (expired or not yet valid)')
        return None, None

    # Write to secure temporary files for use with requests library
    try:
        # Create temp files with secure permissions
        cert_fd, cert_path = tempfile.mkstemp(prefix='candlepin_cert_', suffix='.pem')
        key_fd, key_path = tempfile.mkstemp(prefix='candlepin_key_', suffix='.pem')

        try:
            # Write cert
            with open(cert_fd, 'w', closefd=True) as f:
                f.write(cert_pem)
            os.chmod(cert_path, 0o644)  # Certificate can be world-readable

            # Write key
            with open(key_fd, 'w', closefd=True) as f:
                f.write(key_pem)
            os.chmod(key_path, 0o600)  # Private key: owner read+write only

            logger.debug(f'Candlepin certificate written to temporary files: {cert_path}, {key_path}')
            return cert_path, key_path

        except Exception as e:
            # Clean up on failure
            try:
                if os.path.exists(cert_path):
                    os.unlink(cert_path)
                if os.path.exists(key_path):
                    os.unlink(key_path)
            except Exception:
                pass
            raise e

    except Exception as e:
        logger.error(f'Failed to write Candlepin certificate to temporary files: {e}')
        return None, None
