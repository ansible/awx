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
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import parse_qsl

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.compute.drivers.ktucloud import KTUCloudNodeDriver

from libcloud.test import MockHttpTestCase
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures


class KTUCloudNodeDriverTest(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        KTUCloudNodeDriver.connectionCls.conn_classes = \
            (None, KTUCloudStackMockHttp)
        self.driver = KTUCloudNodeDriver('apikey', 'secret',
                                         path='/test/path',
                                         host='api.dummy.com')
        self.driver.path = '/test/path'
        self.driver.type = -1
        KTUCloudStackMockHttp.fixture_tag = 'default'
        self.driver.connection.poll_interval = 0.0

    def test_create_node_immediate_failure(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        KTUCloudStackMockHttp.fixture_tag = 'deployfail'
        try:
            self.driver.create_node(name='node-name', image=image, size=size)
        except:
            return
        self.assertTrue(False)

    def test_create_node_delayed_failure(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        KTUCloudStackMockHttp.fixture_tag = 'deployfail2'
        try:
            self.driver.create_node(name='node-name', image=image, size=size)
        except:
            return
        self.assertTrue(False)

    def test_list_images_no_images_available(self):
        KTUCloudStackMockHttp.fixture_tag = 'notemplates'

        images = self.driver.list_images()
        self.assertEqual(0, len(images))

    def test_list_images_available(self):
        images = self.driver.list_images()
        self.assertEqual(112, len(images))

    def test_list_sizes_available(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(112, len(sizes))

    def test_list_sizes_nodisk(self):
        KTUCloudStackMockHttp.fixture_tag = 'nodisk'

        sizes = self.driver.list_sizes()
        self.assertEqual(2, len(sizes))

        check = False
        size = sizes[1]
        if size.id == KTUCloudNodeDriver.EMPTY_DISKOFFERINGID:
            check = True

        self.assertTrue(check)


class KTUCloudStackMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('ktucloud')
    fixture_tag = 'default'

    def _load_fixture(self, fixture):
        body = self.fixtures.load(fixture)
        return body, json.loads(body)

    def _test_path(self, method, url, body, headers):
        url = urlparse.urlparse(url)
        query = dict(parse_qsl(url.query))

        self.assertTrue('apiKey' in query)
        self.assertTrue('command' in query)
        self.assertTrue('response' in query)
        self.assertTrue('signature' in query)

        self.assertTrue(query['response'] == 'json')

        del query['apiKey']
        del query['response']
        del query['signature']
        command = query.pop('command')

        if hasattr(self, '_cmd_' + command):
            return getattr(self, '_cmd_' + command)(**query)
        else:
            fixture = command + '_' + self.fixture_tag + '.json'
            body, obj = self._load_fixture(fixture)
            return (httplib.OK, body, obj, httplib.responses[httplib.OK])

    def _cmd_queryAsyncJobResult(self, jobid):
        fixture = 'queryAsyncJobResult' + '_' + str(jobid) + '.json'
        body, obj = self._load_fixture(fixture)
        return (httplib.OK, body, obj, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
