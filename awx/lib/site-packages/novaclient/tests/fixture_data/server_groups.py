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

    base_url = 'os-server-groups'

    def setUp(self):
        super(Fixture, self).setUp()

        server_groups = [
            {
                "members": [],
                "metadata": {},
                "id": "2cbd51f4-fafe-4cdb-801b-cf913a6f288b",
                "policies": [],
                "name": "ig1"
            },
            {
                "members": [],
                "metadata": {},
                "id": "4473bb03-4370-4bfb-80d3-dc8cffc47d94",
                "policies": ["anti-affinity"],
                "name": "ig2"
            },
            {
                "members": [],
                "metadata": {"key": "value"},
                "id": "31ab9bdb-55e1-4ac3-b094-97eeb1b65cc4",
                "policies": [], "name": "ig3"
            },
            {
                "members": ["2dccb4a1-02b9-482a-aa23-5799490d6f5d"],
                "metadata": {},
                "id": "4890bb03-7070-45fb-8453-d34556c87d94",
                "policies": ["anti-affinity"],
                "name": "ig2"
            }
        ]

        get_server_groups = {'server_groups': server_groups}
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_server_groups),
                               content_type='application/json')

        server = server_groups[0]
        server_json = jsonutils.dumps({'server_group': server})

        def _register(method, *args):
            httpretty.register_uri(method, self.url(*args), body=server_json)

        _register(httpretty.POST)
        _register(httpretty.POST, server['id'])
        _register(httpretty.GET, server['id'])
        _register(httpretty.PUT, server['id'])
        _register(httpretty.POST, server['id'], '/action')

        httpretty.register_uri(httpretty.DELETE, self.url(server['id']),
                               status=202)
