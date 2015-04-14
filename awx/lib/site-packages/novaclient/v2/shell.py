# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from __future__ import print_function

import argparse
import copy
import datetime
import getpass
import locale
import logging
import os
import sys
import time

from oslo.utils import encodeutils
from oslo.utils import strutils
from oslo.utils import timeutils
import six

from novaclient import client
from novaclient import exceptions
from novaclient.i18n import _
from novaclient.openstack.common import cliutils
from novaclient.openstack.common import uuidutils
from novaclient import utils
from novaclient.v2 import availability_zones
from novaclient.v2 import quotas
from novaclient.v2 import servers


logger = logging.getLogger(__name__)


CLIENT_BDM2_KEYS = {
    'id': 'uuid',
    'source': 'source_type',
    'dest': 'destination_type',
    'bus': 'disk_bus',
    'device': 'device_name',
    'size': 'volume_size',
    'format': 'guest_format',
    'bootindex': 'boot_index',
    'type': 'device_type',
    'shutdown': 'delete_on_termination',
}


def _key_value_pairing(text):
    try:
        (k, v) = text.split('=', 1)
        return (k, v)
    except ValueError:
        msg = "%r is not in the format of key=value" % text
        raise argparse.ArgumentTypeError(msg)


def _match_image(cs, wanted_properties):
    image_list = cs.images.list()
    images_matched = []
    match = set(wanted_properties)
    for img in image_list:
        try:
            if match == match.intersection(set(img.metadata.items())):
                images_matched.append(img)
        except AttributeError:
            pass
    return images_matched


def _parse_block_device_mapping_v2(args, image):
    bdm = []

    if args.boot_volume:
        bdm_dict = {'uuid': args.boot_volume, 'source_type': 'volume',
                    'destination_type': 'volume', 'boot_index': 0,
                    'delete_on_termination': False}
        bdm.append(bdm_dict)

    if args.snapshot:
        bdm_dict = {'uuid': args.snapshot, 'source_type': 'snapshot',
                    'destination_type': 'volume', 'boot_index': 0,
                    'delete_on_termination': False}
        bdm.append(bdm_dict)

    for device_spec in args.block_device:
        spec_dict = dict(v.split('=') for v in device_spec.split(','))
        bdm_dict = {}

        for key, value in six.iteritems(spec_dict):
            bdm_dict[CLIENT_BDM2_KEYS[key]] = value

        # Convert the delete_on_termination to a boolean or set it to true by
        # default for local block devices when not specified.
        if 'delete_on_termination' in bdm_dict:
            action = bdm_dict['delete_on_termination']
            bdm_dict['delete_on_termination'] = (action == 'remove')
        elif bdm_dict.get('destination_type') == 'local':
            bdm_dict['delete_on_termination'] = True

        bdm.append(bdm_dict)

    for ephemeral_spec in args.ephemeral:
        bdm_dict = {'source_type': 'blank', 'destination_type': 'local',
                    'boot_index': -1, 'delete_on_termination': True}

        eph_dict = dict(v.split('=') for v in ephemeral_spec.split(','))
        if 'size' in eph_dict:
            bdm_dict['volume_size'] = eph_dict['size']
        if 'format' in eph_dict:
            bdm_dict['guest_format'] = eph_dict['format']

        bdm.append(bdm_dict)

    if args.swap:
        bdm_dict = {'source_type': 'blank', 'destination_type': 'local',
                    'boot_index': -1, 'delete_on_termination': True,
                    'guest_format': 'swap', 'volume_size': args.swap}
        bdm.append(bdm_dict)

    return bdm


def _boot(cs, args):
    """Boot a new server."""
    if args.image:
        image = _find_image(cs, args.image)
    else:
        image = None

    if not image and args.image_with:
        images = _match_image(cs, args.image_with)
        if images:
            # TODO(harlowja): log a warning that we
            # are selecting the first of many?
            image = images[0]

    if not args.flavor:
        raise exceptions.CommandError(_("you need to specify a Flavor ID "))

    min_count = 1
    max_count = 1
    # Don't let user mix num_instances and max_count/min_count.
    if (args.num_instances is not None and
            args.min_count is None and
            args.max_count is None):
        if args.num_instances < 1:
            raise exceptions.CommandError(_("num_instances should be >= 1"))
        max_count = args.num_instances
    elif (args.num_instances is not None and
          (args.min_count is not None or args.max_count is not None)):
        raise exceptions.CommandError(_("Don't mix num-instances and "
                                        "max/min-count"))
    if args.min_count is not None:
        if args.min_count < 1:
            raise exceptions.CommandError(_("min_count should be >= 1"))
        min_count = args.min_count
        max_count = min_count
    if args.max_count is not None:
        if args.max_count < 1:
            raise exceptions.CommandError(_("max_count should be >= 1"))
        max_count = args.max_count
    if (args.min_count is not None and
            args.max_count is not None and
            args.min_count > args.max_count):
        raise exceptions.CommandError(_("min_count should be <= max_count"))

    flavor = _find_flavor(cs, args.flavor)

    meta = dict(v.split('=', 1) for v in args.meta)

    files = {}
    for f in args.files:
        try:
            dst, src = f.split('=', 1)
            files[dst] = open(src)
        except IOError as e:
            raise exceptions.CommandError(_("Can't open '%(src)s': %(exc)s") %
                                          {'src': src, 'exc': e})
        except ValueError:
            raise exceptions.CommandError(_("Invalid file argument '%s'. "
                                            "File arguments must be of the "
                                            "form '--file "
                                            "<dst-path=src-path>'") % f)

    # use the os-keypair extension
    key_name = None
    if args.key_name is not None:
        key_name = args.key_name

    if args.user_data:
        try:
            userdata = open(args.user_data)
        except IOError as e:
            raise exceptions.CommandError(_("Can't open '%(user_data)s': "
                                            "%(exc)s") %
                                          {'user_data': args.user_data,
                                           'exc': e})
    else:
        userdata = None

    if args.availability_zone:
        availability_zone = args.availability_zone
    else:
        availability_zone = None

    if args.security_groups:
        security_groups = args.security_groups.split(',')
    else:
        security_groups = None

    block_device_mapping = {}
    for bdm in args.block_device_mapping:
        device_name, mapping = bdm.split('=', 1)
        block_device_mapping[device_name] = mapping

    block_device_mapping_v2 = _parse_block_device_mapping_v2(args, image)

    n_boot_args = len(list(filter(
        bool, (image, args.boot_volume, args.snapshot))))
    have_bdm = block_device_mapping_v2 or block_device_mapping

    # Fail if more than one boot devices are present
    # or if there is no device to boot from.
    if n_boot_args > 1 or n_boot_args == 0 and not have_bdm:
        raise exceptions.CommandError(
            _("you need to specify at least one source ID (Image, Snapshot, "
              "or Volume), a block device mapping or provide a set of "
              "properties to match against an image"))

    if block_device_mapping and block_device_mapping_v2:
        raise exceptions.CommandError(
            _("you can't mix old block devices (--block-device-mapping) "
              "with the new ones (--block-device, --boot-volume, --snapshot, "
              "--ephemeral, --swap)"))

    nics = []
    for nic_str in args.nics:
        err_msg = (_("Invalid nic argument '%s'. Nic arguments must be of "
                     "the form --nic <net-id=net-uuid,v4-fixed-ip=ip-addr,"
                     "v6-fixed-ip=ip-addr,port-id=port-uuid>, with at minimum "
                     "net-id or port-id (but not both) specified.") % nic_str)
        nic_info = {"net-id": "", "v4-fixed-ip": "", "v6-fixed-ip": "",
                    "port-id": ""}

        for kv_str in nic_str.split(","):
            try:
                k, v = kv_str.split("=", 1)
            except ValueError:
                raise exceptions.CommandError(err_msg)

            if k in nic_info:
                nic_info[k] = v
            else:
                raise exceptions.CommandError(err_msg)

        if bool(nic_info['net-id']) == bool(nic_info['port-id']):
            raise exceptions.CommandError(err_msg)

        nics.append(nic_info)

    hints = {}
    if args.scheduler_hints:
        for hint in args.scheduler_hints:
            key, _sep, value = hint.partition('=')
            # NOTE(vish): multiple copies of the same hint will
            #             result in a list of values
            if key in hints:
                if isinstance(hints[key], six.string_types):
                    hints[key] = [hints[key]]
                hints[key] += [value]
            else:
                hints[key] = value
    boot_args = [args.name, image, flavor]

    if str(args.config_drive).lower() in ("true", "1"):
        config_drive = True
    elif str(args.config_drive).lower() in ("false", "0", "", "none"):
        config_drive = None
    else:
        config_drive = args.config_drive

    boot_kwargs = dict(
        meta=meta,
        files=files,
        key_name=key_name,
        min_count=min_count,
        max_count=max_count,
        userdata=userdata,
        availability_zone=availability_zone,
        security_groups=security_groups,
        block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics,
        scheduler_hints=hints,
        config_drive=config_drive)

    return boot_args, boot_kwargs


@cliutils.arg(
    '--flavor',
    default=None,
    metavar='<flavor>',
    help=_("Name or ID of flavor (see 'nova flavor-list')."))
@cliutils.arg(
    '--image',
    default=None,
    metavar='<image>',
    help=_("Name or ID of image (see 'nova image-list'). "))
@cliutils.arg(
    '--image-with',
    default=[],
    type=_key_value_pairing,
    action='append',
    metavar='<key=value>',
    help=_("Image metadata property (see 'nova image-show'). "))
@cliutils.arg(
    '--boot-volume',
    default=None,
    metavar="<volume_id>",
    help=_("Volume ID to boot from."))
@cliutils.arg(
    '--snapshot',
    default=None,
    metavar="<snapshot_id>",
    help=_("Snapshot ID to boot from (will create a volume)."))
@cliutils.arg(
    '--num-instances',
    default=None,
    type=int,
    metavar='<number>',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--min-count',
    default=None,
    type=int,
    metavar='<number>',
    help=_("Boot at least <number> servers (limited by quota)."))
@cliutils.arg(
    '--max-count',
    default=None,
    type=int,
    metavar='<number>',
    help=_("Boot up to <number> servers (limited by quota)."))
@cliutils.arg(
    '--meta',
    metavar="<key=value>",
    action='append',
    default=[],
    help=_("Record arbitrary key/value metadata to /meta_data.json "
           "on the metadata server. Can be specified multiple times."))
@cliutils.arg(
    '--file',
    metavar="<dst-path=src-path>",
    action='append',
    dest='files',
    default=[],
    help=_("Store arbitrary files from <src-path> locally to <dst-path> "
           "on the new server. You may store up to 5 files."))
@cliutils.arg(
    '--key-name',
    default=os.environ.get('NOVACLIENT_DEFAULT_KEY_NAME'),
    metavar='<key-name>',
    help=_("Key name of keypair that should be created earlier with \
           the command keypair-add"))
@cliutils.arg(
    '--key_name',
    help=argparse.SUPPRESS)
@cliutils.arg('name', metavar='<name>', help=_('Name for the new server'))
@cliutils.arg(
    '--user-data',
    default=None,
    metavar='<user-data>',
    help=_("user data file to pass to be exposed by the metadata server."))
@cliutils.arg(
    '--user_data',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--availability-zone',
    default=None,
    metavar='<availability-zone>',
    help=_("The availability zone for server placement."))
@cliutils.arg(
    '--availability_zone',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--security-groups',
    default=None,
    metavar='<security-groups>',
    help=_("Comma separated list of security group names."))
@cliutils.arg(
    '--security_groups',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--block-device-mapping',
    metavar="<dev-name=mapping>",
    action='append',
    default=[],
    help=_("Block device mapping in the format "
           "<dev-name>=<id>:<type>:<size(GB)>:<delete-on-terminate>."))
@cliutils.arg(
    '--block_device_mapping',
    action='append',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--block-device',
    metavar="key1=value1[,key2=value2...]",
    action='append',
    default=[],
    help=_("Block device mapping with the keys: "
           "id=UUID (image_id, snapshot_id or volume_id only if using source "
           "image, snapshot or volume) "
           "source=source type (image, snapshot, volume or blank), "
           "dest=destination type of the block device (volume or local), "
           "bus=device's bus (e.g. uml, lxc, virtio, ...; if omitted, "
           "hypervisor driver chooses a suitable default, "
           "honoured only if device type is supplied) "
           "type=device type (e.g. disk, cdrom, ...; defaults to 'disk') "
           "device=name of the device (e.g. vda, xda, ...; "
           "if omitted, hypervisor driver chooses suitable device "
           "depending on selected bus), "
           "size=size of the block device in GB (if omitted, "
           "hypervisor driver calculates size), "
           "format=device will be formatted (e.g. swap, ntfs, ...; optional), "
           "bootindex=integer used for ordering the boot disks "
           "(for image backed instances it is equal to 0, "
           "for others need to be specified) and "
           "shutdown=shutdown behaviour (either preserve or remove, "
           "for local destination set to remove)."))
@cliutils.arg(
    '--swap',
    metavar="<swap_size>",
    default=None,
    help=_("Create and attach a local swap block device of <swap_size> MB."))
@cliutils.arg(
    '--ephemeral',
    metavar="size=<size>[,format=<format>]",
    action='append',
    default=[],
    help=_("Create and attach a local ephemeral block device of <size> GB "
           "and format it to <format>."))
@cliutils.arg(
    '--hint',
    action='append',
    dest='scheduler_hints',
    default=[],
    metavar='<key=value>',
    help=_("Send arbitrary key/value pairs to the scheduler for custom "
           "use."))
@cliutils.arg(
    '--nic',
    metavar="<net-id=net-uuid,v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr,"
            "port-id=port-uuid>",
    action='append',
    dest='nics',
    default=[],
    help=_("Create a NIC on the server. "
           "Specify option multiple times to create multiple NICs. "
           "net-id: attach NIC to network with this UUID "
           "(either port-id or net-id must be provided), "
           "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
           "v6-fixed-ip: IPv6 fixed address for NIC (optional), "
           "port-id: attach NIC to port with this UUID "
           "(either port-id or net-id must be provided)."))
@cliutils.arg(
    '--config-drive',
    metavar="<value>",
    dest='config_drive',
    default=False,
    help=_("Enable config drive"))
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the new server boot progress until it completes.'))
def do_boot(cs, args):
    """Boot a new server."""
    boot_args, boot_kwargs = _boot(cs, args)

    extra_boot_kwargs = utils.get_resource_manager_extra_kwargs(do_boot, args)
    boot_kwargs.update(extra_boot_kwargs)

    server = cs.servers.create(*boot_args, **boot_kwargs)
    _print_server(cs, args, server)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'building', ['active'])


def do_cloudpipe_list(cs, _args):
    """Print a list of all cloudpipe instances."""
    cloudpipes = cs.cloudpipe.list()
    columns = ['Project Id', "Public IP", "Public Port", "Internal IP"]
    utils.print_list(cloudpipes, columns)


@cliutils.arg(
    'project',
    metavar='<project_id>',
    help=_('UUID of the project to create the cloudpipe for.'))
