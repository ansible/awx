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
from novaclient.tests.fixture_data import keypairs as data
from novaclient.tests import utils
from novaclient.v1_1 import keypairs


class KeypairsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    def setUp(self):
        super(KeypairsTest, self).setUp()
        self.keypair_type = self._get_keypair_type()
        self.keypair_prefix = self._get_keypair_prefix()

    def _get_keypair_type(self):
        return keypairs.Keypair

    def _get_keypair_prefix(self):
        return keypairs.KeypairManager.keypair_prefix

    def test_get_keypair(self):
        kp = self.cs.keypairs.get('test')
        self.assert_called('GET', '/%s/test' % self.keypair_prefix)
        self.assertIsInstance(kp, keypairs.Keypair)
        self.assertEqual('test', kp.name)

    def test_list_keypairs(self):
        kps = self.cs.keypairs.list()
        self.assert_called('GET', '/%s' % self.keypair_prefix)
        [self.assertIsInstance(kp, keypairs.Keypair) for kp in kps]

    def test_delete_keypair(self):
        kp = self.cs.keypairs.list()[0]
        kp.delete()
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)
        self.cs.keypairs.delete('test')
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)
        self.cs.keypairs.delete(kp)
        self.assert_called('DELETE', '/%s/test' % self.keypair_prefix)

    def test_create_keypair(self):
        kp = self.cs.keypairs.create("foo")
        self.assert_called('POST', '/%s' % self.keypair_prefix)
        self.assertIsInstance(kp, keypairs.Keypair)

    def test_import_keypair(self):
        kp = self.cs.keypairs.create("foo", "fake-public-key")
        self.assert_called('POST', '/%s' % self.keypair_prefix)
        self.assertIsInstance(kp, keypairs.Keypair)
