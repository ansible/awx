# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import httpretty

from novaclient.openstack.common import jsonutils
from novaclient.tests import fakes
from novaclient.tests.fixture_data import base


class V1(base.Fixture):

    base_url = 'images'

    def setUp(self):
        super(V1, self).setUp()

        get_images = {
            'images': [
                {'id': 1, 'name': 'CentOS 5.2'},
                {'id': 2, 'name': 'My Server Backup'}
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_images),
                               content_type='application/json')

        image_1 = {
            'id': 1,
            'name': 'CentOS 5.2',
            "updated": "2010-10-10T12:00:00Z",
            "created": "2010-08-10T12:00:00Z",
            "status": "ACTIVE",
            "metadata": {
                "test_key": "test_value",
            },
            "links": {},
        }

        image_2 = {
            "id": 2,
            "name": "My Server Backup",
            "serverId": 1234,
            "updated": "2010-10-10T12:00:00Z",
            "created": "2010-08-10T12:00:00Z",
            "status": "SAVING",
            "progress": 80,
            "links": {},
        }

        get_images_detail = {'images': [image_1, image_2]}

        httpretty.register_uri(httpretty.GET, self.url('detail'),
                               body=jsonutils.dumps(get_images_detail),
                               content_type='application/json')

        get_images_1 = {'image': image_1}

        httpretty.register_uri(httpretty.GET, self.url(1),
                               body=jsonutils.dumps(get_images_1),
                               content_type='application/json')

        get_images_2 = {'image': image_2}

        httpretty.register_uri(httpretty.GET, self.url(2),
                               body=jsonutils.dumps(get_images_2),
                               content_type='application/json')

        httpretty.register_uri(httpretty.GET, self.url(456),
                               body=jsonutils.dumps(get_images_2),
                               content_type='application/json')

        def post_images(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            assert list(body) == ['image']
            fakes.assert_has_keys(body['image'], required=['serverId', 'name'])
            return 202, headers, jsonutils.dumps(images_1)

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_images,
                               content_type='application/json')

        def post_images_1_metadata(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            assert list(body) == ['metadata']
            fakes.assert_has_keys(body['metadata'], required=['test_key'])
            data = jsonutils.dumps({'metadata': image_1['metadata']})
            return 200, headers, data

        httpretty.register_uri(httpretty.POST, self.url(1, 'metadata'),
                               body=post_images_1_metadata,
                               content_type='application/json')

        for u in (1, 2, '1/metadata/test_key'):
            httpretty.register_uri(httpretty.DELETE, self.url(u),
                                   status=204)

        httpretty.register_uri(httpretty.HEAD, self.url(1), status=200,
                               x_image_meta_id=1,
                               x_image_meta_name='CentOS 5.2',
                               x_image_meta_updated='2010-10-10T12:00:00Z',
                               x_image_meta_created='2010-10-10T12:00:00Z',
                               x_image_meta_status='ACTIVE',
                               x_image_meta_property_test_key='test_value')


class V3(V1):

    base_url = 'v1/images'