def do_cloudpipe_create(cs, args):
    """Create a cloudpipe instance for the given project."""
    cs.cloudpipe.create(args.project)


@cliutils.arg('address', metavar='<ip address>', help=_('New IP Address.'))
@cliutils.arg('port', metavar='<port>', help='New Port.')
def do_cloudpipe_configure(cs, args):
    """Update the VPN IP/port of a cloudpipe instance."""
    cs.cloudpipe.update(args.address, args.port)


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True,
                     status_field="status", silent=False):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = (_('\rServer %(action)s... %(progress)s%% complete')
                   % dict(action=action, progress=progress))
        else:
            msg = _('\rServer %(action)s...') % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    if not silent:
        print()

    while True:
        obj = poll_fn(obj_id)

        status = getattr(obj, status_field)

        if status:
            status = status.lower()

        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            if not silent:
                print_progress(100)
                print(_("\nFinished"))
            break
        elif status == "error":
            if not silent:
                print(_("\nError %s server") % action)
            raise exceptions.InstanceInErrorState(obj.fault['message'])

        if not silent:
            print_progress(progress)

        time.sleep(poll_period)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _translate_extended_states(collection):
    power_states = [
        'NOSTATE',      # 0x00
        'Running',      # 0x01
        '',             # 0x02
        'Paused',       # 0x03
        'Shutdown',     # 0x04
        '',             # 0x05
        'Crashed',      # 0x06
        'Suspended'     # 0x07
    ]

    for item in collection:
        try:
            setattr(item, 'power_state',
                    power_states[getattr(item, 'power_state')])
        except AttributeError:
            setattr(item, 'power_state', "N/A")
        try:
            getattr(item, 'task_state')
        except AttributeError:
            setattr(item, 'task_state', "N/A")


def _translate_flavor_keys(collection):
    _translate_keys(collection, [('ram', 'memory_mb')])


def _print_flavor_extra_specs(flavor):
    try:
        return flavor.get_keys()
    except exceptions.NotFound:
        return "N/A"


def _print_flavor_list(flavors, show_extra_specs=False):
    _translate_flavor_keys(flavors)

    headers = [
        'ID',
        'Name',
        'Memory_MB',
        'Disk',
        'Ephemeral',
        'Swap',
        'VCPUs',
        'RXTX_Factor',
        'Is_Public',
    ]

    if show_extra_specs:
        formatters = {'extra_specs': _print_flavor_extra_specs}
        headers.append('extra_specs')
    else:
        formatters = {}

    utils.print_list(flavors, headers, formatters)


@cliutils.arg(
    '--extra-specs',
    dest='extra_specs',
    action='store_true',
    default=False,
    help=_('Get extra-specs of each flavor.'))
@cliutils.arg(
    '--all',
    dest='all',
    action='store_true',
    default=False,
    help=_('Display all flavors (Admin only).'))
def do_flavor_list(cs, args):
    """Print a list of available 'flavors' (sizes of servers)."""
    if args.all:
        flavors = cs.flavors.list(is_public=None)
    else:
        flavors = cs.flavors.list()
    _print_flavor_list(flavors, args.extra_specs)


@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of the flavor to delete"))
def do_flavor_delete(cs, args):
    """Delete a specific flavor"""
    flavorid = _find_flavor(cs, args.flavor)
    cs.flavors.delete(flavorid)
    _print_flavor_list([flavorid])


@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of flavor"))
def do_flavor_show(cs, args):
    """Show details about the given flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_flavor(flavor)


@cliutils.arg(
    'name',
    metavar='<name>',
    help=_("Name of the new flavor"))
@cliutils.arg(
    'id',
    metavar='<id>',
    help=_("Unique ID (integer or UUID) for the new flavor."
           " If specifying 'auto', a UUID will be generated as id"))
@cliutils.arg(
    'ram',
    metavar='<ram>',
    help=_("Memory size in MB"))
@cliutils.arg(
    'disk',
    metavar='<disk>',
    help=_("Disk size in GB"))
@cliutils.arg(
    '--ephemeral',
    metavar='<ephemeral>',
    help=_("Ephemeral space size in GB (default 0)"),
    default=0)
@cliutils.arg(
    'vcpus',
    metavar='<vcpus>',
    help=_("Number of vcpus"))
@cliutils.arg(
    '--swap',
    metavar='<swap>',
    help=_("Swap space size in MB (default 0)"),
    default=0)
@cliutils.arg(
    '--rxtx-factor',
    metavar='<factor>',
    help=_("RX/TX factor (default 1)"),
    default=1.0)
@cliutils.arg(
    '--is-public',
    metavar='<is-public>',
    help=_("Make flavor accessible to the public (default true)"),
    type=lambda v: strutils.bool_from_string(v, True),
    default=True)
def do_flavor_create(cs, args):
    """Create a new flavor"""
    f = cs.flavors.create(args.name, args.ram, args.vcpus, args.disk, args.id,
                          args.ephemeral, args.swap, args.rxtx_factor,
                          args.is_public)
    _print_flavor_list([f])


@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of flavor"))
@cliutils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'unset'],
    help=_("Actions: 'set' or 'unset'"))
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Extra_specs to set/unset (only key is necessary on unset)'))
def do_flavor_key(cs, args):
    """Set or unset extra_spec for a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    keypair = _extract_metadata(args)

    if args.action == 'set':
        flavor.set_keys(keypair)
    elif args.action == 'unset':
        flavor.unset_keys(keypair.keys())


@cliutils.arg(
    '--flavor',
    metavar='<flavor>',
    help=_("Filter results by flavor name or ID."))
@cliutils.arg(
    '--tenant', metavar='<tenant_id>',
    help=_('Filter results by tenant ID.'))
def do_flavor_access_list(cs, args):
    """Print access information about the given flavor."""
    if args.flavor and args.tenant:
        raise exceptions.CommandError(_("Unable to filter results by "
                                        "both --flavor and --tenant."))
    elif args.flavor:
        flavor = _find_flavor(cs, args.flavor)
        if flavor.is_public:
            raise exceptions.CommandError(_("Failed to get access list "
                                            "for public flavor type."))
        kwargs = {'flavor': flavor}
    elif args.tenant:
        kwargs = {'tenant': args.tenant}
    else:
        raise exceptions.CommandError(_("Unable to get all access lists. "
                                        "Specify --flavor or --tenant"))

    try:
        access_list = cs.flavor_access.list(**kwargs)
    except NotImplementedError as e:
        raise exceptions.CommandError("%s" % str(e))

    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Flavor name or ID to add access for the given tenant."))
@cliutils.arg(
    'tenant', metavar='<tenant_id>',
    help=_('Tenant ID to add flavor access for.'))
