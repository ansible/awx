# -*- coding: utf-8 -*-
#
# Copyright 2013 Red Hat, Inc.
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

import argparse

import six

from ironicclient.common.i18n import _
from ironicclient.common import utils
from ironicclient.openstack.common.apiclient import exceptions
from ironicclient.openstack.common import cliutils
from ironicclient.v1 import resource_fields as res_fields


def _print_node_show(node):
    data = dict([(f, getattr(node, f, '')) for f in res_fields.NODE_FIELDS])
    cliutils.print_dict(data, wrap=72)


@cliutils.arg(
    'node',
    metavar='<id>',
    help="Name or UUID of the node "
         "(or instance UUID if --instance is specified).")
@cliutils.arg(
    '--instance',
    dest='instance_uuid',
    action='store_true',
    default=False,
    help='<id> is an instance UUID.')
def do_node_show(cc, args):
    """Show detailed information about a node."""
    if args.instance_uuid:
        node = cc.node.get_by_instance_uuid(args.node)
    else:
        node = cc.node.get(args.node)
    _print_node_show(node)


@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    help='Maximum number of nodes to return per request, '
         '0 for no limit. Default is the maximum number used '
         'by the Ironic API Service.')
@cliutils.arg(
    '--marker',
    metavar='<node>',
    help='Node UUID (for example, of the last node in the list from '
         'a previous request). Returns the list of nodes after this UUID.')
@cliutils.arg(
    '--sort-key',
    metavar='<field>',
    help='Node field that will be used for sorting.')
@cliutils.arg(
    '--sort-dir',
    metavar='<direction>',
    choices=['asc', 'desc'],
    help='Sort direction: "asc" (the default) or "desc".')
@cliutils.arg(
    '--maintenance',
    metavar='<boolean>',
    choices=['true', 'True', 'false', 'False'],
    help="List nodes in maintenance mode: 'true' or 'false'.")
@cliutils.arg(
    '--associated',
    metavar='<boolean>',
    choices=['true', 'True', 'false', 'False'],
    help="List nodes by instance association: 'true' or 'false'.")
@cliutils.arg(
    '--detail',
    dest='detail',
    action='store_true',
    default=False,
    help="Show detailed information about the nodes.")
def do_node_list(cc, args):
    """List the nodes which are registered with the Ironic service."""
    params = {}
    if args.associated is not None:
        params['associated'] = args.associated
    if args.maintenance is not None:
        params['maintenance'] = args.maintenance
    params['detail'] = args.detail

    if args.detail:
        fields = res_fields.NODE_FIELDS
        field_labels = res_fields.NODE_FIELD_LABELS
    else:
        fields = res_fields.NODE_LIST_FIELDS
        field_labels = res_fields.NODE_LIST_FIELD_LABELS

    params.update(utils.common_params_for_list(args,
                                               fields,
                                               field_labels))
    nodes = cc.node.list(**params)
    cliutils.print_list(nodes, fields,
                        field_labels=field_labels,
                        sortby_index=None)


@cliutils.arg(
    '-c', '--chassis',
    dest='chassis_uuid',
    metavar='<chassis>',
    help='UUID of the chassis that this node belongs to.')
@cliutils.arg(
    '--chassis_uuid',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '-d', '--driver',
    metavar='<driver>',
    required=True,
    help='Driver used to control the node [REQUIRED].')
@cliutils.arg(
    '-i', '--driver-info',
    metavar='<key=value>',
    action='append',
    help='Key/value pair used by the driver, such as out-of-band management '
         'credentials. Can be specified multiple times.')
@cliutils.arg(
    '--driver_info',
    action='append',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '-p', '--properties',
    metavar='<key=value>',
    action='append',
    help='Key/value pair describing the physical characteristics of the '
         'node. This is exported to Nova and used by the scheduler. '
         'Can be specified multiple times.')
@cliutils.arg(
    '-e', '--extra',
    metavar='<key=value>',
    action='append',
    help="Record arbitrary key/value metadata. "
         "Can be specified multiple times.")
@cliutils.arg(
    '-u', '--uuid',
    metavar='<uuid>',
    help="Unique UUID for the node.")
@cliutils.arg(
    '-n', '--name',
    metavar='<name>',
    help="Unique name for the node.")
