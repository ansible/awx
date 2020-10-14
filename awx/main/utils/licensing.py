# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

'''
This is intended to be a lightweight license class for verifying subscriptions, and parsing subscription data
from entitlement certificates.

The Licenser class can do the following:
 - Parse an Entitlement cert to generate license
'''

from datetime import datetime
import os
import collections
import copy
import time
import tempfile
import logging
import subprocess
import re
import requests

from django.conf import settings
from awx.conf.models import Setting
from django.utils.encoding import smart_text

from awx.main.models import Host
from awx.main.utils import set_environ

from rhsm import certificate

MAX_INSTANCES = 9999999

logger = logging.getLogger(__name__)


def str_to_datetime(string):
    if not string:
        return 0
    t_parts = re.split('-| |:|\+', string) # noqa

    year = int(t_parts[0])
    month = int(t_parts[1])
    day = int(t_parts[2])
    hour = int(t_parts[3])
    minute = int(t_parts[4])
    second = int(t_parts[5])
    microsecond = int(t_parts[7])

    return datetime(year, month, day, hour, minute, second, microsecond)


class Licenser(object):
    # warn when there is a month (30 days) left on the license
    LICENSE_TIMEOUT = 60 * 60 * 24 * 30

    UNLICENSED_DATA = dict(
        subscription_name=None,
        sku=None,
        support_level=None,
        instance_count=0,
        license_date=0,
        license_type="UNLICENSED",
        product_name="Red Hat Ansible Tower",
        valid_key=False
    )

    def __init__(self, **kwargs):
        self._attrs = dict(
            instance_count=0,
            license_date=0,
            license_type='UNLICENSED',
        )
        if not kwargs:
            license_setting = Setting.objects.filter(key='LICENSE').first()
            if license_setting is not None:
                kwargs = license_setting.value

        if 'company_name' in kwargs:
            kwargs.pop('company_name')
        self._attrs.update(kwargs)
        if self._check_product_cert():
            if 'license_key' in self._attrs:
                self._attrs = self.UNLICENSED_DATA
            if 'valid_key' in self._attrs:
                if not self._attrs['valid_key']:
                    self._attrs = self.UNLICENSED_DATA
            else:
                self._attrs = self.UNLICENSED_DATA
        else:
            self._generate_open_config()


    def _check_product_cert(self):
        # Product Cert Name: ansible-tower-3.7-rhel-7.x86_64.pem
        # Maybe check validity of Product Cert somehow?
        if os.path.exists('/etc/tower/certs') and os.path.exists('/var/lib/awx/.tower_version'):
            return True
        return False


    def _generate_open_config(self):
        self._attrs.update(dict(license_type='open',
                                valid_key=True,
                                subscription_name='OPEN',
                                product_name="AWX",
                                ))
        settings.LICENSE = self._attrs


    def _clear_license_setting(self):
        self._attrs.update(self.UNLICENSED_DATA)
        settings.LICENSE = {}


    def _generate_product_config(self):
        raw_cert = getattr(settings, 'ENTITLEMENT_CERT', None)
        # Fail early if no entitlement cert is available
        if not raw_cert or raw_cert == '':
            self._clear_license_setting()
            return

        # Read certificate
        certinfo = certificate.create_from_pem(raw_cert)
        if not certinfo.is_valid():
            raise ValueError("Could not parse entitlement certificate")
        if certinfo.is_expired():
            raise ValueError("Certificate is expired")
        if not any(map(lambda x: x.id == '480', certinfo.products)):
            self._clear_license_setting()
            raise ValueError("Certificate is for another product")

        # Verify the entitlment cert is authorized to access appropriate content
        try:
            from rhsm.config import get_config_parser
            config = get_config_parser()
            base_url = config.get("rhsm", "baseurl")
        except ValueError:
            content_url = getattr(settings, 'REDHAT_CONTENT_URL', None)
            if content_url:
                base_url = content_url
        content_path = getattr(settings, 'REDHAT_CONTENT_PATH', None)
        verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', False)
        content_repo_url = '{0}{1}'.format(base_url, content_path)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f:
            f.write(raw_cert)
            # clear the buffer to ensure the complete cert has been written to the file
            f.flush()
            os.fsync(f)

            request = requests.get(url=content_repo_url,
                                   cert=f.name,
                                   verify=verify,
                                   # timeout=(5, 5)
                                   )
            if request.status_code != 200:
                logger.exception('Validation Error: Entitlement key not valid.  Ensure the correct key is present in the entitlement certificate.')
                return

        license_type = 'enterprise'

        # Parse output for subscription metadata to build config
        license = dict()
        license['sku'] = certinfo.order.sku
        license['instance_count'] = int(certinfo.order.quantity_used)
        license['support_level'] = certinfo.order.service_level
        license['subscription_name'] = certinfo.order.name
        license['pool_id'] = certinfo.pool.id
        license['license_date'] = certinfo.end.strftime('%s')
        license['product_name'] = certinfo.order.name
        license['valid_key'] = True
        license['license_type'] = license_type

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
        from rhsm.config import get_config_parser
        config = get_config_parser()
        host = 'https://' + str(config.get("server", "hostname"))
        if not host:
            host = getattr(settings, 'REDHAT_CANDLEPIN_HOST', None)
        
        if not user:
            raise ValueError('subscriptions_username is required')

        if not pw:
            raise ValueError('subscriptions_password is required')

        if host and user and pw:
            import requests
            verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', False)

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

            return self.generate_license_options_from_entitlements(json)
        return []


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
        ValidSub = collections.namedtuple('ValidSub', 'sku name end_date trial quantity pool_id')
        valid_subs = []
        for sub in json:
            if self.is_appropriate_sub(sub):
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
                for attr in sub.get('productAttributes', []):
                    if attr.get('name') == 'support_level':
                        support_level = attr.get('value')

                valid_subs.append(ValidSub(
                    sku, sub['productName'], end_date, trial, quantity, pool_id
                ))

        if valid_subs:
            licenses = []
            for sub in valid_subs:
                license = self.__class__(subscription_name='Ansible Tower by Red Hat')
                license._attrs['instance_count'] = int(sub.quantity)
                license._attrs['sku'] = sub.sku
                license._attrs['license_type'] = 'enterprise'
                if sub.trial:
                    license._attrs['trial'] = True
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


    def validate(self, new_cert=False):

        # Generate Config from Entitlement cert if it exists
        if new_cert:
            self._generate_product_config()

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
        attrs['free_instances'] = available_instances - current_instances

        license_date = int(attrs.get('license_date', None) or 0)
        current_date = int(time.time())
        time_remaining = license_date - current_date
        attrs['time_remaining'] = time_remaining
        if attrs.setdefault('trial', False):
            attrs['grace_period_remaining'] = time_remaining
        else:
            attrs['grace_period_remaining'] = (license_date + 2592000) - current_date
        attrs['compliant'] = bool(time_remaining > 0 and attrs['free_instances'] >= 0)
        attrs['date_warning'] = bool(time_remaining < self.LICENSE_TIMEOUT)
        attrs['date_expired'] = bool(time_remaining <= 0)
        return attrs
