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

from keystoneclient import fixture

from cinderclient.tests.fixture_data import base
from cinderclient.v1 import client as v1client
from cinderclient.v2 import client as v2client


class Base(base.Fixture):

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)

        self.token = fixture.V2Token()
        self.token.set_scope()

    def setUp(self):
        super(Base, self).setUp()

        auth_url = '%s/tokens' % self.identity_url
        self.requests.register_uri('POST', auth_url,
                                   json=self.token,
                                   headers=self.json_headers)


class V1(Base):

    def __init__(self, *args, **kwargs):
        super(V1, self).__init__(*args, **kwargs)

        svc = self.token.add_service('volume')
        svc.add_endpoint(self.volume_url)

    def new_client(self):
        return v1client.Client(username='xx',
                               api_key='xx',
                               project_id='xx',
                               auth_url=self.identity_url)


class V2(Base):

    def __init__(self, *args, **kwargs):
        super(V2, self).__init__(*args, **kwargs)

        svc = self.token.add_service('volumev2')
        svc.add_endpoint(self.volume_url)

    def new_client(self):
        return v2client.Client(username='xx',
                               api_key='xx',
                               project_id='xx',
                               auth_url=self.identity_url)
