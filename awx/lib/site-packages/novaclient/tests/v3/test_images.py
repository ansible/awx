# Copyright 2013 IBM Corp.
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
from novaclient.tests.v3 import fakes
from novaclient.v3 import images


cs = fakes.FakeClient()


class ImagesTest(utils.TestCase):

    def test_list_images(self):
        il = cs.images.list()
        cs.assert_called('GET', '/v1/images/detail')
        for i in il:
            self.assertIsInstance(i, images.Image)

    def test_list_images_undetailed(self):
        il = cs.images.list(detailed=False)
        cs.assert_called('GET', '/v1/images')
        for i in il:
            self.assertIsInstance(i, images.Image)

    def test_list_images_with_limit(self):
        il = cs.images.list(limit=4)
        cs.assert_called('GET', '/v1/images/detail?limit=4')

    def test_get_image_details(self):
        i = cs.images.get(1)
        cs.assert_called('HEAD', '/v1/images/1')
        self.assertIsInstance(i, images.Image)
        self.assertEqual(i.id, '1')
        self.assertEqual(i.name, 'CentOS 5.2')

    def test_find(self):
        i = cs.images.find(name="CentOS 5.2")
        self.assertEqual(i.id, '1')
        cs.assert_called('GET', '/v1/images', pos=-2)
        cs.assert_called('HEAD', '/v1/images/1', pos=-1)

        iml = cs.images.findall(status='SAVING')
        self.assertEqual(len(iml), 1)
        self.assertEqual(iml[0].name, 'My Server Backup')
