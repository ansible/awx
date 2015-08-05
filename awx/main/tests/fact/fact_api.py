# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import unittest2 as unittest

# Django
from django.core.urlresolvers import reverse

# AWX
from awx.main.utils import timestamp_apiformat
from awx.main.models import * # noqa
from awx.main.tests.base import BaseLiveServerTest
from awx.fact.models import * # noqa
from awx.fact.tests.base import BaseFactTestMixin, FactScanBuilder, TEST_FACT_ANSIBLE, TEST_FACT_PACKAGES, TEST_FACT_SERVICES
from awx.main.utils import build_url

__all__ = ['FactVersionApiTest', 'FactViewApiTest', 'SingleFactApiTest',]

class FactApiBaseTest(BaseLiveServerTest, BaseFactTestMixin):
    def setUp(self):
        super(FactApiBaseTest, self).setUp()
        self.create_test_license_file()
        self.setup_instances()
        self.setup_users()
        self.organization = self.make_organization(self.super_django_user)
        self.organization.admins.add(self.normal_django_user)
        self.inventory = self.organization.inventories.create(name='test-inventory', description='description for test-inventory')
        self.host = self.inventory.hosts.create(name='host.example.com')
        self.host2 = self.inventory.hosts.create(name='host2.example.com')
        self.host3 = self.inventory.hosts.create(name='host3.example.com')

    def setup_facts(self, scan_count):
        self.builder = FactScanBuilder()
        self.builder.set_inventory_id(self.inventory.pk)
        self.builder.add_fact('ansible', TEST_FACT_ANSIBLE)
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.add_fact('services', TEST_FACT_SERVICES)
        self.builder.add_hostname('host.example.com')
        self.builder.add_hostname('host2.example.com')
        self.builder.add_hostname('host3.example.com')
        self.builder.build(scan_count=scan_count, host_count=3)

        self.fact_host = FactHost.objects.get(hostname=self.host.name)

class FactVersionApiTest(FactApiBaseTest):
    def check_equal(self, fact_versions, results):
        def find(element, set1):
            for e in set1:
                if all([ e.get(field) == element.get(field) for field in element.keys()]):
                    return e
            return None

        self.assertEqual(len(results), len(fact_versions))
        for v in fact_versions:
            v_dict = {
                'timestamp': timestamp_apiformat(v.timestamp),
                'module': v.module
            }
            e = find(v_dict, results)
            self.assertIsNotNone(e, "%s not found in %s" % (v_dict, results))

    def get_list(self, fact_versions, params=None):
        url = build_url('api:host_fact_versions_list', args=(self.host.pk,), get=params)
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)

        self.check_equal(fact_versions, response['results'])
        return response

    def test_permission_list(self):
        url = reverse('api:host_fact_versions_list', args=(self.host.pk,))
        with self.current_user('admin'):
            self.get(url, expect=200)
        with self.current_user('normal'):
            self.get(url, expect=200)
        with self.current_user('other'):
            self.get(url, expect=403)
        with self.current_user('nobody'):
            self.get(url, expect=403)
        with self.current_user(None):
            self.get(url, expect=401)

    def test_list_empty(self):
        url = reverse('api:host_fact_versions_list', args=(self.host.pk,))
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
            self.assertIn('results', response)
            self.assertIsInstance(response['results'], list)
            self.assertEqual(len(response['results']), 0)

    def test_list_related_fact_view(self):
        self.setup_facts(2)
        url = reverse('api:host_fact_versions_list', args=(self.host.pk,))
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
            for entry in response['results']:
                self.assertIn('fact_view', entry['related'])
                self.get(entry['related']['fact_view'], expect=200)

    def test_list(self):
        self.setup_facts(2)
        self.get_list(FactVersion.objects.filter(host=self.fact_host))

    def test_list_module(self):
        self.setup_facts(10)
        self.get_list(FactVersion.objects.filter(host=self.fact_host, module='packages'), dict(module='packages'))

    def test_list_time_from(self):
        self.setup_facts(10)

        params = {
            'from': timestamp_apiformat(self.builder.get_timestamp(1)),
        }
        #    'to': timestamp_apiformat(self.builder.get_timestamp(3))
        fact_versions = FactVersion.objects.filter(host=self.fact_host, timestamp__gt=params['from'])
        self.get_list(fact_versions, params)

    def test_list_time_to(self):
        self.setup_facts(10)

        params = {
            'to': timestamp_apiformat(self.builder.get_timestamp(3))
        }
        fact_versions = FactVersion.objects.filter(host=self.fact_host, timestamp__lte=params['to'])
        self.get_list(fact_versions, params)

    def test_list_time_from_to(self):
        self.setup_facts(10)

        params = {
            'from': timestamp_apiformat(self.builder.get_timestamp(1)),
            'to': timestamp_apiformat(self.builder.get_timestamp(3))
        }
        fact_versions = FactVersion.objects.filter(host=self.fact_host, timestamp__gt=params['from'], timestamp__lte=params['to'])
        self.get_list(fact_versions, params)


