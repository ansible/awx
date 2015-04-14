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

from oslo.serialization import jsonutils

from neutronclient.common import exceptions
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


def _format_fixed_ips(port):
    try:
        return '\n'.join([jsonutils.dumps(ip) for ip in port['fixed_ips']])
    except (TypeError, KeyError):
        return ''


def _format_fixed_ips_csv(port):
    try:
        return jsonutils.dumps(port['fixed_ips'])
    except (TypeError, KeyError):
        return ''


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this port.'))
    parser.add_argument(
        '--fixed-ip', metavar='subnet_id=SUBNET,ip_address=IP_ADDR',
        action='append',
        help=_('Desired IP and/or subnet for this port: '
               'subnet_id=<name_or_id>,ip_address=<ip>. '
               'You can repeat this option.'))
    parser.add_argument(
        '--fixed_ip',
        action='append',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--device-id',
        help=_('Device ID of this port.'))
    parser.add_argument(
        '--device_id',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--device-owner',
        help=_('Device owner of this port.'))
    parser.add_argument(
        '--device_owner',
        help=argparse.SUPPRESS)


def _updatable_args2body(parsed_args, body, client):
    if parsed_args.device_id:
        body['port'].update({'device_id': parsed_args.device_id})
    if parsed_args.device_owner:
        body['port'].update({'device_owner': parsed_args.device_owner})
    if parsed_args.name:
        body['port'].update({'name': parsed_args.name})
    ips = []
    if parsed_args.fixed_ip:
        for ip_spec in parsed_args.fixed_ip:
            ip_dict = utils.str2dict(ip_spec)
            if 'subnet_id' in ip_dict:
                subnet_name_id = ip_dict['subnet_id']
                _subnet_id = neutronV20.find_resourceid_by_name_or_id(
                    client, 'subnet', subnet_name_id)
                ip_dict['subnet_id'] = _subnet_id
            ips.append(ip_dict)
    if ips:
        body['port'].update({'fixed_ips': ips})


class ListPort(neutronV20.ListCommand):
    """List ports that belong to a given tenant."""

    resource = 'port'
    _formatters = {'fixed_ips': _format_fixed_ips, }
    _formatters_csv = {'fixed_ips': _format_fixed_ips_csv, }
    list_columns = ['id', 'name', 'mac_address', 'fixed_ips']
    pagination_support = True
    sorting_support = True


class ListRouterPort(neutronV20.ListCommand):
    """List ports that belong to a given tenant, with specified router."""

    resource = 'port'
    _formatters = {'fixed_ips': _format_fixed_ips, }
    list_columns = ['id', 'name', 'mac_address', 'fixed_ips']
    pagination_support = True
    sorting_support = True

    def get_parser(self, prog_name):
        parser = super(ListRouterPort, self).get_parser(prog_name)
        parser.add_argument(
            'id', metavar='router',
            help=_('ID or name of router to look up.'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        _id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'router', parsed_args.id)
        self.values_specs.append('--device_id=%s' % _id)
        return super(ListRouterPort, self).get_data(parsed_args)


class ShowPort(neutronV20.ShowCommand):
    """Show information of a given port."""

    resource = 'port'


class UpdatePortSecGroupMixin(object):
    def add_arguments_secgroup(self, parser):
        group_sg = parser.add_mutually_exclusive_group()
        group_sg.add_argument(
            '--security-group', metavar='SECURITY_GROUP',
            default=[], action='append', dest='security_groups',
            help=_('Security group associated with the port. You can '
                   'repeat this option.'))
        group_sg.add_argument(
            '--no-security-groups',
            action='store_true',
            help=_('Associate no security groups with the port.'))

    def _resolv_sgid(self, secgroup):
        return neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'security_group', secgroup)

    def args2body_secgroup(self, parsed_args, port):
        if parsed_args.security_groups:
            port['security_groups'] = [self._resolv_sgid(sg) for sg
                                       in parsed_args.security_groups]
        elif parsed_args.no_security_groups:
            port['security_groups'] = []


