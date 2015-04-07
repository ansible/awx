# Copyright 2013 OpenStack Foundation.
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

from __future__ import print_function

from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20

GW_RESOURCE = 'network_gateway'
DEV_RESOURCE = 'gateway_device'
CONNECTOR_TYPE_HELP = _("Type of the transport zone connector to use for this "
                        "device. Valid values are gre, stt, ipsecgre, "
                        "ipsecstt, and bridge. Defaults to stt.")
CONNECTOR_IP_HELP = _("IP address for this device's transport connector. "
                      "It must correspond to the IP address of the interface "
                      "used for tenant traffic on the NSX gateway node.")
CLIENT_CERT_HELP = _("PEM certificate used by the NSX gateway transport node "
                     "to authenticate with the NSX controller.")
CLIENT_CERT_FILE_HELP = _("File containing the PEM certificate used by the "
                          "NSX gateway transport node to authenticate with "
                          "the NSX controller.")


class ListGatewayDevice(neutronV20.ListCommand):
    """List network gateway devices for a given tenant."""

    resource = DEV_RESOURCE
    list_columns = ['id', 'name']


class ShowGatewayDevice(neutronV20.ShowCommand):
    """Show information for a given network gateway device."""

    resource = DEV_RESOURCE


def read_cert_file(cert_file):
    return open(cert_file, 'rb').read()


def gateway_device_args2body(parsed_args):
    body = {}
    if parsed_args.name:
        body['name'] = parsed_args.name
    if parsed_args.connector_type:
        body['connector_type'] = parsed_args.connector_type
    if parsed_args.connector_ip:
        body['connector_ip'] = parsed_args.connector_ip
    cert_data = None
    if parsed_args.cert_file:
        cert_data = read_cert_file(parsed_args.cert_file)
    elif parsed_args.cert_data:
        cert_data = parsed_args.cert_data
    if cert_data:
        body['client_certificate'] = cert_data
    if getattr(parsed_args, 'tenant_id', None):
        body['tenant_id'] = parsed_args.tenant_id
    return {DEV_RESOURCE: body}


class CreateGatewayDevice(neutronV20.CreateCommand):
    """Create a network gateway device."""

    resource = DEV_RESOURCE

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help='Name of network gateway device to create.')
        parser.add_argument(
            '--connector-type',
            default='stt',
            choices=['stt', 'gre', 'ipsecgre', 'ipsecstt', 'bridge'],
            help=CONNECTOR_TYPE_HELP)
        parser.add_argument(
            '--connector-ip',
            required=True,
            help=CONNECTOR_IP_HELP)
        client_cert_group = parser.add_mutually_exclusive_group(
            required=True)
        client_cert_group.add_argument(
            '--client-certificate',
            dest='cert_data',
            help=CLIENT_CERT_HELP)
        client_cert_group.add_argument(
            '--client-certificate-file',
            dest='cert_file',
            help=CLIENT_CERT_FILE_HELP)

    def args2body(self, parsed_args):
        return gateway_device_args2body(parsed_args)


class UpdateGatewayDevice(neutronV20.UpdateCommand):
    """Update a network gateway device."""

    resource = DEV_RESOURCE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', metavar='NAME',
            help='New name for network gateway device.')
        parser.add_argument(
            '--connector-type',
            required=False,
            choices=['stt', 'gre', 'ipsecgre', 'ipsecstt', 'bridge'],
            help=CONNECTOR_TYPE_HELP)
        parser.add_argument(
            '--connector-ip',
            required=False,
            help=CONNECTOR_IP_HELP)
        client_cert_group = parser.add_mutually_exclusive_group()
        client_cert_group.add_argument(
            '--client-certificate',
            dest='cert_data',
            help=CLIENT_CERT_HELP)
        client_cert_group.add_argument(
            '--client-certificate-file',
            dest='cert_file',
            help=CLIENT_CERT_FILE_HELP)

    def args2body(self, parsed_args):
        return gateway_device_args2body(parsed_args)


