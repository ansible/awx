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

from libcloud.common.base import Response
from libcloud.common.base import Connection, ConnectionKey, ConnectionUserAndKey
from libcloud.common.types import LibcloudError
from libcloud.compute.base import Node, NodeSize, NodeImage, NodeDriver
from libcloud.compute.base import NodeAuthSSHKey, NodeAuthPassword

from libcloud.test import MockResponse           # pylint: disable-msg=E0611


class FakeDriver(object):
    type = 0


class BaseTests(unittest.TestCase):

    def test_base_node(self):
        Node(id=0, name=0, state=0, public_ips=0, private_ips=0,
             driver=FakeDriver())

    def test_base_node_size(self):
        NodeSize(id=0, name=0, ram=0, disk=0, bandwidth=0, price=0,
                 driver=FakeDriver())

    def test_base_node_image(self):
        NodeImage(id=0, name=0, driver=FakeDriver())

    def test_base_response(self):
        Response(MockResponse(status=200, body='foo'), ConnectionKey('foo'))

    def test_base_node_driver(self):
        NodeDriver('foo')

    def test_base_connection_key(self):
        ConnectionKey('foo')

    def test_base_connection_userkey(self):
        ConnectionUserAndKey('foo', 'bar')

    def test_base_connection_timeout(self):
        Connection(timeout=10)


class TestValidateAuth(unittest.TestCase):

    def test_get_auth_ssh(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['ssh_key']}
        auth = NodeAuthSSHKey('pubkey...')
        self.assertEqual(auth, n._get_and_check_auth(auth))

    def test_get_auth_ssh_but_given_password(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['ssh_key']}
        auth = NodeAuthPassword('password')
        self.assertRaises(LibcloudError, n._get_and_check_auth, auth)

    def test_get_auth_password(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['password']}
        auth = NodeAuthPassword('password')
        self.assertEqual(auth, n._get_and_check_auth(auth))

    def test_get_auth_password_but_given_ssh_key(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['password']}
        auth = NodeAuthSSHKey('publickey')
        self.assertRaises(LibcloudError, n._get_and_check_auth, auth)

    def test_get_auth_default_ssh_key(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['ssh_key']}
        self.assertEqual(None, n._get_and_check_auth(None))

    def test_get_auth_default_password(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['password']}
        auth = n._get_and_check_auth(None)
        self.assertTrue(isinstance(auth, NodeAuthPassword))

    def test_get_auth_default_no_feature(self):
        n = NodeDriver('foo')
        self.assertEqual(None, n._get_and_check_auth(None))

    def test_get_auth_generates_password_but_given_nonsense(self):
        n = NodeDriver('foo')
        n.features = {'create_node': ['generates_password']}
        auth = "nonsense"
        self.assertRaises(LibcloudError, n._get_and_check_auth, auth)

    def test_get_auth_no_features_but_given_nonsense(self):
        n = NodeDriver('foo')
        auth = "nonsense"
        self.assertRaises(LibcloudError, n._get_and_check_auth, auth)


if __name__ == '__main__':
    sys.exit(unittest.main())
