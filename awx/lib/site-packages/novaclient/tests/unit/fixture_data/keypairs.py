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

    base_url = 'os-keypairs'

    def setUp(self):
        super(V1, self).setUp()
        keypair = {'fingerprint': 'FAKE_KEYPAIR', 'name': 'test'}

        headers = {'Content-Type': 'application/json'}

        self.requests.register_uri('GET', self.url(),
                                   json={'keypairs': [keypair]},
                                   headers=headers)

        self.requests.register_uri('GET', self.url('test'),
                                   json={'keypair': keypair},
                                   headers=headers)

        self.requests.register_uri('DELETE', self.url('test'), status_code=202)

        def post_os_keypairs(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['keypair']
            fakes.assert_has_keys(body['keypair'], required=['name'])
            return {'keypair': keypair}

        self.requests.register_uri('POST', self.url(),
                                   json=post_os_keypairs,
                                   headers=headers)
