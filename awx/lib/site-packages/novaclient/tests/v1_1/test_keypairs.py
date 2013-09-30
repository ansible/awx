from novaclient.v1_1 import keypairs
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class KeypairsTest(utils.TestCase):

    def test_get_keypair(self):
        kp = cs.keypairs.get('test')
        cs.assert_called('GET', '/os-keypairs/test')
        self.assertTrue(isinstance(kp, keypairs.Keypair))
        self.assertEqual(kp.name, 'test')

    def test_list_keypairs(self):
        kps = cs.keypairs.list()
        cs.assert_called('GET', '/os-keypairs')
        [self.assertTrue(isinstance(kp, keypairs.Keypair)) for kp in kps]

    def test_delete_keypair(self):
        kp = cs.keypairs.list()[0]
        kp.delete()
        cs.assert_called('DELETE', '/os-keypairs/test')
        cs.keypairs.delete('test')
        cs.assert_called('DELETE', '/os-keypairs/test')
        cs.keypairs.delete(kp)
        cs.assert_called('DELETE', '/os-keypairs/test')

    def test_create_keypair(self):
        kp = cs.keypairs.create("foo")
        cs.assert_called('POST', '/os-keypairs')
        self.assertTrue(isinstance(kp, keypairs.Keypair))

    def test_import_keypair(self):
        kp = cs.keypairs.create("foo", "fake-public-key")
        cs.assert_called('POST', '/os-keypairs')
        self.assertTrue(isinstance(kp, keypairs.Keypair))
