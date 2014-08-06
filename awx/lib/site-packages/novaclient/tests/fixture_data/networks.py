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
from novaclient.tests.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-networks'

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_networks = {
            'networks': [
                {
                    "label": "1",
                    "cidr": "10.0.0.0/24",
                    'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                    'id': '1'
                }
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_networks),
                               content_type='application/json')

        def post_os_networks(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            data = jsonutils.dumps({'network': body})
            return 202, headers, data

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_os_networks,
                               content_type='application/json')

        get_os_networks_1 = {'network': {"label": "1", "cidr": "10.0.0.0/24"}}

        httpretty.register_uri(httpretty.GET, self.url(1),
                               body=jsonutils.dumps(get_os_networks_1),
                               content_type='application/json')

        httpretty.register_uri(httpretty.DELETE,
                               self.url('networkdelete'),
                               stauts=202)

        for u in ('add', 'networkdisassociate/action', 'networktest/action',
                  '1/action', '2/action'):
            httpretty.register_uri(httpretty.POST, self.url(u), stauts=202)