def do_flavor_access_add(cs, args):
    """Add flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.add_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Flavor name or ID to remove access for the given tenant."))
@cliutils.arg(
    'tenant', metavar='<tenant_id>',
    help=_('Tenant ID to remove flavor access for.'))
def do_flavor_access_remove(cs, args):
    """Remove flavor access for the given tenant."""
    flavor = _find_flavor(cs, args.flavor)
    access_list = cs.flavor_access.remove_tenant_access(flavor, args.tenant)
    columns = ['Flavor_ID', 'Tenant_ID']
    utils.print_list(access_list, columns)


@cliutils.arg(
    'project_id', metavar='<project_id>',
    help=_('The ID of the project.'))
def do_scrub(cs, args):
    """Delete networks and security groups associated with a project."""
    networks_list = cs.networks.list()
    networks_list = [network for network in networks_list
                     if getattr(network, 'project_id', '') == args.project_id]
    search_opts = {'all_tenants': 1}
    groups = cs.security_groups.list(search_opts)
    groups = [group for group in groups
              if group.tenant_id == args.project_id]
    for network in networks_list:
        cs.networks.disassociate(network)
    for group in groups:
        cs.security_groups.delete(group)


@cliutils.arg(
    '--fields',
    default=None,
    metavar='<fields>',
    help='Comma-separated list of fields to display. '
         'Use the show command to see which fields are available.')
def do_network_list(cs, args):
    """Print a list of available networks."""
    network_list = cs.networks.list()
    columns = ['ID', 'Label', 'Cidr']

    formatters = {}
    field_titles = []
    if args.fields:
        for field in args.fields.split(','):
            field_title, formatter = utils._make_field_formatter(field, {})
            field_titles.append(field_title)
            formatters[field_title] = formatter

    columns = columns + field_titles
    utils.print_list(network_list, columns)


@cliutils.arg(
    'network',
    metavar='<network>',
    help=_("uuid or label of network"))
def do_network_show(cs, args):
    """Show details about the given network."""
    network = utils.find_resource(cs.networks, args.network)
    utils.print_dict(network._info)


@cliutils.arg(
    'network',
    metavar='<network>',
    help=_("uuid or label of network"))
def do_network_delete(cs, args):
    """Delete network by label or id."""
    network = utils.find_resource(cs.networks, args.network)
    network.delete()


@cliutils.arg(
    '--host-only',
    dest='host_only',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0)
@cliutils.arg(
    '--project-only',
    dest='project_only',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0)
@cliutils.arg(
    'network',
    metavar='<network>',
    help="uuid of network")
def do_network_disassociate(cs, args):
    """Disassociate host and/or project from the given network."""
    if args.host_only:
        cs.networks.disassociate(args.network, True, False)
    elif args.project_only:
        cs.networks.disassociate(args.network, False, True)
    else:
        cs.networks.disassociate(args.network, True, True)


@cliutils.arg(
    'network',
    metavar='<network>',
    help="uuid of network")
@cliutils.arg(
    'host',
    metavar='<host>',
    help="Name of host")
def do_network_associate_host(cs, args):
    """Associate host with network."""
    cs.networks.associate_host(args.network, args.host)


@cliutils.arg(
    'network',
    metavar='<network>',
    help="uuid of network")
def do_network_associate_project(cs, args):
    """Associate project with network."""
    cs.networks.associate_project(args.network)


def _filter_network_create_options(args):
    valid_args = ['label', 'cidr', 'vlan_start', 'vpn_start', 'cidr_v6',
                  'gateway', 'gateway_v6', 'bridge', 'bridge_interface',
                  'multi_host', 'dns1', 'dns2', 'uuid', 'fixed_cidr',
                  'project_id', 'priority', 'vlan', 'mtu', 'dhcp_server',
                  'allowed_start', 'allowed_end']
    kwargs = {}
    for k, v in args.__dict__.items():
        if k in valid_args and v is not None:
            kwargs[k] = v

    return kwargs


@cliutils.arg(
    'label',
    metavar='<network_label>',
    help=_("Label for network"))
@cliutils.arg(
    '--fixed-range-v4',
    dest='cidr',
    metavar='<x.x.x.x/yy>',
    help=_("IPv4 subnet (ex: 10.0.0.0/8)"))
@cliutils.arg(
    '--fixed-range-v6',
    dest="cidr_v6",
    help=_('IPv6 subnet (ex: fe80::/64'))
@cliutils.arg(
    '--vlan',
    dest='vlan',
    type=int,
    metavar='<vlan id>',
    help=_("The vlan ID to be assigned to the project."))
@cliutils.arg(
    '--vlan-start',
    dest='vlan_start',
    type=int,
    metavar='<vlan start>',
    help=_('First vlan ID to be assigned to the project. Subsequent vlan '
           'IDs will be assigned incrementally.'))
@cliutils.arg(
    '--vpn',
    dest='vpn_start',
    type=int,
    metavar='<vpn start>',
    help=_("vpn start"))
@cliutils.arg(
    '--gateway',
    dest="gateway",
    help=_('gateway'))
@cliutils.arg(
    '--gateway-v6',
    dest="gateway_v6",
    help=_('IPv6 gateway'))
@cliutils.arg(
    '--bridge',
    dest="bridge",
    metavar='<bridge>',
    help=_('VIFs on this network are connected to this bridge.'))
@cliutils.arg(
    '--bridge-interface',
    dest="bridge_interface",
    metavar='<bridge interface>',
    help=_('The bridge is connected to this interface.'))
@cliutils.arg(
    '--multi-host',
    dest="multi_host",
    metavar="<'T'|'F'>",
    help=_('Multi host'))
@cliutils.arg(
    '--dns1',
    dest="dns1",
    metavar="<DNS Address>", help='First DNS')
@cliutils.arg(
    '--dns2',
    dest="dns2",
    metavar="<DNS Address>",
    help=_('Second DNS'))
@cliutils.arg(
    '--uuid',
    dest="uuid",
    metavar="<network uuid>",
    help=_('Network UUID'))
@cliutils.arg(
    '--fixed-cidr',
    dest="fixed_cidr",
    metavar='<x.x.x.x/yy>',
    help=_('IPv4 subnet for fixed IPs (ex: 10.20.0.0/16)'))
@cliutils.arg(
    '--project-id',
    dest="project_id",
    metavar="<project id>",
    help=_('Project ID'))
@cliutils.arg(
    '--priority',
    dest="priority",
    metavar="<number>",
    help=_('Network interface priority'))
@cliutils.arg(
    '--mtu',
    dest="mtu",
    type=int,
    help=_('MTU for network'))
@cliutils.arg(
    '--enable-dhcp',
    dest="enable_dhcp",
    metavar="<'T'|'F'>",
    help=_('Enable dhcp'))
@cliutils.arg(
    '--dhcp-server',
    dest="dhcp_server",
    help=_('Dhcp-server (defaults to gateway address)'))
@cliutils.arg(
    '--share-address',
    dest="share_address",
    metavar="<'T'|'F'>",
    help=_('Share address'))
@cliutils.arg(
    '--allowed-start',
    dest="allowed_start",
    help=_('Start of allowed addresses for instances'))
@cliutils.arg(
    '--allowed-end',
    dest="allowed_end",
    help=_('End of allowed addresses for instances'))
def do_network_create(cs, args):
    """Create a network."""

    if not (args.cidr or args.cidr_v6):
        raise exceptions.CommandError(
            _("Must specify either fixed_range_v4 or fixed_range_v6"))
    kwargs = _filter_network_create_options(args)
    if args.multi_host is not None:
        kwargs['multi_host'] = bool(args.multi_host == 'T' or
                                    strutils.bool_from_string(args.multi_host))
    if args.enable_dhcp is not None:
        kwargs['enable_dhcp'] = bool(
            args.enable_dhcp == 'T' or
            strutils.bool_from_string(args.enable_dhcp))
    if args.share_address is not None:
        kwargs['share_address'] = bool(
            args.share_address == 'T' or
            strutils.bool_from_string(args.share_address))

    cs.networks.create(**kwargs)


@cliutils.arg(
    '--limit',
    dest="limit",
    metavar="<limit>",
    help=_('Number of images to return per request.'))
def do_image_list(cs, _args):
    """Print a list of available images to boot from."""
    limit = _args.limit
    image_list = cs.images.list(limit=limit)

    def parse_server_name(image):
        try:
            return image.server['id']
        except (AttributeError, KeyError):
            return ''

    fmts = {'Server': parse_server_name}
    utils.print_list(image_list, ['ID', 'Name', 'Status', 'Server'],
                     fmts, sortby_index=1)


@cliutils.arg(
    'image',
    metavar='<image>',
    help=_("Name or ID of image"))
@cliutils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'delete'],
    help=_("Actions: 'set' or 'delete'"))
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to add/update or delete (only key is necessary on '
           'delete)'))
def do_image_meta(cs, args):
    """Set or Delete metadata on an image."""
    image = _find_image(cs, args.image)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.images.set_meta(image, metadata)
    elif args.action == 'delete':
        cs.images.delete_meta(image, metadata.keys())


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata[0]:
        # Can only pass the key in on 'delete'
        # So this doesn't have to have '='
        if metadatum.find('=') > -1:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata


def _print_image(image):
    info = image._info.copy()

    # ignore links, we don't need to present those
    info.pop('links')

    # try to replace a server entity to just an id
    server = info.pop('server', None)
    try:
        info['server'] = server['id']
    except (KeyError, TypeError):
        pass

    # break up metadata and display each on its own row
    metadata = info.pop('metadata', {})
    try:
        for key, value in metadata.items():
            _key = 'metadata %s' % key
            info[_key] = value
    except AttributeError:
        pass

    utils.print_dict(info)


def _print_flavor(flavor):
    info = flavor._info.copy()
    # ignore links, we don't need to present those
    info.pop('links')
    info.update({"extra_specs": _print_flavor_extra_specs(flavor)})
    utils.print_dict(info)


@cliutils.arg(
    'image',
    metavar='<image>',
    help=_("Name or ID of image"))
def do_image_show(cs, args):
    """Show details about the given image."""
    image = _find_image(cs, args.image)
    _print_image(image)


@cliutils.arg(
    'image', metavar='<image>', nargs='+',
    help=_('Name or ID of image(s).'))
def do_image_delete(cs, args):
    """Delete specified image(s)."""
    for image in args.image:
        try:
            _find_image(cs, image).delete()
        except Exception as e:
            print(_("Delete for image %(image)s failed: %(e)s") %
                  {'image': image, 'e': e})


@cliutils.arg(
    '--reservation-id',
    dest='reservation_id',
    metavar='<reservation-id>',
    default=None,
    help=_('Only return servers that match reservation-id.'))
@cliutils.arg(
    '--reservation_id',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--ip',
    dest='ip',
    metavar='<ip-regexp>',
    default=None,
    help=_('Search with regular expression match by IP address.'))
@cliutils.arg(
    '--ip6',
    dest='ip6',
    metavar='<ip6-regexp>',
    default=None,
    help=_('Search with regular expression match by IPv6 address.'))
@cliutils.arg(
    '--name',
    dest='name',
    metavar='<name-regexp>',
    default=None,
    help=_('Search with regular expression match by name'))
@cliutils.arg(
    '--instance-name',
    dest='instance_name',
    metavar='<name-regexp>',
    default=None,
    help=_('Search with regular expression match by server name.'))
@cliutils.arg(
    '--instance_name',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--status',
    dest='status',
    metavar='<status>',
    default=None,
    help=_('Search by server status'))
@cliutils.arg(
    '--flavor',
    dest='flavor',
    metavar='<flavor>',
    default=None,
    help=_('Search by flavor name or ID'))
@cliutils.arg(
    '--image',
    dest='image',
    metavar='<image>',
    default=None,
    help=_('Search by image name or ID'))
@cliutils.arg(
    '--host',
    dest='host',
    metavar='<hostname>',
    default=None,
    help=_('Search servers by hostname to which they are assigned (Admin '
           'only).'))
@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=int(strutils.bool_from_string(
        os.environ.get("ALL_TENANTS", 'false'), True)),
    help=_('Display information from all tenants (Admin only).'))
@cliutils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--tenant',
    # nova db searches by project_id
    dest='tenant',
    metavar='<tenant>',
    nargs='?',
    help=_('Display information from single tenant (Admin only). '
           'The --all-tenants option must also be provided.'))
@cliutils.arg(
    '--user',
    dest='user',
    metavar='<user>',
    nargs='?',
    help=_('Display information from single user (Admin only).'))
@cliutils.arg(
    '--deleted',
    dest='deleted',
    action="store_true",
    default=False,
    help='Only display deleted servers (Admin only).')
@cliutils.arg(
    '--fields',
    default=None,
    metavar='<fields>',
    help=_('Comma-separated list of fields to display. '
           'Use the show command to see which fields are available.'))
@cliutils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Get only uuid and name.'))
@cliutils.arg(
    '--sort',
    dest='sort',
    metavar='<key>[:<direction>]',
    help=('Comma-separated list of sort keys and directions in the form'
          ' of <key>[:<asc|desc>]. The direction defaults to descending if'
          ' not specified.'))
def do_list(cs, args):
    """List active servers."""
    imageid = None
    flavorid = None
    if args.image:
        imageid = _find_image(cs, args.image).id
    if args.flavor:
        flavorid = _find_flavor(cs, args.flavor).id
    # search by tenant or user only works with all_tenants
    if args.tenant or args.user:
        args.all_tenants = 1
    search_opts = {
        'all_tenants': args.all_tenants,
        'reservation_id': args.reservation_id,
        'ip': args.ip,
        'ip6': args.ip6,
        'name': args.name,
        'image': imageid,
        'flavor': flavorid,
        'status': args.status,
        'tenant_id': args.tenant,
        'user_id': args.user,
        'host': args.host,
        'deleted': args.deleted,
        'instance_name': args.instance_name}

    filters = {'flavor': lambda f: f['id'],
               'security_groups': utils._format_security_groups}

    formatters = {}
    field_titles = []
    if args.fields:
        for field in args.fields.split(','):
            field_title, formatter = utils._make_field_formatter(field,
                                                                 filters)
            field_titles.append(field_title)
            formatters[field_title] = formatter

    id_col = 'ID'

    detailed = not args.minimal

    sort_keys = []
    sort_dirs = []
    if args.sort:
        for sort in args.sort.split(','):
            sort_key, _sep, sort_dir = sort.partition(':')
            if not sort_dir:
                sort_dir = 'desc'
            elif sort_dir not in ('asc', 'desc'):
                raise exceptions.CommandError(_(
                    'Unknown sort direction: %s') % sort_dir)
            sort_keys.append(sort_key)
            sort_dirs.append(sort_dir)

    servers = cs.servers.list(detailed=detailed,
                              search_opts=search_opts,
                              sort_keys=sort_keys,
                              sort_dirs=sort_dirs)
    convert = [('OS-EXT-SRV-ATTR:host', 'host'),
               ('OS-EXT-STS:task_state', 'task_state'),
               ('OS-EXT-SRV-ATTR:instance_name', 'instance_name'),
               ('OS-EXT-STS:power_state', 'power_state'),
               ('hostId', 'host_id')]
    _translate_keys(servers, convert)
    _translate_extended_states(servers)
    if args.minimal:
        columns = [
            id_col,
            'Name']
    elif field_titles:
        columns = [id_col] + field_titles
    else:
        columns = [
            id_col,
            'Name',
            'Status',
            'Task State',
            'Power State',
            'Networks'
        ]
        # If getting the data for all tenants, print
        # Tenant ID as well
        if search_opts['all_tenants']:
            columns.insert(2, 'Tenant ID')
    formatters['Networks'] = utils._format_servers_list_networks
    sortby_index = 1
    if args.sort:
        sortby_index = None
    utils.print_list(servers, columns,
                     formatters, sortby_index=sortby_index)


@cliutils.arg(
    '--hard',
    dest='reboot_type',
    action='store_const',
    const=servers.REBOOT_HARD,
    default=servers.REBOOT_SOFT,
    help=_('Perform a hard reboot (instead of a soft one).'))
@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Poll until reboot is complete.'))
def do_reboot(cs, args):
    """Reboot a server."""
    server = _find_server(cs, args.server)
    server.reboot(args.reboot_type)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'rebooting', ['active'],
                         show_progress=False)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('image', metavar='<image>', help=_("Name or ID of new image."))
@cliutils.arg(
    '--rebuild-password',
    dest='rebuild_password',
    metavar='<rebuild-password>',
    default=False,
    help=_("Set the provided admin password on the rebuilt server."))
@cliutils.arg(
    '--rebuild_password',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server rebuild progress until it completes.'))
@cliutils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Skips flavor/image lookups when showing servers'))
@cliutils.arg(
    '--preserve-ephemeral',
    action="store_true",
    default=False,
    help='Preserve the default ephemeral storage partition on rebuild.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help=_('Name for the new server'))
@cliutils.arg(
    '--meta',
    metavar="<key=value>",
    action='append',
    default=[],
    help=_("Record arbitrary key/value metadata to /meta_data.json "
           "on the metadata server. Can be specified multiple times."))
@cliutils.arg(
    '--file',
    metavar="<dst-path=src-path>",
    action='append',
    dest='files',
    default=[],
    help=_("Store arbitrary files from <src-path> locally to <dst-path> "
           "on the new server. You may store up to 5 files."))
def do_rebuild(cs, args):
    """Shutdown, re-image, and re-boot a server."""
    server = _find_server(cs, args.server)
    image = _find_image(cs, args.image)

    if args.rebuild_password is not False:
        _password = args.rebuild_password
    else:
        _password = None

    kwargs = utils.get_resource_manager_extra_kwargs(do_rebuild, args)
    kwargs['preserve_ephemeral'] = args.preserve_ephemeral
    kwargs['name'] = args.name
    meta = dict(v.split('=', 1) for v in args.meta)
    kwargs['meta'] = meta

    files = {}
    for f in args.files:
        try:
            dst, src = f.split('=', 1)
            with open(src, 'r') as s:
                files[dst] = s.read()
        except IOError as e:
            raise exceptions.CommandError(_("Can't open '%(src)s': %(exc)s") %
                                          {'src': src, 'exc': e})
        except ValueError:
            raise exceptions.CommandError(_("Invalid file argument '%s'. "
                                            "File arguments must be of the "
                                            "form '--file "
                                            "<dst-path=src-path>'") % f)
    kwargs['files'] = files
    server = server.rebuild(image, _password, **kwargs)
    _print_server(cs, args, server)

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'rebuilding', ['active'])


@cliutils.arg(
    'server', metavar='<server>',
    help=_('Name (old name) or ID of server.'))
@cliutils.arg('name', metavar='<name>', help=_('New name for the server.'))
def do_rename(cs, args):
    """Rename a server."""
    _find_server(cs, args.server).update(name=args.name)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'flavor',
    metavar='<flavor>',
    help=_("Name or ID of new flavor."))
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server resize progress until it completes.'))
def do_resize(cs, args):
    """Resize a server."""
    server = _find_server(cs, args.server)
    flavor = _find_flavor(cs, args.flavor)
    kwargs = utils.get_resource_manager_extra_kwargs(do_resize, args)
    server.resize(flavor, **kwargs)
    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'resizing',
                         ['active', 'verify_resize'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resize_confirm(cs, args):
    """Confirm a previous resize."""
    _find_server(cs, args.server).confirm_resize()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resize_revert(cs, args):
    """Revert a previous resize (and return to the previous VM)."""
    _find_server(cs, args.server).revert_resize()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the server migration progress until it completes.'))
def do_migrate(cs, args):
    """Migrate a server. The new host will be selected by the scheduler."""
    server = _find_server(cs, args.server)
    server.migrate()

    if args.poll:
        _poll_for_status(cs.servers.get, server.id, 'migrating',
                         ['active', 'verify_resize'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_pause(cs, args):
    """Pause a server."""
    _find_server(cs, args.server).pause()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unpause(cs, args):
    """Unpause a server."""
    _find_server(cs, args.server).unpause()


@cliutils.arg(
    'server',
    metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_stop(cs, args):
    """Stop the server(s)."""
    utils.do_action_on_many(
        lambda s: _find_server(cs, s).stop(),
        args.server,
        _("Request to stop server %s has been accepted."),
        _("Unable to stop the specified server(s)."))


@cliutils.arg(
    'server',
    metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_start(cs, args):
    """Start the server(s)."""
    utils.do_action_on_many(
        lambda s: _find_server(cs, s).start(),
        args.server,
        _("Request to start server %s has been accepted."),
        _("Unable to start the specified server(s)."))


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_lock(cs, args):
    """Lock a server. A normal (non-admin) user will not be able to execute
    actions on a locked server.
    """
    _find_server(cs, args.server).lock()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unlock(cs, args):
    """Unlock a server."""
    _find_server(cs, args.server).unlock()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_suspend(cs, args):
    """Suspend a server."""
    _find_server(cs, args.server).suspend()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_resume(cs, args):
    """Resume a server."""
    _find_server(cs, args.server).resume()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--password',
    metavar='<password>',
    dest='password',
    help=_('The admin password to be set in the rescue environment.'))
@cliutils.arg(
    '--image',
    metavar='<image>',
    dest='image',
    help=_('The image to rescue with.'))
def do_rescue(cs, args):
    """Reboots a server into rescue mode, which starts the machine
    from either the initial image or a specified image, attaching the current
    boot disk as secondary.
    """
    kwargs = {}
    if args.image:
        kwargs['image'] = _find_image(cs, args.image)
    if args.password:
        kwargs['password'] = args.password
    utils.print_dict(_find_server(cs, args.server).rescue(**kwargs)[1])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unrescue(cs, args):
    """Restart the server from normal boot disk again."""
    _find_server(cs, args.server).unrescue()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_shelve(cs, args):
    """Shelve a server."""
    _find_server(cs, args.server).shelve()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_shelve_offload(cs, args):
    """Remove a shelved server from the compute node."""
    _find_server(cs, args.server).shelve_offload()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_unshelve(cs, args):
    """Unshelve a server."""
    _find_server(cs, args.server).unshelve()


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_diagnostics(cs, args):
    """Retrieve server diagnostics."""
    server = _find_server(cs, args.server)
    utils.print_dict(cs.servers.diagnostics(server)[1], wrap=80)


@cliutils.arg(
    'server', metavar='<server>',
    help=_('Name or ID of a server for which the network cache should '
           'be refreshed from neutron (Admin only).'))
def do_refresh_network(cs, args):
    """Refresh server network information."""
    server = _find_server(cs, args.server)
    cs.server_external_events.create([{'server_uuid': server.id,
                                       'name': 'network-changed'}])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_root_password(cs, args):
    """
    Change the admin password for a server.
    """
    server = _find_server(cs, args.server)
    p1 = getpass.getpass('New password: ')
    p2 = getpass.getpass('Again: ')
    if p1 != p2:
        raise exceptions.CommandError(_("Passwords do not match."))
    server.change_password(p1)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('name', metavar='<name>', help=_('Name of snapshot.'))
@cliutils.arg(
    '--show',
    dest='show',
    action="store_true",
    default=False,
    help=_('Print image info.'))
@cliutils.arg(
    '--poll',
    dest='poll',
    action="store_true",
    default=False,
    help=_('Report the snapshot progress and poll until image creation is '
           'complete.'))
def do_image_create(cs, args):
    """Create a new image by taking a snapshot of a running server."""
    server = _find_server(cs, args.server)
    image_uuid = cs.servers.create_image(server, args.name)

    if args.poll:
        _poll_for_status(cs.images.get, image_uuid, 'snapshotting',
                         ['active'])

        # NOTE(sirp):  A race-condition exists between when the image finishes
        # uploading and when the servers's `task_state` is cleared. To account
        # for this, we need to poll a second time to ensure the `task_state` is
        # cleared before returning, ensuring that a snapshot taken immediately
        # after this function returns will succeed.
        #
        # A better long-term solution will be to separate 'snapshotting' and
        # 'image-uploading' in Nova and clear the task-state once the VM
        # snapshot is complete but before the upload begins.
        task_state_field = "OS-EXT-STS:task_state"
        if hasattr(server, task_state_field):
            _poll_for_status(cs.servers.get, server.id, 'image_snapshot',
                             [None], status_field=task_state_field,
                             show_progress=False, silent=True)

    if args.show:
        _print_image(cs.images.get(image_uuid))


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('name', metavar='<name>', help=_('Name of the backup image.'))
@cliutils.arg(
    'backup_type', metavar='<backup-type>',
    help=_('The backup type, like "daily" or "weekly".'))
@cliutils.arg(
    'rotation', metavar='<rotation>',
    help=_('Int parameter representing how many backups to keep '
           'around.'))
def do_backup(cs, args):
    """Backup a server by creating a 'backup' type snapshot."""
    _find_server(cs, args.server).backup(args.name,
                                         args.backup_type,
                                         args.rotation)


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_("Name or ID of server"))
@cliutils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'delete'],
    help=_("Actions: 'set' or 'delete'"))
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to set or delete (only key is necessary on delete)'))
def do_meta(cs, args):
    """Set or Delete metadata on a server."""
    server = _find_server(cs, args.server)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.servers.set_meta(server, metadata)
    elif args.action == 'delete':
        cs.servers.delete_meta(server, sorted(metadata.keys(), reverse=True))


def _print_server(cs, args, server=None):
    # By default when searching via name we will do a
    # findall(name=blah) and due a REST /details which is not the same
    # as a .get() and doesn't get the information about flavors and
    # images. This fix it as we redo the call with the id which does a
    # .get() to get all informations.
    if not server:
        server = _find_server(cs, args.server)

    minimal = getattr(args, "minimal", False)

    networks = server.networks
    info = server._info.copy()
    for network_label, address_list in networks.items():
        info['%s network' % network_label] = ', '.join(address_list)

    flavor = info.get('flavor', {})
    flavor_id = flavor.get('id', '')
    if minimal:
        info['flavor'] = flavor_id
    else:
        info['flavor'] = '%s (%s)' % (_find_flavor(cs, flavor_id).name,
                                      flavor_id)

    if 'security_groups' in info:
        # when we have multiple nics the info will include the
        # security groups N times where N == number of nics. Be nice
        # and only display it once.
        info['security_groups'] = ', '.join(
            sorted(set(group['name'] for group in info['security_groups'])))

    image = info.get('image', {})
    if image:
        image_id = image.get('id', '')
        if minimal:
            info['image'] = image_id
        else:
            try:
                info['image'] = '%s (%s)' % (_find_image(cs, image_id).name,
                                             image_id)
            except Exception:
                info['image'] = '%s (%s)' % (_("Image not found"), image_id)
    else:  # Booted from volume
        info['image'] = _("Attempt to boot from volume - no image supplied")

    info.pop('links', None)
    info.pop('addresses', None)

    utils.print_dict(info)


@cliutils.arg(
    '--minimal',
    dest='minimal',
    action="store_true",
    default=False,
    help=_('Skips flavor/image lookups when showing servers'))
@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_show(cs, args):
    """Show details about the given server."""
    _print_server(cs, args)


@cliutils.arg(
    'server', metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
def do_delete(cs, args):
    """Immediately shut down and delete specified server(s)."""
    find_args = {'all_tenants': '1'}
    utils.do_action_on_many(
        lambda s: _find_server(cs, s, **find_args).delete(),
        args.server,
        _("Request to delete server %s has been accepted."),
        _("Unable to delete the specified server(s)."))


def _find_server(cs, server, **find_args):
    """Get a server by name or ID."""
    return utils.find_resource(cs.servers, server, **find_args)


def _find_image(cs, image):
    """Get an image by name or ID."""
    return utils.find_resource(cs.images, image)


def _find_flavor(cs, flavor):
    """Get a flavor by name, ID, or RAM size."""
    try:
        return utils.find_resource(cs.flavors, flavor, is_public=None)
    except exceptions.NotFound:
        return cs.flavors.find(ram=flavor)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'network_id',
    metavar='<network-id>',
    help='Network ID.')
def do_add_fixed_ip(cs, args):
    """Add new IP address on a network to server."""
    server = _find_server(cs, args.server)
    server.add_fixed_ip(args.network_id)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('address', metavar='<address>', help=_('IP Address.'))
def do_remove_fixed_ip(cs, args):
    """Remove an IP address from a server."""
    server = _find_server(cs, args.server)
    server.remove_fixed_ip(args.address)


def _find_volume(cs, volume):
    """Get a volume by name or ID."""
    return utils.find_resource(cs.volumes, volume)


def _find_volume_snapshot(cs, snapshot):
    """Get a volume snapshot by name or ID."""
    return utils.find_resource(cs.volume_snapshots, snapshot)


def _print_volume(volume):
    utils.print_dict(volume._info)


def _print_volume_snapshot(snapshot):
    utils.print_dict(snapshot._info)


def _translate_volume_keys(collection):
    _translate_keys(collection,
                    [('displayName', 'display_name'),
                     ('volumeType', 'volume_type')])


def _translate_volume_snapshot_keys(collection):
    _translate_keys(collection,
                    [('displayName', 'display_name'),
                     ('volumeId', 'volume_id')])


def _translate_availability_zone_keys(collection):
    _translate_keys(collection,
                    [('zoneName', 'name'), ('zoneState', 'status')])


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=int(strutils.bool_from_string(
        os.environ.get("ALL_TENANTS", 'false'), True)),
    help=_('Display information from all tenants (Admin only).'))
@cliutils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@cliutils.service_type('volume')
def do_volume_list(cs, args):
    """List all the volumes."""
    search_opts = {'all_tenants': args.all_tenants}
    volumes = cs.volumes.list(search_opts=search_opts)
    _translate_volume_keys(volumes)

    # Create a list of servers to which the volume is attached
    for vol in volumes:
        servers = [s.get('server_id') for s in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))
    utils.print_list(volumes, ['ID', 'Status', 'Display Name',
                               'Size', 'Volume Type', 'Attached to'])


@cliutils.arg(
    'volume',
    metavar='<volume>',
    help=_('Name or ID of the volume.'))
@cliutils.service_type('volume')
def do_volume_show(cs, args):
    """Show details about a volume."""
    volume = _find_volume(cs, args.volume)
    _print_volume(volume)


@cliutils.arg(
    'size',
    metavar='<size>',
    type=int,
    help=_('Size of volume in GB'))
@cliutils.arg(
    '--snapshot-id',
    metavar='<snapshot-id>',
    default=None,
    help=_('Optional snapshot id to create the volume from. (Default=None)'))
@cliutils.arg(
    '--snapshot_id',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--image-id',
    metavar='<image-id>',
    help=_('Optional image id to create the volume from. (Default=None)'),
    default=None)
@cliutils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help=_('Optional volume name. (Default=None)'))
@cliutils.arg(
    '--display_name',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--display-description',
    metavar='<display-description>',
    default=None,
    help=_('Optional volume description. (Default=None)'))
@cliutils.arg(
    '--display_description',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--volume-type',
    metavar='<volume-type>',
    default=None,
    help=_('Optional volume type. (Default=None)'))
@cliutils.arg(
    '--volume_type',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--availability-zone', metavar='<availability-zone>',
    help=_('Optional Availability Zone for volume. (Default=None)'),
    default=None)
@cliutils.service_type('volume')
def do_volume_create(cs, args):
    """Add a new volume."""
    volume = cs.volumes.create(args.size,
                               args.snapshot_id,
                               args.display_name,
                               args.display_description,
                               args.volume_type,
                               args.availability_zone,
                               imageRef=args.image_id)
    _print_volume(volume)


@cliutils.arg(
    'volume',
    metavar='<volume>', nargs='+',
    help=_('Name or ID of the volume(s) to delete.'))
@cliutils.service_type('volume')
def do_volume_delete(cs, args):
    """Remove volume(s)."""
    for volume in args.volume:
        try:
            _find_volume(cs, volume).delete()
        except Exception as e:
            print(_("Delete for volume %(volume)s failed: %(e)s") %
                  {'volume': volume, 'e': e})


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@cliutils.arg(
    'volume',
    metavar='<volume>',
    help=_('ID of the volume to attach.'))
@cliutils.arg(
    'device', metavar='<device>', default=None, nargs='?',
    help=_('Name of the device e.g. /dev/vdb. '
           'Use "auto" for autoassign (if supported)'))
def do_volume_attach(cs, args):
    """Attach a volume to a server."""
    if args.device == 'auto':
        args.device = None

    volume = cs.volumes.create_server_volume(_find_server(cs, args.server).id,
                                             args.volume,
                                             args.device)
    _print_volume(volume)


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@cliutils.arg(
    'attachment_id',
    metavar='<attachment>',
    help=_('Attachment ID of the volume.'))
@cliutils.arg(
    'new_volume',
    metavar='<volume>',
    help=_('ID of the volume to attach.'))
def do_volume_update(cs, args):
    """Update volume attachment."""
    cs.volumes.update_server_volume(_find_server(cs, args.server).id,
                                    args.attachment_id,
                                    args.new_volume)


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_('Name or ID of server.'))
@cliutils.arg(
    'attachment_id',
    metavar='<volume>',
    help=_('ID of the volume to detach.'))
def do_volume_detach(cs, args):
    """Detach a volume from a server."""
    cs.volumes.delete_server_volume(_find_server(cs, args.server).id,
                                    args.attachment_id)


@cliutils.service_type('volume')
def do_volume_snapshot_list(cs, _args):
    """List all the snapshots."""
    snapshots = cs.volume_snapshots.list()
    _translate_volume_snapshot_keys(snapshots)
    utils.print_list(snapshots, ['ID', 'Volume ID', 'Status', 'Display Name',
                                 'Size'])


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help=_('Name or ID of the snapshot.'))
@cliutils.service_type('volume')
def do_volume_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    _print_volume_snapshot(snapshot)


@cliutils.arg(
    'volume_id',
    metavar='<volume-id>',
    help=_('ID of the volume to snapshot'))
@cliutils.arg(
    '--force',
    metavar='<True|False>',
    help=_('Optional flag to indicate whether to snapshot a volume even if '
           'its attached to a server. (Default=False)'),
    default=False)
@cliutils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help=_('Optional snapshot name. (Default=None)'))
@cliutils.arg(
    '--display_name',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--display-description',
    metavar='<display-description>',
    default=None,
    help=_('Optional snapshot description. (Default=None)'))
@cliutils.arg(
    '--display_description',
    help=argparse.SUPPRESS)
@cliutils.service_type('volume')
def do_volume_snapshot_create(cs, args):
    """Add a new snapshot."""
    snapshot = cs.volume_snapshots.create(args.volume_id,
                                          args.force,
                                          args.display_name,
                                          args.display_description)
    _print_volume_snapshot(snapshot)


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help=_('Name or ID of the snapshot to delete.'))
@cliutils.service_type('volume')
def do_volume_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    snapshot.delete()


def _print_volume_type_list(vtypes):
    utils.print_list(vtypes, ['ID', 'Name'])


@cliutils.service_type('volume')
def do_volume_type_list(cs, args):
    """Print a list of available 'volume types'."""
    vtypes = cs.volume_types.list()
    _print_volume_type_list(vtypes)


@cliutils.arg(
    'name',
    metavar='<name>',
    help=_("Name of the new volume type"))
@cliutils.service_type('volume')
def do_volume_type_create(cs, args):
    """Create a new volume type."""
    vtype = cs.volume_types.create(args.name)
    _print_volume_type_list([vtype])


@cliutils.arg(
    'id',
    metavar='<id>',
    help=_("Unique ID of the volume type to delete"))
@cliutils.service_type('volume')
def do_volume_type_delete(cs, args):
    """Delete a specific volume type."""
    cs.volume_types.delete(args.id)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'console_type',
    metavar='<console-type>',
    help=_('Type of vnc console ("novnc" or "xvpvnc").'))
def do_get_vnc_console(cs, args):
    """Get a vnc console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_vnc_console(args.console_type)

    class VNCConsole(object):
        def __init__(self, console_dict):
            self.type = console_dict['type']
            self.url = console_dict['url']

    utils.print_list([VNCConsole(data['console'])], ['Type', 'Url'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'console_type',
    metavar='<console-type>',
    help=_('Type of spice console ("spice-html5").'))
def do_get_spice_console(cs, args):
    """Get a spice console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_spice_console(args.console_type)

    class SPICEConsole(object):
        def __init__(self, console_dict):
            self.type = console_dict['type']
            self.url = console_dict['url']

    utils.print_list([SPICEConsole(data['console'])], ['Type', 'Url'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'console_type',
    metavar='<console-type>',
    help='Type of rdp console ("rdp-html5").')
def do_get_rdp_console(cs, args):
    """Get a rdp console to a server."""
    server = _find_server(cs, args.server)
    data = server.get_rdp_console(args.console_type)

    class RDPConsole(object):
        def __init__(self, console_dict):
            self.type = console_dict['type']
            self.url = console_dict['url']

    utils.print_list([RDPConsole(data['console'])], ['Type', 'Url'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--console_type', default='serial',
    help=_('Type of serial console, default="serial".'))
def do_get_serial_console(cs, args):
    """Get a serial console to a server."""
    if args.console_type not in ('serial',):
        raise exceptions.CommandError(
            _("Invalid parameter value for 'console_type', "
              "currently supported 'serial'."))

    server = _find_server(cs, args.server)
    data = server.get_serial_console(args.console_type)

    class SerialConsole(object):
        def __init__(self, console_dict):
            self.type = console_dict['type']
            self.url = console_dict['url']

    utils.print_list([SerialConsole(data['console'])], ['Type', 'Url'])


@cliutils.arg('server', metavar='<server>', help='Name or ID of server.')
@cliutils.arg(
    'private_key',
    metavar='<private-key>',
    help=_('Private key (used locally to decrypt password) (Optional). '
           'When specified, the command displays the clear (decrypted) VM '
           'password. When not specified, the ciphered VM password is '
           'displayed.'),
    nargs='?',
    default=None)
def do_get_password(cs, args):
    """Get the admin password for a server."""
    server = _find_server(cs, args.server)
    data = server.get_password(args.private_key)
    print(data)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_clear_password(cs, args):
    """Clear the admin password for a server."""
    server = _find_server(cs, args.server)
    server.clear_password()


def _print_floating_ip_list(floating_ips):
    convert = [('instance_id', 'server_id')]
    _translate_keys(floating_ips, convert)

    utils.print_list(floating_ips,
                     ['Id', 'IP', 'Server Id', 'Fixed IP', 'Pool'])


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--length',
    metavar='<length>',
    default=None,
    help=_('Length in lines to tail.'))
def do_console_log(cs, args):
    """Get console log output of a server."""
    server = _find_server(cs, args.server)
    data = server.get_console_output(length=args.length)
    print(data)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('address', metavar='<address>', help=_('IP Address.'))
@cliutils.arg(
    '--fixed-address',
    metavar='<fixed_address>',
    default=None,
    help=_('Fixed IP Address to associate with.'))
def do_add_floating_ip(cs, args):
    """DEPRECATED, use floating-ip-associate instead."""
    _associate_floating_ip(cs, args)


@cliutils.arg('server', metavar='<server>', help='Name or ID of server.')
@cliutils.arg('address', metavar='<address>', help='IP Address.')
@cliutils.arg(
    '--fixed-address',
    metavar='<fixed_address>',
    default=None,
    help='Fixed IP Address to associate with.')
def do_floating_ip_associate(cs, args):
    """Associate a floating IP address to a server."""
    _associate_floating_ip(cs, args)


def _associate_floating_ip(cs, args):
    server = _find_server(cs, args.server)
    server.add_floating_ip(args.address, args.fixed_address)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('address', metavar='<address>', help=_('IP Address.'))
def do_remove_floating_ip(cs, args):
    """DEPRECATED, use floating-ip-disassociate instead."""
    _disassociate_floating_ip(cs, args)


@cliutils.arg('server', metavar='<server>', help='Name or ID of server.')
@cliutils.arg('address', metavar='<address>', help='IP Address.')
def do_floating_ip_disassociate(cs, args):
    """Disassociate a floating IP address from a server."""
    _disassociate_floating_ip(cs, args)


def _disassociate_floating_ip(cs, args):
    server = _find_server(cs, args.server)
    server.remove_floating_ip(args.address)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('Name of Security Group.'))
def do_add_secgroup(cs, args):
    """Add a Security Group to a server."""
    server = _find_server(cs, args.server)
    server.add_security_group(args.secgroup)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('Name of Security Group.'))
def do_remove_secgroup(cs, args):
    """Remove a Security Group from a server."""
    server = _find_server(cs, args.server)
    server.remove_security_group(args.secgroup)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_list_secgroup(cs, args):
    """List Security Group(s) of a server."""
    server = _find_server(cs, args.server)
    groups = server.list_security_group()
    _print_secgroups(groups)


@cliutils.arg(
    'pool',
    metavar='<floating-ip-pool>',
    help=_('Name of Floating IP Pool. (Optional)'),
    nargs='?',
    default=None)
def do_floating_ip_create(cs, args):
    """Allocate a floating IP for the current tenant."""
    _print_floating_ip_list([cs.floating_ips.create(pool=args.pool)])


@cliutils.arg('address', metavar='<address>', help=_('IP of Floating IP.'))
def do_floating_ip_delete(cs, args):
    """De-allocate a floating IP."""
    floating_ips = cs.floating_ips.list()
    for floating_ip in floating_ips:
        if floating_ip.ip == args.address:
            return cs.floating_ips.delete(floating_ip.id)
    raise exceptions.CommandError(_("Floating IP %s not found.") %
                                  args.address)


@cliutils.arg(
    '--all-tenants',
    action='store_true',
    default=False,
    help=_('Display floatingips from all tenants (Admin only).'))
def do_floating_ip_list(cs, args):
    """List floating IPs."""
    _print_floating_ip_list(cs.floating_ips.list(args.all_tenants))


def do_floating_ip_pool_list(cs, _args):
    """List all floating IP pools."""
    utils.print_list(cs.floating_ip_pools.list(), ['name'])


@cliutils.arg(
    '--host', dest='host', metavar='<host>', default=None,
    help=_('Filter by host'))
def do_floating_ip_bulk_list(cs, args):
    """List all floating IPs."""
    utils.print_list(cs.floating_ips_bulk.list(args.host), ['project_id',
                                                            'address',
                                                            'instance_uuid',
                                                            'pool',
                                                            'interface'])


@cliutils.arg('ip_range', metavar='<range>', help=_('Address range to create'))
@cliutils.arg(
    '--pool', dest='pool', metavar='<pool>', default=None,
    help=_('Pool for new Floating IPs'))
@cliutils.arg(
    '--interface', metavar='<interface>', default=None,
    help=_('Interface for new Floating IPs'))
def do_floating_ip_bulk_create(cs, args):
    """Bulk create floating IPs by range."""
    cs.floating_ips_bulk.create(args.ip_range, args.pool, args.interface)


@cliutils.arg('ip_range', metavar='<range>', help=_('Address range to delete'))
def do_floating_ip_bulk_delete(cs, args):
    """Bulk delete floating IPs by range."""
    cs.floating_ips_bulk.delete(args.ip_range)


def _print_dns_list(dns_entries):
    utils.print_list(dns_entries, ['ip', 'name', 'domain'])


def _print_domain_list(domain_entries):
    utils.print_list(domain_entries, ['domain', 'scope',
                                      'project', 'availability_zone'])


def do_dns_domains(cs, args):
    """Print a list of available dns domains."""
    domains = cs.dns_domains.domains()
    _print_domain_list(domains)


@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
@cliutils.arg('--ip', metavar='<ip>', help=_('IP address'), default=None)
@cliutils.arg('--name', metavar='<name>', help=_('DNS name'), default=None)
def do_dns_list(cs, args):
    """List current DNS entries for domain and IP or domain and name."""
    if not (args.ip or args.name):
        raise exceptions.CommandError(
            _("You must specify either --ip or --name"))
    if args.name:
        entry = cs.dns_entries.get(args.domain, args.name)
        _print_dns_list([entry])
    else:
        entries = cs.dns_entries.get_for_ip(args.domain,
                                            ip=args.ip)
        _print_dns_list(entries)


@cliutils.arg('ip', metavar='<ip>', help=_('IP address'))
@cliutils.arg('name', metavar='<name>', help=_('DNS name'))
@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
@cliutils.arg(
    '--type',
    metavar='<type>',
    help=_('dns type (e.g. "A")'),
    default='A')
def do_dns_create(cs, args):
    """Create a DNS entry for domain, name and IP."""
    cs.dns_entries.create(args.domain, args.name, args.ip, args.type)


@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
@cliutils.arg('name', metavar='<name>', help=_('DNS name'))
def do_dns_delete(cs, args):
    """Delete the specified DNS entry."""
    cs.dns_entries.delete(args.domain, args.name)


@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
def do_dns_delete_domain(cs, args):
    """Delete the specified DNS domain."""
    cs.dns_domains.delete(args.domain)


@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
@cliutils.arg(
    '--availability-zone',
    metavar='<availability-zone>',
    default=None,
    help=_('Limit access to this domain to servers '
           'in the specified availability zone.'))
@cliutils.arg(
    '--availability_zone',
    help=argparse.SUPPRESS)
def do_dns_create_private_domain(cs, args):
    """Create the specified DNS domain."""
    cs.dns_domains.create_private(args.domain,
                                  args.availability_zone)


@cliutils.arg('domain', metavar='<domain>', help=_('DNS domain'))
@cliutils.arg(
    '--project', metavar='<project>',
    help=_('Limit access to this domain to users '
           'of the specified project.'),
    default=None)
def do_dns_create_public_domain(cs, args):
    """Create the specified DNS domain."""
    cs.dns_domains.create_public(args.domain,
                                 args.project)


def _print_secgroup_rules(rules, show_source_group=True):
    class FormattedRule(object):
        def __init__(self, obj):
            items = (obj if isinstance(obj, dict) else obj._info).items()
            for k, v in items:
                if k == 'ip_range':
                    v = v.get('cidr')
                elif k == 'group':
                    k = 'source_group'
                    v = v.get('name')
                if v is None:
                    v = ''

                setattr(self, k, v)

    rules = [FormattedRule(rule) for rule in rules]
    headers = ['IP Protocol', 'From Port', 'To Port', 'IP Range']
    if show_source_group:
        headers.append('Source Group')
    utils.print_list(rules, headers)


def _print_secgroups(secgroups):
    utils.print_list(secgroups, ['Id', 'Name', 'Description'])


def _get_secgroup(cs, secgroup):
    # Check secgroup is an ID (nova-network) or UUID (neutron)
    if (utils.is_integer_like(encodeutils.safe_encode(secgroup)) or
            uuidutils.is_uuid_like(secgroup)):
        try:
            return cs.security_groups.get(secgroup)
        except exceptions.NotFound:
            pass

    # Check secgroup as a name
    match_found = False
    for s in cs.security_groups.list():
        encoding = (
            locale.getpreferredencoding() or sys.stdin.encoding or 'UTF-8')
        if not six.PY3:
            s.name = s.name.encode(encoding)
        if secgroup == s.name:
            if match_found is not False:
                msg = (_("Multiple security group matches found for name '%s'"
                         ", use an ID to be more specific.") % secgroup)
                raise exceptions.NoUniqueMatch(msg)
            match_found = s
    if match_found is False:
        raise exceptions.CommandError(_("Secgroup ID or name '%s' not found.")
                                      % secgroup)
    return match_found


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
@cliutils.arg('cidr', metavar='<cidr>', help=_('CIDR for address range.'))
def do_secgroup_add_rule(cs, args):
    """Add a rule to a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    rule = cs.security_group_rules.create(secgroup.id,
                                          args.ip_proto,
                                          args.from_port,
                                          args.to_port,
                                          args.cidr)
    _print_secgroup_rules([rule])


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
@cliutils.arg('cidr', metavar='<cidr>', help=_('CIDR for address range.'))
def do_secgroup_delete_rule(cs, args):
    """Delete a rule from a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    for rule in secgroup.rules:
        if (rule['ip_protocol'] and
                rule['ip_protocol'].upper() == args.ip_proto.upper() and
                rule['from_port'] == int(args.from_port) and
                rule['to_port'] == int(args.to_port) and
                rule['ip_range']['cidr'] == args.cidr):
            _print_secgroup_rules([rule])
            return cs.security_group_rules.delete(rule['id'])

    raise exceptions.CommandError(_("Rule not found"))


@cliutils.arg('name', metavar='<name>', help=_('Name of security group.'))
@cliutils.arg(
    'description', metavar='<description>',
    help=_('Description of security group.'))
def do_secgroup_create(cs, args):
    """Create a security group."""
    secgroup = cs.security_groups.create(args.name, args.description)
    _print_secgroups([secgroup])


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
@cliutils.arg('name', metavar='<name>', help=_('Name of security group.'))
@cliutils.arg(
    'description', metavar='<description>',
    help=_('Description of security group.'))
def do_secgroup_update(cs, args):
    """Update a security group."""
    sg = _get_secgroup(cs, args.secgroup)
    secgroup = cs.security_groups.update(sg, args.name, args.description)
    _print_secgroups([secgroup])


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
def do_secgroup_delete(cs, args):
    """Delete a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    cs.security_groups.delete(secgroup)
    _print_secgroups([secgroup])


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=int(strutils.bool_from_string(
        os.environ.get("ALL_TENANTS", 'false'), True)),
    help=_('Display information from all tenants (Admin only).'))
