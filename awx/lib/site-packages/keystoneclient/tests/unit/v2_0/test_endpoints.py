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

import uuid

from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import endpoints


class EndpointTests(utils.TestCase):
    def setUp(self):
        super(EndpointTests, self).setUp()
        self.TEST_ENDPOINTS = {
            'endpoints': [
                {
                    'adminurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'id': '8f9531231e044e218824b0e58688d262',
                    'internalurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'publicurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'region': 'RegionOne',
                },
                {
                    'adminurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'id': '8f9531231e044e218824b0e58688d263',
                    'internalurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'publicurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'region': 'RegionOne',
                }
            ]
        }

    def test_create_with_optional_params(self):
        req_body = {
            "endpoint": {
                "region": "RegionOne",
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "internalurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "service_id": uuid.uuid4().hex,
            }
        }

        resp_body = {
            "endpoint": {
                "adminurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "region": "RegionOne",
                "id": uuid.uuid4().hex,
                "internalurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
            }
        }

        self.stub_url('POST', ['endpoints'], json=resp_body)

        endpoint = self.client.endpoints.create(
            region=req_body['endpoint']['region'],
            publicurl=req_body['endpoint']['publicurl'],
            adminurl=req_body['endpoint']['adminurl'],
            internalurl=req_body['endpoint']['internalurl'],
            service_id=req_body['endpoint']['service_id']
        )
        self.assertIsInstance(endpoint, endpoints.Endpoint)
        self.assertRequestBodyIs(json=req_body)

    def test_create_with_optional_params_as_none(self):
        req_body_without_defaults = {
            "endpoint": {
                "region": "RegionOne",
                "service_id": uuid.uuid4().hex,
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": None,
                "internalurl": None,
            }
        }

        resp_body = {
            "endpoint": {
                "region": "RegionOne",
                "id": uuid.uuid4().hex,
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": None,
                "internalurl": None,
            }
        }

        self.stub_url('POST', ['endpoints'], json=resp_body)

        endpoint_without_defaults = self.client.endpoints.create(
            region=req_body_without_defaults['endpoint']['region'],
            publicurl=req_body_without_defaults['endpoint']['publicurl'],
            service_id=req_body_without_defaults['endpoint']['service_id'],
            adminurl=None,
            internalurl=None
        )
        self.assertIsInstance(endpoint_without_defaults, endpoints.Endpoint)
        self.assertRequestBodyIs(json=req_body_without_defaults)

    def test_create_without_optional_params(self):
        req_body_without_defaults = {
            "endpoint": {
                "region": "RegionOne",
                "service_id": uuid.uuid4().hex,
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": None,
                "internalurl": None,
            }
        }

        resp_body = {
            "endpoint": {
                "region": "RegionOne",
                "id": uuid.uuid4().hex,
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": None,
                "internalurl": None,
            }
        }

        self.stub_url('POST', ['endpoints'], json=resp_body)

        endpoint_without_defaults = self.client.endpoints.create(
            region=req_body_without_defaults['endpoint']['region'],
            publicurl=req_body_without_defaults['endpoint']['publicurl'],
            service_id=req_body_without_defaults['endpoint']['service_id']
        )
        self.assertIsInstance(endpoint_without_defaults, endpoints.Endpoint)
        self.assertRequestBodyIs(json=req_body_without_defaults)

    def test_delete(self):
        self.stub_url('DELETE', ['endpoints', '8f953'], status_code=204)
        self.client.endpoints.delete('8f953')

    def test_list(self):
        self.stub_url('GET', ['endpoints'], json=self.TEST_ENDPOINTS)

        endpoint_list = self.client.endpoints.list()
        [self.assertIsInstance(r, endpoints.Endpoint)
         for r in endpoint_list]
