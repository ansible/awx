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
#@author Abhishek Raut, Cisco Systems
#@author Sergey Sudakovich, Cisco Systems
#@author Rudrajit Tapadar, Cisco Systems

from __future__ import print_function

from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import parse_args_to_dict

RESOURCE = 'network_profile'
SEGMENT_TYPE_CHOICES = ['vlan', 'overlay', 'multi-segment', 'trunk']


class ListNetworkProfile(neutronV20.ListCommand):
    """List network profiles that belong to a given tenant."""

    resource = RESOURCE
    _formatters = {}
    list_columns = ['id', 'name', 'segment_type', 'sub_type', 'segment_range',
                    'physical_network', 'multicast_ip_index',
                    'multicast_ip_range']


class ShowNetworkProfile(neutronV20.ShowCommand):
    """Show information of a given network profile."""

    resource = RESOURCE
    allow_names = True


class CreateNetworkProfile(neutronV20.CreateCommand):
    """Creates a network profile."""

    resource = RESOURCE

    def add_known_arguments(self, parser):
        parser.add_argument('name',
                            help=_('Name for network profile.'))
        parser.add_argument('segment_type',
                            choices=SEGMENT_TYPE_CHOICES,
                            help='Segment type.')
        # TODO(Abhishek): Check on sub-type choices depending on segment_type
        parser.add_argument('--sub_type',
                            help=_('Sub-type for the segment. Available '
                                   'sub-types for overlay segments: '
                                   'native, enhanced; For trunk segments: '
                                   'vlan, overlay.'))
        parser.add_argument('--segment_range',
                            help=_('Range for the segment.'))
        parser.add_argument('--physical_network',
                            help=_('Name for the physical network.'))
        parser.add_argument('--multicast_ip_range',
                            help=_('Multicast IPv4 range.'))
        parser.add_argument("--add-tenant",
                            action='append', dest='add_tenants',
                            help=_("Add tenant to the network profile. "
                                   "You can repeat this option."))

    def args2body(self, parsed_args):
        body = {'network_profile': {'name': parsed_args.name}}
        if parsed_args.segment_type:
            body['network_profile'].update({'segment_type':
                                           parsed_args.segment_type})
        if parsed_args.sub_type:
            body['network_profile'].update({'sub_type':
                                           parsed_args.sub_type})
        if parsed_args.segment_range:
            body['network_profile'].update({'segment_range':
                                           parsed_args.segment_range})
        if parsed_args.physical_network:
            body['network_profile'].update({'physical_network':
                                           parsed_args.physical_network})
        if parsed_args.multicast_ip_range:
            body['network_profile'].update({'multicast_ip_range':
                                           parsed_args.multicast_ip_range})
        if parsed_args.add_tenants:
            body['network_profile'].update({'add_tenants':
                                           parsed_args.add_tenants})
        return body


class DeleteNetworkProfile(neutronV20.DeleteCommand):
    """Delete a given network profile."""

    resource = RESOURCE
    allow_names = True


class UpdateNetworkProfile(neutronV20.UpdateCommand):
    """Update network profile's information."""

    resource = RESOURCE

    def add_known_arguments(self, parser):
        parser.add_argument("--remove-tenant",
                            action='append', dest='remove_tenants',
                            help=_("Remove tenant from the network profile. "
                                   "You can repeat this option."))
        parser.add_argument("--add-tenant",
                            action='append', dest='add_tenants',
                            help=_("Add tenant to the network profile. "
                                   "You can repeat this option."))

    def args2body(self, parsed_args):
        body = {'network_profile': {}}
        if parsed_args.remove_tenants:
            body['network_profile']['remove_tenants'] = (parsed_args.
                                                         remove_tenants)
        if parsed_args.add_tenants:
            body['network_profile']['add_tenants'] = parsed_args.add_tenants
        return body


# Aaron: This function is deprecated
class UpdateNetworkProfileV2(neutronV20.NeutronCommand):

    api = 'network'
    resource = RESOURCE

    def get_parser(self, prog_name):
        parser = super(UpdateNetworkProfileV2, self).get_parser(prog_name)
        parser.add_argument("--remove-tenant",
                            help="Remove tenant from the network profile.")
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        data = {self.resource: parse_args_to_dict(parsed_args)}
        if parsed_args.remove_tenant:
            data[self.resource]['remove_tenant'] = parsed_args.remove_tenant
        neutron_client.update_network_profile(parsed_args.id,
                                              {self.resource: data})
        print((_('Updated %(resource)s: %(id)s') %
               {'id': parsed_args.id, 'resource': self.resource}),
              file=self.app.stdout)
        return
