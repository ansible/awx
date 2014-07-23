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
# limitations under the License.

import sys
import unittest

from libcloud.utils.py3 import httplib

from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.dns.types import RecordDoesNotExistError
from libcloud.dns.drivers.hostvirtual import HostVirtualDNSDriver
from libcloud.test import MockHttp
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test.secrets import DNS_PARAMS_HOSTVIRTUAL


class HostVirtualTests(unittest.TestCase):
    def setUp(self):
        HostVirtualDNSDriver.connectionCls.conn_classes = (
            None, HostVirtualMockHttp)
        HostVirtualMockHttp.type = None
        self.driver = HostVirtualDNSDriver(*DNS_PARAMS_HOSTVIRTUAL)

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 7)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 5)

        zone = zones[0]
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 't.com')
        self.assertEqual(zone.ttl, '3600')

    def test_list_records(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 3)

        record = records[1]
        self.assertEqual(record.name, 'www.t.com')
        self.assertEqual(record.id, '300719')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '208.111.35.173')

    def test_get_zone(self):
        zone = self.driver.get_zone(zone_id='47234')
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 't.com')
        self.assertEqual(zone.ttl, '3600')

    def test_get_record(self):
        record = self.driver.get_record(zone_id='47234', record_id='300377')
        self.assertEqual(record.id, '300377')
        self.assertEqual(record.name, '*.t.com')
        self.assertEqual(record.type, RecordType.CNAME)
        self.assertEqual(record.data, 't.com')

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        HostVirtualMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.list_records(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_get_zone_does_not_exist(self):
        HostVirtualMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_zone(zone_id='4444')
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, '4444')
        else:
            self.fail('Exception was not thrown')

    def test_get_record_zone_does_not_exist(self):
        HostVirtualMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='4444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        HostVirtualMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='47234', record_id='4444')
        except RecordDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone(self):
        zone = self.driver.create_zone(domain='t.com', type='master',
                                       ttl=None, extra=None)
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.domain, 't.com')

    def test_update_zone(self):
        zone = self.driver.list_zones()[0]
        updated_zone = self.driver.update_zone(zone=zone, domain='tt.com')

        self.assertEqual(updated_zone.id, zone.id)
        self.assertEqual(updated_zone.domain, 'tt.com')
        self.assertEqual(updated_zone.type, zone.type)
        self.assertEqual(updated_zone.ttl, '3600')

    def test_create_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.create_record(
            name='www', zone=zone,
            type=RecordType.A, data='127.0.0.1'
        )

        self.assertEqual(record.id, '300377')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.zone, zone)
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '127.0.0.1')

    def test_update_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[1]
        updated_record = self.driver.update_record(record=record, name='www',
                                                   type=RecordType.AAAA,
                                                   data='::1')
        self.assertEqual(record.data, '208.111.35.173')

        self.assertEqual(updated_record.id, record.id)
        self.assertEqual(updated_record.name, 'www')
        self.assertEqual(updated_record.zone, record.zone)
        self.assertEqual(updated_record.type, RecordType.AAAA)
        self.assertEqual(updated_record.data, '::1')

    def test_delete_zone(self):
        zone = self.driver.list_zones()[0]
        status = self.driver.delete_zone(zone=zone)
        self.assertTrue(status)

    def test_delete_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        HostVirtualMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.delete_zone(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_delete_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]
        status = self.driver.delete_record(record=record)
        self.assertTrue(status)

    def test_delete_record_does_not_exist(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[0]
        HostVirtualMockHttp.type = 'RECORD_DOES_NOT_EXIST'
        try:
            self.driver.delete_record(record=record)
        except RecordDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.record_id, record.id)
        else:
            self.fail('Exception was not thrown')


class HostVirtualMockHttp(MockHttp):
    fixtures = DNSFileFixtures('hostvirtual')

    def _dns_zone(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _dns_zones(self, method, url, body, headers):
        body = self.fixtures.load('list_zones.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _dns_record(self, method, url, body, headers):
        body = self.fixtures.load('get_record.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _dns_records(self, method, url, body, headers):
        body = self.fixtures.load('list_records.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _dns_zone_ZONE_DOES_NOT_EXIST(self, method, url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _dns_zone_RECORD_DOES_NOT_EXIST(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _dns_zones_ZONE_DOES_NOT_EXIST(self, method, url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _dns_record_ZONE_DOES_NOT_EXIST(self, method,
                                        url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _dns_record_RECORD_DOES_NOT_EXIST(self, method,
                                          url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _dns_records_ZONE_DOES_NOT_EXIST(self, method,
                                         url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _dns_zones_RECORD_DOES_NOT_EXIST(self, method,
                                         url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.json')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])


if __name__ == '__main__':
    sys.exit(unittest.main())
