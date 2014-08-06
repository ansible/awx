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

from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import limits as data
from novaclient.tests import utils
from novaclient.v1_1 import limits


class LimitsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_get_limits(self):
        obj = self.cs.limits.get()
        self.assert_called('GET', '/limits')
        self.assertIsInstance(obj, limits.Limits)

    def test_get_limits_for_a_tenant(self):
        obj = self.cs.limits.get(tenant_id=1234)
        self.assert_called('GET', '/limits?tenant_id=1234')
        self.assertIsInstance(obj, limits.Limits)

    def test_absolute_limits(self):
        obj = self.cs.limits.get()

        expected = (
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5),
            limits.AbsoluteLimit("maxImageMeta", 5),
            limits.AbsoluteLimit("maxPersonality", 5),
            limits.AbsoluteLimit("maxPersonalitySize", 10240),
        )

        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertTrue(limit in expected)

    def test_absolute_limits_reserved(self):
        obj = self.cs.limits.get(reserved=True)

        expected = (
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5),
            limits.AbsoluteLimit("maxImageMeta", 5),
            limits.AbsoluteLimit("maxPersonality", 5),
            limits.AbsoluteLimit("maxPersonalitySize", 10240),
        )

        self.assert_called('GET', '/limits?reserved=1')
        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertTrue(limit in expected)

    def test_rate_limits(self):
        obj = self.cs.limits.get()

        expected = (
            limits.RateLimit('POST', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('PUT', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('DELETE', '*', '.*', 100, 100, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('POST', '*/servers', '^/servers', 25, 24, 'DAY',
                             '2011-12-15T22:42:45Z'),
        )

        rate_limits = list(obj.rate)
        self.assertEqual(len(rate_limits), len(expected))

        for limit in rate_limits:
            self.assertTrue(limit in expected)
