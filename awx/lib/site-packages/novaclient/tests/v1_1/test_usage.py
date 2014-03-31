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

import datetime

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes
from novaclient.v1_1 import usage


class UsageTest(utils.TestCase):
    def setUp(self):
        super(UsageTest, self).setUp()
        self.cs = self._get_fake_client()
        self.usage_type = self._get_usage_type()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_usage_type(self):
        return usage.Usage

    def test_usage_list(self, detailed=False):
        now = datetime.datetime.now()
        usages = self.cs.usage.list(now, now, detailed)

        self.cs.assert_called('GET',
                         "/os-simple-tenant-usage?" +
                         ("start=%s&" % now.isoformat()) +
                         ("end=%s&" % now.isoformat()) +
                         ("detailed=%s" % int(bool(detailed))))
        [self.assertIsInstance(u, usage.Usage) for u in usages]

    def test_usage_list_detailed(self):
        self.test_usage_list(True)

    def test_usage_get(self):
        now = datetime.datetime.now()
        u = self.cs.usage.get("tenantfoo", now, now)

        self.cs.assert_called('GET',
                         "/os-simple-tenant-usage/tenantfoo?" +
                         ("start=%s&" % now.isoformat()) +
                         ("end=%s" % now.isoformat()))
        self.assertIsInstance(u, usage.Usage)
