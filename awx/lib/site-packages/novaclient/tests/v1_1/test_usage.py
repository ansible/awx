import datetime

from novaclient.v1_1 import usage
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class UsageTest(utils.TestCase):

    def test_usage_list(self, detailed=False):
        now = datetime.datetime.now()
        usages = cs.usage.list(now, now, detailed)

        cs.assert_called('GET',
                         "/os-simple-tenant-usage?" +
                         ("start=%s&" % now.isoformat()) +
                         ("end=%s&" % now.isoformat()) +
                         ("detailed=%s" % int(bool(detailed))))
        [self.assertTrue(isinstance(u, usage.Usage)) for u in usages]

    def test_usage_list_detailed(self):
        self.test_usage_list(True)

    def test_usage_get(self):
        now = datetime.datetime.now()
        u = cs.usage.get("tenantfoo", now, now)

        cs.assert_called('GET',
                         "/os-simple-tenant-usage/tenantfoo?" +
                         ("start=%s&" % now.isoformat()) +
                         ("end=%s" % now.isoformat()))
        self.assertTrue(isinstance(u, usage.Usage))
