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

from libcloud.common.linode import LinodeException
from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.dns.types import RecordDoesNotExistError
from libcloud.dns.drivers.linode import LinodeDNSDriver

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test.secrets import DNS_PARAMS_LINODE


class LinodeTests(unittest.TestCase):
    def setUp(self):
        LinodeDNSDriver.connectionCls.conn_classes = (
            None, LinodeMockHttp)
        LinodeMockHttp.use_param = 'api_action'
        LinodeMockHttp.type = None
        self.driver = LinodeDNSDriver(*DNS_PARAMS_LINODE)

    def assertHasKeys(self, dictionary, keys):
        for key in keys:
            self.assertTrue(key in dictionary, 'key "%s" not in dictionary' %
                            (key))

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 7)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones_success(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 2)

        zone = zones[0]
        self.assertEqual(zone.id, '5093')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 'linode.com')
        self.assertEqual(zone.ttl, None)
        self.assertHasKeys(zone.extra, ['description', 'SOA_Email', 'status'])

    def test_list_records_success(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 2)

        arecord = records[0]
        self.assertEqual(arecord.id, '3585100')
        self.assertEqual(arecord.name, 'mc')
        self.assertEqual(arecord.type, RecordType.A)
        self.assertEqual(arecord.data, '127.0.0.1')
        self.assertHasKeys(arecord.extra, ['protocol', 'ttl_sec', 'port',
                                           'weight'])

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        LinodeMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        try:
            self.driver.list_records(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_get_zone_success(self):
        LinodeMockHttp.type = 'GET_ZONE'

        zone = self.driver.get_zone(zone_id='5093')
        self.assertEqual(zone.id, '5093')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 'linode.com')
        self.assertEqual(zone.ttl, None)
        self.assertHasKeys(zone.extra, ['description', 'SOA_Email', 'status'])

    def test_get_zone_does_not_exist(self):
        LinodeMockHttp.type = 'GET_ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_zone(zone_id='4444')
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, '4444')
        else:
            self.fail('Exception was not thrown')

    def test_get_record_success(self):
        LinodeMockHttp.type = 'GET_RECORD'
        record = self.driver.get_record(zone_id='1234', record_id='3585100')
        self.assertEqual(record.id, '3585100')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '127.0.0.1')
        self.assertHasKeys(record.extra, ['protocol', 'ttl_sec', 'port',
                                          'weight'])

    def test_get_record_zone_does_not_exist(self):
        LinodeMockHttp.type = 'GET_RECORD_ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='444', record_id='3585100')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        LinodeMockHttp.type = 'GET_RECORD_RECORD_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='4441', record_id='3585100')
        except RecordDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone_success(self):
        zone = self.driver.create_zone(domain='foo.bar.com', type='master',
                                       ttl=None, extra=None)
        self.assertEqual(zone.id, '5094')
        self.assertEqual(zone.domain, 'foo.bar.com')

    def test_create_zone_validaton_error(self):
        LinodeMockHttp.type = 'VALIDATION_ERROR'

        try:
            self.driver.create_zone(domain='foo.bar.com', type='master',
                                    ttl=None, extra=None)
        except LinodeException:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_update_zone_success(self):
        zone = self.driver.list_zones()[0]
        updated_zone = self.driver.update_zone(zone=zone,
                                               domain='libcloud.org',
                                               ttl=10,
                                               extra={'SOA_Email':
                                                      'bar@libcloud.org'})

        self.assertEqual(zone.extra['SOA_Email'], 'dns@example.com')

        self.assertEqual(updated_zone.id, zone.id)
        self.assertEqual(updated_zone.domain, 'libcloud.org')
        self.assertEqual(updated_zone.type, zone.type)
        self.assertEqual(updated_zone.ttl, 10)
        self.assertEqual(updated_zone.extra['SOA_Email'], 'bar@libcloud.org')
        self.assertEqual(updated_zone.extra['status'], zone.extra['status'])
        self.assertEqual(updated_zone.extra['description'],
                         zone.extra['description'])

    def test_create_record_success(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.create_record(name='www', zone=zone,
                                           type=RecordType.A, data='127.0.0.1')

        self.assertEqual(record.id, '3585100')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.zone, zone)
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '127.0.0.1')

    def test_update_record_success(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]
        updated_record = self.driver.update_record(record=record, name='www',
                                                   type=RecordType.AAAA,
                                                   data='::1')

        self.assertEqual(record.data, '127.0.0.1')

        self.assertEqual(updated_record.id, record.id)
        self.assertEqual(updated_record.name, 'www')
        self.assertEqual(updated_record.zone, record.zone)
        self.assertEqual(updated_record.type, RecordType.AAAA)
        self.assertEqual(updated_record.data, '::1')

    def test_delete_zone_success(self):
        zone = self.driver.list_zones()[0]
        status = self.driver.delete_zone(zone=zone)
        self.assertTrue(status)

    def test_delete_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        LinodeMockHttp.type = 'ZONE_DOES_NOT_EXIST'

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

        LinodeMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.delete_record(record=record)
        except RecordDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.record_id, record.id)
        else:
            self.fail('Exception was not thrown')


class LinodeMockHttp(MockHttp):
    fixtures = DNSFileFixtures('linode')

    def _domain_list(self, method, url, body, headers):
        body = self.fixtures.load('domain_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_resource_list(self, method, url, body, headers):
        body = self.fixtures.load('resource_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _ZONE_DOES_NOT_EXIST_domain_resource_list(self, method, url, body,
                                                  headers):
        body = self.fixtures.load('resource_list_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_ZONE_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_ZONE_DOES_NOT_EXIST_domain_list(self, method, url, body,
                                             headers):
        body = self.fixtures.load('get_zone_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_domain_resource_list(self, method, url, body, headers):
        body = self.fixtures.load('get_record.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_ZONE_DOES_NOT_EXIST_domain_list(self, method, url, body,
                                                    headers):
        body = self.fixtures.load('get_zone_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_ZONE_DOES_NOT_EXIST_domain_resource_list(self, method, url,
                                                             body, headers):
        body = self.fixtures.load('get_record_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_RECORD_DOES_NOT_EXIST_domain_list(self, method, url, body,
                                                      headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_RECORD_DOES_NOT_EXIST_domain_resource_list(self, method,
                                                               url, body,
                                                               headers):
        body = self.fixtures.load('get_record_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_create(self, method, url, body, headers):
        body = self.fixtures.load('create_domain.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _VALIDATION_ERROR_domain_create(self, method, url, body, headers):
        body = self.fixtures.load('create_domain_validation_error.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_update(self, method, url, body, headers):
        body = self.fixtures.load('update_domain.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_resource_create(self, method, url, body, headers):
        body = self.fixtures.load('create_resource.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_resource_update(self, method, url, body, headers):
        body = self.fixtures.load('update_resource.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_delete(self, method, url, body, headers):
        body = self.fixtures.load('delete_domain.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _ZONE_DOES_NOT_EXIST_domain_delete(self, method, url, body, headers):
        body = self.fixtures.load('delete_domain_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_resource_delete(self, method, url, body, headers):
        body = self.fixtures.load('delete_resource.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _RECORD_DOES_NOT_EXIST_domain_resource_delete(self, method, url, body,
                                                      headers):
        body = self.fixtures.load('delete_resource_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
