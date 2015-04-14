# Copyright 2013 Mirantis Inc.
# Copyright 2014 Blue Box Group, Inc.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved
#
# Author: Ilya Shakhat, Mirantis Inc.
# Author: Craig Tracey <craigtracey@gmail.com>
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
#

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _get_pool_id(client, pool_id_or_name):
    return neutronV20.find_resourceid_by_name_or_id(client, 'pool',
                                                    pool_id_or_name,
                                                    cmd_resource='lbaas_pool')


class LbaasMemberMixin(object):

    def set_extra_attrs(self, parsed_args):
        self.parent_id = _get_pool_id(self.get_client(), parsed_args.pool)

    def add_known_arguments(self, parser):
        parser.add_argument(
            'pool', metavar='POOL',
            help=_('ID or name of the pool that this member belongs to.'))


class ListMember(LbaasMemberMixin, neutronV20.ListCommand):
    """LBaaS v2 List members that belong to a given tenant."""

    resource = 'member'
    shadow_resource = 'lbaas_member'
    list_columns = [
        'id', 'address', 'protocol_port', 'weight',
        'subnet_id', 'admin_state_up', 'status'
    ]
    pagination_support = True
    sorting_support = True


class ShowMember(LbaasMemberMixin, neutronV20.ShowCommand):
    """LBaaS v2 Show information of a given member."""

    resource = 'member'
    shadow_resource = 'lbaas_member'


class CreateMember(neutronV20.CreateCommand):
    """LBaaS v2 Create a member."""

    resource = 'member'
    shadow_resource = 'lbaas_member'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false'))
        parser.add_argument(
            '--weight',
            help=_('Weight of member in the pool (default:1, [0..256]).'))
        parser.add_argument(
            '--subnet',
            required=True,
            help=_('Subnet ID or name for the member.'))
        parser.add_argument(
            '--address',
            required=True,
            help=_('IP address of the pool member in the pool.'))
        parser.add_argument(
            '--protocol-port',
            required=True,
            help=_('Port on which the pool member listens for requests or '
                   'connections.'))
        parser.add_argument(
            'pool', metavar='POOL',
            help=_('ID or name of the pool that this member belongs to.'))

    def args2body(self, parsed_args):
        self.parent_id = _get_pool_id(self.get_client(), parsed_args.pool)
        _subnet_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'subnet', parsed_args.subnet)
        body = {
            self.resource: {
                'subnet_id': _subnet_id,
                'admin_state_up': parsed_args.admin_state,
                'protocol_port': parsed_args.protocol_port,
                'address': parsed_args.address,
            },
        }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['weight', 'subnet_id'])
        return body


class UpdateMember(neutronV20.UpdateCommand):
    """LBaaS v2 Update a given member."""

    resource = 'member'
    shadow_resource = 'lbaas_member'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false'))
        parser.add_argument(
            '--weight',
            help=_('Weight of member in the pool (default:1, [0..256])'))
        parser.add_argument(
            'pool', metavar='POOL',
            help=_('ID or name of the pool that this member belongs to'))

    def args2body(self, parsed_args):
        self.parent_id = _get_pool_id(self.get_client(), parsed_args.pool)
        body = {
            self.resource: {}
        }
        neutronV20.update_dict(parsed_args, body[self.resource],
                               ['admin_state_up', 'weight'])
        return body


class DeleteMember(LbaasMemberMixin, neutronV20.DeleteCommand):
    """LBaaS v2 Delete a given member."""

    resource = 'member'
    shadow_resource = 'lbaas_member'
