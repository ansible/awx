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

import fixtures
import httpretty
from keystoneclient.auth.identity import v2
from keystoneclient import session

from novaclient.openstack.common import jsonutils
from novaclient.v1_1 import client as v1_1client
from novaclient.v3 import client as v3client

IDENTITY_URL = 'http://identityserver:5000/v2.0'
COMPUTE_URL = 'http://compute.host'


class V1(fixtures.Fixture):

    def __init__(self, compute_url=COMPUTE_URL, identity_url=IDENTITY_URL):
        super(V1, self).__init__()
        self.identity_url = identity_url
        self.compute_url = compute_url
        self.client = None

        self.token = {
            'access': {
                "token": {
                    "id": "ab48a9efdfedb23ty3494",
                    "expires": "2010-11-01T03:32:15-05:00",
                    "tenant": {
                        "id": "345",
                        "name": "My Project"
                    }
                },
                "user": {
                    "id": "123",
                    "name": "jqsmith",
                    "roles": [
                        {
                            "id": "234",
                            "name": "compute:admin",
                        },
                        {
                            "id": "235",
                            "name": "object-store:admin",
                            "tenantId": "1",
                        }
                    ],
                    "roles_links": [],
                },
                "serviceCatalog": [
                    {
                        "name": "Cloud Servers",
                        "type": "compute",
                        "endpoints": [
                            {
                                "publicURL": self.compute_url,
                                "internalURL": "https://compute1.host/v1/1",
                            },
                        ],
                        "endpoints_links": [],
                    },
                    {
                        "name": "Cloud Servers",
                        "type": "computev3",
                        "endpoints": [
                            {
                                "publicURL": self.compute_url,
                                "internalURL": "https://compute1.host/v1/1",
                            },
                        ],
                        "endpoints_links": [],
                    },
                ],
            }
        }

    def setUp(self):
        super(V1, self).setUp()
        httpretty.enable()
        self.addCleanup(httpretty.disable)

        auth_url = '%s/tokens' % self.identity_url
        httpretty.register_uri(httpretty.POST, auth_url,
                               body=jsonutils.dumps(self.token),
                               content_type='application/json')
        self.client = self.new_client()

    def new_client(self):
        return v1_1client.Client(username='xx',
                                 api_key='xx',
                                 project_id='xx',
                                 auth_url=self.identity_url)


class V3(V1):

    def new_client(self):
        return v3client.Client(username='xx',
                               password='xx',
                               project_id='xx',
                               auth_url=self.identity_url)


class SessionV1(V1):

    def new_client(self):
        self.session = session.Session()
        self.session.auth = v2.Password(self.identity_url, 'xx', 'xx')
        return v1_1client.Client(session=self.session)


class SessionV3(V1):

    def new_client(self):
        self.session = session.Session()
        self.session.auth = v2.Password(self.identity_url, 'xx', 'xx')
        return v3client.Client(session=self.session)
