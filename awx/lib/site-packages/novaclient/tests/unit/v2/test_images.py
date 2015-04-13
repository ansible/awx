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
from novaclient.tests.unit.fixture_data import images as data
from novaclient.tests.unit import utils
from novaclient.v2 import images


class ImagesTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.V1

    def test_list_images(self):
        il = self.cs.images.list()
        self.assert_called('GET', '/images/detail')
        [self.assertIsInstance(i, images.Image) for i in il]
        self.assertEqual(2, len(il))

    def test_list_images_undetailed(self):
        il = self.cs.images.list(detailed=False)
        self.assert_called('GET', '/images')
        [self.assertIsInstance(i, images.Image) for i in il]

    def test_list_images_with_limit(self):
        self.cs.images.list(limit=4)
        self.assert_called('GET', '/images/detail?limit=4')

    def test_get_image_details(self):
        i = self.cs.images.get(1)
        self.assert_called('GET', '/images/1')
        self.assertIsInstance(i, images.Image)
        self.assertEqual(1, i.id)
        self.assertEqual('CentOS 5.2', i.name)

    def test_delete_image(self):
        self.cs.images.delete(1)
        self.assert_called('DELETE', '/images/1')

    def test_delete_meta(self):
        self.cs.images.delete_meta(1, {'test_key': 'test_value'})
        self.assert_called('DELETE', '/images/1/metadata/test_key')

    def test_set_meta(self):
        self.cs.images.set_meta(1, {'test_key': 'test_value'})
        self.assert_called('POST', '/images/1/metadata',
                           {"metadata": {'test_key': 'test_value'}})

    def test_find(self):
        i = self.cs.images.find(name="CentOS 5.2")
        self.assertEqual(1, i.id)
        self.assert_called('GET', '/images/1')

        iml = self.cs.images.findall(status='SAVING')
        self.assertEqual(1, len(iml))
        self.assertEqual('My Server Backup', iml[0].name)