@cliutils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
def do_secgroup_list(cs, args):
    """List security groups for the current tenant."""
    search_opts = {'all_tenants': args.all_tenants}
    columns = ['Id', 'Name', 'Description']
    if args.all_tenants:
        columns.append('Tenant_ID')
    groups = cs.security_groups.list(search_opts=search_opts)
    utils.print_list(groups, columns)


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
def do_secgroup_list_rules(cs, args):
    """List rules for a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    _print_secgroup_rules(secgroup.rules)


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
@cliutils.arg(
    'source_group',
    metavar='<source-group>',
    help=_('ID or name of source group.'))
@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
def do_secgroup_add_group_rule(cs, args):
    """Add a source group rule to a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    source_group = _get_secgroup(cs, args.source_group)
    params = {}
    params['group_id'] = source_group.id

    if args.ip_proto or args.from_port or args.to_port:
        if not (args.ip_proto and args.from_port and args.to_port):
            raise exceptions.CommandError(_("ip_proto, from_port, and to_port"
                                            " must be specified together"))
        params['ip_protocol'] = args.ip_proto.upper()
        params['from_port'] = args.from_port
        params['to_port'] = args.to_port

    rule = cs.security_group_rules.create(secgroup.id, **params)
    _print_secgroup_rules([rule])


