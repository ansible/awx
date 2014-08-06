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

    base_url = 'os-aggregates'

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_aggregates = {"aggregates": [
            {'id': '1',
             'name': 'test',
             'availability_zone': 'nova1'},
            {'id': '2',
             'name': 'test2',
             'availability_zone': 'nova1'},
        ]}

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_aggregates),
                               content_type='application/json')

        r = jsonutils.dumps({'aggregate': get_os_aggregates['aggregates'][0]})

        httpretty.register_uri(httpretty.POST, self.url(), body=r,
                               content_type='application/json')

        for agg_id in (1, 2):
            for method in (httpretty.GET, httpretty.PUT):
                httpretty.register_uri(method, self.url(agg_id), body=r,
                                       content_type='application/json')

            httpretty.register_uri(httpretty.POST, self.url(agg_id, 'action'),
                                   body=r, content_type='application/json')

        httpretty.register_uri(httpretty.DELETE, self.url(1), status=202)
