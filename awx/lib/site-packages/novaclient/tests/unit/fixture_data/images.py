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

from oslo.serialization import jsonutils

from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base


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

        headers = {'Content-Type': 'application/json'}

        self.requests.register_uri('GET', self.url(),
                                   json=get_images,
                                   headers=headers)

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

        self.requests.register_uri('GET', self.url('detail'),
                                   json={'images': [image_1, image_2]},
                                   headers=headers)

        self.requests.register_uri('GET', self.url(1),
                                   json={'image': image_1},
                                   headers=headers)

        self.requests.register_uri('GET', self.url(2),
                                   json={'image': image_2},
                                   headers=headers)

        self.requests.register_uri('GET', self.url(456),
                                   json={'image': image_2},
                                   headers=headers)

        def post_images(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['image']
            fakes.assert_has_keys(body['image'], required=['serverId', 'name'])
            return images_1

        self.requests.register_uri('POST', self.url(),
                                   json=post_images,
                                   headers=headers,
                                   status_code=202)

        def post_images_1_metadata(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['metadata']
            fakes.assert_has_keys(body['metadata'], required=['test_key'])
            return {'metadata': image_1['metadata']}

        self.requests.register_uri('POST', self.url(1, 'metadata'),
                                   json=post_images_1_metadata,
                                   headers=headers)

        for u in (1, 2, '1/metadata/test_key'):
            self.requests.register_uri('DELETE', self.url(u), status_code=204)

        image_headers = {'x-image-meta-id': '1',
                         'x-image-meta-name': 'CentOS 5.2',
                         'x-image-meta-updated': '2010-10-10T12:00:00Z',
                         'x-image-meta-created': '2010-10-10T12:00:00Z',
                         'x-image-meta-status': 'ACTIVE',
                         'x-image-meta-property-test-key': 'test_value'}
        self.requests.register_uri('HEAD', self.url(1), headers=image_headers)


class V3(V1):

    base_url = 'v1/images'
