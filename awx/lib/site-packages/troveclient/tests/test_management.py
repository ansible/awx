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

from troveclient import base
from troveclient.v1 import management

"""
Unit tests for management.py
"""


class RootHistoryTest(testtools.TestCase):

    def setUp(self):
        super(RootHistoryTest, self).setUp()
        self.orig__init = management.RootHistory.__init__
        management.RootHistory.__init__ = mock.Mock(return_value=None)

    def tearDown(self):
        super(RootHistoryTest, self).tearDown()
        management.RootHistory.__init__ = self.orig__init

    def test___repr__(self):
        root_history = management.RootHistory()
        root_history.id = "1"
        root_history.created = "ct"
        root_history.user = "tu"
        self.assertEqual('<Root History: Instance 1 enabled at ct by tu>',
                         root_history.__repr__())


class ManagementTest(testtools.TestCase):

    def setUp(self):
        super(ManagementTest, self).setUp()
        self.orig__init = management.Management.__init__
        management.Management.__init__ = mock.Mock(return_value=None)
        self.management = management.Management()
        self.management.api = mock.Mock()
        self.management.api.client = mock.Mock()

        self.orig_hist__init = management.RootHistory.__init__
        self.orig_base_getid = base.getid
        base.getid = mock.Mock(return_value="instance1")

    def tearDown(self):
        super(ManagementTest, self).tearDown()
        management.Management.__init__ = self.orig__init
        management.RootHistory.__init__ = self.orig_hist__init
        base.getid = self.orig_base_getid

    def test_show(self):
        def side_effect_func(path, instance):
            return path, instance
        self.management._get = mock.Mock(side_effect=side_effect_func)
        p, i = self.management.show(1)
        self.assertEqual(('/mgmt/instances/instance1', 'instance'), (p, i))

    def test_index(self):
        page_mock = mock.Mock()
        self.management._paginated = page_mock
        self.management.index(deleted=True)
        page_mock.assert_called_with('/mgmt/instances?deleted=true',
                                     'instances', None, None)
        self.management.index(deleted=False)
        page_mock.assert_called_with('/mgmt/instances?deleted=false',
                                     'instances', None, None)
        self.management.index(deleted=True, limit=10, marker="foo")
        page_mock.assert_called_with('/mgmt/instances?deleted=true',
                                     'instances', 10, "foo")

    def test_root_enabled_history(self):
        self.management.api.client.get = mock.Mock(return_value=('resp', None))
        self.assertRaises(Exception,
                          self.management.root_enabled_history, "instance")
        body = {'root_history': 'rh'}
        self.management.api.client.get = mock.Mock(return_value=('resp', body))
        management.RootHistory.__init__ = mock.Mock(return_value=None)
        rh = self.management.root_enabled_history("instance")
        self.assertTrue(isinstance(rh, management.RootHistory))

    def test__action(self):
        resp = mock.Mock()
        self.management.api.client.post = mock.Mock(
            return_value=(resp, 'body')
        )
        resp.status_code = 200
        self.management._action(1, 'body')
        self.assertEqual(1, self.management.api.client.post.call_count)
        resp.status_code = 400
        self.assertRaises(Exception, self.management._action, 1, 'body')
        self.assertEqual(2, self.management.api.client.post.call_count)

    def _mock_action(self):
        self.body_ = ""

        def side_effect_func(instance_id, body):
            self.body_ = body
        self.management._action = mock.Mock(side_effect=side_effect_func)

    def test_stop(self):
        self._mock_action()
        self.management.stop(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'stop': {}}, self.body_)

    def test_reboot(self):
        self._mock_action()
        self.management.reboot(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'reboot': {}}, self.body_)

    def test_migrate(self):
        self._mock_action()
        self.management.migrate(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'migrate': {}}, self.body_)

    def test_migrate_to_host(self):
        hostname = 'hostname2'
        self._mock_action()
        self.management.migrate(1, host=hostname)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'migrate': {'host': hostname}}, self.body_)

    def test_update(self):
        self._mock_action()
        self.management.update(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'update': {}}, self.body_)

    def test_reset_task_status(self):
        self._mock_action()
        self.management.reset_task_status(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'reset-task-status': {}}, self.body_)


class MgmtFlavorsTest(testtools.TestCase):

    def setUp(self):
        super(MgmtFlavorsTest, self).setUp()
        self.orig__init = management.MgmtFlavors.__init__
        management.MgmtFlavors.__init__ = mock.Mock(return_value=None)
        self.flavors = management.MgmtFlavors()
        self.flavors.api = mock.Mock()
        self.flavors.api.client = mock.Mock()
        self.flavors.resource_class = mock.Mock(return_value="flavor-1")
        self.orig_base_getid = base.getid
        base.getid = mock.Mock(return_value="flavor1")

    def tearDown(self):
        super(MgmtFlavorsTest, self).tearDown()
        management.MgmtFlavors.__init__ = self.orig__init
        base.getid = self.orig_base_getid

    def test_create(self):
        def side_effect_func(path, body, inst):
            return path, body, inst

        self.flavors._create = mock.Mock(side_effect=side_effect_func)
        p, b, i = self.flavors.create("test-name", 1024, 30, 2, 1)
        self.assertEqual("/mgmt/flavors", p)
        self.assertEqual("flavor", i)
        self.assertEqual("test-name", b["flavor"]["name"])
        self.assertEqual(1024, b["flavor"]["ram"])
        self.assertEqual(2, b["flavor"]["vcpu"])
        self.assertEqual(1, b["flavor"]["flavor_id"])
