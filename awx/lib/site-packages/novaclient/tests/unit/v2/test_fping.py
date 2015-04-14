# Copyright 2012 OpenStack Foundation
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

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import fping as data
from novaclient.tests.unit import utils
from novaclient.v2 import fping


class FpingTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_fping_repr(self):
        r = self.cs.fping.get(1)
        self.assertEqual("<Fping: 1>", repr(r))

    def test_list_fpings(self):
        fl = self.cs.fping.list()
        self.assert_called('GET', '/os-fping')
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
            self.assertEqual("fake-project", f.project_id)
            self.assertEqual(True, f.alive)

    def test_list_fpings_all_tenants(self):
        fl = self.cs.fping.list(all_tenants=True)
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        self.assert_called('GET', '/os-fping?all_tenants=1')

    def test_list_fpings_exclude(self):
        fl = self.cs.fping.list(exclude=['1'])
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        self.assert_called('GET', '/os-fping?exclude=1')

    def test_list_fpings_include(self):
        fl = self.cs.fping.list(include=['1'])
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        self.assert_called('GET', '/os-fping?include=1')

    def test_get_fping(self):
        f = self.cs.fping.get(1)
        self.assert_called('GET', '/os-fping/1')
        self.assertIsInstance(f, fping.Fping)
        self.assertEqual("fake-project", f.project_id)
        self.assertEqual(True, f.alive)
