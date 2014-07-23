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

from __future__ import with_statement

import sys
import tempfile

from mock import Mock

from libcloud.test import unittest
from libcloud.dns.base import DNSDriver, Zone, Record
from libcloud.dns.types import RecordType


MOCK_RECORDS_VALUES = [
    {'id': 1, 'name': 'www', 'type': RecordType.A, 'data': '127.0.0.1'},
    {'id': 2, 'name': 'www', 'type': RecordType.AAAA,
     'data': '2a01:4f8:121:3121::2'},

    # Custom TTL
    {'id': 3, 'name': 'www', 'type': RecordType.A, 'data': '127.0.0.1',
     'extra': {'ttl': 123}},

    # Record without a name
    {'id': 4, 'name': '', 'type': RecordType.A,
     'data': '127.0.0.1'},

    {'id': 5, 'name': 'test1', 'type': RecordType.TXT,
     'data': 'test foo bar'},

    # TXT record with quotes
    {'id': 5, 'name': 'test2', 'type': RecordType.TXT,
     'data': 'test "foo" "bar"'},

    # Records with priority
    {'id': 5, 'name': '', 'type': RecordType.MX,
     'data': 'mx.example.com', 'extra': {'priority': 10}},
    {'id': 5, 'name': '', 'type': RecordType.SRV,
     'data': '10 3333 example.com', 'extra': {'priority': 20}},
]


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.driver = DNSDriver('none', 'none')
        self.tmp_file = tempfile.mkstemp()
        self.tmp_path = self.tmp_file[1]

    def test_export_zone_to_bind_format_slave_should_throw(self):
        zone = Zone(id=1, domain='example.com', type='slave', ttl=900,
                    driver=self.driver)
        self.assertRaises(ValueError, zone.export_to_bind_format)

    def test_export_zone_to_bind_format_success(self):
        zone = Zone(id=1, domain='example.com', type='master', ttl=900,
                    driver=self.driver)

        mock_records = []

        for values in MOCK_RECORDS_VALUES:
            values = values.copy()
            values['driver'] = self.driver
            values['zone'] = zone
            record = Record(**values)
            mock_records.append(record)

        self.driver.list_records = Mock()
        self.driver.list_records.return_value = mock_records

        result = self.driver.export_zone_to_bind_format(zone=zone)
        self.driver.export_zone_to_bind_zone_file(zone=zone,
                                                  file_path=self.tmp_path)

        with open(self.tmp_path, 'r') as fp:
            content = fp.read()

        lines1 = result.split('\n')
        lines2 = content.split('\n')

        for lines in [lines1, lines2]:
            self.assertEqual(len(lines), 2 + 1 + 9)
            self.assertRegexpMatches(lines[1], r'\$ORIGIN example\.com\.')
            self.assertRegexpMatches(lines[2], r'\$TTL 900')

            self.assertRegexpMatches(lines[4], r'www.example.com\.\s+900\s+IN\s+A\s+127\.0\.0\.1')
            self.assertRegexpMatches(lines[5], r'www.example.com\.\s+900\s+IN\s+AAAA\s+2a01:4f8:121:3121::2')
            self.assertRegexpMatches(lines[6], r'www.example.com\.\s+123\s+IN\s+A\s+127\.0\.0\.1')
            self.assertRegexpMatches(lines[7], r'example.com\.\s+900\s+IN\s+A\s+127\.0\.0\.1')
            self.assertRegexpMatches(lines[8], r'test1.example.com\.\s+900\s+IN\s+TXT\s+"test foo bar"')
            self.assertRegexpMatches(lines[9], r'test2.example.com\.\s+900\s+IN\s+TXT\s+"test \\"foo\\" \\"bar\\""')
            self.assertRegexpMatches(lines[10], r'example.com\.\s+900\s+IN\s+MX\s+10\s+mx.example.com')
            self.assertRegexpMatches(lines[11], r'example.com\.\s+900\s+IN\s+SRV\s+20\s+10 3333 example.com')


if __name__ == '__main__':
    sys.exit(unittest.main())
