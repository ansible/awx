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
from libcloud.dns.drivers.route53 import Route53DNSDriver
from libcloud.test import MockHttp
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test.secrets import DNS_PARAMS_ROUTE53


class Route53Tests(unittest.TestCase):
    def setUp(self):
        Route53DNSDriver.connectionCls.conn_classes = (
            Route53MockHttp, Route53MockHttp)
        Route53MockHttp.type = None
        self.driver = Route53DNSDriver(*DNS_PARAMS_ROUTE53)

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 10)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 5)

        zone = zones[0]
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 't.com')

    def test_list_records(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 10)

        record = records[1]
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.id, 'A:www')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '208.111.35.173')
        self.assertEqual(record.extra['ttl'], 86400)

        record = records[3]
        self.assertEqual(record.type, RecordType.MX)
        self.assertEqual(record.data, 'ASPMX.L.GOOGLE.COM.')
        self.assertEqual(record.extra['priority'], 1)

        record = records[4]
        self.assertEqual(record.type, RecordType.MX)
        self.assertEqual(record.data, 'ALT1.ASPMX.L.GOOGLE.COM.')
        self.assertEqual(record.extra['priority'], 5)

        record = records[8]
        self.assertEqual(record.type, RecordType.SRV)
        self.assertEqual(record.data, 'xmpp-server.example.com.')
        self.assertEqual(record.extra['priority'], 1)
        self.assertEqual(record.extra['weight'], 10)
        self.assertEqual(record.extra['port'], 5269)

    def test_get_zone(self):
        zone = self.driver.get_zone(zone_id='47234')
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 't.com')

    def test_get_record(self):
        record = self.driver.get_record(zone_id='47234',
                                        record_id='CNAME:wibble')
        self.assertEqual(record.name, 'wibble')
        self.assertEqual(record.type, RecordType.CNAME)
        self.assertEqual(record.data, 't.com')

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        Route53MockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.list_records(zone=zone)
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_get_zone_does_not_exist(self):
        Route53MockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_zone(zone_id='47234')
        except ZoneDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.zone_id, '47234')
        else:
            self.fail('Exception was not thrown')

    def test_get_record_zone_does_not_exist(self):
        Route53MockHttp.type = 'ZONE_DOES_NOT_EXIST'

        try:
            self.driver.get_record(zone_id='4444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        Route53MockHttp.type = 'RECORD_DOES_NOT_EXIST'

        rid = 'CNAME:doesnotexist.t.com'
        try:
            self.driver.get_record(zone_id='47234',
                                   record_id=rid)
        except RecordDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone(self):
        zone = self.driver.create_zone(domain='t.com', type='master',
                                       ttl=None, extra=None)
        self.assertEqual(zone.id, '47234')
        self.assertEqual(zone.domain, 't.com')

    def test_create_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.create_record(
            name='www', zone=zone,
            type=RecordType.A, data='127.0.0.1',
            extra={'ttl': 0}
        )

        self.assertEqual(record.id, 'A:www')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.zone, zone)
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '127.0.0.1')

    def test_update_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.list_records(zone=zone)[1]

        params = {
            'record': record,
            'name': 'www',
            'type': RecordType.A,
            'data': '::1',
            'extra': {'ttle': 0}}
        updated_record = self.driver.update_record(**params)

        self.assertEqual(record.data, '208.111.35.173')

        self.assertEqual(updated_record.id, 'A:www')
        self.assertEqual(updated_record.name, 'www')
        self.assertEqual(updated_record.zone, record.zone)
        self.assertEqual(updated_record.type, RecordType.A)
        self.assertEqual(updated_record.data, '::1')

    def test_delete_zone(self):
        zone = self.driver.list_zones()[0]
        status = self.driver.delete_zone(zone=zone)
        self.assertTrue(status)

    def test_delete_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        Route53MockHttp.type = 'ZONE_DOES_NOT_EXIST'

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
        Route53MockHttp.type = 'RECORD_DOES_NOT_EXIST'
        try:
            self.driver.delete_record(record=record)
        except RecordDoesNotExistError:
            e = sys.exc_info()[1]
            self.assertEqual(e.record_id, record.id)
        else:
            self.fail('Exception was not thrown')


class Route53MockHttp(MockHttp):
    fixtures = DNSFileFixtures('route53')

    def _2012_02_29_hostedzone_47234(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_02_29_hostedzone(self, method, url, body, headers):
        # print method, url, body, headers
        if method == "POST":
            body = self.fixtures.load("create_zone.xml")
            return (httplib.CREATED, body, {}, httplib.responses[httplib.OK])
        body = self.fixtures.load('list_zones.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_02_29_hostedzone_47234_rrset(self, method, url, body, headers):
        body = self.fixtures.load('list_records.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_02_29_hostedzone_47234_rrset_ZONE_DOES_NOT_EXIST(self, method,
                                                               url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.xml')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _2012_02_29_hostedzone_4444_ZONE_DOES_NOT_EXIST(self, method,
                                                        url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.xml')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _2012_02_29_hostedzone_47234_ZONE_DOES_NOT_EXIST(self, method,
                                                         url, body, headers):
        body = self.fixtures.load('zone_does_not_exist.xml')
        return (httplib.NOT_FOUND, body,
                {}, httplib.responses[httplib.NOT_FOUND])

    def _2012_02_29_hostedzone_47234_rrset_RECORD_DOES_NOT_EXIST(self, method,
                                                                 url, body, headers):
        if method == "POST":
            body = self.fixtures.load('invalid_change_batch.xml')
            return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.BAD_REQUEST])
        body = self.fixtures.load('record_does_not_exist.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_02_29_hostedzone_47234_RECORD_DOES_NOT_EXIST(self, method,
                                                           url, body, headers):
        body = self.fixtures.load('get_zone.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