def do_node_create(cc, args):
    """Register a new node with the Ironic service."""
    field_list = ['chassis_uuid', 'driver', 'driver_info',
                  'properties', 'extra', 'uuid', 'name']
    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in field_list and not (v is None))
    fields = utils.args_array_to_dict(fields, 'driver_info')
    fields = utils.args_array_to_dict(fields, 'extra')
    fields = utils.args_array_to_dict(fields, 'properties')
    node = cc.node.create(**fields)

    data = dict([(f, getattr(node, f, '')) for f in field_list])
    cliutils.print_dict(data, wrap=72)


@cliutils.arg('node',
              metavar='<node>',
              nargs='+',
              help="Name or UUID of the node.")
def do_node_delete(cc, args):
    """Unregister a node from the Ironic service."""
    for n in args.node:
        cc.node.delete(n)
        print(_('Deleted node %s') % n)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'op',
    metavar='<op>',
    choices=['add', 'replace', 'remove'],
    help="Operation: 'add', 'replace', or 'remove'.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. For 'remove', only <path> is necessary.")
def do_node_update(cc, args):
    """Update information about a registered node."""
    patch = utils.args_array_to_patch(args.op, args.attributes[0])
    node = cc.node.update(args.node, patch)
    _print_node_show(node)


@cliutils.arg('node',
              metavar='<node>',
              help="Name or UUID of the node.")
@cliutils.arg('method',
              metavar='<method>',
              help="Vendor-passthru method to be called.")
@cliutils.arg('arguments',
              metavar='<arg=value>',
              nargs='*',
              action='append',
              default=[],
              help=("Argument to be passed to the vendor-passthru method. Can "
                    "be specified mutiple times."))
@cliutils.arg('--http-method',
              metavar='<http-method>',
              choices=['POST', 'PUT', 'GET', 'DELETE', 'PATCH'],
              help="The HTTP method to use in the request. Valid HTTP "
              "methods are: 'POST', 'PUT', 'GET', 'DELETE', and 'PATCH'. "
              "Defaults to 'POST'.")
@cliutils.arg('--http_method',
              help=argparse.SUPPRESS)
def do_node_vendor_passthru(cc, args):
    """Call a vendor-passthru extension for a node."""
    arguments = utils.args_array_to_dict({'args': args.arguments[0]},
                                         'args')['args']

    # If there were no arguments for the method, arguments will still
    # be an empty list. So make it an empty dict.
    if not arguments:
        arguments = {}

    resp = cc.node.vendor_passthru(args.node, args.method,
                                   http_method=args.http_method,
                                   args=arguments)
    if resp:
        # Print the raw response we don't know how it should be formated
        print(str(resp.to_dict()))


@cliutils.arg(
    '--detail',
    dest='detail',
    action='store_true',
    default=False,
    help="Show detailed information about the ports.")
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    help='Maximum number of ports to return per request, '
         '0 for no limit. Default is the maximum number used '
         'by the Ironic API Service.')
@cliutils.arg(
    '--marker',
    metavar='<port>',
    help='Port UUID (for example, of the last port in the list from a '
         'previous request). Returns the list of ports after this UUID.')
@cliutils.arg(
    '--sort-key',
    metavar='<field>',
    help='Port field that will be used for sorting.')
@cliutils.arg(
    '--sort-dir',
    metavar='<direction>',
    choices=['asc', 'desc'],
    help='Sort direction: "asc" (the default) or "desc".')
@cliutils.arg('node', metavar='<node>', help="UUID of the node.")
def do_node_port_list(cc, args):
    """List the ports associated with a node."""
    if args.detail:
        fields = res_fields.PORT_FIELDS
        field_labels = res_fields.PORT_FIELD_LABELS
    else:
        fields = res_fields.PORT_LIST_FIELDS
        field_labels = res_fields.PORT_LIST_FIELD_LABELS

    params = utils.common_params_for_list(args, fields, field_labels)

    ports = cc.node.list_ports(args.node, **params)
    cliutils.print_list(ports, fields,
                        field_labels=field_labels,
                        sortby_index=None)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'maintenance_mode',
    metavar='<maintenance-mode>',
    choices=['true', 'True', 'false', 'False', 'on', 'off'],
    help="'true' or 'false'; 'on' or 'off'.")