class DeleteGatewayDevice(neutronV20.DeleteCommand):
    """Delete a given network gateway device."""

    resource = DEV_RESOURCE


class ListNetworkGateway(neutronV20.ListCommand):
    """List network gateways for a given tenant."""

    resource = GW_RESOURCE
    list_columns = ['id', 'name']


class ShowNetworkGateway(neutronV20.ShowCommand):
    """Show information of a given network gateway."""

    resource = GW_RESOURCE


class CreateNetworkGateway(neutronV20.CreateCommand):
    """Create a network gateway."""

    resource = GW_RESOURCE

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Name of network gateway to create.'))
        parser.add_argument(
            '--device', metavar='id=ID,interface_name=NAME_OR_ID',
            action='append',
            help=_('Device info for this gateway. You can repeat this '
                   'option for multiple devices for HA gateways.'))

    def args2body(self, parsed_args):
        body = {self.resource: {
            'name': parsed_args.name}}
        devices = []
        if parsed_args.device:
            for device in parsed_args.device:
                devices.append(utils.str2dict(device))
        if devices:
            body[self.resource].update({'devices': devices})
        if parsed_args.tenant_id:
            body[self.resource].update({'tenant_id': parsed_args.tenant_id})
        return body


class DeleteNetworkGateway(neutronV20.DeleteCommand):
    """Delete a given network gateway."""

    resource = GW_RESOURCE


class UpdateNetworkGateway(neutronV20.UpdateCommand):
    """Update the name for a network gateway."""

    resource = GW_RESOURCE


class NetworkGatewayInterfaceCommand(neutronV20.NeutronCommand):
    """Base class for connecting/disconnecting networks to/from a gateway."""

    resource = GW_RESOURCE

    def get_parser(self, prog_name):
        parser = super(NetworkGatewayInterfaceCommand,
                       self).get_parser(prog_name)
        parser.add_argument(
            'net_gateway_id', metavar='NET-GATEWAY-ID',
            help=_('ID of the network gateway.'))
        parser.add_argument(
            'network_id', metavar='NETWORK-ID',
            help=_('ID of the internal network to connect on the gateway.'))
        parser.add_argument(
            '--segmentation-type',
            help=_('L2 segmentation strategy on the external side of '
                   'the gateway (e.g.: VLAN, FLAT).'))
        parser.add_argument(
            '--segmentation-id',
            help=_('Identifier for the L2 segment on the external side '
                   'of the gateway.'))
        return parser

    def retrieve_ids(self, client, args):
        gateway_id = neutronV20.find_resourceid_by_name_or_id(
            client, self.resource, args.net_gateway_id)
        network_id = neutronV20.find_resourceid_by_name_or_id(
            client, 'network', args.network_id)
        return (gateway_id, network_id)


class ConnectNetworkGateway(NetworkGatewayInterfaceCommand):
    """Add an internal network interface to a router."""

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        (gateway_id, network_id) = self.retrieve_ids(neutron_client,
                                                     parsed_args)
        neutron_client.connect_network_gateway(
            gateway_id, {'network_id': network_id,
                         'segmentation_type': parsed_args.segmentation_type,
                         'segmentation_id': parsed_args.segmentation_id})
        # TODO(Salvatore-Orlando): Do output formatting as
        # any other command
        print(_('Connected network to gateway %s') % gateway_id,
              file=self.app.stdout)


class DisconnectNetworkGateway(NetworkGatewayInterfaceCommand):
    """Remove a network from a network gateway."""

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        (gateway_id, network_id) = self.retrieve_ids(neutron_client,
                                                     parsed_args)
        neutron_client.disconnect_network_gateway(
            gateway_id, {'network_id': network_id,
                         'segmentation_type': parsed_args.segmentation_type,
                         'segmentation_id': parsed_args.segmentation_id})
        # TODO(Salvatore-Orlando): Do output formatting as
        # any other command
        print(_('Disconnected network from gateway %s') % gateway_id,
              file=self.app.stdout)
