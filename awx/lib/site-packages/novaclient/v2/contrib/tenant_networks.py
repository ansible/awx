# Copyright 2013 OpenStack Foundation
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

from novaclient import base
from novaclient.i18n import _
from novaclient.openstack.common import cliutils
from novaclient import utils


class TenantNetwork(base.Resource):
    def delete(self):
        self.manager.delete(network=self)


class TenantNetworkManager(base.ManagerWithFind):
    resource_class = base.Resource

    def list(self):
        return self._list('/os-tenant-networks', 'networks')

    def get(self, network):
        return self._get('/os-tenant-networks/%s' % base.getid(network),
                         'network')

    def delete(self, network):
        self._delete('/os-tenant-networks/%s' % base.getid(network))

    def create(self, label, cidr):
        body = {'network': {'label': label, 'cidr': cidr}}
        return self._create('/os-tenant-networks', body, 'network')


@cliutils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_net(cs, args):
    """
    DEPRECATED, Use tenant-network-show instead.
    """
    do_tenant_network_show(cs, args)


@cliutils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_tenant_network_show(cs, args):
    """
    Show a tenant network.
    """
    network = cs.tenant_networks.get(args.network_id)
    utils.print_dict(network._info)


def do_net_list(cs, args):
    """
    DEPRECATED, use tenant-network-list instead.
    """
    do_tenant_network_list(cs, args)


def do_tenant_network_list(cs, args):
    """
    List tenant networks.
    """
    networks = cs.tenant_networks.list()
    utils.print_list(networks, ['ID', 'Label', 'CIDR'])


@cliutils.arg(
    'label',
    metavar='<network_label>',
    help=_('Network label (ex. my_new_network)'))
@cliutils.arg(
    'cidr',
    metavar='<cidr>',
    help=_('IP block to allocate from (ex. 172.16.0.0/24 or 2001:DB8::/64)'))
def do_net_create(cs, args):
    """
    DEPRECATED, use tenant-network-create instead.
    """
    do_tenant_network_create(cs, args)


@cliutils.arg(
    'label',
    metavar='<network_label>',
    help=_('Network label (ex. my_new_network)'))
@cliutils.arg(
    'cidr',
    metavar='<cidr>',
    help=_('IP block to allocate from (ex. 172.16.0.0/24 or 2001:DB8::/64)'))
def do_tenant_network_create(cs, args):
    """
    Create a tenant network.
    """
    network = cs.tenant_networks.create(args.label, args.cidr)
    utils.print_dict(network._info)


@cliutils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_net_delete(cs, args):
    """
    DEPRECATED, use tenant-network-delete instead.
    """
    do_tenant_network_delete(cs, args)


@cliutils.arg('network_id', metavar='<network_id>', help='ID of network')
def do_tenant_network_delete(cs, args):
    """
    Delete a tenant network.
    """
    cs.tenant_networks.delete(args.network_id)