@cliutils.arg(
    '--reason',
    metavar='<reason>',
    default=None,
    help=('Reason for setting maintenance mode to "true" or "on";'
          ' not valid when setting to "false" or "off".'))
def do_node_set_maintenance(cc, args):
    """Enable or disable maintenance mode for a node."""
    if args.reason and args.maintenance_mode.lower() in ('false', 'off'):
        raise exceptions.CommandError(_('Cannot set "reason" when turning off '
                                        'maintenance mode.'))
    cc.node.set_maintenance(args.node, args.maintenance_mode.lower(),
                            maint_reason=args.reason)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'power_state',
    metavar='<power-state>',
    choices=['on', 'off', 'reboot'],
    help="'on', 'off', or 'reboot'.")
def do_node_set_power_state(cc, args):
    """Power a node on or off or reboot."""
    cc.node.set_power_state(args.node, args.power_state)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'provision_state',
    metavar='<provision-state>',
    choices=['active', 'deleted', 'rebuild', 'inspect', 'provide',
             'manage'],
    help="Supported states: 'active', 'deleted', 'rebuild', "
         "'inspect', 'provide' or 'manage'")
@cliutils.arg(
    '--config-drive',
    metavar='<config-drive>',
    default=None,
    help=("A gzipped, base64-encoded configuration drive string OR the path "
          "to the configuration drive file OR the path to a directory "
          "containing the config drive files. In case it's a directory, a "
          "config drive will be generated from it. This parameter is only "
          "valid when setting provision state to 'active'."))
def do_node_set_provision_state(cc, args):
    """Provision, rebuild, delete, inspect, provide or manage an instance."""
    if args.config_drive and args.provision_state != 'active':
        raise exceptions.CommandError(_('--config-drive is only valid when '
                                        'setting provision state to "active"'))
    cc.node.set_provision_state(args.node, args.provision_state,
                                configdrive=args.config_drive)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
def do_node_validate(cc, args):
    """Validate a node's driver interfaces."""
    ifaces = cc.node.validate(args.node)
    obj_list = []
    for key, value in six.iteritems(ifaces.to_dict()):
        data = {'interface': key}
        data.update(value)
        obj_list.append(type('iface', (object,), data))
    field_labels = ['Interface', 'Result', 'Reason']
    fields = ['interface', 'result', 'reason']
    cliutils.print_list(obj_list, fields, field_labels=field_labels)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
def do_node_get_console(cc, args):
    """Get the connection information for a node's console, if enabled."""
    info = cc.node.get_console(args.node)
    cliutils.print_dict(info, wrap=72)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'enabled',
    metavar='<enabled>',
    choices=['true', 'false'],
    help="Enable or disable console access for a node. Supported options are: "
         "'true' or 'false'.")
def do_node_set_console_mode(cc, args):
    """Enable or disable serial console access for a node."""
    cc.node.set_console_mode(args.node, args.enabled)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
@cliutils.arg(
    'device',
    metavar='<boot-device>',
    choices=['pxe', 'disk', 'cdrom', 'bios', 'safe'],
    help="'pxe', 'disk', 'cdrom', 'bios', or 'safe'.")
@cliutils.arg(
    '--persistent',
    dest='persistent',
    action='store_true',
    default=False,
    help="Make changes persistent for all future boots.")
def do_node_set_boot_device(cc, args):
    """Set the boot device for a node."""
    cc.node.set_boot_device(args.node, args.device, args.persistent)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
def do_node_get_boot_device(cc, args):
    """Get the current boot device for a node."""
    boot_device = cc.node.get_boot_device(args.node)
    cliutils.print_dict(boot_device, wrap=72)


@cliutils.arg('node', metavar='<node>', help="Name or UUID of the node.")
def do_node_get_supported_boot_devices(cc, args):
    """Get the supported boot devices for a node."""
    boot_devices = cc.node.get_supported_boot_devices(args.node)
    boot_device_list = boot_devices.get('supported_boot_devices', [])
    boot_devices['supported_boot_devices'] = ', '.join(boot_device_list)
    cliutils.print_dict(boot_devices, wrap=72)
