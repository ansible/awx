# Copyright 2013 Big Switch Networks
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
# @author: KC Wang, Big Switch Networks
#

import argparse

from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20


class ListFirewallRule(neutronv20.ListCommand):
    """List firewall rules that belong to a given tenant."""

    resource = 'firewall_rule'
    list_columns = ['id', 'name', 'firewall_policy_id', 'summary', 'enabled']
    pagination_support = True
    sorting_support = True

    def extend_list(self, data, parsed_args):
        for d in data:
            val = []
            if d.get('protocol'):
                protocol = d['protocol'].upper()
            else:
                protocol = 'no-protocol'
            val.append(protocol)
            if 'source_ip_address' in d and 'source_port' in d:
                src = 'source: ' + str(d['source_ip_address']).lower()
                src = src + '(' + str(d['source_port']).lower() + ')'
            else:
                src = 'source: none specified'
            val.append(src)
            if 'destination_ip_address' in d and 'destination_port' in d:
                dst = 'dest: ' + str(d['destination_ip_address']).lower()
                dst = dst + '(' + str(d['destination_port']).lower() + ')'
            else:
                dst = 'dest: none specified'
            val.append(dst)
            if 'action' in d:
                action = d['action']
            else:
                action = 'no-action'
            val.append(action)
            d['summary'] = ',\n '.join(val)


class ShowFirewallRule(neutronv20.ShowCommand):
    """Show information of a given firewall rule."""

    resource = 'firewall_rule'


class CreateFirewallRule(neutronv20.CreateCommand):
    """Create a firewall rule."""

    resource = 'firewall_rule'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name',
            help=_('Name for the firewall rule.'))
        parser.add_argument(
            '--description',
            help=_('Description for the firewall rule.'))
        parser.add_argument(
            '--shared',
            dest='shared',
            action='store_true',
            help=_('Set shared to True (default is False).'),
            default=argparse.SUPPRESS)
        parser.add_argument(
            '--source-ip-address',
            help=_('Source IP address or subnet.'))
        parser.add_argument(
            '--destination-ip-address',
            help=_('Destination IP address or subnet.'))
        parser.add_argument(
            '--source-port',
            help=_('Source port (integer in [1, 65535] or range in a:b).'))
        parser.add_argument(
            '--destination-port',
            help=_('Destination port (integer in [1, 65535] or range in '
                   'a:b).'))
        utils.add_boolean_argument(
            parser, '--enabled', dest='enabled',
            help=_('Whether to enable or disable this rule.'))
        parser.add_argument(
            '--protocol', choices=['tcp', 'udp', 'icmp', 'any'],
            required=True,
            help=_('Protocol for the firewall rule.'))
        parser.add_argument(
            '--action',
            required=True,
            choices=['allow', 'deny'],
            help=_('Action for the firewall rule.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }
        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['name', 'description', 'shared', 'protocol',
                                'source_ip_address', 'destination_ip_address',
                                'source_port', 'destination_port',
                                'action', 'enabled', 'tenant_id'])
        protocol = parsed_args.protocol
        if protocol == 'any':
            protocol = None
        body[self.resource]['protocol'] = protocol
        return body


class UpdateFirewallRule(neutronv20.UpdateCommand):
    """Update a given firewall rule."""

    resource = 'firewall_rule'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--protocol', choices=['tcp', 'udp', 'icmp', 'any'],
            required=False,
            help=_('Protocol for the firewall rule.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }
        protocol = parsed_args.protocol
        if protocol:
            if protocol == 'any':
                protocol = None
            body[self.resource]['protocol'] = protocol
        return body


class DeleteFirewallRule(neutronv20.DeleteCommand):
    """Delete a given firewall rule."""

    resource = 'firewall_rule'
