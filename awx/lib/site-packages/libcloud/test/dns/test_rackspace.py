# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

import sys
import unittest

from libcloud.utils.py3 import httplib

from libcloud.common.types import LibcloudError
from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.dns.types import RecordDoesNotExistError
from libcloud.dns.drivers.rackspace import RackspaceUSDNSDriver
from libcloud.dns.drivers.rackspace import RackspaceUKDNSDriver

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test.secrets import DNS_PARAMS_RACKSPACE


class RackspaceUSTests(unittest.TestCase):
    klass = RackspaceUSDNSDriver
    endpoint_url = 'https://dns.api.rackspacecloud.com/v1.0/11111'

    def setUp(self):
        self.klass.connectionCls.conn_classes = (
            None, RackspaceMockHttp)
        RackspaceMockHttp.type = None
        self.driver = self.klass(*DNS_PARAMS_RACKSPACE)
        self.driver.connection.poll_interval = 0.0
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()

    def test_force_auth_token_kwargs(self):
        kwargs = {
            'ex_force_auth_token': 'some-auth-token',
            'ex_force_base_url': 'https://dns.api.rackspacecloud.com/v1.0/11111'
        }
        driver = self.klass(*DNS_PARAMS_RACKSPACE, **kwargs)
        driver.list_zones()

        self.assertEqual(kwargs['ex_force_auth_token'],
                         driver.connection.auth_token)
        self.assertEqual('/v1.0/11111',
                         driver.connection.request_path)

    def test_force_auth_url_kwargs(self):
        kwargs = {
            'ex_force_auth_version': '2.0',
            'ex_force_auth_url': 'https://identity.api.rackspace.com'
        }
        driver = self.klass(*DNS_PARAMS_RACKSPACE, **kwargs)

        self.assertEqual(kwargs['ex_force_auth_url'],
                         driver.connection._ex_force_auth_url)
        self.assertEqual(kwargs['ex_force_auth_version'],
                         driver.connection._auth_version)

    def test_gets_auth_2_0_endpoint(self):
        kwargs = {'ex_force_auth_version': '2.0_password'}
        driver = self.klass(*DNS_PARAMS_RACKSPACE, **kwargs)
        driver.connection._populate_hosts_and_request_paths()

        self.assertEquals(self.endpoint_url, driver.connection.get_endpoint())

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 8)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones_success(self):
        zones = self.driver.list_zones()

        self.assertEqual(len(zones), 6)
        self.assertEqual(zones[0].domain, 'foo4.bar.com')
        self.assertEqual(zones[0].extra['comment'], 'wazaaa')

    def test_list_zones_http_413(self):
        RackspaceMockHttp.type = '413'

        try:
            self.driver.list_zones()
        except LibcloudError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_list_zones_no_results(self):
        RackspaceMockHttp.type = 'NO_RESULTS'
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 0)

    def test_list_records_success(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].name, 'test3')
        self.assertEqual(records[0].type, RecordType.A)
        self.assertEqual(records[0].data, '127.7.7.7')
        self.assertEqual(records[0].extra['ttl'], 777)
        self.assertEqual(records[0].extra['comment'], 'lulz')
        self.assertEqual(records[0].extra['fqdn'], 'test3.%s' %
                         (records[0].zone.domain))

    def test_list_records_no_results(self):
        zone = self.driver.list_zones()[0]
        RackspaceMockHttp.type = 'NO_RESULTS'
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 0)

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        try:
            self.driver.list_records(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_get_zone_success(self):
        RackspaceMockHttp.type = 'GET_ZONE'
        zone = self.driver.get_zone(zone_id='2946063')

        self.assertEqual(zone.id, '2946063')
        self.assertEqual(zone.domain, 'foo4.bar.com')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.extra['email'], 'test@test.com')

    def test_get_zone_does_not_exist(self):
        RackspaceMockHttp.type = 'DOES_NOT_EXIST'

        try:
            self.driver.get_zone(zone_id='4444')
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, '4444')
        else:
            self.fail('Exception was not thrown')

    def test_get_record_success(self):
        record = self.driver.get_record(zone_id='12345678',
                                        record_id='23456789')
        self.assertEqual(record.id, 'A-7423034')
        self.assertEqual(record.name, 'test3')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.extra['comment'], 'lulz')

    def test_get_record_zone_does_not_exist(self):
        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        RackspaceMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='12345678',
                                   record_id='28536')
        except RecordDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone_success(self):
        RackspaceMockHttp.type = 'CREATE_ZONE'

        zone = self.driver.create_zone(domain='bar.foo1.com', type='master',
                                       ttl=None,
                                       extra={'email': 'test@test.com'})
        self.assertEqual(zone.id, '2946173')
        self.assertEqual(zone.domain, 'bar.foo1.com')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.extra['email'], 'test@test.com')

    def test_create_zone_validaton_error(self):
        RackspaceMockHttp.type = 'CREATE_ZONE_VALIDATION_ERROR'

        try:
            self.driver.create_zone(domain='foo.bar.com', type='master',
                                    ttl=10,
                                    extra={'email': 'test@test.com'})
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(str(e), 'Validation errors: Domain TTL is ' +
                                     'required and must be greater than ' +
                                     'or equal to 300')
        else:
            self.fail('Exception was not thrown')

    def test_update_zone_success(self):
        zone = self.driver.list_zones()[0]
        updated_zone = self.driver.update_zone(zone=zone,
                                               extra={'comment':
                                                      'bar foo'})

        self.assertEqual(zone.extra['comment'], 'wazaaa')

        self.assertEqual(updated_zone.id, zone.id)
        self.assertEqual(updated_zone.domain, 'foo4.bar.com')
        self.assertEqual(updated_zone.type, zone.type)
        self.assertEqual(updated_zone.ttl, zone.ttl)
        self.assertEqual(updated_zone.extra['comment'], 'bar foo')

    def test_update_zone_domain_cannot_be_changed(self):
        zone = self.driver.list_zones()[0]

        try:
            self.driver.update_zone(zone=zone, domain='libcloud.org')
        except LibcloudError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_record_success(self):
        zone = self.driver.list_zones()[0]

        RackspaceMockHttp.type = 'CREATE_RECORD'
        record = self.driver.create_record(name='www', zone=zone,
                                           type=RecordType.A, data='127.1.1.1')

        self.assertEqual(record.id, 'A-7423317')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.zone, zone)
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '127.1.1.1')
        self.assertEqual(record.extra['fqdn'], 'www.%s' % (zone.domain))

    def test_update_record_success(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]
        updated_record = self.driver.update_record(record=record,
                                                   data='127.3.3.3')

        self.assertEqual(record.name, 'test3')
        self.assertEqual(record.data, '127.7.7.7')

        self.assertEqual(updated_record.id, record.id)
        self.assertEqual(updated_record.name, record.name)
        self.assertEqual(updated_record.zone, record.zone)
        self.assertEqual(updated_record.type, record.type)
        self.assertEqual(updated_record.data, '127.3.3.3')

    def test_delete_zone_success(self):
        zone = self.driver.list_zones()[0]
        status = self.driver.delete_zone(zone=zone)
        self.assertTrue(status)

    def test_delete_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.delete_zone(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_delete_record_success(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]
        status = self.driver.delete_record(record=record)
        self.assertTrue(status)

    def test_delete_record_does_not_exist(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]

        RackspaceMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.delete_record(record=record)
        except RecordDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.record_id, record.id)
        else:
            self.fail('Exception was not thrown')

    def test_to_full_record_name_name_provided(self):
        domain = 'foo.bar'
        name = 'test'
        self.assertEqual(self.driver._to_full_record_name(domain, name),
                         'test.foo.bar')

    def test_to_full_record_name_name_not_provided(self):
        domain = 'foo.bar'
        name = None
        self.assertEqual(self.driver._to_full_record_name(domain, name),
                         'foo.bar')

    def test_to_partial_record_name(self):
        domain = 'example.com'
        names = ['test.example.com', 'foo.bar.example.com',
                 'example.com.example.com', 'example.com']
        expected_values = ['test', 'foo.bar', 'example.com', None]

        for name, expected_value in zip(names, expected_values):
            value = self.driver._to_partial_record_name(domain=domain,
                                                        name=name)
            self.assertEqual(value, expected_value)