class UpdateExtraDhcpOptMixin(object):
    def add_arguments_extradhcpopt(self, parser):
        group_sg = parser.add_mutually_exclusive_group()
        group_sg.add_argument(
            '--extra-dhcp-opt',
            default=[],
            action='append',
            dest='extra_dhcp_opts',
            help=_('Extra dhcp options to be assigned to this port: '
                   'opt_name=<dhcp_option_name>,opt_value=<value>,'
                   'ip_version={4,6}. You can repeat this option.'))

    def args2body_extradhcpopt(self, parsed_args, port):
        ops = []
        if parsed_args.extra_dhcp_opts:
            # the extra_dhcp_opt params (opt_name & opt_value)
            # must come in pairs, if there is a parm error
            # both must be thrown out.
            opt_ele = {}
            edo_err_msg = _("Invalid --extra-dhcp-opt option, can only be: "
                            "opt_name=<dhcp_option_name>,opt_value=<value>,"
                            "ip_version={4,6}. "
                            "You can repeat this option.")
            for opt in parsed_args.extra_dhcp_opts:
                opt_ele.update(utils.str2dict(opt))
                if ('opt_name' in opt_ele and
                        ('opt_value' in opt_ele or 'ip_version' in opt_ele)):
                    if opt_ele.get('opt_value') == 'null':
                        opt_ele['opt_value'] = None
                    ops.append(opt_ele)
                    opt_ele = {}
                else:
                    raise exceptions.CommandError(edo_err_msg)

        if ops:
            port.update({'extra_dhcp_opts': ops})


class CreatePort(neutronV20.CreateCommand, UpdatePortSecGroupMixin,
                 UpdateExtraDhcpOptMixin):
    """Create a port for a given tenant."""

    resource = 'port'

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)
        parser.add_argument(
            '--admin-state-down',
            dest='admin_state', action='store_false',
            help=_('Set admin state up to false.'))
        parser.add_argument(
            '--admin_state_down',
            dest='admin_state', action='store_false',
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--mac-address',
            help=_('MAC address of this port.'))
        parser.add_argument(
            '--mac_address',
            help=argparse.SUPPRESS)
        self.add_arguments_secgroup(parser)
        self.add_arguments_extradhcpopt(parser)

        parser.add_argument(
            'network_id', metavar='NETWORK',
            help=_('Network ID or name this port belongs to.'))

    def args2body(self, parsed_args):
        client = self.get_client()
        _network_id = neutronV20.find_resourceid_by_name_or_id(
            client, 'network', parsed_args.network_id)
        body = {'port': {'admin_state_up': parsed_args.admin_state,
                         'network_id': _network_id, }, }
        _updatable_args2body(parsed_args, body, client)
        if parsed_args.mac_address:
            body['port'].update({'mac_address': parsed_args.mac_address})
        if parsed_args.tenant_id:
            body['port'].update({'tenant_id': parsed_args.tenant_id})

        self.args2body_secgroup(parsed_args, body['port'])
        self.args2body_extradhcpopt(parsed_args, body['port'])

        return body


class DeletePort(neutronV20.DeleteCommand):
    """Delete a given port."""

    resource = 'port'


class UpdatePort(neutronV20.UpdateCommand, UpdatePortSecGroupMixin,
                 UpdateExtraDhcpOptMixin):
    """Update port's information."""

    resource = 'port'

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)
        parser.add_argument(
            '--admin-state-up',
            choices=['True', 'False'],
            help=_('Set admin state up for the port.'))
        parser.add_argument(
            '--admin_state_up',
            choices=['True', 'False'],
            help=argparse.SUPPRESS)
        self.add_arguments_secgroup(parser)
        self.add_arguments_extradhcpopt(parser)

    def args2body(self, parsed_args):
        body = {'port': {}}
        client = self.get_client()
        _updatable_args2body(parsed_args, body, client)
        if parsed_args.admin_state_up:
            body['port'].update({'admin_state_up':
                                parsed_args.admin_state_up})
        self.args2body_secgroup(parsed_args, body['port'])
        self.args2body_extradhcpopt(parsed_args, body['port'])
        return body