@cliutils.arg(
    'secgroup',
    metavar='<secgroup>',
    help=_('ID or name of security group.'))
@cliutils.arg(
    'source_group',
    metavar='<source-group>',
    help=_('ID or name of source group.'))
@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
def do_secgroup_delete_group_rule(cs, args):
    """Delete a source group rule from a security group."""
    secgroup = _get_secgroup(cs, args.secgroup)
    source_group = _get_secgroup(cs, args.source_group)
    params = {}
    params['group_name'] = source_group.name

    if args.ip_proto or args.from_port or args.to_port:
        if not (args.ip_proto and args.from_port and args.to_port):
            raise exceptions.CommandError(_("ip_proto, from_port, and to_port"
                                            " must be specified together"))
        params['ip_protocol'] = args.ip_proto.upper()
        params['from_port'] = int(args.from_port)
        params['to_port'] = int(args.to_port)

    for rule in secgroup.rules:
        if (rule.get('ip_protocol') and
                rule['ip_protocol'].upper() == params.get(
                    'ip_protocol').upper() and
                rule.get('from_port') == params.get('from_port') and
                rule.get('to_port') == params.get('to_port') and
                rule.get('group', {}).get('name') == params.get('group_name')):
            return cs.security_group_rules.delete(rule['id'])

    raise exceptions.CommandError(_("Rule not found"))


@cliutils.arg('name', metavar='<name>', help=_('Name of key.'))
@cliutils.arg(
    '--pub-key',
    metavar='<pub-key>',
    default=None,
    help=_('Path to a public ssh key.'))
@cliutils.arg(
    '--pub_key',
    help=argparse.SUPPRESS)
def do_keypair_add(cs, args):
    """Create a new key pair for use with servers."""
    name = args.name
    pub_key = args.pub_key

    if pub_key:
        if pub_key == '-':
            pub_key = sys.stdin.read()
        else:
            try:
                with open(os.path.expanduser(pub_key)) as f:
                    pub_key = f.read()
            except IOError as e:
                raise exceptions.CommandError(
                    _("Can't open or read '%(key)s': %(exc)s")
                    % {'key': pub_key, 'exc': e}
                )

    keypair = cs.keypairs.create(name, pub_key)

    if not pub_key:
        private_key = keypair.private_key
        print(private_key)


@cliutils.arg('name', metavar='<name>', help=_('Keypair name to delete.'))
def do_keypair_delete(cs, args):
    """Delete keypair given by its name."""
    name = _find_keypair(cs, args.name)
    cs.keypairs.delete(name)


