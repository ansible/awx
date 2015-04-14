# Copyright 2014 Tesora Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient.v1 import databases

"""
Unit tests for databases.py
"""


class DatabaseTest(testtools.TestCase):
    def setUp(self):
        super(DatabaseTest, self).setUp()
        self.orig__init = databases.Database.__init__
        databases.Database.__init__ = mock.Mock(return_value=None)
        self.database = databases.Database()

    def tearDown(self):
        super(DatabaseTest, self).tearDown()
        databases.Database.__init__ = self.orig__init


class DatabasesTest(testtools.TestCase):
    def setUp(self):
        super(DatabasesTest, self).setUp()
        self.orig__init = databases.Databases.__init__
        databases.Databases.__init__ = mock.Mock(return_value=None)
        self.databases = databases.Databases()
        self.databases.api = mock.Mock()
        self.databases.api.client = mock.Mock()

        self.instance_with_id = mock.Mock()
        self.instance_with_id.id = 215

        self.fakedb1 = ['db1']
        self.fakedb2 = ['db1', 'db2']

    def tearDown(self):
        super(DatabasesTest, self).tearDown()
        databases.Databases.__init__ = self.orig__init

    def _get_mock_method(self):
        self._resp = mock.Mock()
        self._body = None
        self._url = None

        def side_effect_func(url, body=None):
            self._body = body
            self._url = url
            return (self._resp, body)

        return mock.Mock(side_effect=side_effect_func)

    def test_create(self):
        self.databases.api.client.post = self._get_mock_method()
        self._resp.status_code = 200

        self.databases.create(23, self.fakedb1)
        self.assertEqual('/instances/23/databases', self._url)
        self.assertEqual({"databases": self.fakedb1}, self._body)

        self.databases.create(23, self.fakedb2)
        self.assertEqual('/instances/23/databases', self._url)
        self.assertEqual({"databases": self.fakedb2}, self._body)

        # test creation with the instance as an object
        self.databases.create(self.instance_with_id, self.fakedb1)
        self.assertEqual({"databases": self.fakedb1}, self._body)

    def test_delete(self):
        self.databases.api.client.delete = self._get_mock_method()
        self._resp.status_code = 200
        self.databases.delete(27, self.fakedb1[0])
        self.assertEqual('/instances/27/databases/%s' % self.fakedb1[0],
                         self._url)
        self.databases.delete(self.instance_with_id, self.fakedb1[0])
        self.assertEqual('/instances/%s/databases/%s' %
                         (self.instance_with_id.id, self.fakedb1[0]),
                         self._url)
        self._resp.status_code = 400
        self.assertRaises(Exception, self.databases.delete, 34, self.fakedb1)

    def test_list(self):
        page_mock = mock.Mock()
        self.databases._paginated = page_mock
        self.databases.list('instance1')
        page_mock.assert_called_with('/instances/instance1/databases',
                                     'databases', None, None)
        limit = 'test-limit'
        marker = 'test-marker'
        self.databases.list('instance1', limit, marker)
        page_mock.assert_called_with('/instances/instance1/databases',
                                     'databases', limit, marker)
