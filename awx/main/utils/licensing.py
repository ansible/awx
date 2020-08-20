# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

'''
This is intended to be a lightweight license class for verifying subscriptions, and parsing subscription data
from entitlement certificates.

The Licenser class can do the following:
 - Parse an Entitlement cert to generate license
'''


MAX_INSTANCES = 9999999

from datetime import datetime, timedelta
import os
import collections
import copy
import hashlib
import time
import tempfile
import logging
import subprocess
import re
import tracemalloc

from django.conf import settings
from django.utils.encoding import smart_text, smart_bytes

from awx.main.models import Host

logger = logging.getLogger(__name__)


class Licenser(object):
    # warn when there is a month (30 days) left on the license
    LICENSE_TIMEOUT = 60 * 60 * 24 * 30

    def __init__(self, **kwargs):
        self._attrs = dict(
            instance_count=0,
            license_date=0,
            license_type='UNLICENSED',
        )
        if not kwargs:
            kwargs = getattr(settings, 'LICENSE', None) or {}
        if 'company_name' in kwargs:
            kwargs.pop('company_name')
        
        self._attrs.update(kwargs)
        self._attrs['license_date'] = int(self._attrs['license_date'])
        if self._check_product_cert():
            self._generate_product_config()
        else:
            self._generate_open_config()


    def _check_product_cert(self):
        if os.path.exists('/etc/tower/certs') and os.path.exists('/var/lib/awx/.tower_version'):
            return True
        return False
        # Product Cert Name: ansible-tower-3.7-rhel-7.x86_64.pem
        # Maybe check validity of Product Cert somehow?


    def _generate_open_config(self):
        self._attrs.update(dict(license_type='open',
            valid_key=True,
            subscription_name='OPEN'
            ))


    def _generate_product_config(self):

        # Catch/check if subman is installed
        try:
            
            raw_cert = getattr(settings, 'ENTITLEMENT_CERT')
            parsed_cert = raw_cert.split('\n')
            
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as f:
                for line in parsed_cert:
                    f.write(line + '\n')


                cmd = ["rct", "cat-cert", f.name, "--no-content"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                output = re.split('\n\n|\n\t', smart_text(stdout))
                cert_dict = dict()

                for line in output:
                    if ': ' in line:
                        key, value = line.split(': ')
                        cert_dict.update({key:value})

        except FileNotFoundError as e:
            logger.exception('Subscription-manager is not installed')
        except Exception as e:
            logger.exception(e)

        # # Keep existing license type
        # type = self._attrs.get('license_type')
        # if type == 'UNLICENSED':
        #     type = 'enterprise'
        
        type = 'enterprise'
        
        # import pdb; pdb.set_trace()
        # Parse output for subscription metadata to build config
        self._attrs.update(dict(subscription_name=cert_dict.get('Name'),
                                sku=cert_dict.get('SKU', ''),
                                instance_count=cert_dict.get('Quantity', 0),
                                support_level=cert_dict.get('Service Level', ''),
                                # license_date=cert_dict.get('End Date', 2524626011), # Need to convert to seconds
                                valid_key=True,
                                license_type=type
                                ))
        settings.LICENSE = self._attrs

    # # TODO: Revisit Cloudforms license code and make sure this works for the CF team
    # def _generate_cloudforms_subscription(self):
    #     self._attrs.update(dict(company_name="Red Hat CloudForms License",
    #                             instance_count=MAX_INSTANCES,
    #                             license_date=253370764800,
    #                             license_key='xxxx',
    #                             license_type='enterprise',
    #                             subscription_name='Red Hat CloudForms License'))
    #
    # def _check_cloudforms_subscription(self):
    #     if os.path.exists('/var/lib/awx/i18n.db'):
    #         return True
    #     if os.path.isdir("/opt/rh/cfme-appliance") and os.path.isdir("/opt/rh/cfme-gemset"):
    #         try:
    #             has_rpms = subprocess.call(["rpm", "--quiet", "-q", "cfme", "cfme-appliance", "cfme-gemset"])
    #             if has_rpms == 0:
    #                 return True
    #         except OSError:
    #             pass
    #     return False

    # def _generate_subscription_name(self):
    #     name_parts = ['Ansible Tower by Red Hat', ' (%d Managed Nodes)' % int(self._attrs['instance_count'])]
    #     license_type = self._attrs.get('license_type', 'legacy')
    #     if license_type == 'legacy':
    #         name_parts.insert(1, ', Legacy')
    #     elif license_type == 'basic':
    #         name_parts.insert(1, ', Self-Support')
    #     elif license_type == 'enterprise':
    #         name_parts.insert(1, ', Standard')
    #     if self._attrs.get('trial', False):
    #         name_parts.append(' Trial')
    #     return ''.join(name_parts)

    def update(self, **kwargs):
        # Update attributes of the current license.
        if 'instance_count' in kwargs:
            kwargs['instance_count'] = int(kwargs['instance_count'])
        if 'license_date' in kwargs:
            kwargs['license_date'] = int(kwargs['license_date'])
        self._attrs.update(kwargs)

    def validate_rh(self, user, pw):
        host = getattr(settings, 'REDHAT_CANDLEPIN_HOST', None)

        if not user:
            raise ValueError('rh_username is required')

        if not pw:
            raise ValueError('rh_password is required')

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
                raise OSError('Unable to open certificate bundle {}. Check that Ansible Tower is running on Red Hat Enterprise Linux.'.format(verify)) from error
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
        # Legacy: products that claim they are Ansible Tower
        attributes = sub.get('productAttributes', [])
        if any(map(lambda attr: attr.get('name') == 'ph_product_name' and attr.get('value').startswith('Ansible Tower'), attributes)): # noqa
            return True
        return False

    def generate_license_options_from_entitlements(self, json):
        from dateutil.parser import parse

        ValidSub = collections.namedtuple('ValidSub', 'sku name end_date trial quantity')

        valid_subs = collections.OrderedDict()
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
                for attr in sub.get('productAttributes', []):
                    if attr.get('name') == 'support_level':
                        support_level = attr.get('value')

                sub_key = (end_date.date(), support_level)
                valid_subs.setdefault(sub_key, []).append(ValidSub(
                    sku, sub['productName'], end_date, trial, quantity
                ))

        if valid_subs:
            licenses = []
            for key, subs in valid_subs.items():
                license = self.__class__(subscription_name='Ansible Tower by Red Hat')
                for sub in subs:
                    license._attrs['instance_count'] += sub.quantity
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
                    license_date=sub.end_date.strftime('%s')
                )
                licenses.append(license._attrs.copy())
            return licenses

        raise ValueError(
            'No valid Red Hat Ansible Automation subscription could be found for this account.'  # noqa
        )

    # TODO: Make this work for x509 Certs
    def validate(self):
        # Return license attributes with additional validation info.
        attrs = copy.deepcopy(self._attrs)
        key = attrs.get('license_type', 'none')

        # Use requests to attempt a GET to the CDN/Satellite content repo
        repo_response = False  #if 403, make this True

        if (key == 'UNLICENSED' or False): # TODO: add logic to check against the CDN here.
            attrs.update(dict(valid_key=False, compliant=False))
            return attrs
        attrs['valid_key'] = True
        attrs['deployment_id'] = hashlib.sha1(smart_bytes(key)).hexdigest()

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