def do_keypair_list(cs, args):
    """Print a list of keypairs for a user"""
    keypairs = cs.keypairs.list()
    columns = ['Name', 'Fingerprint']
    utils.print_list(keypairs, columns)


def _print_keypair(keypair):
    kp = keypair._info.copy()
    pk = kp.pop('public_key')
    utils.print_dict(kp)
    print(_("Public key: %s") % pk)


@cliutils.arg(
    'keypair',
    metavar='<keypair>',
    help=_("Name or ID of keypair"))
def do_keypair_show(cs, args):
    """Show details about the given keypair."""
    keypair = _find_keypair(cs, args.keypair)
    _print_keypair(keypair)


def _find_keypair(cs, keypair):
    """Get a keypair by name or ID."""
    return utils.find_resource(cs.keypairs, keypair)


@cliutils.arg(
    '--tenant',
    # nova db searches by project_id
    dest='tenant',
    metavar='<tenant>',
    nargs='?',
    help=_('Display information from single tenant (Admin only).'))
@cliutils.arg(
    '--reserved',
    dest='reserved',
    action='store_true',
    default=False,
    help=_('Include reservations count.'))
def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user"""
    limits = cs.limits.get(args.reserved, args.tenant).absolute

    class Limit(object):
        def __init__(self, name, used, max, other):
            self.name = name
            self.used = used
            self.max = max
            self.other = other

    limit_map = {
        'maxServerMeta': {'name': 'Server Meta', 'type': 'max'},
        'maxPersonality': {'name': 'Personality', 'type': 'max'},
        'maxPersonalitySize': {'name': 'Personality Size', 'type': 'max'},
        'maxImageMeta': {'name': 'ImageMeta', 'type': 'max'},
        'maxTotalKeypairs': {'name': 'Keypairs', 'type': 'max'},
        'totalCoresUsed': {'name': 'Cores', 'type': 'used'},
        'maxTotalCores': {'name': 'Cores', 'type': 'max'},
        'totalRAMUsed': {'name': 'RAM', 'type': 'used'},
        'maxTotalRAMSize': {'name': 'RAM', 'type': 'max'},
        'totalInstancesUsed': {'name': 'Instances', 'type': 'used'},
        'maxTotalInstances': {'name': 'Instances', 'type': 'max'},
        'totalFloatingIpsUsed': {'name': 'FloatingIps', 'type': 'used'},
        'maxTotalFloatingIps': {'name': 'FloatingIps', 'type': 'max'},
        'totalSecurityGroupsUsed': {'name': 'SecurityGroups', 'type': 'used'},
        'maxSecurityGroups': {'name': 'SecurityGroups', 'type': 'max'},
        'maxSecurityGroupRules': {'name': 'SecurityGroupRules', 'type': 'max'},
        'maxServerGroups': {'name': 'ServerGroups', 'type': 'max'},
        'totalServerGroupsUsed': {'name': 'ServerGroups', 'type': 'used'},
        'maxServerGroupMembers': {'name': 'ServerGroupMembers', 'type': 'max'},
    }

    max = {}
    used = {}
    other = {}
    limit_names = []
    columns = ['Name', 'Used', 'Max']
    for l in limits:
        map = limit_map.get(l.name, {'name': l.name, 'type': 'other'})
        name = map['name']
        if map['type'] == 'max':
            max[name] = l.value
        elif map['type'] == 'used':
            used[name] = l.value
        else:
            other[name] = l.value
            columns.append('Other')
        if name not in limit_names:
            limit_names.append(name)

    limit_names.sort()

    limit_list = []
    for name in limit_names:
        l = Limit(name,
                  used.get(name, "-"),
                  max.get(name, "-"),
                  other.get(name, "-"))
        limit_list.append(l)

    utils.print_list(limit_list, columns)


def do_rate_limits(cs, args):
    """Print a list of rate limits for a user"""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


@cliutils.arg(
    '--start',
    metavar='<start>',
    help=_('Usage range start date ex 2012-01-20 (default: 4 weeks ago)'),
    default=None)
@cliutils.arg(
    '--end',
    metavar='<end>',
    help=_('Usage range end date, ex 2012-01-20 (default: tomorrow)'),
    default=None)
def do_usage_list(cs, args):
    """List usage data for all tenants."""
    dateformat = "%Y-%m-%d"
    rows = ["Tenant ID", "Servers", "RAM MB-Hours", "CPU Hours",
            "Disk GB-Hours"]

    now = timeutils.utcnow()

    if args.start:
        start = datetime.datetime.strptime(args.start, dateformat)
    else:
        start = now - datetime.timedelta(weeks=4)

    if args.end:
        end = datetime.datetime.strptime(args.end, dateformat)
    else:
        end = now + datetime.timedelta(days=1)

    def simplify_usage(u):
        simplerows = [x.lower().replace(" ", "_") for x in rows]

        setattr(u, simplerows[0], u.tenant_id)
        setattr(u, simplerows[1], "%d" % len(u.server_usages))
        setattr(u, simplerows[2], "%.2f" % u.total_memory_mb_usage)
        setattr(u, simplerows[3], "%.2f" % u.total_vcpus_usage)
        setattr(u, simplerows[4], "%.2f" % u.total_local_gb_usage)

    usage_list = cs.usage.list(start, end, detailed=True)

    print(_("Usage from %(start)s to %(end)s:") %
          {'start': start.strftime(dateformat),
           'end': end.strftime(dateformat)})

    for usage in usage_list:
        simplify_usage(usage)

    utils.print_list(usage_list, rows)


@cliutils.arg(
    '--start',
    metavar='<start>',
    help=_('Usage range start date ex 2012-01-20 (default: 4 weeks ago)'),
    default=None)
@cliutils.arg(
    '--end', metavar='<end>',
    help=_('Usage range end date, ex 2012-01-20 (default: tomorrow)'),
    default=None)
@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('UUID of tenant to get usage for.'))
def do_usage(cs, args):
    """Show usage data for a single tenant."""
    dateformat = "%Y-%m-%d"
    rows = ["Servers", "RAM MB-Hours", "CPU Hours", "Disk GB-Hours"]

    now = timeutils.utcnow()

    if args.start:
        start = datetime.datetime.strptime(args.start, dateformat)
    else:
        start = now - datetime.timedelta(weeks=4)

    if args.end:
        end = datetime.datetime.strptime(args.end, dateformat)
    else:
        end = now + datetime.timedelta(days=1)

    def simplify_usage(u):
        simplerows = [x.lower().replace(" ", "_") for x in rows]

        setattr(u, simplerows[0], "%d" % len(u.server_usages))
        setattr(u, simplerows[1], "%.2f" % u.total_memory_mb_usage)
        setattr(u, simplerows[2], "%.2f" % u.total_vcpus_usage)
        setattr(u, simplerows[3], "%.2f" % u.total_local_gb_usage)

    if args.tenant:
        usage = cs.usage.get(args.tenant, start, end)
    else:
        if isinstance(cs.client, client.SessionClient):
            auth = cs.client.auth
            project_id = auth.get_auth_ref(cs.client.session).project_id
            usage = cs.usage.get(project_id, start, end)
        else:
            usage = cs.usage.get(cs.client.tenant_id, start, end)

    print(_("Usage from %(start)s to %(end)s:") %
          {'start': start.strftime(dateformat),
           'end': end.strftime(dateformat)})

    if getattr(usage, 'total_vcpus_usage', None):
        simplify_usage(usage)
        utils.print_list([usage], rows)
    else:
        print(_('None'))


@cliutils.arg(
    'pk_filename',
    metavar='<private-key-filename>',
    nargs='?',
    default='pk.pem',
    help=_('Filename for the private key [Default: pk.pem]'))
@cliutils.arg(
    'cert_filename',
    metavar='<x509-cert-filename>',
    nargs='?',
    default='cert.pem',
    help=_('Filename for the X.509 certificate [Default: cert.pem]'))
def do_x509_create_cert(cs, args):
    """Create x509 cert for a user in tenant."""

    if os.path.exists(args.pk_filename):
        raise exceptions.CommandError(_("Unable to write privatekey - %s "
                                        "exists.") % args.pk_filename)
    if os.path.exists(args.cert_filename):
        raise exceptions.CommandError(_("Unable to write x509 cert - %s "
                                        "exists.") % args.cert_filename)

    certs = cs.certs.create()

    try:
        old_umask = os.umask(0o377)
        with open(args.pk_filename, 'w') as private_key:
            private_key.write(certs.private_key)
            print(_("Wrote private key to %s") % args.pk_filename)
    finally:
        os.umask(old_umask)

    with open(args.cert_filename, 'w') as cert:
        cert.write(certs.data)
        print(_("Wrote x509 certificate to %s") % args.cert_filename)


@cliutils.arg(
    'filename',
    metavar='<filename>',
    nargs='?',
    default='cacert.pem',
    help=_('Filename to write the x509 root cert.'))
def do_x509_get_root_cert(cs, args):
    """Fetch the x509 root cert."""
    if os.path.exists(args.filename):
        raise exceptions.CommandError(_("Unable to write x509 root cert - \
                                      %s exists.") % args.filename)

    with open(args.filename, 'w') as cert:
        cacert = cs.certs.get()
        cert.write(cacert.data)
        print(_("Wrote x509 root cert to %s") % args.filename)


@cliutils.arg(
    '--hypervisor',
    metavar='<hypervisor>',
    default=None,
    help=_('type of hypervisor.'))
def do_agent_list(cs, args):
    """List all builds."""
    result = cs.agents.list(args.hypervisor)
    columns = ["Agent_id", "Hypervisor", "OS", "Architecture", "Version",
               'Md5hash', 'Url']
    utils.print_list(result, columns)


@cliutils.arg('os', metavar='<os>', help=_('type of os.'))
@cliutils.arg(
    'architecture',
    metavar='<architecture>',
    help=_('type of architecture'))
@cliutils.arg('version', metavar='<version>', help=_('version'))
@cliutils.arg('url', metavar='<url>', help=_('url'))
@cliutils.arg('md5hash', metavar='<md5hash>', help=_('md5 hash'))
@cliutils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    default='xen',
    help=_('type of hypervisor.'))
def do_agent_create(cs, args):
    """Create new agent build."""
    result = cs.agents.create(args.os, args.architecture,
                              args.version, args.url,
                              args.md5hash, args.hypervisor)
    utils.print_dict(result._info.copy())


@cliutils.arg('id', metavar='<id>', help=_('id of the agent-build'))
def do_agent_delete(cs, args):
    """Delete existing agent build."""
    cs.agents.delete(args.id)


@cliutils.arg('id', metavar='<id>', help=_('id of the agent-build'))
@cliutils.arg('version', metavar='<version>', help=_('version'))
@cliutils.arg('url', metavar='<url>', help=_('url'))
@cliutils.arg('md5hash', metavar='<md5hash>', help=_('md5hash'))
def do_agent_modify(cs, args):
    """Modify existing agent build."""
    result = cs.agents.update(args.id, args.version,
                              args.url, args.md5hash)
    utils.print_dict(result._info)


def _find_aggregate(cs, aggregate):
    """Get a aggregate by name or ID."""
    return utils.find_resource(cs.aggregates, aggregate)


def do_aggregate_list(cs, args):
    """Print a list of all aggregates."""
    aggregates = cs.aggregates.list()
    columns = ['Id', 'Name', 'Availability Zone']
    utils.print_list(aggregates, columns)


@cliutils.arg('name', metavar='<name>', help=_('Name of aggregate.'))
@cliutils.arg(
    'availability_zone',
    metavar='<availability-zone>',
    default=None,
    nargs='?',
    help=_('The availability zone of the aggregate (optional).'))
def do_aggregate_create(cs, args):
    """Create a new aggregate with the specified details."""
    aggregate = cs.aggregates.create(args.name, args.availability_zone)
    _print_aggregate_details(aggregate)


@cliutils.arg(
    'aggregate',
    metavar='<aggregate>',
    help=_('Name or ID of aggregate to delete.'))
def do_aggregate_delete(cs, args):
    """Delete the aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    cs.aggregates.delete(aggregate)
    print(_("Aggregate %s has been successfully deleted.") % aggregate.id)


@cliutils.arg(
    'aggregate',
    metavar='<aggregate>',
    help=_('Name or ID of aggregate to update.'))
@cliutils.arg('name', metavar='<name>', help=_('Name of aggregate.'))
@cliutils.arg(
    'availability_zone',
    metavar='<availability-zone>',
    nargs='?',
    default=None,
    help=_('The availability zone of the aggregate.'))
def do_aggregate_update(cs, args):
    """Update the aggregate's name and optionally availability zone."""
    aggregate = _find_aggregate(cs, args.aggregate)
    updates = {"name": args.name}
    if args.availability_zone:
        updates["availability_zone"] = args.availability_zone

    aggregate = cs.aggregates.update(aggregate.id, updates)
    print(_("Aggregate %s has been successfully updated.") % aggregate.id)
    _print_aggregate_details(aggregate)


@cliutils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate to update.'))
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    action='append',
    default=[],
    help=_('Metadata to add/update to aggregate. '
           'Specify only the key to delete a metadata item.'))
def do_aggregate_set_metadata(cs, args):
    """Update the metadata associated with the aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    metadata = _extract_metadata(args)
    currentmetadata = getattr(aggregate, 'metadata', {})
    if set(metadata.items()) & set(currentmetadata.items()):
        raise exceptions.CommandError(_("metadata already exists"))
    for key, value in metadata.items():
        if value is None and key not in currentmetadata:
            raise exceptions.CommandError(_("metadata key %s does not exist"
                                          " hence can not be deleted")
                                          % key)
    aggregate = cs.aggregates.set_metadata(aggregate.id, metadata)
    print(_("Metadata has been successfully updated for aggregate %s.") %
          aggregate.id)
    _print_aggregate_details(aggregate)


@cliutils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
@cliutils.arg(
    'host', metavar='<host>',
    help=_('The host to add to the aggregate.'))
def do_aggregate_add_host(cs, args):
    """Add the host to the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    aggregate = cs.aggregates.add_host(aggregate.id, args.host)
    print(_("Host %(host)s has been successfully added for aggregate "
            "%(aggregate_id)s ") % {'host': args.host,
                                    'aggregate_id': aggregate.id})
    _print_aggregate_details(aggregate)


@cliutils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
@cliutils.arg(
    'host', metavar='<host>',
    help=_('The host to remove from the aggregate.'))
