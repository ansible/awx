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
from keystoneclient.v2_0 import services


class ServiceTests(utils.TestCase):
    def setUp(self):
        super(ServiceTests, self).setUp()

        self.NOVA_SERVICE_ID = uuid.uuid4().hex
        self.KEYSTONE_SERVICE_ID = uuid.uuid4().hex

        self.TEST_SERVICES = {
            "OS-KSADM:services": {
                "values": [
                    {
                        "name": "nova",
                        "type": "compute",
                        "description": "Nova-compatible service.",
                        "id": self.NOVA_SERVICE_ID
                    },
                    {
                        "name": "keystone",
                        "type": "identity",
                        "description": "Keystone-compatible service.",
                        "id": self.KEYSTONE_SERVICE_ID
                    },
                ],
            },
        }

    def test_create(self):
        req_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
            }
        }
        service_id = uuid.uuid4().hex
        resp_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
                "id": service_id,
            }
        }
        self.stub_url('POST', ['OS-KSADM', 'services'], json=resp_body)

        service = self.client.services.create(
            req_body['OS-KSADM:service']['name'],
            req_body['OS-KSADM:service']['type'],
            req_body['OS-KSADM:service']['description'])
        self.assertIsInstance(service, services.Service)
        self.assertEqual(service.id, service_id)
        self.assertEqual(service.name, req_body['OS-KSADM:service']['name'])
        self.assertRequestBodyIs(json=req_body)

    def test_delete(self):
        self.stub_url('DELETE',
                      ['OS-KSADM', 'services', self.NOVA_SERVICE_ID],
                      status_code=204)

        self.client.services.delete(self.NOVA_SERVICE_ID)

    def test_get(self):
        test_services = self.TEST_SERVICES['OS-KSADM:services']['values'][0]

        self.stub_url('GET', ['OS-KSADM', 'services', self.NOVA_SERVICE_ID],
                      json={'OS-KSADM:service': test_services})

        service = self.client.services.get(self.NOVA_SERVICE_ID)
        self.assertIsInstance(service, services.Service)
        self.assertEqual(service.id, self.NOVA_SERVICE_ID)
        self.assertEqual(service.name, 'nova')
        self.assertEqual(service.type, 'compute')

    def test_list(self):
        self.stub_url('GET', ['OS-KSADM', 'services'],
                      json=self.TEST_SERVICES)

        service_list = self.client.services.list()
        [self.assertIsInstance(r, services.Service)
         for r in service_list]
