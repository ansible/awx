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

from keystoneclient.generic import client
from keystoneclient.tests.unit.v3 import utils


class DiscoverKeystoneTests(utils.UnauthenticatedTestCase):
    def setUp(self):
        super(DiscoverKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "versions": {
                "values": [{"id": "v3.0",
                            "status": "beta",
                            "updated": "2013-03-06T00:00:00Z",
                            "links": [
                                {"rel": "self",
                                 "href": "http://127.0.0.1:5000/v3.0/", },
                                {"rel": "describedby",
                                 "type": "text/html",
                                 "href": "http://docs.openstack.org/api/"
                                         "openstack-identity-service/3/"
                                         "content/", },
                                {"rel": "describedby",
                                 "type": "application/pdf",
                                 "href": "http://docs.openstack.org/api/"
                                         "openstack-identity-service/3/"
                                         "identity-dev-guide-3.pdf", },
                            ]},
                           {"id": "v2.0",
                            "status": "beta",
                            "updated": "2013-03-06T00:00:00Z",
                            "links": [
                                {"rel": "self",
                                 "href": "http://127.0.0.1:5000/v2.0/", },
                                {"rel": "describedby",
                                 "type": "text/html",
                                 "href": "http://docs.openstack.org/api/"
                                         "openstack-identity-service/2.0/"
                                         "content/", },
                                {"rel": "describedby",
                                 "type": "application/pdf",
                                 "href": "http://docs.openstack.org/api/"
                                         "openstack-identity-service/2.0/"
                                         "identity-dev-guide-2.0.pdf", }
                            ]}],
            },
        }
        self.TEST_REQUEST_HEADERS = {
            'User-Agent': 'python-keystoneclient',
            'Accept': 'application/json',
        }

    def test_get_version_local(self):
        self.requests_mock.get("http://localhost:35357/",
                               status_code=300,
                               json=self.TEST_RESPONSE_DICT)

        cs = client.Client()
        versions = cs.discover()
        self.assertIsInstance(versions, dict)
        self.assertIn('message', versions)
        self.assertIn('v3.0', versions)
        self.assertEqual(
            versions['v3.0']['url'],
            self.TEST_RESPONSE_DICT['versions']['values'][0]['links'][0]
            ['href'])
        self.assertEqual(
            versions['v2.0']['url'],
            self.TEST_RESPONSE_DICT['versions']['values'][1]['links'][0]
            ['href'])
