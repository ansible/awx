#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import networks as data
from novaclient.tests import utils
from novaclient.v1_1 import networks


class NetworksTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_list_networks(self):
        fl = self.cs.networks.list()
        self.assert_called('GET', '/os-networks')
        [self.assertIsInstance(f, networks.Network) for f in fl]

    def test_get_network(self):
        f = self.cs.networks.get(1)
        self.assert_called('GET', '/os-networks/1')
        self.assertIsInstance(f, networks.Network)

    def test_delete(self):
        self.cs.networks.delete('networkdelete')
        self.assert_called('DELETE', '/os-networks/networkdelete')

    def test_create(self):
        f = self.cs.networks.create(label='foo')
        self.assert_called('POST', '/os-networks',
                           {'network': {'label': 'foo'}})
        self.assertIsInstance(f, networks.Network)

    def test_create_allparams(self):
        params = {
            'label': 'bar',
            'bridge': 'br0',
            'bridge_interface': 'int0',
            'cidr': '192.0.2.0/24',
            'cidr_v6': '2001:DB8::/32',
            'dns1': '1.1.1.1',
            'dns2': '1.1.1.2',
            'fixed_cidr': '198.51.100.0/24',
            'gateway': '192.0.2.1',
            'gateway_v6': '2001:DB8::1',
            'multi_host': 'T',
            'priority': '1',
            'project_id': '1',
            'vlan': 5,
            'vlan_start': 1,
            'vpn_start': 1,
            'mtu': 1500,
            'enable_dhcp': 'T',
            'dhcp_server': '1920.2.2',
            'share_address': 'T',
            'allowed_start': '192.0.2.10',
            'allowed_end': '192.0.2.20',
        }

        f = self.cs.networks.create(**params)
        self.assert_called('POST', '/os-networks', {'network': params})
        self.assertIsInstance(f, networks.Network)

    def test_associate_project(self):
        self.cs.networks.associate_project('networktest')
        self.assert_called('POST', '/os-networks/add',
                           {'id': 'networktest'})

    def test_associate_host(self):
        self.cs.networks.associate_host('networktest', 'testHost')
        self.assert_called('POST', '/os-networks/networktest/action',
                           {'associate_host': 'testHost'})

    def test_disassociate(self):
        self.cs.networks.disassociate('networkdisassociate')
        self.assert_called('POST',
                           '/os-networks/networkdisassociate/action',
                           {'disassociate': None})

    def test_disassociate_host_only(self):
        self.cs.networks.disassociate('networkdisassociate', True, False)
        self.assert_called('POST',
                           '/os-networks/networkdisassociate/action',
                           {'disassociate_host': None})

    def test_disassociate_project(self):
        self.cs.networks.disassociate('networkdisassociate', False, True)
        self.assert_called('POST',
                           '/os-networks/networkdisassociate/action',
                           {'disassociate_project': None})

    def test_add(self):
        self.cs.networks.add('networkadd')
        self.assert_called('POST', '/os-networks/add',
                           {'id': 'networkadd'})
