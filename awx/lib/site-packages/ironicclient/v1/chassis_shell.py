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

from ironicclient.common import utils
from ironicclient.openstack.common import cliutils
from ironicclient.v1 import resource_fields as res_fields


def _print_chassis_show(chassis):
    fields = ['uuid', 'description', 'created_at', 'updated_at', 'extra']
    data = dict([(f, getattr(chassis, f, '')) for f in fields])
    cliutils.print_dict(data, wrap=72)


@cliutils.arg('chassis', metavar='<chassis>', help="UUID of the chassis.")
def do_chassis_show(cc, args):
    """Show detailed information about a chassis."""
    chassis = cc.chassis.get(args.chassis)
    _print_chassis_show(chassis)


@cliutils.arg(
    '--detail',
    dest='detail',
    action='store_true',
    default=False,
    help="Show detailed information about the chassis.")
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    help='Maximum number of chassis to return per request, '
         '0 for no limit. Default is the maximum number used '
         'by the Ironic API Service.')
@cliutils.arg(
    '--marker',
    metavar='<chassis>',
    help='Chassis UUID (for example, of the last chassis in the list '
         'from a previous request). Returns the list of chassis '
         'after this UUID.')
@cliutils.arg(
    '--sort-key',
    metavar='<field>',
    help='Chassis field that will be used for sorting.')
@cliutils.arg(
    '--sort-dir',
    metavar='<direction>',
    choices=['asc', 'desc'],
    help='Sort direction: "asc" (the default) or "desc".')
def do_chassis_list(cc, args):
    """List the chassis."""
    if args.detail:
        fields = res_fields.CHASSIS_FIELDS
        field_labels = res_fields.CHASSIS_FIELD_LABELS
    else:
        fields = res_fields.CHASSIS_LIST_FIELDS
        field_labels = res_fields.CHASSIS_LIST_FIELD_LABELS

    params = utils.common_params_for_list(args, fields, field_labels)

    chassis = cc.chassis.list(**params)
    cliutils.print_list(chassis, fields,
                        field_labels=field_labels,
                        sortby_index=None)


@cliutils.arg(
    '-d', '--description',
    metavar='<description>',
    help='Description of the chassis.')
@cliutils.arg(
    '-e', '--extra',
    metavar="<key=value>",
    action='append',
    help="Record arbitrary key/value metadata. "
         "Can be specified multiple times.")
def do_chassis_create(cc, args):
    """Create a new chassis."""
    field_list = ['description', 'extra']
    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in field_list and not (v is None))
    fields = utils.args_array_to_dict(fields, 'extra')
    chassis = cc.chassis.create(**fields)

    field_list.append('uuid')
    data = dict([(f, getattr(chassis, f, '')) for f in field_list])
    cliutils.print_dict(data, wrap=72)


@cliutils.arg(
    'chassis',
    metavar='<chassis>',
    nargs='+',
    help="UUID of the chassis.")
def do_chassis_delete(cc, args):
    """Delete a chassis."""
    for c in args.chassis:
        cc.chassis.delete(c)
        print('Deleted chassis %s' % c)


@cliutils.arg('chassis', metavar='<chassis>', help="UUID of the chassis.")
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
def do_chassis_update(cc, args):
    """Update information about a chassis."""
    patch = utils.args_array_to_patch(args.op, args.attributes[0])
    chassis = cc.chassis.update(args.chassis, patch)
    _print_chassis_show(chassis)


@cliutils.arg(
    '--detail',
    dest='detail',
    action='store_true',
    default=False,
    help="Show detailed information about the nodes.")
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
@cliutils.arg('chassis', metavar='<chassis>', help="UUID of the chassis.")
def do_chassis_node_list(cc, args):
    """List the nodes contained in a chassis."""
    if args.detail:
        fields = res_fields.NODE_FIELDS
        field_labels = res_fields.NODE_FIELD_LABELS
    else:
        fields = res_fields.NODE_LIST_FIELDS
        field_labels = res_fields.NODE_LIST_FIELD_LABELS

    params = utils.common_params_for_list(args, fields, field_labels)

    nodes = cc.chassis.list_nodes(args.chassis, **params)
    cliutils.print_list(nodes, fields,
                        field_labels=field_labels,
                        sortby_index=None)
