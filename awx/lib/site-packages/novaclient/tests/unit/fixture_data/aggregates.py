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

from novaclient.tests.unit.fixture_data import base


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

        self.requests.register_uri('GET', self.url(),
                                   json=get_os_aggregates,
                                   headers=self.json_headers)

        get_aggregates_1 = {'aggregate': get_os_aggregates['aggregates'][0]}

        self.requests.register_uri('POST', self.url(),
                                   json=get_aggregates_1,
                                   headers=self.json_headers)

        for agg_id in (1, 2):
            for method in ('GET', 'PUT'):
                self.requests.register_uri(method, self.url(agg_id),
                                           json=get_aggregates_1,
                                           headers=self.json_headers)

            self.requests.register_uri('POST', self.url(agg_id, 'action'),
                                       json=get_aggregates_1,
                                       headers=self.json_headers)

        self.requests.register_uri('DELETE', self.url(1), status_code=202)
