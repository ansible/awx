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

    base_url = 'os-agents'

    def setUp(self):
        super(Fixture, self).setUp()

        post_os_agents = {
            'agent': {
                'url': '/xxx/xxx/xxx',
                'hypervisor': 'kvm',
                'md5hash': 'add6bb58e139be103324d04d82d8f546',
                'version': '7.0',
                'architecture': 'x86',
                'os': 'win',
                'id': 1
            }
        }

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=jsonutils.dumps(post_os_agents),
                               content_type='application/json')

        put_os_agents_1 = {
            "agent": {
                "url": "/yyy/yyyy/yyyy",
                "version": "8.0",
                "md5hash": "add6bb58e139be103324d04d82d8f546",
                'id': 1
            }
        }

        httpretty.register_uri(httpretty.PUT, self.url(1),
                               body=jsonutils.dumps(put_os_agents_1),
                               content_type='application/json')

        httpretty.register_uri(httpretty.DELETE, self.url(1),
                               content_type='application/json',
                               status=202)
