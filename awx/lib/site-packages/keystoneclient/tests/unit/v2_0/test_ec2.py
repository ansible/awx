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

from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import ec2


class EC2Tests(utils.TestCase):

    def test_create(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        req_body = {
            "tenant_id": tenant_id,
        }
        resp_body = {
            "credential": {
                "access": "access",
                "secret": "secret",
                "tenant_id": tenant_id,
                "created": "12/12/12",
                "enabled": True,
            }
        }
        self.stub_url('POST', ['users', user_id, 'credentials',
                      'OS-EC2'], json=resp_body)

        cred = self.client.ec2.create(user_id, tenant_id)
        self.assertIsInstance(cred, ec2.EC2)
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')
        self.assertRequestBodyIs(json=req_body)

    def test_get(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        resp_body = {
            "credential": {
                "access": "access",
                "secret": "secret",
                "tenant_id": tenant_id,
                "created": "12/12/12",
                "enabled": True,
            }
        }
        self.stub_url('GET', ['users', user_id, 'credentials',
                              'OS-EC2', 'access'], json=resp_body)

        cred = self.client.ec2.get(user_id, 'access')
        self.assertIsInstance(cred, ec2.EC2)
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')

    def test_list(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        resp_body = {
            "credentials": {
                "values": [
                    {
                        "access": "access",
                        "secret": "secret",
                        "tenant_id": tenant_id,
                        "created": "12/12/12",
                        "enabled": True,
                    },
                    {
                        "access": "another",
                        "secret": "key",
                        "tenant_id": tenant_id,
                        "created": "12/12/31",
                        "enabled": True,
                    }
                ]
            }
        }
        self.stub_url('GET', ['users', user_id, 'credentials',
                              'OS-EC2'], json=resp_body)

        creds = self.client.ec2.list(user_id)
        self.assertEqual(len(creds), 2)
        cred = creds[0]
        self.assertIsInstance(cred, ec2.EC2)
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')

    def test_delete(self):
        user_id = 'usr'
        access = 'access'
        self.stub_url('DELETE', ['users', user_id, 'credentials',
                                 'OS-EC2', access], status_code=204)
        self.client.ec2.delete(user_id, access)
