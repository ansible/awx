# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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

import argparse

from neutronclient.common import exceptions
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _format_subnets(network):
    try:
        return '\n'.join([' '.join([s['id'], s.get('cidr', '')])
                          for s in network['subnets']])
    except (TypeError, KeyError):
        return ''


class ListNetwork(neutronV20.ListCommand):
    """List networks that belong to a given tenant."""

    # Length of a query filter on subnet id
    # id=<uuid>& (with len(uuid)=36)
    subnet_id_filter_len = 40
    resource = 'network'
    _formatters = {'subnets': _format_subnets, }
    list_columns = ['id', 'name', 'subnets']
    pagination_support = True
    sorting_support = True

    def extend_list(self, data, parsed_args):
        """Add subnet information to a network list."""
        neutron_client = self.get_client()
        search_opts = {'fields': ['id', 'cidr']}
        if self.pagination_support:
            page_size = parsed_args.page_size
            if page_size:
                search_opts.update({'limit': page_size})
        subnet_ids = []
        for n in data:
            if 'subnets' in n:
                subnet_ids.extend(n['subnets'])

        def _get_subnet_list(sub_ids):
            search_opts['id'] = sub_ids
            return neutron_client.list_subnets(
                **search_opts).get('subnets', [])

        try:
            subnets = _get_subnet_list(subnet_ids)
        except exceptions.RequestURITooLong as uri_len_exc:
            # The URI is too long because of too many subnet_id filters
            # Use the excess attribute of the exception to know how many
            # subnet_id filters can be inserted into a single request
            subnet_count = len(subnet_ids)
            max_size = ((self.subnet_id_filter_len * subnet_count) -
                        uri_len_exc.excess)
            chunk_size = max_size // self.subnet_id_filter_len
            subnets = []
            for i in range(0, subnet_count, chunk_size):
                subnets.extend(
                    _get_subnet_list(subnet_ids[i: i + chunk_size]))

        subnet_dict = dict([(s['id'], s) for s in subnets])
        for n in data:
            if 'subnets' in n:
                n['subnets'] = [(subnet_dict.get(s) or {"id": s})
                                for s in n['subnets']]


class ListExternalNetwork(ListNetwork):
    """List external networks that belong to a given tenant."""

    pagination_support = True
    sorting_support = True

    def retrieve_list(self, parsed_args):
        external = '--router:external=True'
        if external not in self.values_specs:
            self.values_specs.append('--router:external=True')
        return super(ListExternalNetwork, self).retrieve_list(parsed_args)


class ShowNetwork(neutronV20.ShowCommand):
    """Show information of a given network."""

    resource = 'network'


class CreateNetwork(neutronV20.CreateCommand):
    """Create a network for a given tenant."""

    resource = 'network'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--admin_state_down',
            dest='admin_state', action='store_false',
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--shared',
            action='store_true',
            help=_('Set the network as shared.'),
            default=argparse.SUPPRESS)
        parser.add_argument(
            '--router:external',
            action='store_true',
            help=_('Set network as external, it is only available for admin'),
            default=argparse.SUPPRESS)
        parser.add_argument(
            '--provider:network_type',
            metavar='<network_type>',
            help=_('The physical mechanism by which the virtual network'
                   ' is implemented.'))
        parser.add_argument(
            '--provider:physical_network',
            metavar='<physical_network_name>',
            help=_('Name of the physical network over which the virtual'
                   ' network is implemented.'))
        parser.add_argument(
            '--provider:segmentation_id',
            metavar='<segmentation_id>',
            help=_('VLAN ID for VLAN networks or tunnel-id for GRE/VXLAN'
                   ' networks.'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name of network to create.'))

    def args2body(self, parsed_args):
        body = {'network': {
            'name': parsed_args.name,
            'admin_state_up': parsed_args.admin_state}, }
        neutronV20.update_dict(parsed_args, body['network'],
                               ['shared', 'tenant_id', 'router:external',
                                'provider:network_type',
                                'provider:physical_network',
                                'provider:segmentation_id'])
        return body


class DeleteNetwork(neutronV20.DeleteCommand):
    """Delete a given network."""

    resource = 'network'


class UpdateNetwork(neutronV20.UpdateCommand):
    """Update network's information."""

    resource = 'network'
