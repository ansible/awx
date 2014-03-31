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
from novaclient.v1_1 import limits


cs = fakes.FakeClient()


class LimitsTest(utils.TestCase):

    def test_get_limits(self):
        obj = cs.limits.get()
        cs.assert_called('GET', '/limits')
        self.assertIsInstance(obj, limits.Limits)

    def test_get_limits_for_a_tenant(self):
        obj = cs.limits.get(tenant_id=1234)
        cs.assert_called('GET', '/limits?tenant_id=1234')
        self.assertIsInstance(obj, limits.Limits)

    def test_absolute_limits(self):
        obj = cs.limits.get()

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
        obj = cs.limits.get(reserved=True)

        expected = (
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5),
            limits.AbsoluteLimit("maxImageMeta", 5),
            limits.AbsoluteLimit("maxPersonality", 5),
            limits.AbsoluteLimit("maxPersonalitySize", 10240),
        )

        cs.assert_called('GET', '/limits?reserved=1')
        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertTrue(limit in expected)

    def test_rate_limits(self):
        obj = cs.limits.get()

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
