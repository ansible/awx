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

    base_url = 'os-keypairs'

    def setUp(self):
        super(V1, self).setUp()
        keypair = {'fingerprint': 'FAKE_KEYPAIR', 'name': 'test'}

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps({'keypairs': [keypair]}),
                               content_type='application/json')

        httpretty.register_uri(httpretty.GET, self.url('test'),
                               body=jsonutils.dumps({'keypair': keypair}),
                               content_type='application/json')

        httpretty.register_uri(httpretty.DELETE, self.url('test'), status=202)

        def post_os_keypairs(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            assert list(body) == ['keypair']
            fakes.assert_has_keys(body['keypair'], required=['name'])
            return 202, headers, jsonutils.dumps({'keypair': keypair})

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_os_keypairs,
                               content_type='application/json')


class V3(V1):

    base_url = 'keypairs'
