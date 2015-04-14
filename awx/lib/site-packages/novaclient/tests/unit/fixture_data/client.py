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
from keystoneclient.auth.identity import v2
from keystoneclient import fixture
from keystoneclient import session

from novaclient.v2 import client as v2client

IDENTITY_URL = 'http://identityserver:5000/v2.0'
COMPUTE_URL = 'http://compute.host'


class V1(fixtures.Fixture):

    def __init__(self, requests,
                 compute_url=COMPUTE_URL, identity_url=IDENTITY_URL):
        super(V1, self).__init__()
        self.identity_url = identity_url
        self.compute_url = compute_url
        self.client = None
        self.requests = requests

        self.token = fixture.V2Token()
        self.token.set_scope()

        s = self.token.add_service('compute')
        s.add_endpoint(self.compute_url)

        s = self.token.add_service('computev3')
        s.add_endpoint(self.compute_url)

    def setUp(self):
        super(V1, self).setUp()

        auth_url = '%s/tokens' % self.identity_url
        headers = {'X-Content-Type': 'application/json'}
        self.requests.register_uri('POST', auth_url,
                                   json=self.token,
                                   headers=headers)
        self.client = self.new_client()

    def new_client(self):
        return v2client.Client(username='xx',
                               api_key='xx',
                               project_id='xx',
                               auth_url=self.identity_url)


class SessionV1(V1):

    def new_client(self):
        self.session = session.Session()
        self.session.auth = v2.Password(self.identity_url, 'xx', 'xx')
        return v2client.Client(session=self.session)
