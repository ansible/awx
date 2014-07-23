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

from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.dns.types import RecordDoesNotExistError
from libcloud.dns.drivers.zerigo import ZerigoDNSDriver, ZerigoError

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test.secrets import DNS_PARAMS_ZERIGO


class ZerigoTests(unittest.TestCase):
    def setUp(self):
        ZerigoDNSDriver.connectionCls.conn_classes = (
            None, ZerigoMockHttp)
        ZerigoMockHttp.type = None
        self.driver = ZerigoDNSDriver(*DNS_PARAMS_ZERIGO)

    def test_invalid_credentials(self):
        ZerigoMockHttp.type = 'INVALID_CREDS'

        try:
            list(self.driver.list_zones())
        except InvalidCredsError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 13)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones_success(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0].domain, 'example.com')
        self.assertEqual(zones[0].type, 'master')
        self.assertEqual(zones[0].extra['notes'], 'test foo bar')

    def test_list_zones_no_results(self):
        ZerigoMockHttp.type = 'NO_RESULTS'
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 0)

    def test_list_records_success(self):
        zone = self.driver.list_zones()[0]
        records = list(self.driver.list_records(zone=zone))

        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].name, 'www')
        self.assertEqual(records[0].type, RecordType.A)
        self.assertEqual(records[0].data, '172.16.16.1')
        self.assertEqual(records[0].extra['fqdn'], 'www.example.com')
        self.assertEqual(records[0].extra['notes'], None)
        self.assertEqual(records[0].extra['priority'], None)

        self.assertEqual(records[1].name, 'test')
        self.assertEqual(records[1].extra['ttl'], 3600)

    def test_record_with_empty_name(self):
        zone = self.driver.list_zones()[0]
        record1 = list(self.driver.list_records(zone=zone))[-1]
        record2 = list(self.driver.list_records(zone=zone))[-2]

        self.assertEqual(record1.name, None)
        self.assertEqual(record2.name, None)

    def test_list_records_no_results(self):
        zone = self.driver.list_zones()[0]
        ZerigoMockHttp.type = 'NO_RESULTS'
        records = list(self.driver.list_records(zone=zone))
        self.assertEqual(len(records), 0)

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        ZerigoMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        try:
            list(self.driver.list_records(zone=zone))
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')
        pass

    def test_get_zone_success(self):
        zone = self.driver.get_zone(zone_id=12345678)

        self.assertEqual(zone.id, '12345678')
        self.assertEqual(zone.domain, 'example.com')
        self.assertEqual(zone.extra['hostmaster'], 'dnsadmin@example.com')
        self.assertEqual(zone.type, 'master')

    def test_get_zone_does_not_exist(self):
        ZerigoMockHttp.type = 'DOES_NOT_EXIST'

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
        self.assertEqual(record.id, '23456789')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.type, RecordType.A)

    def test_get_record_zone_does_not_exist(self):
        ZerigoMockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        ZerigoMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='12345678',
                                   record_id='28536')
        except RecordDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone_success(self):
        ZerigoMockHttp.type = 'CREATE_ZONE'

        zone = self.driver.create_zone(domain='foo.bar.com', type='master',
                                       ttl=None, extra=None)
        self.assertEqual(zone.id, '12345679')
        self.assertEqual(zone.domain, 'foo.bar.com')

    def test_create_zone_validaton_error(self):
        ZerigoMockHttp.type = 'CREATE_ZONE_VALIDATION_ERROR'

        try:
            self.driver.create_zone(domain='foo.bar.com', type='master',
                                    ttl=10, extra=None)
        except ZerigoError:
            e = sys.exc_info()[1]
            self.assertEqual(len(e.errors), 2)
        else:
            self.fail('Exception was not thrown')

    def test_update_zone_success(self):
        zone = self.driver.list_zones()[0]
        updated_zone = self.driver.update_zone(zone=zone,
                                               ttl=10,
                                               extra={'notes':
                                                      'bar foo'})

        self.assertEqual(zone.extra['notes'], 'test foo bar')

        self.assertEqual(updated_zone.id, zone.id)
        self.assertEqual(updated_zone.domain, 'example.com')
        self.assertEqual(updated_zone.type, zone.type)
        self.assertEqual(updated_zone.ttl, 10)
        self.assertEqual(updated_zone.extra['notes'], 'bar foo')

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

        ZerigoMockHttp.type = 'CREATE_RECORD'
        record = self.driver.create_record(name='www', zone=zone,
                                           type=RecordType.A, data='127.0.0.1')

        self.assertEqual(record.id, '23456780')
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

        self.assertEqual(record.data, '172.16.16.1')

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

        ZerigoMockHttp.type = 'ZONE_DOES_NOT_EXIST'

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

        ZerigoMockHttp.type = 'RECORD_DOES_NOT_EXIST'

        try:
            self.driver.delete_record(record=record)
        except RecordDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.record_id, record.id)
        else:
            self.fail('Exception was not thrown')


