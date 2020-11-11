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
from datetime import datetime
import collections
import copy
import io
import json
import logging
import re
import requests
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
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models import Host

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
    for f in z.filelist:
        if f.filename.startswith('export/entitlements') and f.filename.endswith('.json'):
            return json.loads(z.open(f).read())
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
        valid_key=False
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
        # Parse output for subscription metadata to build config
        license = dict()
        license['sku'] = manifest['pool']['productId']
        try:
            license['instance_count'] = manifest['pool']['exported']
        except KeyError:
            license['instance_count'] = manifest['pool']['quantity']
        license['subscription_name'] = manifest['pool']['productName']
        license['pool_id'] = manifest['pool']['id']
        license['license_date'] = parse_date(manifest['endDate']).strftime('%s')
        license['product_name'] = manifest['pool']['productName']
        license['valid_key'] = True
        license['license_type'] = 'enterprise'
        license['satellite'] = False

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


    def validate_rh(self, user, pw):
        try:
            host = 'https://' + str(self.config.get("server", "hostname"))
        except Exception:
            logger.exception('Cannot access rhsm.conf, make sure subscription manager is installed and configured.')
            host = None
        if not host:
            host = getattr(settings, 'REDHAT_CANDLEPIN_HOST', None)
        
        if not user:
            raise ValueError('subscriptions_username is required')

        if not pw:
            raise ValueError('subscriptions_password is required')

        if host and user and pw:
            if 'subscription.rhsm.redhat.com' in host:
                json = self.get_rhsm_subs(host, user, pw)
            else:
                json = self.get_satellite_subs(host, user, pw)
            return self.generate_license_options_from_entitlements(json)
        return []


    def get_rhsm_subs(self, host, user, pw):
        verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', True)
        json = []
        try:
            subs = requests.get(
                '/'.join([host, 'subscription/users/{}/owners'.format(user)]),
                verify=verify,
                auth=(user, pw)
            )
        except requests.exceptions.ConnectionError as error:
            raise error
        except OSError as error:
            raise OSError('Unable to open certificate bundle {}. Check that Ansible Tower is running on Red Hat Enterprise Linux.'.format(verify)) from error # noqa
        subs.raise_for_status()

        for sub in subs.json():
            resp = requests.get(
                '/'.join([
                    host,
                    'subscription/owners/{}/pools/?match=*tower*'.format(sub['key'])
                ]),
                verify=verify,
                auth=(user, pw)
            )
            resp.raise_for_status()
            json.extend(resp.json())
        return json


    def get_satellite_subs(self, host, user, pw):
        try:
            verify = str(self.config.get("rhsm", "repo_ca_cert"))
        except Exception as e:
            logger.exception('Unable to read rhsm config to get ca_cert location. {}'.format(str(e)))
            verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', True)
        json = []
        try:
            orgs = requests.get(
                '/'.join([host, 'katello/api/organizations']),
                verify=verify,
                auth=(user, pw)
            )
        except requests.exceptions.ConnectionError as error:
            raise error
        except OSError as error:
            raise OSError('Unable to open certificate bundle {}. Check that Ansible Tower is running on Red Hat Enterprise Linux.'.format(verify)) from error # noqa
        orgs.raise_for_status()
        
        for org in orgs.json()['results']:
            resp = requests.get(
                '/'.join([
                    host,
                    '/katello/api/organizations/{}/subscriptions/?search=Red Hat Ansible Automation'.format(org['id'])
                ]),
                verify=verify,
                auth=(user, pw)
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
                    license['subscription_name'] = sub['name']
                    license['id'] = sub['upstream_pool_id']
                    license['endDate'] = sub['end_date']
                    license['productName'] = "Red Hat Ansible Automation"
                    license['valid_key'] = True
                    license['license_type'] = 'enterprise'
                    license['satellite'] = True
                    json.append(license)
        return json


    def is_appropriate_sat_sub(self, sub):
        if 'Red Hat Ansible Automation' not in sub['subscription_name']:
            return False
        return True


    def is_appropriate_sub(self, sub):
        if sub['activeSubscription'] is False:
            return False
        # Products that contain Ansible Tower
        products = sub.get('providedProducts', [])
        if any(map(lambda product: product.get('productId', None) == "480", products)):
            return True
        return False


    def generate_license_options_from_entitlements(self, json):
        from dateutil.parser import parse
        ValidSub = collections.namedtuple('ValidSub', 'sku name support_level end_date trial quantity pool_id satellite')
        valid_subs = []
        for sub in json:
            satellite = sub.get('satellite')
            if satellite:
                is_valid = self.is_appropriate_sat_sub(sub)
            else:
                is_valid = self.is_appropriate_sub(sub)
            if is_valid:
                try:
                    end_date = parse(sub.get('endDate'))
                except Exception:
                    continue
                now = datetime.utcnow()
                now = now.replace(tzinfo=end_date.tzinfo)
                if end_date < now:
                    # If the sub has a past end date, skip it
                    continue
                try:
                    quantity = int(sub['quantity'])
                    if quantity == -1:
                        # effectively, unlimited
                        quantity = MAX_INSTANCES
                except Exception:
                    continue

                sku = sub['productId']
                trial = sku.startswith('S')  # i.e.,, SER/SVC
                support_level = ''
                pool_id = sub['id']
                if satellite:
                    support_level = sub['support_level']
                else:
                    for attr in sub.get('productAttributes', []):
                        if attr.get('name') == 'support_level':
                            support_level = attr.get('value')

                valid_subs.append(ValidSub(
                    sku, sub['productName'], support_level, end_date, trial, quantity, pool_id, satellite
                ))

        if valid_subs:
            licenses = []
            for sub in valid_subs:
                license = self.__class__(subscription_name='Red Hat Ansible Automation Platform')
                license._attrs['instance_count'] = int(sub.quantity)
                license._attrs['sku'] = sub.sku
                license._attrs['support_level'] = sub.support_level
                license._attrs['license_type'] = 'enterprise'
                if sub.trial:
                    license._attrs['trial'] = True
                    license._attrs['license_type'] = 'trial'
                license._attrs['instance_count'] = min(
                    MAX_INSTANCES, license._attrs['instance_count']
                )
                human_instances = license._attrs['instance_count']
                if human_instances == MAX_INSTANCES:
                    human_instances = 'Unlimited'
                subscription_name = re.sub(
                    r' \([\d]+ Managed Nodes',
                    ' ({} Managed Nodes'.format(human_instances),
                    sub.name
                )
                license._attrs['subscription_name'] = subscription_name
                license._attrs['satellite'] = satellite
                license._attrs['valid_key'] = True
                license.update(
                    license_date=int(sub.end_date.strftime('%s'))
                )
                license.update(
                    pool_id=sub.pool_id
                )
                licenses.append(license._attrs.copy())
            return licenses

        raise ValueError(
            'No valid Red Hat Ansible Automation subscription could be found for this account.'  # noqa
        )


    def validate(self):
        # Return license attributes with additional validation info.
        attrs = copy.deepcopy(self._attrs)
        type = attrs.get('license_type', 'none')

        if (type == 'UNLICENSED' or False):
            attrs.update(dict(valid_key=False, compliant=False))
            return attrs
        attrs['valid_key'] = True

        if Host:
            current_instances = Host.objects.active_count()
        else:
            current_instances = 0
        available_instances = int(attrs.get('instance_count', None) or 0)
        attrs['current_instances'] = current_instances
        attrs['available_instances'] = available_instances
        free_instances = (available_instances - current_instances)
        attrs['free_instances'] = max(0, free_instances)

        license_date = int(attrs.get('license_date', 0) or 0)
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
