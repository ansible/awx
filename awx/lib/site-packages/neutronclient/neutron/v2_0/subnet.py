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


def _format_allocation_pools(subnet):
    try:
        return '\n'.join([jsonutils.dumps(pool) for pool in
                          subnet['allocation_pools']])
    except (TypeError, KeyError):
        return ''


def _format_dns_nameservers(subnet):
    try:
        return '\n'.join([jsonutils.dumps(server) for server in
                          subnet['dns_nameservers']])
    except (TypeError, KeyError):
        return ''


def _format_host_routes(subnet):
    try:
        return '\n'.join([jsonutils.dumps(route) for route in
                          subnet['host_routes']])
    except (TypeError, KeyError):
        return ''


def add_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this subnet.'))
    parser.add_argument(
        '--gateway', metavar='GATEWAY_IP',
        help=_('Gateway IP of this subnet.'))
    parser.add_argument(
        '--no-gateway',
        action='store_true',
        help=_('No distribution of gateway.'))
    parser.add_argument(
        '--allocation-pool', metavar='start=IP_ADDR,end=IP_ADDR',
        action='append', dest='allocation_pools', type=utils.str2dict,
        help=_('Allocation pool IP addresses for this subnet '
               '(This option can be repeated).'))
    parser.add_argument(
        '--allocation_pool',
        action='append', dest='allocation_pools', type=utils.str2dict,
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--host-route', metavar='destination=CIDR,nexthop=IP_ADDR',
        action='append', dest='host_routes', type=utils.str2dict,
        help=_('Additional route (This option can be repeated).'))
    parser.add_argument(
        '--dns-nameserver', metavar='DNS_NAMESERVER',
        action='append', dest='dns_nameservers',
        help=_('DNS name server for this subnet '
               '(This option can be repeated).'))
    parser.add_argument(
        '--disable-dhcp',
        action='store_true',
        help=_('Disable DHCP for this subnet.'))
    parser.add_argument(
        '--enable-dhcp',
        action='store_true',
        help=_('Enable DHCP for this subnet.'))
    # NOTE(ihrachys): yes, that's awful, but should be left as-is for
    # backwards compatibility for versions <=2.3.4 that passed the
    # boolean values through to the server without any argument
    # validation.
    parser.add_argument(
        '--enable-dhcp=True',
        action='store_true',
        dest='enable_dhcp',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--enable-dhcp=False',
        action='store_true',
        dest='disable_dhcp',
        help=argparse.SUPPRESS)


def updatable_args2body(parsed_args, body, for_create=True):
    if parsed_args.gateway and parsed_args.no_gateway:
        raise exceptions.CommandError(_("--gateway option and "
                                        "--no-gateway option can "
                                        "not be used same time"))
    if parsed_args.disable_dhcp and parsed_args.enable_dhcp:
        raise exceptions.CommandError(_(
            "You cannot enable and disable DHCP at the same time."))

    if parsed_args.no_gateway:
        body['subnet'].update({'gateway_ip': None})
    if parsed_args.gateway:
        body['subnet'].update({'gateway_ip': parsed_args.gateway})
    if parsed_args.name:
        body['subnet'].update({'name': parsed_args.name})
    if parsed_args.disable_dhcp:
        body['subnet'].update({'enable_dhcp': False})
    if parsed_args.enable_dhcp:
        body['subnet'].update({'enable_dhcp': True})
    if parsed_args.allocation_pools:
        body['subnet']['allocation_pools'] = parsed_args.allocation_pools
    if parsed_args.host_routes:
        body['subnet']['host_routes'] = parsed_args.host_routes
    if parsed_args.dns_nameservers:
        body['subnet']['dns_nameservers'] = parsed_args.dns_nameservers
    if for_create and parsed_args.ipv6_ra_mode:
        if parsed_args.ip_version == 4:
            raise exceptions.CommandError(_("--ipv6-ra-mode is invalid "
                                            "when --ip-version is 4"))
        body['subnet']['ipv6_ra_mode'] = parsed_args.ipv6_ra_mode
    if for_create and parsed_args.ipv6_address_mode:
        if parsed_args.ip_version == 4:
            raise exceptions.CommandError(_("--ipv6-address-mode is "
                                            "invalid when --ip-version "
                                            "is 4"))
        body['subnet']['ipv6_address_mode'] = parsed_args.ipv6_address_mode


class ListSubnet(neutronV20.ListCommand):
    """List subnets that belong to a given tenant."""

    resource = 'subnet'
    _formatters = {'allocation_pools': _format_allocation_pools,
                   'dns_nameservers': _format_dns_nameservers,
                   'host_routes': _format_host_routes, }
    list_columns = ['id', 'name', 'cidr', 'allocation_pools']
    pagination_support = True
    sorting_support = True


class ShowSubnet(neutronV20.ShowCommand):
    """Show information of a given subnet."""

    resource = 'subnet'


class CreateSubnet(neutronV20.CreateCommand):
    """Create a subnet for a given tenant."""

    resource = 'subnet'

    def add_known_arguments(self, parser):
        add_updatable_arguments(parser)
        parser.add_argument(
            '--ip-version',
            type=int,
            default=4, choices=[4, 6],
            help=_('IP version to use, default is 4.'))
        parser.add_argument(
            '--ip_version',
            type=int,
            choices=[4, 6],
            help=argparse.SUPPRESS)
        parser.add_argument(
            'network_id', metavar='NETWORK',
            help=_('Network ID or name this subnet belongs to.'))
        parser.add_argument(
            'cidr', metavar='CIDR',
            help=_('CIDR of subnet to create.'))
        parser.add_argument(
            '--ipv6-ra-mode',
            choices=['dhcpv6-stateful', 'dhcpv6-stateless', 'slaac'],
            help=_('IPv6 RA (Router Advertisement) mode.'))
        parser.add_argument(
            '--ipv6-address-mode',
            choices=['dhcpv6-stateful', 'dhcpv6-stateless', 'slaac'],
            help=_('IPv6 address mode.'))

    def args2body(self, parsed_args):
        if parsed_args.ip_version == 4 and parsed_args.cidr.endswith('/32'):
            self.log.warning(_("An IPv4 subnet with a /32 CIDR will have "
                               "only one usable IP address so the device "
                               "attached to it will not have any IP "
                               "connectivity."))
        _network_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'network', parsed_args.network_id)
        body = {'subnet': {'cidr': parsed_args.cidr,
                           'network_id': _network_id,
                           'ip_version': parsed_args.ip_version, }, }

        updatable_args2body(parsed_args, body)
        if parsed_args.tenant_id:
            body['subnet'].update({'tenant_id': parsed_args.tenant_id})

        return body


class DeleteSubnet(neutronV20.DeleteCommand):
    """Delete a given subnet."""

    resource = 'subnet'


class UpdateSubnet(neutronV20.UpdateCommand):
    """Update subnet's information."""

    resource = 'subnet'

    def add_known_arguments(self, parser):
        add_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'subnet': {}}
        updatable_args2body(parsed_args, body, for_create=False)
        return body
