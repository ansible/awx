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
from six.moves.urllib import parse

from novaclient.tests.unit.fixture_data import base


class BaseFixture(base.Fixture):

    base_url = 'os-hosts'

    def setUp(self):
        super(BaseFixture, self).setUp()

        get_os_hosts_host = {
            'host': [
                {'resource': {'project': '(total)', 'host': 'dummy',
                 'cpu': 16, 'memory_mb': 32234, 'disk_gb': 128}},
                {'resource': {'project': '(used_now)', 'host': 'dummy',
                 'cpu': 1, 'memory_mb': 2075, 'disk_gb': 45}},
                {'resource': {'project': '(used_max)', 'host': 'dummy',
                 'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}},
                {'resource': {'project': 'admin', 'host': 'dummy',
                 'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}}
            ]
        }

        headers = {'Content-Type': 'application/json'}

        self.requests.register_uri('GET', self.url('host'),
                                   json=get_os_hosts_host,
                                   headers=headers)

        def get_os_hosts(request, context):
            host, query = parse.splitquery(request.url)
            zone = 'nova1'
            service = None

            if query:
                qs = parse.parse_qs(query)
                try:
                    zone = qs['zone'][0]
                except Exception:
                    pass

                try:
                    service = qs['service'][0]
                except Exception:
                    pass

            return {
                'hosts': [
                    {
                        'host': 'host1',
                        'service': service or 'nova-compute',
                        'zone': zone
                    },
                    {
                        'host': 'host1',
                        'service': service or 'nova-cert',
                        'zone': zone
                    }
                ]
            }

        self.requests.register_uri('GET', self.url(),
                                   json=get_os_hosts,
                                   headers=headers)

        get_os_hosts_sample_host = {
            'host': [
                {'resource': {'host': 'sample_host'}}
            ],
        }
        self.requests.register_uri('GET', self.url('sample_host'),
                                   json=get_os_hosts_sample_host,
                                   headers=headers)

        self.requests.register_uri('PUT', self.url('sample_host', 1),
                                   json=self.put_host_1(),
                                   headers=headers)

        self.requests.register_uri('PUT', self.url('sample_host', 2),
                                   json=self.put_host_2(),
                                   headers=headers)

        self.requests.register_uri('PUT', self.url('sample_host', 3),
                                   json=self.put_host_3(),
                                   headers=headers)

        self.requests.register_uri('GET', self.url('sample_host', 'reboot'),
                                   json=self.get_host_reboot(),
                                   headers=headers)

        self.requests.register_uri('GET', self.url('sample_host', 'startup'),
                                   json=self.get_host_startup(),
                                   headers=headers)

        self.requests.register_uri('GET', self.url('sample_host', 'shutdown'),
                                   json=self.get_host_shutdown(),
                                   headers=headers)

        def put_os_hosts_sample_host(request, context):
            result = {'host': 'dummy'}
            result.update(jsonutils.loads(request.body))
            return result

        self.requests.register_uri('PUT', self.url('sample_host'),
                                   json=put_os_hosts_sample_host,
                                   headers=headers)


class V1(BaseFixture):

    def put_host_1(self):
        return {'host': 'sample-host_1',
                'status': 'enabled'}

    def put_host_2(self):
        return {'host': 'sample-host_2',
                'maintenance_mode': 'on_maintenance'}

    def put_host_3(self):
        return {'host': 'sample-host_3',
                'status': 'enabled',
                'maintenance_mode': 'on_maintenance'}

    def get_host_reboot(self):
        return {'host': 'sample_host',
                'power_action': 'reboot'}

    def get_host_startup(self):
        return {'host': 'sample_host',
                'power_action': 'startup'}

    def get_host_shutdown(self):
        return {'host': 'sample_host',
                'power_action': 'shutdown'}
