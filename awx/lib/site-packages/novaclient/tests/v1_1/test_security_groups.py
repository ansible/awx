from novaclient.v1_1 import security_groups
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class SecurityGroupsTest(utils.TestCase):
    def _do_test_list_security_groups(self, search_opts, path):
        sgs = cs.security_groups.list(search_opts=search_opts)
        cs.assert_called('GET', path)
        for sg in sgs:
            self.assertTrue(isinstance(sg, security_groups.SecurityGroup))

    def test_list_security_groups_all_tenants_on(self):
        self._do_test_list_security_groups(
            None, '/os-security-groups')

    def test_list_security_groups_all_tenants_on(self):
        self._do_test_list_security_groups(
            {'all_tenants': 1}, '/os-security-groups?all_tenants=1')

    def test_list_security_groups_all_tenants_off(self):
        self._do_test_list_security_groups(
            {'all_tenants': 0}, '/os-security-groups')

    def test_get_security_groups(self):
        sg = cs.security_groups.get(1)
        cs.assert_called('GET', '/os-security-groups/1')
        self.assertTrue(isinstance(sg, security_groups.SecurityGroup))
        self.assertEqual('1', str(sg))

    def test_delete_security_group(self):
        sg = cs.security_groups.list()[0]
        sg.delete()
        cs.assert_called('DELETE', '/os-security-groups/1')
        cs.security_groups.delete(1)
        cs.assert_called('DELETE', '/os-security-groups/1')
        cs.security_groups.delete(sg)
        cs.assert_called('DELETE', '/os-security-groups/1')

    def test_create_security_group(self):
        sg = cs.security_groups.create("foo", "foo barr")
        cs.assert_called('POST', '/os-security-groups')
        self.assertTrue(isinstance(sg, security_groups.SecurityGroup))

    def test_update_security_group(self):
        sg = cs.security_groups.list()[0]
        secgroup = cs.security_groups.update(sg, "update", "update")
        cs.assert_called('PUT', '/os-security-groups/1')
        self.assertTrue(isinstance(secgroup, security_groups.SecurityGroup))

    def test_refresh_security_group(self):
        sg = cs.security_groups.get(1)
        sg2 = cs.security_groups.get(1)
        self.assertEqual(sg.name, sg2.name)
        sg2.name = "should be test"
        self.assertNotEqual(sg.name, sg2.name)
        sg2.get()
        self.assertEqual(sg.name, sg2.name)