def do_aggregate_remove_host(cs, args):
    """Remove the specified host from the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    aggregate = cs.aggregates.remove_host(aggregate.id, args.host)
    print(_("Host %(host)s has been successfully removed from aggregate "
            "%(aggregate_id)s ") % {'host': args.host,
                                    'aggregate_id': aggregate.id})
    _print_aggregate_details(aggregate)


@cliutils.arg(
    'aggregate', metavar='<aggregate>',
    help=_('Name or ID of aggregate.'))
def do_aggregate_details(cs, args):
    """Show details of the specified aggregate."""
    aggregate = _find_aggregate(cs, args.aggregate)
    _print_aggregate_details(aggregate)


def _print_aggregate_details(aggregate):
    columns = ['Id', 'Name', 'Availability Zone', 'Hosts', 'Metadata']

    def parser_metadata(fields):
        return utils.pretty_choice_dict(getattr(fields, 'metadata', {}) or {})

    def parser_hosts(fields):
        return cliutils.pretty_choice_list(getattr(fields, 'hosts', []))

    formatters = {
        'Metadata': parser_metadata,
        'Hosts': parser_hosts,
    }
    utils.print_list([aggregate], columns, formatters=formatters)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'host', metavar='<host>', default=None, nargs='?',
    help=_('destination host name.'))
@cliutils.arg(
    '--block-migrate',
    action='store_true',
    dest='block_migrate',
    default=False,
    help=_('True in case of block_migration. (Default=False:live_migration)'))
@cliutils.arg(
    '--block_migrate',
    action='store_true',
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--disk-over-commit',
    action='store_true',
    dest='disk_over_commit',
    default=False,
    help=_('Allow overcommit.(Default=False)'))
@cliutils.arg(
    '--disk_over_commit',
    action='store_true',
    help=argparse.SUPPRESS)
def do_live_migration(cs, args):
    """Migrate running server to a new machine."""
    _find_server(cs, args.server).live_migrate(args.host,
                                               args.block_migrate,
                                               args.disk_over_commit)


@cliutils.arg(
    'server', metavar='<server>', nargs='+',
    help=_('Name or ID of server(s).'))
@cliutils.arg(
    '--active', action='store_const', dest='state',
    default='error', const='active',
    help=_('Request the server be reset to "active" state instead '
           'of "error" state (the default).'))
def do_reset_state(cs, args):
    """Reset the state of a server."""
    failure_flag = False

    for server in args.server:
        try:
            _find_server(cs, server).reset_state(args.state)
        except Exception as e:
            failure_flag = True
            msg = "Reset state for server %s failed: %s" % (server, e)
            print(msg)

    if failure_flag:
        msg = "Unable to reset the state for the specified server(s)."
        raise exceptions.CommandError(msg)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_reset_network(cs, args):
    """Reset network of a server."""
    _find_server(cs, args.server).reset_network()


@cliutils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help=_('Name of host.'))
@cliutils.arg(
    '--binary',
    metavar='<binary>',
    default=None,
    help=_('Service binary.'))
def do_service_list(cs, args):
    """Show a list of all running services. Filter by host & binary."""
    result = cs.services.list(host=args.host, binary=args.binary)
    columns = ["Binary", "Host", "Zone", "Status", "State", "Updated_at"]
    # NOTE(sulo): we check if the response has disabled_reason
    # so as not to add the column when the extended ext is not enabled.
    if result and hasattr(result[0], 'disabled_reason'):
        columns.append("Disabled Reason")

    # NOTE(gtt): After https://review.openstack.org/#/c/39998/ nova will
    # show id in response.
    if result and hasattr(result[0], 'id'):
        columns.insert(0, "Id")

    utils.print_list(result, columns)


@cliutils.arg('host', metavar='<hostname>', help=_('Name of host.'))
@cliutils.arg('binary', metavar='<binary>', help=_('Service binary.'))
def do_service_enable(cs, args):
    """Enable the service."""
    result = cs.services.enable(args.host, args.binary)
    utils.print_list([result], ['Host', 'Binary', 'Status'])


@cliutils.arg('host', metavar='<hostname>', help=_('Name of host.'))
@cliutils.arg('binary', metavar='<binary>', help=_('Service binary.'))
@cliutils.arg(
    '--reason',
    metavar='<reason>',
    help=_('Reason for disabling service.'))
def do_service_disable(cs, args):
    """Disable the service."""
    if args.reason:
        result = cs.services.disable_log_reason(args.host, args.binary,
                                                args.reason)
        utils.print_list([result], ['Host', 'Binary', 'Status',
                         'Disabled Reason'])
    else:
        result = cs.services.disable(args.host, args.binary)
        utils.print_list([result], ['Host', 'Binary', 'Status'])


@cliutils.arg('id', metavar='<id>', help=_('Id of service.'))
def do_service_delete(cs, args):
    """Delete the service."""
    cs.services.delete(args.id)


@cliutils.arg('fixed_ip', metavar='<fixed_ip>', help=_('Fixed IP Address.'))
def do_fixed_ip_get(cs, args):
    """Retrieve info on a fixed IP."""
    result = cs.fixed_ips.get(args.fixed_ip)
    utils.print_list([result], ['address', 'cidr', 'hostname', 'host'])


@cliutils.arg('fixed_ip', metavar='<fixed_ip>', help=_('Fixed IP Address.'))
def do_fixed_ip_reserve(cs, args):
    """Reserve a fixed IP."""
    cs.fixed_ips.reserve(args.fixed_ip)


@cliutils.arg('fixed_ip', metavar='<fixed_ip>', help=_('Fixed IP Address.'))
def do_fixed_ip_unreserve(cs, args):
    """Unreserve a fixed IP."""
    cs.fixed_ips.unreserve(args.fixed_ip)


@cliutils.arg('host', metavar='<hostname>', help=_('Name of host.'))
def do_host_describe(cs, args):
    """Describe a specific host."""
    result = cs.hosts.get(args.host)
    columns = ["HOST", "PROJECT", "cpu", "memory_mb", "disk_gb"]
    utils.print_list(result, columns)


@cliutils.arg(
    '--zone',
    metavar='<zone>',
    default=None,
    help=_('Filters the list, returning only those hosts in the availability '
           'zone <zone>.'))
def do_host_list(cs, args):
    """List all hosts by service."""
    columns = ["host_name", "service", "zone"]
    result = cs.hosts.list(args.zone)
    utils.print_list(result, columns)


@cliutils.arg('host', metavar='<hostname>', help='Name of host.')
@cliutils.arg(
    '--status', metavar='<enable|disable>', default=None, dest='status',
    help=_('Either enable or disable a host.'))
@cliutils.arg(
    '--maintenance',
    metavar='<enable|disable>',
    default=None,
    dest='maintenance',
    help=_('Either put or resume host to/from maintenance.'))
def do_host_update(cs, args):
    """Update host settings."""
    updates = {}
    columns = ["HOST"]
    if args.status:
        updates['status'] = args.status
        columns.append("status")
    if args.maintenance:
        updates['maintenance_mode'] = args.maintenance
        columns.append("maintenance_mode")
    result = cs.hosts.update(args.host, updates)
    utils.print_list([result], columns)


@cliutils.arg('host', metavar='<hostname>', help='Name of host.')
@cliutils.arg(
    '--action', metavar='<action>', dest='action',
    choices=['startup', 'shutdown', 'reboot'],
    help=_('A power action: startup, reboot, or shutdown.'))
def do_host_action(cs, args):
    """Perform a power action on a host."""
    result = cs.hosts.host_action(args.host, args.action)
    utils.print_list([result], ['HOST', 'power_action'])


def _find_hypervisor(cs, hypervisor):
    """Get a hypervisor by name or ID."""
    return utils.find_resource(cs.hypervisors, hypervisor)


@cliutils.arg(
    '--matching',
    metavar='<hostname>',
    default=None,
    help=_('List hypervisors matching the given <hostname>.'))
def do_hypervisor_list(cs, args):
    """List hypervisors."""
    columns = ['ID', 'Hypervisor hostname', 'State', 'Status']
    if args.matching:
        utils.print_list(cs.hypervisors.search(args.matching), columns)
    else:
        # Since we're not outputting detail data, choose
        # detailed=False for server-side efficiency
        utils.print_list(cs.hypervisors.list(False), columns)


@cliutils.arg(
    'hostname',
    metavar='<hostname>',
    help=_('The hypervisor hostname (or pattern) to search for.'))
def do_hypervisor_servers(cs, args):
    """List servers belonging to specific hypervisors."""
    hypers = cs.hypervisors.search(args.hostname, servers=True)

    class InstanceOnHyper(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    # Massage the result into a list to be displayed
    instances = []
    for hyper in hypers:
        hyper_host = hyper.hypervisor_hostname
        hyper_id = hyper.id
        if hasattr(hyper, 'servers'):
            instances.extend([InstanceOnHyper(id=serv['uuid'],
                                              name=serv['name'],
                                              hypervisor_hostname=hyper_host,
                                              hypervisor_id=hyper_id)
                              for serv in hyper.servers])

    # Output the data
    utils.print_list(instances, ['ID', 'Name', 'Hypervisor ID',
                                 'Hypervisor Hostname'])


@cliutils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    help=_('Name or ID of the hypervisor to show the details of.'))
def do_hypervisor_show(cs, args):
    """Display the details of the specified hypervisor."""
    hyper = _find_hypervisor(cs, args.hypervisor)
    utils.print_dict(utils.flatten_dict(hyper._info))


@cliutils.arg(
    'hypervisor',
    metavar='<hypervisor>',
    help=_('Name or ID of the hypervisor to show the uptime of.'))
def do_hypervisor_uptime(cs, args):
    """Display the uptime of the specified hypervisor."""
    hyper = _find_hypervisor(cs, args.hypervisor)
    hyper = cs.hypervisors.uptime(hyper)

    # Output the uptime information
    utils.print_dict(hyper._info.copy())


def do_hypervisor_stats(cs, args):
    """Get hypervisor statistics over all compute nodes."""
    stats = cs.hypervisor_stats.statistics()
    utils.print_dict(stats._info.copy())


def ensure_service_catalog_present(cs):
    if not hasattr(cs.client, 'service_catalog'):
        # Turn off token caching and re-auth
        cs.client.unauthenticate()
        cs.client.use_token_cache(False)
        cs.client.authenticate()


def do_endpoints(cs, _args):
    """Discover endpoints that get returned from the authenticate services."""
    if isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        sc = auth.get_access(cs.client.session).service_catalog
        for service in sc.get_data():
            _print_endpoints(service, cs.client.region_name)
    else:
        ensure_service_catalog_present(cs)

        catalog = cs.client.service_catalog.catalog
        region = cs.client.region_name
        for service in catalog['access']['serviceCatalog']:
            _print_endpoints(service, region)


def _print_endpoints(service, region):
    name, endpoints = service["name"], service["endpoints"]

    try:
        endpoint = _get_first_endpoint(endpoints, region)
        utils.print_dict(endpoint, name)
    except LookupError:
        print(_("WARNING: %(service)s has no endpoint in %(region)s! "
                "Available endpoints for this service:") %
              {'service': name, 'region': region})
        for other_endpoint in endpoints:
            utils.print_dict(other_endpoint, name)


def _get_first_endpoint(endpoints, region):
    """Find the first suitable endpoint in endpoints.

    If there is only one endpoint, return it. If there is more than
    one endpoint, return the first one with the given region. If there
    are no endpoints, or there is more than one endpoint but none of
    them match the given region, raise KeyError.

    """
    if len(endpoints) == 1:
        return endpoints[0]
    else:
        for candidate_endpoint in endpoints:
            if candidate_endpoint["region"] == region:
                return candidate_endpoint

    raise LookupError("No suitable endpoint found")


@cliutils.arg(
    '--wrap', dest='wrap', metavar='<integer>', default=64,
    help=_('wrap PKI tokens to a specified length, or 0 to disable'))
def do_credentials(cs, _args):
    """Show user credentials returned from auth."""
    if isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        sc = auth.get_access(cs.client.session).service_catalog
        utils.print_dict(sc.catalog['user'], 'User Credentials',
                         wrap=int(_args.wrap))
        utils.print_dict(sc.get_token(), 'Token', wrap=int(_args.wrap))
    else:
        ensure_service_catalog_present(cs)
        catalog = cs.client.service_catalog.catalog
        utils.print_dict(catalog['access']['user'], "User Credentials",
                         wrap=int(_args.wrap))
        utils.print_dict(catalog['access']['token'], "Token",
                         wrap=int(_args.wrap))


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--port',
    dest='port',
    action='store',
    type=int,
    default=22,
    help=_('Optional flag to indicate which port to use for ssh. '
           '(Default=22)'))
@cliutils.arg(
    '--private',
    dest='private',
    action='store_true',
    default=False,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--address-type',
    dest='address_type',
    action='store',
    type=str,
    default='floating',
    help=_('Optional flag to indicate which IP type to use. Possible values  '
           'includes fixed and floating (the Default).'))
@cliutils.arg(
    '--network', metavar='<network>',
    help=_('Network to use for the ssh.'), default=None)
@cliutils.arg(
    '--ipv6',
    dest='ipv6',
    action='store_true',
    default=False,
    help=_('Optional flag to indicate whether to use an IPv6 address '
           'attached to a server. (Defaults to IPv4 address)'))
@cliutils.arg(
    '--login', metavar='<login>', help=_('Login to use.'),
    default="root")
@cliutils.arg(
    '-i', '--identity',
    dest='identity',
    help=_('Private key file, same as the -i option to the ssh command.'),
    default='')
@cliutils.arg(
    '--extra-opts',
    dest='extra',
    help=_('Extra options to pass to ssh. see: man ssh'),
    default='')
def do_ssh(cs, args):
    """SSH into a server."""
    if '@' in args.server:
        user, server = args.server.split('@', 1)
        args.login = user
        args.server = server

    addresses = _find_server(cs, args.server).addresses
    address_type = "fixed" if args.private else args.address_type
    version = 6 if args.ipv6 else 4
    pretty_version = 'IPv%d' % version

    # Select the network to use.
    if args.network:
        network_addresses = addresses.get(args.network)
        if not network_addresses:
            msg = _("Server '%(server)s' is not attached to network "
                    "'%(network)s'")
            raise exceptions.ResourceNotFound(
                msg % {'server': args.server, 'network': args.network})
    else:
        if len(addresses) > 1:
            msg = _("Server '%(server)s' is attached to more than one network."
                    " Please pick the network to use.")
            raise exceptions.CommandError(msg % {'server': args.server})
        elif not addresses:
            msg = _("Server '%(server)s' is not attached to any network.")
            raise exceptions.CommandError(msg % {'server': args.server})
        else:
            network_addresses = list(six.itervalues(addresses))[0]

    # Select the address in the selected network.
    # If the extension is not present, we assume the address to be floating.
    match = lambda addr: all((
        addr.get('version') == version,
        addr.get('OS-EXT-IPS:type', 'floating') == address_type))
    matching_addresses = [address.get('addr')
                          for address in network_addresses if match(address)]
    if not any(matching_addresses):
        msg = _("No address that would match network '%(network)s'"
                " and type '%(address_type)s' of version %(pretty_version)s "
                "has been found for server '%(server)s'.")
        raise exceptions.ResourceNotFound(msg % {
            'network': args.network, 'address_type': address_type,
            'pretty_version': pretty_version, 'server': args.server})
    elif len(matching_addresses) > 1:
        msg = _("More than one %(pretty_version)s %(address_type)s address"
                "found.")
        raise exceptions.CommandError(msg % {'pretty_version': pretty_version,
                                             'address_type': address_type})
    else:
        ip_address = matching_addresses[0]

    identity = '-i %s' % args.identity if len(args.identity) else ''

    cmd = "ssh -%d -p%d %s %s@%s %s" % (version, args.port, identity,
                                        args.login, ip_address, args.extra)
    logger.debug("Executing cmd '%s'", cmd)
    os.system(cmd)


_quota_resources = ['instances', 'cores', 'ram',
                    'floating_ips', 'fixed_ips', 'metadata_items',
                    'injected_files', 'injected_file_content_bytes',
                    'injected_file_path_bytes', 'key_pairs',
                    'security_groups', 'security_group_rules',
                    'server_groups', 'server_group_members']


def _quota_show(quotas):
    class FormattedQuota(object):
        def __init__(self, key, value):
            setattr(self, 'quota', key)
            setattr(self, 'limit', value)

    quota_list = []
    for resource in _quota_resources:
        try:
            quota = FormattedQuota(resource, getattr(quotas, resource))
            quota_list.append(quota)
        except AttributeError:
            pass
    columns = ['Quota', 'Limit']
    utils.print_list(quota_list, columns)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        # default value of force is None to make sure this client
        # will be compatibile with old nova server
        force_update = getattr(args, 'force', None)
        user_id = getattr(args, 'user', None)
        if isinstance(manager, quotas.QuotaSetManager):
            manager.update(identifier, force=force_update, user_id=user_id,
                           **updates)
        else:
            manager.update(identifier, **updates)


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('ID of tenant to list the quotas for.'))
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to list the quotas for.'))
def do_quota_show(cs, args):
    """List the quotas for a tenant/user."""

    if args.tenant:
        project_id = args.tenant
    elif isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        project_id = auth.get_auth_ref(cs.client.session).project_id
    else:
        project_id = cs.client.tenant_id

    _quota_show(cs.quotas.get(project_id, user_id=args.user))


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help=_('ID of tenant to list the default quotas for.'))
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    if args.tenant:
        project_id = args.tenant
    elif isinstance(cs.client, client.SessionClient):
        auth = cs.client.auth
        project_id = auth.get_auth_ref(cs.client.session).project_id
    else:
        project_id = cs.client.tenant_id

    _quota_show(cs.quotas.defaults(project_id))


@cliutils.arg(
    'tenant',
    metavar='<tenant-id>',
    help=_('ID of tenant to set the quotas for.'))
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help=_('ID of user to set the quotas for.'))
@cliutils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@cliutils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@cliutils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@cliutils.arg(
    '--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    help=_('New value for the "floating-ips" quota.'))
@cliutils.arg(
    '--floating_ips',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--fixed-ips',
    metavar='<fixed-ips>',
    type=int,
    default=None,
    help=_('New value for the "fixed-ips" quota.'))
@cliutils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@cliutils.arg(
    '--metadata_items',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'))
@cliutils.arg(
    '--injected_files',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'))
@cliutils.arg(
    '--injected_file_content_bytes',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'))
@cliutils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@cliutils.arg(
    '--security-groups',
    metavar='<security-groups>',
    type=int,
    default=None,
    help=_('New value for the "security-groups" quota.'))
@cliutils.arg(
    '--security-group-rules',
    metavar='<security-group-rules>',
    type=int,
    default=None,
    help=_('New value for the "security-group-rules" quota.'))
@cliutils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@cliutils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
@cliutils.arg(
    '--force',
    dest='force',
    action="store_true",
    default=None,
    help=_('Whether force update the quota even if the already used and '
           'reserved exceeds the new quota'))
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user."""

    _quota_update(cs.quotas, args.tenant, args)


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    required=True,
    help=_('ID of tenant to delete quota for.'))
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    help=_('ID of user to delete quota for.'))
def do_quota_delete(cs, args):
    """Delete quota for a tenant/user so their quota will Revert
       back to default.
    """

    cs.quotas.delete(args.tenant, user_id=args.user)