class RackspaceUKTests(RackspaceUSTests):
    klass = RackspaceUKDNSDriver
    endpoint_url = 'https://lon.dns.api.rackspacecloud.com/v1.0/11111'


class RackspaceMockHttp(MockHttp):
    fixtures = DNSFileFixtures('rackspace')
    base_headers = {'content-type': 'application/json'}

    def _v2_0_tokens(self, method, url, body, headers):
        body = self.fixtures.load('auth_2_0.json')
        headers = {
            'content-type': 'application/json'
        }
        return (httplib.OK, body, headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains(self, method, url, body, headers):
        body = self.fixtures.load('list_zones_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_413(self, method, url, body, headers):
        body = ''
        return (httplib.REQUEST_ENTITY_TOO_LARGE, body, self.base_headers,
                httplib.responses[httplib.REQUEST_ENTITY_TOO_LARGE])

    def _v1_0_11111_domains_NO_RESULTS(self, method, url, body, headers):
        body = self.fixtures.load('list_zones_no_results.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('list_records_success.json')
        elif method == 'PUT':
            # Async - update_zone
            body = self.fixtures.load('update_zone_success.json')
        elif method == 'DELETE':
            # Aync - delete_zone
            body = self.fixtures.load('delete_zone_success.json')

        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063_NO_RESULTS(self, method, url, body,
                                               headers):
        body = self.fixtures.load('list_records_no_results.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063_ZONE_DOES_NOT_EXIST(self, method, url,
                                                        body, headers):
        body = self.fixtures.load('does_not_exist.json')
        return (httplib.NOT_FOUND, body, self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _v1_0_11111_domains_2946063_GET_ZONE(self, method, url, body, headers):
        body = self.fixtures.load('get_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_4444_DOES_NOT_EXIST(self, method, url, body,
                                                headers):
        body = self.fixtures.load('does_not_exist.json')
        return (httplib.NOT_FOUND, body, self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _v1_0_11111_domains_12345678(self, method, url, body, headers):
        body = self.fixtures.load('get_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_12345678_records_23456789(self, method, url, body,
                                                      headers):
        body = self.fixtures.load('get_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_444_ZONE_DOES_NOT_EXIST(self, method, url, body,
                                                    headers):
        body = self.fixtures.load('does_not_exist.json')
        return (httplib.NOT_FOUND, body, self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _v1_0_11111_domains_12345678_RECORD_DOES_NOT_EXIST(self, method, url,
                                                           body, headers):
        body = self.fixtures.load('get_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_12345678_records_28536_RECORD_DOES_NOT_EXIST(self, method, url, body, headers):
        body = self.fixtures.load('does_not_exist.json')
        return (httplib.NOT_FOUND, body, self.base_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _v1_0_11111_domains_CREATE_ZONE(self, method, url, body, headers):
        # Async response - create_zone
        body = self.fixtures.load('create_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_status_288795f9_e74d_48be_880b_a9e36e0de61e_CREATE_ZONE(self, method, url, body, headers):
        # Async status - create_zone
        body = self.fixtures.load('create_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_CREATE_ZONE_VALIDATION_ERROR(self, method, url, body, headers):
        body = self.fixtures.load('create_zone_validation_error.json')
        return (httplib.BAD_REQUEST, body, self.base_headers,
                httplib.responses[httplib.BAD_REQUEST])

    def _v1_0_11111_status_116a8f17_38ac_4862_827c_506cd04800d5(self, method, url, body, headers):
        # Aync status - update_zone
        body = self.fixtures.load('update_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_status_586605c8_5739_43fb_8939_f3a2c4c0e99c_CREATE_RECORD(self, method, url, body, headers):
        # Aync status - create_record
        body = self.fixtures.load('create_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063_records_CREATE_RECORD(self, method, url, body, headers):
        # Aync response - create_record
        body = self.fixtures.load('create_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_status_251c0d0c_95bc_4e09_b99f_4b8748b66246(self, method, url, body, headers):
        # Aync response - update_record
        body = self.fixtures.load('update_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063_records_A_7423034(self, method, url, body,
                                                      headers):
        # Aync response - update_record
        body = self.fixtures.load('update_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_status_0b40cd14_2e5d_490f_bb6e_fdc65d1118a9(self, method,
                                                                url, body,
                                                                headers):
        # Async status - delete_zone
        body = self.fixtures.load('delete_zone_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_status_0b40cd14_2e5d_490f_bb6e_fdc65d1118a9_RECORD_DOES_NOT_EXIST(self, method, url, body, headers):
        # Async status - delete_record
        body = self.fixtures.load('delete_record_success.json')
        return (httplib.OK, body, self.base_headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_domains_2946063_records_A_7423034_RECORD_DOES_NOT_EXIST(self, method, url, body, headers):
        # Async response - delete_record
        body = self.fixtures.load('does_not_exist.json')
        return (httplib.NOT_FOUND, body, self.base_headers,
                httplib.responses[httplib.NOT_FOUND])


if __name__ == '__main__':
    sys.exit(unittest.main())
