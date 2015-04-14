# Copyright 2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import client


class FakeClient(fakes.FakeClient):
    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(fakes.FakeHTTPClient):
    def get_os_tenant_networks(self):
        return (200, {}, {
            'networks': [{"label": "1", "cidr": "10.0.0.0/24",
                          'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                          'id': '1'}]})

    def get_os_tenant_networks_1(self, **kw):
        return (200, {}, {
            'network': {"label": "1", "cidr": "10.0.0.0/24",
                        'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                        'id': '1'}})

    def post_os_tenant_networks(self, **kw):
        return (201, {}, {
            'network': {"label": "1", "cidr": "10.0.0.0/24",
                        'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                        'id': '1'}})

    def delete_os_tenant_networks_1(self, **kw):
        return (204, {}, None)

    def get_os_baremetal_nodes(self, **kw):
        return (
            200, {}, {
                'nodes': [
                    {
                        "id": 1,
                        "instance_uuid": None,
                        "interfaces": [],
                        "cpus": 2,
                        "local_gb": 10,
                        "memory_mb": 5,
                        "pm_address": "2.3.4.5",
                        "pm_user": "pmuser",
                        "pm_password": "pmpass",
                        "prov_mac_address": "aa:bb:cc:dd:ee:ff",
                        "prov_vlan_id": 1,
                        "service_host": "somehost",
                        "terminal_port": 8080,
                    }
                ]
            }
        )

    def get_os_baremetal_nodes_1(self, **kw):
        return (
            200, {}, {
                'node': {
                    "id": 1,
                    "instance_uuid": None,
                    "pm_address": "1.2.3.4",
                    "interfaces": [],
                    "cpus": 2,
                    "local_gb": 10,
                    "memory_mb": 5,
                    "pm_user": "pmuser",
                    "pm_password": "pmpass",
                    "prov_mac_address": "aa:bb:cc:dd:ee:ff",
                    "prov_vlan_id": 1,
                    "service_host": "somehost",
                    "terminal_port": 8080,
                }
            }
        )

    def post_os_baremetal_nodes(self, **kw):
        return (
            200, {}, {
                'node': {
                    "id": 1,
                    "instance_uuid": None,
                    "cpus": 2,
                    "local_gb": 10,
                    "memory_mb": 5,
                    "pm_address": "2.3.4.5",
                    "pm_user": "pmuser",
                    "pm_password": "pmpass",
                    "prov_mac_address": "aa:bb:cc:dd:ee:ff",
                    "prov_vlan_id": 1,
                    "service_host": "somehost",
                    "terminal_port": 8080,
                }
            }
        )

    def delete_os_baremetal_nodes_1(self, **kw):
        return (202, {}, {})

    def post_os_baremetal_nodes_1_action(self, **kw):
        body = kw['body']
        action = list(body)[0]
        if action == "add_interface":
            return (
                200, {}, {
                    'interface': {
                        "id": 2,
                        "address": "bb:cc:dd:ee:ff:aa",
                        "datapath_id": 1,
                        "port_no": 2,
                    }
                }
            )
        elif action == "remove_interface":
            return (202, {}, {})
        else:
            return (500, {}, {})

    def post_os_assisted_volume_snapshots(self, **kw):
        return (202, {}, {'snapshot': {'id': 'blah', 'volumeId': '1'}})

    def delete_os_assisted_volume_snapshots_x(self, **kw):
        return (202, {}, {})

    def post_os_server_external_events(self, **kw):
        return (200, {}, {
            'events': [
                {'name': 'test-event',
                 'status': 'completed',
                 'tag': 'tag',
                 'server_uuid': 'fake-uuid1'},
                {'name': 'test-event',
                 'status': 'completed',
                 'tag': 'tag',
                 'server_uuid': 'fake-uuid2'}]})
