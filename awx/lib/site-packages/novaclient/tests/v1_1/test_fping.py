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

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes
from novaclient.v1_1 import fping


cs = fakes.FakeClient()


class FpingTest(utils.TestCase):

    def test_fping_repr(self):
        r = cs.fping.get(1)
        self.assertEqual(repr(r), "<Fping: 1>")

    def test_list_fpings(self):
        fl = cs.fping.list()
        cs.assert_called('GET', '/os-fping')
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
            self.assertEqual(f.project_id, "fake-project")
            self.assertEqual(f.alive, True)

    def test_list_fpings_all_tenants(self):
        fl = cs.fping.list(all_tenants=True)
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        cs.assert_called('GET', '/os-fping?all_tenants=1')

    def test_list_fpings_exclude(self):
        fl = cs.fping.list(exclude=['1'])
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        cs.assert_called('GET', '/os-fping?exclude=1')

    def test_list_fpings_include(self):
        fl = cs.fping.list(include=['1'])
        for f in fl:
            self.assertIsInstance(f, fping.Fping)
        cs.assert_called('GET', '/os-fping?include=1')

    def test_get_fping(self):
        f = cs.fping.get(1)
        cs.assert_called('GET', '/os-fping/1')
        self.assertIsInstance(f, fping.Fping)
        self.assertEqual(f.project_id, "fake-project")
        self.assertEqual(f.alive, True)
