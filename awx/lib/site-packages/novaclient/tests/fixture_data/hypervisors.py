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

        self.headers = {'Content-Type': 'application/json'}

        self.requests.register_uri('GET', self.url(),
                                   json=get_os_hypervisors,
                                   headers=self.headers)

        get_os_hypervisors_detail = {
            'hypervisors': [
                {
                    'id': 1234,
                    'service': {
                        'id': 1,
                        'host': 'compute1',
                    },
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
                    'service': {
                        'id': 2,
                        'host': 'compute2',
                    },
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

        self.requests.register_uri('GET', self.url('detail'),
                                   json=get_os_hypervisors_detail,
                                   headers=self.headers)

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

        self.requests.register_uri('GET', self.url('statistics'),
                                   json=get_os_hypervisors_stats,
                                   headers=self.headers)

        get_os_hypervisors_search = {
            'hypervisors': [
                {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                {'id': 5678, 'hypervisor_hostname': 'hyper2'}
            ]
        }

        self.requests.register_uri('GET', self.url('hyper', 'search'),
                                   json=get_os_hypervisors_search,
                                   headers=self.headers)

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

        self.requests.register_uri('GET', self.url('hyper', 'servers'),
                                   json=get_hyper_server,
                                   headers=self.headers)

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

        self.requests.register_uri('GET', self.url(1234),
                                   json=get_os_hypervisors_1234,
                                   headers=self.headers)

        get_os_hypervisors_uptime = {
            'hypervisor': {
                'id': 1234,
                'hypervisor_hostname': 'hyper1',
                'uptime': 'fake uptime'
            }
        }

        self.requests.register_uri('GET', self.url(1234, 'uptime'),
                                   json=get_os_hypervisors_uptime,
                                   headers=self.headers)


class V3(V1):

    def setUp(self):
        super(V3, self).setUp()

        get_os_hypervisors_search = {
            'hypervisors': [
                {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                {'id': 5678, 'hypervisor_hostname': 'hyper2'}
            ]
        }

        self.requests.register_uri('GET',
                                   self.url('search', query='hyper'),
                                   json=get_os_hypervisors_search,
                                   headers=self.headers)

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

        self.requests.register_uri('GET', self.url(1234, 'servers'),
                                   json=get_1234_servers,
                                   headers=self.headers)