class FactViewApiTest(FactApiBaseTest):
    def check_equal(self, fact_obj, results):
        fact_dict = {
            'timestamp': timestamp_apiformat(fact_obj.timestamp),
            'module': fact_obj.module,
            'host': {
                'hostname': fact_obj.host.hostname,
                'inventory_id': fact_obj.host.inventory_id,
                'id': str(fact_obj.host.id)
            },
            'fact': fact_obj.fact
        }
        self.assertEqual(fact_dict, results)

    def test_permission_view(self):
        url = reverse('api:host_fact_compare_view', args=(self.host.pk,))
        with self.current_user('admin'):
            self.get(url, expect=200)
        with self.current_user('normal'):
            self.get(url, expect=200)
        with self.current_user('other'):
            self.get(url, expect=403)
        with self.current_user('nobody'):
            self.get(url, expect=403)
        with self.current_user(None):
            self.get(url, expect=401)

    def get_fact(self, fact_obj, params=None):
        url = build_url('api:host_fact_compare_view', args=(self.host.pk,), get=params)
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)

        self.check_equal(fact_obj, response)

    def test_view(self):
        self.setup_facts(2)
        self.get_fact(Fact.objects.filter(host=self.fact_host, module='ansible').order_by('-timestamp')[0])

    def test_view_module_filter(self):
        self.setup_facts(2)
        self.get_fact(Fact.objects.filter(host=self.fact_host, module='services').order_by('-timestamp')[0], dict(module='services'))

    def test_view_time_filter(self):
        self.setup_facts(6)
        ts = self.builder.get_timestamp(3)
        self.get_fact(Fact.objects.filter(host=self.fact_host, module='ansible', timestamp__lte=ts).order_by('-timestamp')[0], 
                      dict(datetime=ts))


@unittest.skip("single fact query needs to be updated to use inventory_id attribute on host document")
class SingleFactApiTest(FactApiBaseTest):
    def setUp(self):
        super(SingleFactApiTest, self).setUp()

        self.group = self.inventory.groups.create(name='test-group')
        self.group.hosts.add(self.host, self.host2, self.host3)

    def test_permission_list(self):
        url = reverse('api:host_fact_versions_list', args=(self.host.pk,))
        with self.current_user('admin'):
            self.get(url, expect=200)
        with self.current_user('normal'):
            self.get(url, expect=200)
        with self.current_user('other'):
            self.get(url, expect=403)
        with self.current_user('nobody'):
            self.get(url, expect=403)
        with self.current_user(None):
            self.get(url, expect=401)

    def _test_related(self, url):
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
            self.assertTrue(len(response['results']) > 0)
            for entry in response['results']:
                self.assertIn('single_fact', entry['related'])
                # Requires fields
                self.get(entry['related']['single_fact'], expect=400)

    def test_related_host_list(self):
        self.setup_facts(2)
        self._test_related(reverse('api:host_list'))

    def test_related_group_list(self):
        self.setup_facts(2)
        self._test_related(reverse('api:group_list'))

    def test_related_inventory_list(self):
        self.setup_facts(2)
        self._test_related(reverse('api:inventory_list'))

    def test_params(self):
        self.setup_facts(2)
        params = {
            'module': 'packages',
            'fact_key': 'name',
            'fact_value': 'acpid',
        }
        url = build_url('api:inventory_single_fact_view', args=(self.inventory.pk,), get=params)
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
            self.assertEqual(len(response['results']), 3)
            for entry in response['results']:
                self.assertEqual(entry['fact'][0]['name'], 'acpid')