class ZerigoMockHttp(MockHttp):
    fixtures = DNSFileFixtures('zerigo')

    def _api_1_1_zones_xml_INVALID_CREDS(self, method, url, body, headers):
        body = 'HTTP Basic: Access denied.\n'
        return (httplib.UNAUTHORIZED, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_xml(self, method, url, body, headers):
        body = self.fixtures.load('list_zones.xml')
        return (httplib.OK, body, {'x-query-count': 1},
                httplib.responses[httplib.OK])

    def _api_1_1_zones_xml_NO_RESULTS(self, method, url, body, headers):
        body = self.fixtures.load('list_zones_no_results.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_hosts_xml(self, method, url, body, headers):
        body = self.fixtures.load('list_records.xml')
        return (httplib.OK, body, {'x-query-count': 1},
                httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_hosts_xml_NO_RESULTS(self, method, url, body,
                                                     headers):
        body = self.fixtures.load('list_records_no_results.xml')
        return (httplib.OK, body, {'x-query-count': 0},
                httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_hosts_xml_ZONE_DOES_NOT_EXIST(self, method,
                                                              url, body,
                                                              headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_xml(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_4444_xml_DOES_NOT_EXIST(self, method, url, body,
                                               headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_hosts_23456789_xml(self, method, url, body, headers):
        body = self.fixtures.load('get_record.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_444_xml_ZONE_DOES_NOT_EXIST(self, method, url, body,
                                                   headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_xml_RECORD_DOES_NOT_EXIST(self, method, url,
                                                          body, headers):
        body = self.fixtures.load('get_zone.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_hosts_28536_xml_RECORD_DOES_NOT_EXIST(self, method, url, body,
                                                       headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_xml_CREATE_ZONE(self, method, url, body, headers):
        body = self.fixtures.load('create_zone.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_xml_CREATE_ZONE_VALIDATION_ERROR(self, method, url,
                                                        body, headers):
        body = self.fixtures.load('create_zone_validation_error.xml')
        return (httplib.UNPROCESSABLE_ENTITY, body, {},
                httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_hosts_xml_CREATE_RECORD(self, method, url,
                                                        body, headers):
        body = self.fixtures.load('create_record.xml')
        return (httplib.CREATED, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_zones_12345678_xml_ZONE_DOES_NOT_EXIST(self, method, url,
                                                        body, headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    def _api_1_1_hosts_23456789_xml_RECORD_DOES_NOT_EXIST(self, method, url,
                                                          body, headers):
        body = ''
        return (httplib.NOT_FOUND, body, {}, httplib.responses[httplib.OK])

    """
    def (self, method, url, body, headers):
        body = self.fixtures.load('.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def (self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def (self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def (self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def (self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def (self, method, url, body, headers):
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])
    """


if __name__ == '__main__':
    sys.exit(unittest.main())
