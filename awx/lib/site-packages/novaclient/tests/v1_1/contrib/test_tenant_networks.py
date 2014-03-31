# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

from novaclient import extension
from novaclient.v1_1.contrib import tenant_networks

from novaclient.tests import utils
from novaclient.tests.v1_1.contrib import fakes


extensions = [
    extension.Extension(tenant_networks.__name__.split(".")[-1],
                        tenant_networks),
]
cs = fakes.FakeClient(extensions=extensions)


class TenantNetworkExtensionTests(utils.TestCase):
    def test_list_tenant_networks(self):
        nets = cs.tenant_networks.list()
        cs.assert_called('GET', '/os-tenant-networks')
        self.assertTrue(len(nets) > 0)

    def test_get_tenant_network(self):
        cs.tenant_networks.get(1)
        cs.assert_called('GET', '/os-tenant-networks/1')

    def test_create_tenant_networks(self):
        cs.tenant_networks.create(label="net",
                                  cidr="10.0.0.0/24")
        cs.assert_called('POST', '/os-tenant-networks')

    def test_delete_tenant_networks(self):
        cs.tenant_networks.delete(1)
        cs.assert_called('DELETE', '/os-tenant-networks/1')