@cliutils.arg(
    'class_name',
    metavar='<class>',
    help=_('Name of quota class to list the quotas for.'))
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@cliutils.arg(
    'class_name',
    metavar='<class>',
    help=_('Name of quota class to set the quotas for.'))
@cliutils.arg(
    '--instances',
    metavar='<instances>',
    type=int, default=None,
    help=_('New value for the "instances" quota.'))
@cliutils.arg(
    '--cores',
    metavar='<cores>',
    type=int, default=None,
    help=_('New value for the "cores" quota.'))
@cliutils.arg(
    '--ram',
    metavar='<ram>',
    type=int, default=None,
    help=_('New value for the "ram" quota.'))
@cliutils.arg(
    '--floating-ips',
    metavar='<floating-ips>',
    type=int,
    default=None,
    help=_('New value for the "floating-ips" quota.'))
@cliutils.arg(
    '--floating_ips',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--fixed-ips',
    metavar='<fixed-ips>',
    type=int,
    default=None,
    help=_('New value for the "fixed-ips" quota.'))
@cliutils.arg(
    '--metadata-items',
    metavar='<metadata-items>',
    type=int,
    default=None,
    help=_('New value for the "metadata-items" quota.'))
@cliutils.arg(
    '--metadata_items',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-files',
    metavar='<injected-files>',
    type=int,
    default=None,
    help=_('New value for the "injected-files" quota.'))
@cliutils.arg(
    '--injected_files',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-file-content-bytes',
    metavar='<injected-file-content-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-content-bytes" quota.'))
@cliutils.arg(
    '--injected_file_content_bytes',
    type=int,
    help=argparse.SUPPRESS)
@cliutils.arg(
    '--injected-file-path-bytes',
    metavar='<injected-file-path-bytes>',
    type=int,
    default=None,
    help=_('New value for the "injected-file-path-bytes" quota.'))
@cliutils.arg(
    '--key-pairs',
    metavar='<key-pairs>',
    type=int,
    default=None,
    help=_('New value for the "key-pairs" quota.'))
@cliutils.arg(
    '--security-groups',
    metavar='<security-groups>',
    type=int,
    default=None,
    help=_('New value for the "security-groups" quota.'))
@cliutils.arg(
    '--security-group-rules',
    metavar='<security-group-rules>',
    type=int,
    default=None,
    help=_('New value for the "security-group-rules" quota.'))
@cliutils.arg(
    '--server-groups',
    metavar='<server-groups>',
    type=int,
    default=None,
    help=_('New value for the "server-groups" quota.'))
@cliutils.arg(
    '--server-group-members',
    metavar='<server-group-members>',
    type=int,
    default=None,
    help=_('New value for the "server-group-members" quota.'))
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    'host', metavar='<host>', nargs='?',
    help=_("Name or ID of the target host.  "
           "If no host is specified, the scheduler will choose one."))
@cliutils.arg(
    '--password',
    dest='password',
    metavar='<password>',
    help=_("Set the provided admin password on the evacuated server. Not"
            " applicable with on-shared-storage flag"))
@cliutils.arg(
    '--on-shared-storage',
    dest='on_shared_storage',
    action="store_true",
    default=False,
    help=_('Specifies whether server files are located on shared storage'))
def do_evacuate(cs, args):
    """Evacuate server from failed host."""

    server = _find_server(cs, args.server)

    res = server.evacuate(args.host, args.on_shared_storage, args.password)[1]
    if type(res) is dict:
        utils.print_dict(res)


def _print_interfaces(interfaces):
    columns = ['Port State', 'Port ID', 'Net ID', 'IP addresses',
               'MAC Addr']

    class FormattedInterface(object):
        def __init__(self, interface):
            for col in columns:
                key = col.lower().replace(" ", "_")
                if hasattr(interface, key):
                    setattr(self, key, getattr(interface, key))
            self.ip_addresses = ",".join([fip['ip_address']
                                          for fip in interface.fixed_ips])
    utils.print_list([FormattedInterface(i) for i in interfaces], columns)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
def do_interface_list(cs, args):
    """List interfaces attached to a server."""
    server = _find_server(cs, args.server)

    res = server.interface_list()
    if type(res) is list:
        _print_interfaces(res)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg(
    '--port-id',
    metavar='<port_id>',
    help=_('Port ID.'),
    dest="port_id")
@cliutils.arg(
    '--net-id',
    metavar='<net_id>',
    help=_('Network ID'),
    default=None, dest="net_id")
@cliutils.arg(
    '--fixed-ip',
    metavar='<fixed_ip>',
    help=_('Requested fixed IP.'),
    default=None, dest="fixed_ip")
def do_interface_attach(cs, args):
    """Attach a network interface to a server."""
    server = _find_server(cs, args.server)

    res = server.interface_attach(args.port_id, args.net_id, args.fixed_ip)
    if type(res) is dict:
        utils.print_dict(res)


@cliutils.arg('server', metavar='<server>', help=_('Name or ID of server.'))
@cliutils.arg('port_id', metavar='<port_id>', help=_('Port ID.'))
def do_interface_detach(cs, args):
    """Detach a network interface from a server."""
    server = _find_server(cs, args.server)

    res = server.interface_detach(args.port_id)
    if type(res) is dict:
        utils.print_dict(res)


def _treeizeAvailabilityZone(zone):
    """Build a tree view for availability zones."""
    AvailabilityZone = availability_zones.AvailabilityZone

    az = AvailabilityZone(zone.manager,
                          copy.deepcopy(zone._info), zone._loaded)
    result = []

    # Zone tree view item
    az.zoneName = zone.zoneName
    az.zoneState = ('available'
                    if zone.zoneState['available'] else 'not available')
    az._info['zoneName'] = az.zoneName
    az._info['zoneState'] = az.zoneState
    result.append(az)

    if zone.hosts is not None:
        zone_hosts = sorted(zone.hosts.items(), key=lambda x: x[0])
        for (host, services) in zone_hosts:
            # Host tree view item
            az = AvailabilityZone(zone.manager,
                                  copy.deepcopy(zone._info), zone._loaded)
            az.zoneName = '|- %s' % host
            az.zoneState = ''
            az._info['zoneName'] = az.zoneName
            az._info['zoneState'] = az.zoneState
            result.append(az)

            for (svc, state) in services.items():
                # Service tree view item
                az = AvailabilityZone(zone.manager,
                                      copy.deepcopy(zone._info), zone._loaded)
                az.zoneName = '| |- %s' % svc
                az.zoneState = '%s %s %s' % (
                               'enabled' if state['active'] else 'disabled',
                               ':-)' if state['available'] else 'XXX',
                               state['updated_at'])
                az._info['zoneName'] = az.zoneName
                az._info['zoneState'] = az.zoneState
                result.append(az)
    return result


@cliutils.service_type('compute')
def do_availability_zone_list(cs, _args):
    """List all the availability zones."""
    try:
        availability_zones = cs.availability_zones.list()
    except exceptions.Forbidden as e:  # policy doesn't allow probably
        try:
            availability_zones = cs.availability_zones.list(detailed=False)
        except Exception:
            raise e

    result = []
    for zone in availability_zones:
        result += _treeizeAvailabilityZone(zone)
    _translate_availability_zone_keys(result)
    utils.print_list(result, ['Name', 'Status'],
                     sortby_index=None)


def _print_server_group_details(server_group):
    columns = ['Id', 'Name', 'Policies', 'Members', 'Metadata']
    utils.print_list(server_group, columns)


def do_server_group_list(cs, args):
    """Print a list of all server groups."""
    server_groups = cs.server_groups.list()
    _print_server_group_details(server_groups)


def do_secgroup_list_default_rules(cs, args):
    """List rules for the default security group."""
    _print_secgroup_rules(cs.security_group_default_rules.list(),
                          show_source_group=False)


@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
@cliutils.arg('cidr', metavar='<cidr>', help=_('CIDR for address range.'))
def do_secgroup_add_default_rule(cs, args):
    """Add a rule to the default security group."""
    rule = cs.security_group_default_rules.create(args.ip_proto,
                                                  args.from_port,
                                                  args.to_port,
                                                  args.cidr)
    _print_secgroup_rules([rule], show_source_group=False)


@cliutils.arg(
    'ip_proto',
    metavar='<ip-proto>',
    help=_('IP protocol (icmp, tcp, udp).'))
@cliutils.arg(
    'from_port',
    metavar='<from-port>',
    help=_('Port at start of range.'))
@cliutils.arg(
    'to_port',
    metavar='<to-port>',
    help=_('Port at end of range.'))
@cliutils.arg('cidr', metavar='<cidr>', help=_('CIDR for address range.'))
def do_secgroup_delete_default_rule(cs, args):
    """Delete a rule from the default security group."""
    for rule in cs.security_group_default_rules.list():
        if (rule.ip_protocol and
                rule.ip_protocol.upper() == args.ip_proto.upper() and
                rule.from_port == int(args.from_port) and
                rule.to_port == int(args.to_port) and
                rule.ip_range['cidr'] == args.cidr):
            _print_secgroup_rules([rule], show_source_group=False)
            return cs.security_group_default_rules.delete(rule.id)

    raise exceptions.CommandError(_("Rule not found"))


@cliutils.arg('name', metavar='<name>', help='Server group name.')
# NOTE(wingwj): The '--policy' way is still reserved here for preserving
# the backwards compatibility of CLI, even if a user won't get this usage
# in '--help' description. It will be deprecated after an suitable deprecation
# period(probably 2 coordinated releases or so).
#
# Moreover, we imagine that a given user will use only positional parameters or
# only the "--policy" option. So we don't need to properly handle
# the possibility that they might mix them here. That usage is unsupported.
# The related discussion can be found in
# https://review.openstack.org/#/c/96382/2/.
@cliutils.arg(
    'policy',
    metavar='<policy>',
    default=argparse.SUPPRESS,
    nargs='*',
    help='Policies for the server groups ("affinity" or "anti-affinity")')
@cliutils.arg(
    '--policy',
    default=[],
    action='append',
    help=argparse.SUPPRESS)
def do_server_group_create(cs, args):
    """Create a new server group with the specified details."""
    if not args.policy:
        raise exceptions.CommandError(_("at least one policy must be "
                                        "specified"))
    kwargs = {'name': args.name,
              'policies': args.policy}
    server_group = cs.server_groups.create(**kwargs)
    _print_server_group_details([server_group])


@cliutils.arg(
    'id',
    metavar='<id>',
    nargs='+',
    help="Unique ID(s) of the server group to delete")
def do_server_group_delete(cs, args):
    """Delete specific server group(s)."""
    failure_count = 0

    for sg in args.id:
        try:
            cs.server_groups.delete(sg)
            print(_("Server group %s has been successfully deleted.") % sg)
        except Exception as e:
            failure_count += 1
            print(_("Delete for server group %(sg)s failed: %(e)s") %
                  {'sg': sg, 'e': e})
    if failure_count == len(args.id):
        raise exceptions.CommandError(_("Unable to delete any of the "
                                        "specified server groups."))


@cliutils.arg(
    'id',
    metavar='<id>',
    help="Unique ID of the server group to get")
def do_server_group_get(cs, args):
    """Get a specific server group."""
    server_group = cs.server_groups.get(args.id)
    _print_server_group_details([server_group])


def do_version_list(cs, args):
    """List all API versions."""
    result = cs.versions.list()
    columns = ["Id", "Status", "Updated"]
    utils.print_list(result, columns)
