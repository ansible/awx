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


class V1(base.Fixture):

    base_url = 'os-hypervisors'

    def setUp(self):
        super(V1, self).setUp()

        get_os_hypervisors = {
            'hypervisors': [
                {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                {'id': 5678, 'hypervisor_hostname': 'hyper2'},
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_hypervisors),
                               content_type='application/json')

        get_os_hypervisors_detail = {
            'hypervisors': [
                {
                    'id': 1234,
                    'service': {'id': 1, 'host': 'compute1'},
                    'vcpus': 4,
                    'memory_mb': 10 * 1024,
                    'local_gb': 250,
                    'vcpus_used': 2,
                    'memory_mb_used': 5 * 1024,
                    'local_gb_used': 125,
                    'hypervisor_type': 'xen',
                    'hypervisor_version': 3,
                    'hypervisor_hostname': 'hyper1',
                    'free_ram_mb': 5 * 1024,
                    'free_disk_gb': 125,
                    'current_workload': 2,
                    'running_vms': 2,
                    'cpu_info': 'cpu_info',
                    'disk_available_least': 100
                },
                {
                    'id': 2,
                     'service': {'id': 2, 'host': 'compute2'},
                     'vcpus': 4,
                     'memory_mb': 10 * 1024,
                     'local_gb': 250,
                     'vcpus_used': 2,
                     'memory_mb_used': 5 * 1024,
                     'local_gb_used': 125,
                     'hypervisor_type': 'xen',
                     'hypervisor_version': 3,
                     'hypervisor_hostname': 'hyper2',
                     'free_ram_mb': 5 * 1024,
                     'free_disk_gb': 125,
                     'current_workload': 2,
                     'running_vms': 2,
                     'cpu_info': 'cpu_info',
                     'disk_available_least': 100
                }
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url('detail'),
                               body=jsonutils.dumps(get_os_hypervisors_detail),
                               content_type='application/json')

        get_os_hypervisors_stats = {
            'hypervisor_statistics': {
                'count': 2,
                'vcpus': 8,
                'memory_mb': 20 * 1024,
                'local_gb': 500,
                'vcpus_used': 4,
                'memory_mb_used': 10 * 1024,
                'local_gb_used': 250,
                'free_ram_mb': 10 * 1024,
                'free_disk_gb': 250,
                'current_workload': 4,
                'running_vms': 4,
                'disk_available_least': 200,
            }
        }

        httpretty.register_uri(httpretty.GET, self.url('statistics'),
                               body=jsonutils.dumps(get_os_hypervisors_stats),
                               content_type='application/json')

        get_os_hypervisors_search = {
            'hypervisors': [
                {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                {'id': 5678, 'hypervisor_hostname': 'hyper2'}
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url('hyper', 'search'),
                               body=jsonutils.dumps(get_os_hypervisors_search),
                               content_type='application/json')

        get_hyper_server = {
            'hypervisors': [
                {
                    'id': 1234,
                    'hypervisor_hostname': 'hyper1',
                    'servers': [
                        {'name': 'inst1', 'uuid': 'uuid1'},
                        {'name': 'inst2', 'uuid': 'uuid2'}
                    ]
                },
                {
                    'id': 5678,
                    'hypervisor_hostname': 'hyper2',
                    'servers': [
                        {'name': 'inst3', 'uuid': 'uuid3'},
                        {'name': 'inst4', 'uuid': 'uuid4'}
                    ]
                }
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url('hyper', 'servers'),
                               body=jsonutils.dumps(get_hyper_server),
                               content_type='application/json')

        get_os_hypervisors_1234 = {
            'hypervisor': {
                'id': 1234,
                'service': {'id': 1, 'host': 'compute1'},
                'vcpus': 4,
                'memory_mb': 10 * 1024,
                'local_gb': 250,
                'vcpus_used': 2,
                'memory_mb_used': 5 * 1024,
                'local_gb_used': 125,
                'hypervisor_type': 'xen',
                'hypervisor_version': 3,
                'hypervisor_hostname': 'hyper1',
                'free_ram_mb': 5 * 1024,
                'free_disk_gb': 125,
                'current_workload': 2,
                'running_vms': 2,
                'cpu_info': 'cpu_info',
                'disk_available_least': 100
            }
        }

        httpretty.register_uri(httpretty.GET, self.url(1234),
                               body=jsonutils.dumps(get_os_hypervisors_1234),
                               content_type='application/json')

        get_os_hypervisors_uptime = {
            'hypervisor': {
                'id': 1234,
                'hypervisor_hostname': 'hyper1',
                'uptime': 'fake uptime'
            }
        }

        httpretty.register_uri(httpretty.GET, self.url(1234, 'uptime'),
                               body=jsonutils.dumps(get_os_hypervisors_uptime),
                               content_type='application/json')


class V3(V1):

    def setUp(self):
        super(V3, self).setUp()

        get_os_hypervisors_search = {
            'hypervisors': [
                {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                {'id': 5678, 'hypervisor_hostname': 'hyper2'}
            ]
        }

        httpretty.register_uri(httpretty.GET,
                               self.url('search', query='hyper'),
                               body=jsonutils.dumps(get_os_hypervisors_search),
                               content_type='application/json')

        get_1234_servers = {
            'hypervisor': {
                'id': 1234,
                'hypervisor_hostname': 'hyper1',
                'servers': [
                    {'name': 'inst1', 'id': 'uuid1'},
                    {'name': 'inst2', 'id': 'uuid2'}
                ]
            },
        }

        httpretty.register_uri(httpretty.GET, self.url(1234, 'servers'),
                               body=jsonutils.dumps(get_1234_servers),
                               content_type='application/json')
