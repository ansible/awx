# Copyright 2014 NEC Corporation
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

from neutronclient.common import exceptions
from neutronclient.common import utils
from neutronclient.common import validators
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


class ListPacketFilter(neutronV20.ListCommand):
    """List packet filters that belong to a given tenant."""

    resource = 'packet_filter'
    list_columns = ['id', 'name', 'action', 'priority', 'summary']
    pagination_support = True
    sorting_support = True

    def extend_list(self, data, parsed_args):
        for d in data:
            val = []
            proto_eth_type = []
            if d.get('protocol'):
                proto_eth_type.append('protocol: %s' % d['protocol'].upper())
            if d.get('eth_type'):
                proto_eth_type.append('eth_type: %s' % d['eth_type'])
            if proto_eth_type:
                val.append(', '.join(proto_eth_type))
            val.append('network: ' + d['network_id'])
            if d.get('in_port'):
                val.append('in_port: ' + d['in_port'])
            source = [str(d.get(field)) for field
                      in ['src_mac', 'src_cidr', 'src_port'] if d.get(field)]
            if source:
                val.append('source: ' + ' '.join(source))
            dest = [str(d.get(field)) for field
                    in ['dst_mac', 'dst_cidr', 'dst_port'] if d.get(field)]
            if dest:
                val.append('destination: ' + ' '.join(dest))
            d['summary'] = '\n'.join(val)


class ShowPacketFilter(neutronV20.ShowCommand):
    """Show information of a given packet filter."""

    resource = 'packet_filter'


class PacketFilterOptionMixin(object):
    def add_known_arguments(self, parser):
        mode = self._get_mode()
        if not mode:
            return
        mode_create = mode == 'create'

        if mode_create:
            parser.add_argument(
                '--admin-state-down',
                dest='admin_state', action='store_false',
                help=_('Set Admin State Up to false'))
        else:
            utils.add_boolean_argument(
                parser, '--admin-state',
                help=_('Set a value of Admin State Up'))

        parser.add_argument(
            '--name',
            help=_('Name of this packet filter'))

        if mode_create:
            parser.add_argument(
                '--in-port', metavar='PORT',
                help=_('Name or ID of the input port'))

        parser.add_argument(
            '--src-mac',
            help=_('Source MAC address'))
        parser.add_argument(
            '--dst-mac',
            help=_('Destination MAC address'))
        parser.add_argument(
            '--eth-type',
            help=_('Ether Type. Integer [0:65535] (hex or decimal).'
                   ' E.g., 0x0800 (IPv4), 0x0806 (ARP), 0x86DD (IPv6)'))
        parser.add_argument(
            '--protocol',
            help=_('IP Protocol.'
                   ' Protocol name or integer.'
                   ' Recognized names are icmp, tcp, udp, arp'
                   ' (case insensitive).'
                   ' Integer should be [0:255] (decimal or hex).'))
        parser.add_argument(
            '--src-cidr',
            help=_('Source IP address CIDR'))
        parser.add_argument(
            '--dst-cidr',
            help=_('Destination IP address CIDR'))
        parser.add_argument(
            '--src-port',
            help=_('Source port address'))
        parser.add_argument(
            '--dst-port',
            help=_('Destination port address'))

        default_priority = '30000' if mode_create else None
        parser.add_argument(
            '--priority', metavar='PRIORITY',
            default=default_priority,
            help=(_('Priority of the filter. Integer of [0:65535].%s')
                  % (' Default: 30000.' if mode_create else '')))

        default_action = 'allow' if mode_create else None
        parser.add_argument(
            '--action',
            choices=['allow', 'drop'],
            default=default_action,
            help=(_('Action of the filter.%s')
                  % (' Default: allow' if mode_create else '')))

        if mode_create:
            parser.add_argument(
                'network', metavar='NETWORK',
                help=_('network to which this packet filter is applied'))

    def _get_mode(self):
        klass = self.__class__.__name__.lower()
        if klass.startswith('create'):
            mode = 'create'
        elif klass.startswith('update'):
            mode = 'update'
        else:
            mode = None
        return mode

    def validate_fields(self, parsed_args):
        self._validate_protocol(parsed_args.protocol)
        validators.validate_int_range(parsed_args, 'priority', 0, 0xffff)
        validators.validate_int_range(parsed_args, 'src_port', 0, 0xffff)
        validators.validate_int_range(parsed_args, 'dst_port', 0, 0xffff)
        validators.validate_ip_subnet(parsed_args, 'src_cidr')
        validators.validate_ip_subnet(parsed_args, 'dst_cidr')

    def _validate_protocol(self, protocol):
        if not protocol or protocol == 'action=clear':
            return
        try:
            protocol = int(protocol, 0)
            if 0 <= protocol <= 255:
                return
        except ValueError:
            # Use string as a protocol name
            # Exact check will be done in the server side.
            return
        msg = (_('protocol %s should be either of name '
                 '(tcp, udp, icmp, arp; '
                 'case insensitive) or integer [0:255] (decimal or hex).') %
               protocol)
        raise exceptions.CommandError(msg)


class CreatePacketFilter(PacketFilterOptionMixin,
                         neutronV20.CreateCommand):
    """Create a packet filter for a given tenant."""

    resource = 'packet_filter'

    def args2body(self, parsed_args):
        self.validate_fields(parsed_args)

        _network_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'network', parsed_args.network)
        body = {'network_id': _network_id,
                'admin_state_up': parsed_args.admin_state}
        if parsed_args.in_port:
            _port_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'port', parsed_args.in_port)
            body['in_port'] = _port_id

        neutronV20.update_dict(
            parsed_args, body,
            ['action', 'priority', 'name',
             'eth_type', 'protocol', 'src_mac', 'dst_mac',
             'src_cidr', 'dst_cidr', 'src_port', 'dst_port'])

        return {self.resource: body}


class UpdatePacketFilter(PacketFilterOptionMixin,
                         neutronV20.UpdateCommand):
    """Update packet filter's information."""

    resource = 'packet_filter'

    def args2body(self, parsed_args):
        self.validate_fields(parsed_args)

        body = {}
        if hasattr(parsed_args, 'admin_state'):
            body['admin_state_up'] = (parsed_args.admin_state == 'True')

        # fields which allows None
        for attr in ['eth_type', 'protocol', 'src_mac', 'dst_mac',
                     'src_cidr', 'dst_cidr', 'src_port', 'dst_port']:
            if not hasattr(parsed_args, attr):
                continue
            val = getattr(parsed_args, attr)
            if val is None:
                continue
            if val == '' or val == 'action=clear':
                body[attr] = None
            else:
                body[attr] = val

        for attr in ['action', 'priority', 'name']:
            if (hasattr(parsed_args, attr) and
                    getattr(parsed_args, attr) is not None):
                body[attr] = getattr(parsed_args, attr)

        return {self.resource: body}


class DeletePacketFilter(neutronV20.DeleteCommand):
    """Delete a given packet filter."""

    resource = 'packet_filter'
