# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from troveclient.v1 import users

"""
Unit tests for users.py
"""


class UserTest(testtools.TestCase):
    def setUp(self):
        super(UserTest, self).setUp()
        self.orig__init = users.User.__init__
        users.User.__init__ = mock.Mock(return_value=None)
        self.user = users.User()

    def tearDown(self):
        super(UserTest, self).tearDown()
        users.User.__init__ = self.orig__init

    def test___repr__(self):
        self.user.name = "user-1"
        self.assertEqual('<User: user-1>', self.user.__repr__())


class UsersTest(testtools.TestCase):
    def setUp(self):
        super(UsersTest, self).setUp()
        self.orig__init = users.Users.__init__
        users.Users.__init__ = mock.Mock(return_value=None)
        self.users = users.Users()
        self.users.api = mock.Mock()
        self.users.api.client = mock.Mock()

        self.instance_with_id = mock.Mock()
        self.instance_with_id.id = 215

    def tearDown(self):
        super(UsersTest, self).tearDown()
        users.Users.__init__ = self.orig__init

    def _get_mock_method(self):
        self._resp = mock.Mock()
        self._body = None
        self._url = None

        def side_effect_func(url, body=None):
            self._body = body
            self._url = url
            return (self._resp, body)

        return mock.Mock(side_effect=side_effect_func)

    def _build_fake_user(self, name, hostname=None, password=None,
                         databases=None):
        return {
            'name': name,
            'password': password if password else 'password',
            'host': hostname,
            'databases': databases if databases else [],
        }

    def test_create(self):
        self.users.api.client.post = self._get_mock_method()
        self._resp.status_code = 200
        user = self._build_fake_user('user1')

        self.users.create(23, [user])
        self.assertEqual('/instances/23/users', self._url)
        self.assertEqual({"users": [user]}, self._body)

        # Even if host isn't supplied originally,
        # the default is supplied.
        del user['host']
        self.users.create(23, [user])
        self.assertEqual('/instances/23/users', self._url)
        user['host'] = '%'
        self.assertEqual({"users": [user]}, self._body)

        # If host is supplied, of course it's put into the body.
        user['host'] = '127.0.0.1'
        self.users.create(23, [user])
        self.assertEqual({"users": [user]}, self._body)

        # test creation with the instance as an object
        self.users.create(self.instance_with_id, [user])
        self.assertEqual({"users": [user]}, self._body)

        # Make sure that response of 400 is recognized as an error.
        user['host'] = '%'
        self._resp.status_code = 400
        self.assertRaises(Exception, self.users.create, 12, [user])

    def test_delete(self):
        self.users.api.client.delete = self._get_mock_method()
        self._resp.status_code = 200
        self.users.delete(27, 'user1')
        self.assertEqual('/instances/27/users/user1', self._url)
        self.users.delete(self.instance_with_id, 'user1')
        self.assertEqual('/instances/%s/users/user1' %
                         self.instance_with_id.id, self._url)
        self._resp.status_code = 400
        self.assertRaises(Exception, self.users.delete, 34, 'user1')

    def test_list(self):
        page_mock = mock.Mock()
        self.users._paginated = page_mock
        self.users.list('instance1')
        page_mock.assert_called_with('/instances/instance1/users',
                                     'users', None, None)
        limit = 'test-limit'
        marker = 'test-marker'
        self.users.list('instance1', limit, marker)
        page_mock.assert_called_with('/instances/instance1/users',
                                     'users', limit, marker)

    def test_update_no_changes(self):
        self.users.api.client.post = self._get_mock_method()
        self._resp.status_code = 200
        username = 'upd_user'
        user = self._build_fake_user(username)

        self.users.create(99, [user])
        instance = 'instance1'
        newuserattr = None
        self.assertRaises(Exception, self.users.update_attributes, instance,
                          username, newuserattr)
