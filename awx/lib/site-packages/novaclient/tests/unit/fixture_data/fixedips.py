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

    base_url = 'os-fixed-ips'

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_fixed_ips = {
            "fixed_ip": {
                'cidr': '192.168.1.0/24',
                'address': '192.168.1.1',
                'hostname': 'foo',
                'host': 'bar'
            }
        }

        self.requests.register_uri('GET', self.url('192.168.1.1'),
                                   json=get_os_fixed_ips,
                                   headers=self.json_headers)

        self.requests.register_uri('POST',
                                   self.url('192.168.1.1', 'action'),
                                   headers=self.json_headers,
                                   status_code=202)
