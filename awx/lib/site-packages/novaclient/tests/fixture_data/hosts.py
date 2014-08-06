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
from six.moves.urllib import parse

from novaclient.openstack.common import jsonutils
from novaclient.tests.fixture_data import base


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
        httpretty.register_uri(httpretty.GET, self.url('host'),
                               body=jsonutils.dumps(get_os_hosts_host),
                               content_type='application/json')

        def get_os_hosts(request, url, headers):
            host, query = parse.splitquery(url)
            zone = 'nova1'

            if query:
                qs = parse.parse_qs(query)
                try:
                    zone = qs['zone'][0]
                except Exception:
                    pass

            data = {
                'hosts': [
                    {
                        'host': 'host1',
                        'service': 'nova-compute',
                        'zone': zone
                    },
                    {
                        'host': 'host1',
                        'service': 'nova-cert',
                        'zone': zone
                    }
                ]
            }
            return 200, headers, jsonutils.dumps(data)

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=get_os_hosts,
                               content_type='application/json')

        get_os_hosts_sample_host = {
            'host': [
                {'resource': {'host': 'sample_host'}}
            ],
        }
        httpretty.register_uri(httpretty.GET, self.url('sample_host'),
                               body=jsonutils.dumps(get_os_hosts_sample_host),
                               content_type='application/json')

        httpretty.register_uri(httpretty.PUT, self.url('sample_host', 1),
                               body=jsonutils.dumps(self.put_host_1()),
                               content_type='application/json')

        httpretty.register_uri(httpretty.PUT, self.url('sample_host', 2),
                               body=jsonutils.dumps(self.put_host_2()),
                               content_type='application/json')

        httpretty.register_uri(httpretty.PUT, self.url('sample_host', 3),
                               body=jsonutils.dumps(self.put_host_3()),
                               content_type='application/json')

        url = self.url('sample_host', 'reboot')
        httpretty.register_uri(httpretty.GET, url,
                               body=jsonutils.dumps(self.get_host_reboot()),
                               content_type='application/json')

        url = self.url('sample_host', 'startup')
        httpretty.register_uri(httpretty.GET, url,
                               body=jsonutils.dumps(self.get_host_startup()),
                               content_type='application/json')

        url = self.url('sample_host', 'shutdown')
        httpretty.register_uri(httpretty.GET, url,
                               body=jsonutils.dumps(self.get_host_shutdown()),
                               content_type='application/json')

        def put_os_hosts_sample_host(request, url, headers):
            result = {'host': 'dummy'}
            result.update(jsonutils.loads(request.body.decode('utf-8')))
            return 200, headers, jsonutils.dumps(result)

        httpretty.register_uri(httpretty.PUT, self.url('sample_host'),
                               body=put_os_hosts_sample_host,
                               content_type='application/json')


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


class V3(V1):
    def put_host_1(self):
        return {'host': super(V3, self).put_host_1()}

    def put_host_2(self):
        return {'host': super(V3, self).put_host_2()}

    def put_host_3(self):
        return {'host': super(V3, self).put_host_3()}

    def get_host_reboot(self):
        return {'host': super(V3, self).get_host_reboot()}

    def get_host_startup(self):
        return {'host': super(V3, self).get_host_startup()}

    def get_host_shutdown(self):
        return {'host': super(V3, self).get_host_shutdown()}
