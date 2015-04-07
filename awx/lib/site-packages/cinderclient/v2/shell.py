# Copyright (c) 2013-2014 OpenStack Foundation
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import argparse
import copy
import os
import sys
import time

import six

from cinderclient import exceptions
from cinderclient import utils
from cinderclient.openstack.common import strutils
from cinderclient.v2 import availability_zones


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Blocks while an action occurs. Periodically shows progress."""
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _find_volume_snapshot(cs, snapshot):
    """Gets a volume snapshot by name or ID."""
    return utils.find_resource(cs.volume_snapshots, snapshot)


def _find_backup(cs, backup):
    """Gets a backup by name or ID."""
    return utils.find_resource(cs.backups, backup)


def _find_consistencygroup(cs, consistencygroup):
    """Gets a consistencygroup by name or ID."""
    return utils.find_resource(cs.consistencygroups, consistencygroup)


def _find_cgsnapshot(cs, cgsnapshot):
    """Gets a cgsnapshot by name or ID."""
    return utils.find_resource(cs.cgsnapshots, cgsnapshot)


def _find_transfer(cs, transfer):
    """Gets a transfer by name or ID."""
    return utils.find_resource(cs.transfers, transfer)


def _find_qos_specs(cs, qos_specs):
    """Gets a qos specs by ID."""
    return utils.find_resource(cs.qos_specs, qos_specs)


def _print_volume_snapshot(snapshot):
    utils.print_dict(snapshot._info)


def _print_volume_image(image):
    utils.print_dict(image[1]['os-volume_upload_image'])


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _translate_volume_keys(collection):
    convert = [('volumeType', 'volume_type'),
               ('os-vol-tenant-attr:tenant_id', 'tenant_id')]
    _translate_keys(collection, convert)


def _translate_volume_snapshot_keys(collection):
    convert = [('volumeId', 'volume_id')]
    _translate_keys(collection, convert)


def _translate_availability_zone_keys(collection):
    convert = [('zoneName', 'name'), ('zoneState', 'status')]
    _translate_keys(collection, convert)


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata:
        # unset doesn't require a val, so we have the if/else
        if '=' in metadatum:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata


@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--all_tenants',
           nargs='?',
           type=int,
           const=1,
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Filters results by a name. OPTIONAL: Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help='Filters results by a status. OPTIONAL: Default=None.')
@utils.arg('--metadata',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Filters results by a metadata key and value pair. '
           'OPTIONAL: Default=None.',
           default=None)
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning volumes that appear later in the volume '
           'list than that represented by this volume id. '
           'OPTIONAL: Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of volumes to return. OPTIONAL: Default=None.')
@utils.arg('--sort_key',
           metavar='<sort_key>',
           default=None,
           help='Key to be sorted, should be (`id`, `status`, `size`, '
           '`availability_zone`, `name`, `bootable`, `created_at`). '
           'OPTIONAL: Default=None.')
@utils.arg('--sort_dir',
           metavar='<sort_dir>',
           default=None,
           help='Sort direction, should be `desc` or `asc`. '
           'OPTIONAL: Default=None.')
@utils.service_type('volumev2')
def do_list(cs, args):
    """Lists all volumes."""
    # NOTE(thingee): Backwards-compatibility with v1 args
    if args.display_name is not None:
        args.name = args.display_name

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'metadata': _extract_metadata(args) if args.metadata else None,
    }
    volumes = cs.volumes.list(search_opts=search_opts, marker=args.marker,
                              limit=args.limit, sort_key=args.sort_key,
                              sort_dir=args.sort_dir)
    _translate_volume_keys(volumes)

    # Create a list of servers to which the volume is attached
    for vol in volumes:
        servers = [s.get('server_id') for s in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))

    if all_tenants:
        key_list = ['ID', 'Tenant ID', 'Status', 'Name',
                    'Size', 'Volume Type', 'Bootable', 'Attached to']
    else:
        key_list = ['ID', 'Status', 'Name',
                    'Size', 'Volume Type', 'Bootable', 'Attached to']
    utils.print_list(volumes, key_list)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume.')
@utils.service_type('volumev2')
def do_show(cs, args):
    """Shows volume details."""
    info = dict()
    volume = utils.find_volume(cs, args.volume)
    info.update(volume._info)

    info.pop('links', None)
    utils.print_dict(info)


class CheckSizeArgForCreate(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        if (values or args.snapshot_id or args.source_volid
           or args.source_replica) is None:
            parser.error('Size is a required parameter if snapshot '
                         'or source volume is not specified.')
        setattr(args, self.dest, values)


@utils.arg('size',
           metavar='<size>',
           nargs='?',
           type=int,
           action=CheckSizeArgForCreate,
           help='Size of volume, in GBs. (Required unless '
                'snapshot-id/source-volid is specified).')
@utils.arg('--consisgroup-id',
           metavar='<consistencygroup-id>',
           default=None,
           help='ID of a consistency group where the new volume belongs to. '
                'Default=None.')
@utils.arg('--snapshot-id',
           metavar='<snapshot-id>',
           default=None,
           help='Creates volume from snapshot ID. Default=None.')
@utils.arg('--snapshot_id',
           help=argparse.SUPPRESS)
@utils.arg('--source-volid',
           metavar='<source-volid>',
           default=None,
           help='Creates volume from volume ID. Default=None.')
@utils.arg('--source_volid',
           help=argparse.SUPPRESS)
@utils.arg('--source-replica',
           metavar='<source-replica>',
           default=None,
           help='Creates volume from replicated volume ID. Default=None.')
@utils.arg('--image-id',
           metavar='<image-id>',
           default=None,
           help='Creates volume from image ID. Default=None.')
@utils.arg('--image_id',
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Volume name. Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--display_name',
           help=argparse.SUPPRESS)
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Volume description. Default=None.')
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--display_description',
           help=argparse.SUPPRESS)
@utils.arg('--volume-type',
           metavar='<volume-type>',
           default=None,
           help='Volume type. Default=None.')
@utils.arg('--volume_type',
           help=argparse.SUPPRESS)
@utils.arg('--availability-zone',
           metavar='<availability-zone>',
           default=None,
           help='Availability zone for volume. Default=None.')
@utils.arg('--availability_zone',
           help=argparse.SUPPRESS)
@utils.arg('--metadata',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Metadata key and value pairs. Default=None.',
           default=None)
@utils.arg('--hint',
           metavar='<key=value>',
           dest='scheduler_hints',
           action='append',
           default=[],
           help='Scheduler hint, like in nova.')
@utils.service_type('volumev2')
def do_create(cs, args):
    """Creates a volume."""
    # NOTE(thingee): Backwards-compatibility with v1 args
    if args.display_name is not None:
        args.name = args.display_name

    if args.display_description is not None:
        args.description = args.display_description

    volume_metadata = None
    if args.metadata is not None:
        volume_metadata = _extract_metadata(args)

    #NOTE(N.S.): take this piece from novaclient
    hints = {}
    if args.scheduler_hints:
        for hint in args.scheduler_hints:
            key, _sep, value = hint.partition('=')
            # NOTE(vish): multiple copies of same hint will
            #             result in a list of values
            if key in hints:
                if isinstance(hints[key], six.string_types):
                    hints[key] = [hints[key]]
                hints[key] += [value]
            else:
                hints[key] = value
    #NOTE(N.S.): end of taken piece

    volume = cs.volumes.create(args.size,
                               args.consisgroup_id,
                               args.snapshot_id,
                               args.source_volid,
                               args.name,
                               args.description,
                               args.volume_type,
                               availability_zone=args.availability_zone,
                               imageRef=args.image_id,
                               metadata=volume_metadata,
                               scheduler_hints=hints,
                               source_replica=args.source_replica)

    info = dict()
    volume = cs.volumes.get(volume.id)
    info.update(volume._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('volume',
           metavar='<volume>', nargs='+',
           help='Name or ID of volume or volumes to delete.')
@utils.service_type('volumev2')
def do_delete(cs, args):
    """Removes one or more volumes."""
    failure_count = 0
    for volume in args.volume:
        try:
            utils.find_volume(cs, volume).delete()
        except Exception as e:
            failure_count += 1
            print("Delete for volume %s failed: %s" % (volume, e))
    if failure_count == len(args.volume):
        raise exceptions.CommandError("Unable to delete any of specified "
                                      "volumes.")


@utils.arg('volume',
           metavar='<volume>', nargs='+',
           help='Name or ID of volume or volumes to delete.')
@utils.service_type('volumev2')
def do_force_delete(cs, args):
    """Attempts force-delete of volume, regardless of state."""
    failure_count = 0
    for volume in args.volume:
        try:
            utils.find_volume(cs, volume).force_delete()
        except Exception as e:
            failure_count += 1
            print("Delete for volume %s failed: %s" % (volume, e))
    if failure_count == len(args.volume):
        raise exceptions.CommandError("Unable to force delete any of "
                                      "specified volumes.")


@utils.arg('volume', metavar='<volume>', nargs='+',
           help='Name or ID of volume to modify.')
@utils.arg('--state', metavar='<state>', default='available',
           help=('The state to assign to the volume. Valid values are '
                 '"available," "error," "creating," "deleting," and '
                 '"error_deleting." '
                 'Default=available.'))
@utils.service_type('volumev2')
def do_reset_state(cs, args):
    """Explicitly updates the volume state."""
    failure_flag = False

    for volume in args.volume:
        try:
            utils.find_volume(cs, volume).reset_state(args.state)
        except Exception as e:
            failure_flag = True
            msg = "Reset state for volume %s failed: %s" % (volume, e)
            print(msg)

    if failure_flag:
        msg = "Unable to reset the state for the specified volume(s)."
        raise exceptions.CommandError(msg)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume to rename.')
@utils.arg('name',
           nargs='?',
           metavar='<name>',
           help='New name for volume.')
@utils.arg('--description', metavar='<description>',
           help='Volume description. Default=None.',
           default=None)
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--display_description',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_rename(cs, args):
    """Renames a volume."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name
    if args.display_description is not None:
        kwargs['description'] = args.display_description
    elif args.description is not None:
        kwargs['description'] = args.description

    if not any(kwargs):
        msg = 'Must supply either name or description.'
        raise exceptions.ClientException(code=1, message=msg)

    utils.find_volume(cs, args.volume).update(**kwargs)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume for which to update metadata.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="The action. Valid values are 'set' or 'unset.'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata key and value pair to set or unset. '
           'For unset, specify only the key.')
@utils.service_type('volumev2')
def do_metadata(cs, args):
    """Sets or deletes volume metadata."""
    volume = utils.find_volume(cs, args.volume)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.volumes.set_metadata(volume, metadata)
    elif args.action == 'unset':
        # NOTE(zul): Make sure py2/py3 sorting is the same
        cs.volumes.delete_metadata(volume, sorted(metadata.keys(),
                                   reverse=True))


@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--all_tenants',
           nargs='?',
           type=int,
           const=1,
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Filters results by a name. Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--display_name',
           help=argparse.SUPPRESS)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help='Filters results by a status. Default=None.')
@utils.arg('--volume-id',
           metavar='<volume-id>',
           default=None,
           help='Filters results by a volume ID. Default=None.')
@utils.arg('--volume_id',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_snapshot_list(cs, args):
    """Lists all snapshots."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    if args.display_name is not None:
        args.name = args.display_name

    search_opts = {
        'all_tenants': all_tenants,
        'display_name': args.name,
        'status': args.status,
        'volume_id': args.volume_id,
    }

    snapshots = cs.volume_snapshots.list(search_opts=search_opts)
    _translate_volume_snapshot_keys(snapshots)
    utils.print_list(snapshots,
                     ['ID', 'Volume ID', 'Status', 'Name', 'Size'])


@utils.arg('snapshot',
           metavar='<snapshot>',
           help='Name or ID of snapshot.')
@utils.service_type('volumev2')
def do_snapshot_show(cs, args):
    """Shows snapshot details."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    _print_volume_snapshot(snapshot)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume to snapshot.')
@utils.arg('--force',
           metavar='<True|False>',
           help='Allows or disallows snapshot of '
           'a volume when the volume is attached to an instance. '
           'If set to True, ignores the current status of the '
           'volume when attempting to snapshot it rather '
           'than forcing it to be available. '
           'Default=False.',
           default=False)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Snapshot name. Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--display_name',
           help=argparse.SUPPRESS)
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Snapshot description. Default=None.')
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--display_description',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_snapshot_create(cs, args):
    """Creates a snapshot."""
    if args.display_name is not None:
        args.name = args.display_name

    if args.display_description is not None:
        args.description = args.display_description

    volume = utils.find_volume(cs, args.volume)
    snapshot = cs.volume_snapshots.create(volume.id,
                                          args.force,
                                          args.name,
                                          args.description)
    _print_volume_snapshot(snapshot)


@utils.arg('snapshot',
           metavar='<snapshot>', nargs='+',
           help='Name or ID of the snapshot(s) to delete.')
@utils.service_type('volumev2')
def do_snapshot_delete(cs, args):
    """Removes one or more snapshots."""
    failure_count = 0
    for snapshot in args.snapshot:
        try:
            _find_volume_snapshot(cs, snapshot).delete()
        except Exception as e:
            failure_count += 1
            print("Delete for snapshot %s failed: %s" % (snapshot, e))
    if failure_count == len(args.snapshot):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "snapshots.")


@utils.arg('snapshot', metavar='<snapshot>',
           help='Name or ID of snapshot.')
@utils.arg('name', nargs='?', metavar='<name>',
           help='New name for snapshot.')
@utils.arg('--description', metavar='<description>',
           help='Snapshot description. Default=None.',
           default=None)
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--display_description',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_snapshot_rename(cs, args):
    """Renames a snapshot."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name

    if args.description is not None:
        kwargs['description'] = args.description
    elif args.display_description is not None:
        kwargs['description'] = args.display_description

    if not any(kwargs):
        msg = 'Must supply either name or description.'
        raise exceptions.ClientException(code=1, message=msg)

    _find_volume_snapshot(cs, args.snapshot).update(**kwargs)


@utils.arg('snapshot', metavar='<snapshot>', nargs='+',
           help='Name or ID of snapshot to modify.')
@utils.arg('--state', metavar='<state>',
           default='available',
           help=('The state to assign to the snapshot. Valid values are '
           '"available," "error," "creating," "deleting," and '
           '"error_deleting." '
           'Default is "available."'))
@utils.service_type('volumev2')
def do_snapshot_reset_state(cs, args):
    """Explicitly updates the snapshot state."""
    failure_count = 0

    single = (len(args.snapshot) == 1)

    for snapshot in args.snapshot:
        try:
            _find_volume_snapshot(cs, snapshot).reset_state(args.state)
        except Exception as e:
            failure_count += 1
            msg = "Reset state for snapshot %s failed: %s" % (snapshot, e)
            if not single:
                print(msg)

    if failure_count == len(args.snapshot):
        if not single:
            msg = ("Unable to reset the state for any of the specified "
                   "snapshots.")
        raise exceptions.CommandError(msg)


def _print_volume_type_list(vtypes):
    utils.print_list(vtypes, ['ID', 'Name'])


@utils.service_type('volumev2')
def do_type_list(cs, args):
    """Lists available 'volume types'."""
    vtypes = cs.volume_types.list()
    _print_volume_type_list(vtypes)


@utils.service_type('volumev2')
def do_extra_specs_list(cs, args):
    """Lists current volume types and extra specs."""
    vtypes = cs.volume_types.list()
    utils.print_list(vtypes, ['ID', 'Name', 'extra_specs'])


@utils.arg('name',
           metavar='<name>',
           help="Name of new volume type.")
@utils.service_type('volumev2')
def do_type_create(cs, args):
    """Creates a volume type."""
    vtype = cs.volume_types.create(args.name)
    _print_volume_type_list([vtype])


@utils.arg('id',
           metavar='<id>',
           help="ID of volume type to delete.")
@utils.service_type('volumev2')
def do_type_delete(cs, args):
    """Deletes a volume type."""
    cs.volume_types.delete(args.id)


@utils.arg('vtype',
           metavar='<vtype>',
           help="Name or ID of volume type.")
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="The action. Valid values are 'set' or 'unset.'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='The extra specs key and value pair to set or unset. '
           'For unset, specify only the key.')
@utils.service_type('volumev2')
def do_type_key(cs, args):
    """Sets or unsets extra_spec for a volume type."""
    vtype = _find_volume_type(cs, args.vtype)
    keypair = _extract_metadata(args)

    if args.action == 'set':
        vtype.set_keys(keypair)
    elif args.action == 'unset':
        vtype.unset_keys(list(keypair))


@utils.service_type('volumev2')
def do_endpoints(cs, args):
    """Discovers endpoints registered by authentication service."""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


@utils.service_type('volumev2')
def do_credentials(cs, args):
    """Shows user credentials returned from auth."""
    catalog = cs.client.service_catalog.catalog
    utils.print_dict(catalog['user'], "User Credentials")
    utils.print_dict(catalog['token'], "Token")


_quota_resources = ['volumes', 'snapshots', 'gigabytes']
_quota_infos = ['Type', 'In_use', 'Reserved', 'Limit']


def _quota_show(quotas):
    quota_dict = {}
    for resource in quotas._info:
        good_name = False
        for name in _quota_resources:
            if resource.startswith(name):
                good_name = True
        if not good_name:
            continue
        quota_dict[resource] = getattr(quotas, resource, None)
    utils.print_dict(quota_dict)


def _quota_usage_show(quotas):
    quota_list = []
    for resource in quotas._info.keys():
        good_name = False
        for name in _quota_resources:
            if resource.startswith(name):
                good_name = True
        if not good_name:
            continue
        quota_info = getattr(quotas, resource, None)
        quota_info['Type'] = resource
        quota_info = dict((k.capitalize(), v) for k, v in quota_info.items())
        quota_list.append(quota_info)
    utils.print_list(quota_list, _quota_infos)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            if args.volume_type:
                resource = resource + '_%s' % args.volume_type
            updates[resource] = val

    if updates:
        _quota_show(manager.update(identifier, **updates))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='ID of tenant for which to list quotas.')
@utils.service_type('volumev2')
def do_quota_show(cs, args):
    """Lists quotas for a tenant."""

    _quota_show(cs.quotas.get(args.tenant))


@utils.arg('tenant', metavar='<tenant_id>',
           help='ID of tenant for which to list quota usage.')
@utils.service_type('volumev2')
def do_quota_usage(cs, args):
    """Lists quota usage for a tenant."""

    _quota_usage_show(cs.quotas.get(args.tenant, usage=True))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='ID of tenant for which to list quota defaults.')
@utils.service_type('volumev2')
def do_quota_defaults(cs, args):
    """Lists default quotas for a tenant."""

    _quota_show(cs.quotas.defaults(args.tenant))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='ID of tenant for which to set quotas.')
@utils.arg('--volumes',
           metavar='<volumes>',
           type=int, default=None,
           help='The new "volumes" quota value. Default=None.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='The new "snapshots" quota value. Default=None.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='The new "gigabytes" quota value. Default=None.')
@utils.arg('--volume-type',
           metavar='<volume_type_name>',
           default=None,
           help='Volume type. Default=None.')
@utils.service_type('volumev2')
def do_quota_update(cs, args):
    """Updates quotas for a tenant."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg('tenant', metavar='<tenant_id>',
           help='UUID of tenant to delete the quotas for.')
@utils.service_type('volume')
def do_quota_delete(cs, args):
    """Delete the quotas for a tenant."""

    cs.quotas.delete(args.tenant)


@utils.arg('class_name',
           metavar='<class>',
           help='Name of quota class for which to list quotas.')
@utils.service_type('volumev2')
def do_quota_class_show(cs, args):
    """Lists quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@utils.arg('class-name',
           metavar='<class-name>',
           help='Name of quota class for which to set quotas.')
@utils.arg('--volumes',
           metavar='<volumes>',
           type=int, default=None,
           help='The new "volumes" quota value. Default=None.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='The new "snapshots" quota value. Default=None.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='The new "gigabytes" quota value. Default=None.')
@utils.arg('--volume-type',
           metavar='<volume_type_name>',
           default=None,
           help='Volume type. Default=None.')
@utils.service_type('volumev2')
def do_quota_class_update(cs, args):
    """Updates quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@utils.service_type('volumev2')
def do_absolute_limits(cs, args):
    """Lists absolute limits for a user."""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    utils.print_list(limits, columns)


@utils.service_type('volumev2')
def do_rate_limits(cs, args):
    """Lists rate limits for a user."""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


def _find_volume_type(cs, vtype):
    """Gets a volume type by name or ID."""
    return utils.find_resource(cs.volume_types, vtype)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume to snapshot.')
@utils.arg('--force',
           metavar='<True|False>',
           help='Enables or disables upload of '
           'a volume that is attached to an instance. '
           'Default=False.',
           default=False)
@utils.arg('--container-format',
           metavar='<container-format>',
           help='Container format type. '
           'Default is bare.',
           default='bare')
@utils.arg('--container_format',
           help=argparse.SUPPRESS)
@utils.arg('--disk-format',
           metavar='<disk-format>',
           help='Disk format type. '
           'Default is raw.',
           default='raw')
@utils.arg('--disk_format',
           help=argparse.SUPPRESS)
@utils.arg('image_name',
           metavar='<image-name>',
           help='The new image name.')
@utils.arg('--image_name',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_upload_to_image(cs, args):
    """Uploads volume to Image Service as an image."""
    volume = utils.find_volume(cs, args.volume)
    _print_volume_image(volume.upload_to_image(args.force,
                                               args.image_name,
                                               args.container_format,
                                               args.disk_format))


@utils.arg('volume', metavar='<volume>', help='ID of volume to migrate.')
@utils.arg('host', metavar='<host>', help='Destination host.')
@utils.arg('--force-host-copy', metavar='<True|False>',
           choices=['True', 'False'], required=False,
           help='Enables or disables generic host-based '
           'force-migration, which bypasses driver '
           'optimizations. Default=False.',
           default=False)
@utils.service_type('volumev2')
def do_migrate(cs, args):
    """Migrates volume to a new host."""
    volume = utils.find_volume(cs, args.volume)
    volume.migrate_volume(args.host, args.force_host_copy)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of volume for which to modify type.')
@utils.arg('new_type', metavar='<volume-type>', help='New volume type.')
@utils.arg('--migration-policy', metavar='<never|on-demand>', required=False,
           choices=['never', 'on-demand'], default='never',
           help='Migration policy during retype of volume.')
@utils.service_type('volumev2')
def do_retype(cs, args):
    """Changes the volume type for a volume."""
    volume = utils.find_volume(cs, args.volume)
    volume.retype(args.new_type, args.migration_policy)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of volume to backup.')
@utils.arg('--container', metavar='<container>',
           help='Backup container name. Default=None.',
           default=None)
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--name', metavar='<name>',
           help='Backup name. Default=None.',
           default=None)
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Backup description. Default=None.')
@utils.service_type('volumev2')
def do_backup_create(cs, args):
    """Creates a volume backup."""
    if args.display_name is not None:
        args.name = args.display_name

    if args.display_description is not None:
        args.description = args.display_description

    volume = utils.find_volume(cs, args.volume)
    backup = cs.backups.create(volume.id,
                               args.container,
                               args.name,
                               args.description)

    info = {"volume_id": volume.id}
    info.update(backup._info)

    if 'links' in info:
        info.pop('links')

    utils.print_dict(info)


@utils.arg('backup', metavar='<backup>', help='Name or ID of backup.')
@utils.service_type('volumev2')
def do_backup_show(cs, args):
    """Shows backup details."""
    backup = _find_backup(cs, args.backup)
    info = dict()
    info.update(backup._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.service_type('volumev2')
def do_backup_list(cs, args):
    """Lists all backups."""
    backups = cs.backups.list()
    columns = ['ID', 'Volume ID', 'Status', 'Name', 'Size', 'Object Count',
               'Container']
    utils.print_list(backups, columns)


@utils.arg('backup', metavar='<backup>',
           help='Name or ID of backup to delete.')
@utils.service_type('volumev2')
def do_backup_delete(cs, args):
    """Removes a backup."""
    backup = _find_backup(cs, args.backup)
    backup.delete()


@utils.arg('backup', metavar='<backup>',
           help='ID of backup to restore.')
@utils.arg('--volume-id', metavar='<volume>',
           help=argparse.SUPPRESS,
           default=None)
@utils.arg('--volume', metavar='<volume>',
           help='Name or ID of volume to which to restore. '
           'Default=None.',
           default=None)
@utils.service_type('volumev2')
def do_backup_restore(cs, args):
    """Restores a backup."""
    vol = args.volume or args.volume_id
    if vol:
        volume_id = utils.find_volume(cs, vol).id
    else:
        volume_id = None
    cs.restores.restore(args.backup, volume_id)


@utils.arg('backup', metavar='<backup>',
           help='ID of the backup to export.')
@utils.service_type('volumev2')
def do_backup_export(cs, args):
    """Export backup metadata record."""
    info = cs.backups.export_record(args.backup)
    utils.print_dict(info)


@utils.arg('backup_service', metavar='<backup_service>',
           help='Backup service to use for importing the backup.')
@utils.arg('backup_url', metavar='<backup_url>',
           help='Backup URL for importing the backup metadata.')
@utils.service_type('volumev2')
def do_backup_import(cs, args):
    """Import backup metadata record."""
    info = cs.backups.import_record(args.backup_service, args.backup_url)
    info.pop('links', None)

    utils.print_dict(info)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of volume to transfer.')
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Transfer name. Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.service_type('volumev2')
def do_transfer_create(cs, args):
    """Creates a volume transfer."""
    if args.display_name is not None:
        args.name = args.display_name

    volume = utils.find_volume(cs, args.volume)
    transfer = cs.transfers.create(volume.id,
                                   args.name)
    info = dict()
    info.update(transfer._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('transfer', metavar='<transfer>',
           help='Name or ID of transfer to delete.')
@utils.service_type('volumev2')
def do_transfer_delete(cs, args):
    """Undoes a transfer."""
    transfer = _find_transfer(cs, args.transfer)
    transfer.delete()


@utils.arg('transfer', metavar='<transfer>',
           help='ID of transfer to accept.')
@utils.arg('auth_key', metavar='<auth_key>',
           help='Authentication key of transfer to accept.')
@utils.service_type('volumev2')
def do_transfer_accept(cs, args):
    """Accepts a volume transfer."""
    transfer = cs.transfers.accept(args.transfer, args.auth_key)
    info = dict()
    info.update(transfer._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.service_type('volumev2')
def do_transfer_list(cs, args):
    """Lists all transfers."""
    transfers = cs.transfers.list()
    columns = ['ID', 'Volume ID', 'Name']
    utils.print_list(transfers, columns)


@utils.arg('transfer', metavar='<transfer>',
           help='Name or ID of transfer to accept.')
@utils.service_type('volumev2')
def do_transfer_show(cs, args):
    """Shows transfer details."""
    transfer = _find_transfer(cs, args.transfer)
    info = dict()
    info.update(transfer._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of volume to extend.')
@utils.arg('new_size',
           metavar='<new_size>',
           type=int,
           help='New size of volume, in GBs.')
@utils.service_type('volumev2')
def do_extend(cs, args):
    """Attempts to extend size of an existing volume."""
    volume = utils.find_volume(cs, args.volume)
    cs.volumes.extend(volume, args.new_size)


@utils.arg('--host', metavar='<hostname>', default=None,
           help='Host name. Default=None.')
@utils.arg('--binary', metavar='<binary>', default=None,
           help='Service binary. Default=None.')
@utils.service_type('volumev2')
def do_service_list(cs, args):
    """Lists all services. Filter by host and service binary."""
    result = cs.services.list(host=args.host, binary=args.binary)
    columns = ["Binary", "Host", "Zone", "Status", "State", "Updated_at"]
    # NOTE(jay-lau-513): we check if the response has disabled_reason
    # so as not to add the column when the extended ext is not enabled.
    if result and hasattr(result[0], 'disabled_reason'):
        columns.append("Disabled Reason")
    utils.print_list(result, columns)


@utils.arg('host', metavar='<hostname>', help='Host name.')
@utils.arg('binary', metavar='<binary>', help='Service binary.')
@utils.service_type('volumev2')
def do_service_enable(cs, args):
    """Enables the service."""
    result = cs.services.enable(args.host, args.binary)
    columns = ["Host", "Binary", "Status"]
    utils.print_list([result], columns)


@utils.arg('host', metavar='<hostname>', help='Host name.')
@utils.arg('binary', metavar='<binary>', help='Service binary.')
@utils.arg('--reason', metavar='<reason>',
           help='Reason for disabling service.')
@utils.service_type('volumev2')
def do_service_disable(cs, args):
    """Disables the service."""
    columns = ["Host", "Binary", "Status"]
    if args.reason:
        columns.append('Disabled Reason')
        result = cs.services.disable_log_reason(args.host, args.binary,
                                                args.reason)
    else:
        result = cs.services.disable(args.host, args.binary)
    utils.print_list([result], columns)


def _treeizeAvailabilityZone(zone):
    """Builds a tree view for availability zones."""
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

    if getattr(zone, "hosts", None) and zone.hosts is not None:
        for (host, services) in zone.hosts.items():
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


@utils.service_type('volumev2')
def do_availability_zone_list(cs, _args):
    """Lists all availability zones."""
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
    utils.print_list(result, ['Name', 'Status'])


def _print_volume_encryption_type_list(encryption_types):
    """
    Lists volume encryption types.

    :param encryption_types: a list of :class: VolumeEncryptionType instances
    """
    utils.print_list(encryption_types, ['Volume Type ID', 'Provider',
                                        'Cipher', 'Key Size',
                                        'Control Location'])


@utils.service_type('volumev2')
def do_encryption_type_list(cs, args):
    """Shows encryption type details for volume types. Admin only."""
    result = cs.volume_encryption_types.list()
    utils.print_list(result, ['Volume Type ID', 'Provider', 'Cipher',
                              'Key Size', 'Control Location'])


@utils.arg('volume_type',
           metavar='<volume_type>',
           type=str,
           help="Name or ID of volume type.")
@utils.service_type('volumev2')
def do_encryption_type_show(cs, args):
    """Shows encryption type details for a volume type. Admin only."""
    volume_type = _find_volume_type(cs, args.volume_type)

    result = cs.volume_encryption_types.get(volume_type)

    # Display result or an empty table if no result
    if hasattr(result, 'volume_type_id'):
        _print_volume_encryption_type_list([result])
    else:
        _print_volume_encryption_type_list([])


@utils.arg('volume_type',
           metavar='<volume_type>',
           type=str,
           help="Name or ID of volume type.")
@utils.arg('provider',
           metavar='<provider>',
           type=str,
           help='The class that provides encryption support. '
           'For example, LuksEncryptor.')
@utils.arg('--cipher',
           metavar='<cipher>',
           type=str,
           required=False,
           default=None,
           help='The encryption algorithm or mode. '
           'For example, aes-xts-plain64. Default=None.')
@utils.arg('--key_size',
           metavar='<key_size>',
           type=int,
           required=False,
           default=None,
           help='Size of encryption key, in bits. '
           'For example, 128 or 256. Default=None.')
@utils.arg('--control_location',
           metavar='<control_location>',
           choices=['front-end', 'back-end'],
           type=str,
           required=False,
           default='front-end',
           help='Notional service where encryption is performed. '
           'Valid values are "front-end" or "back-end." '
           'For example, front-end=Nova. Default is "front-end."')
@utils.service_type('volumev2')
def do_encryption_type_create(cs, args):
    """Creates encryption type for a volume type. Admin only."""
    volume_type = _find_volume_type(cs, args.volume_type)

    body = {}
    body['provider'] = args.provider
    body['cipher'] = args.cipher
    body['key_size'] = args.key_size
    body['control_location'] = args.control_location

    result = cs.volume_encryption_types.create(volume_type, body)
    _print_volume_encryption_type_list([result])


@utils.arg('volume_type',
           metavar='<volume_type>',
           type=str,
           help="Name or ID of volume type.")
@utils.service_type('volumev2')
def do_encryption_type_delete(cs, args):
    """Deletes encryption type for a volume type. Admin only."""
    volume_type = _find_volume_type(cs, args.volume_type)
    cs.volume_encryption_types.delete(volume_type)


def _print_qos_specs(qos_specs):
    utils.print_dict(qos_specs._info)


def _print_qos_specs_list(q_specs):
    utils.print_list(q_specs, ['ID', 'Name', 'Consumer', 'specs'])


def _print_qos_specs_and_associations_list(q_specs):
    utils.print_list(q_specs, ['ID', 'Name', 'Consumer', 'specs'])


def _print_associations_list(associations):
    utils.print_list(associations, ['Association_Type', 'Name', 'ID'])


@utils.arg('name',
           metavar='<name>',
           help="Name of new QoS specifications.")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help="QoS specifications.")
@utils.service_type('volumev2')
def do_qos_create(cs, args):
    """Creates a qos specs."""
    keypair = None
    if args.metadata is not None:
        keypair = _extract_metadata(args)
    qos_specs = cs.qos_specs.create(args.name, keypair)
    _print_qos_specs(qos_specs)


@utils.service_type('volumev2')
def do_qos_list(cs, args):
    """Lists qos specs."""
    qos_specs = cs.qos_specs.list()
    _print_qos_specs_list(qos_specs)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help="ID of QoS specifications to show.")
@utils.service_type('volumev2')
def do_qos_show(cs, args):
    """Shows qos specs details."""
    qos_specs = _find_qos_specs(cs, args.qos_specs)
    _print_qos_specs(qos_specs)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help="ID of QoS specifications to delete.")
@utils.arg('--force',
           metavar='<True|False>',
           default=False,
           help='Enables or disables deletion of in-use '
                'QoS specifications. Default=False.')
@utils.service_type('volumev2')
def do_qos_delete(cs, args):
    """Deletes a specified qos specs."""
    force = strutils.bool_from_string(args.force)
    qos_specs = _find_qos_specs(cs, args.qos_specs)
    cs.qos_specs.delete(qos_specs, force)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help='ID of QoS specifications.')
@utils.arg('vol_type_id', metavar='<volume_type_id>',
           help='ID of volume type with which to associate '
           'QoS specifications.')
@utils.service_type('volumev2')
def do_qos_associate(cs, args):
    """Associates qos specs with specified volume type."""
    cs.qos_specs.associate(args.qos_specs, args.vol_type_id)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help='ID of QoS specifications.')
@utils.arg('vol_type_id', metavar='<volume_type_id>',
           help='ID of volume type with which to associate '
           'QoS specifications.')
@utils.service_type('volumev2')
def do_qos_disassociate(cs, args):
    """Disassociates qos specs from specified volume type."""
    cs.qos_specs.disassociate(args.qos_specs, args.vol_type_id)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help='ID of QoS specifications on which to operate.')
@utils.service_type('volumev2')
def do_qos_disassociate_all(cs, args):
    """Disassociates qos specs from all its associations."""
    cs.qos_specs.disassociate_all(args.qos_specs)


@utils.arg('qos_specs', metavar='<qos_specs>',
           help='ID of QoS specifications.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="The action. Valid values are 'set' or 'unset.'")
@utils.arg('metadata', metavar='key=value',
           nargs='+',
           default=[],
           help='Metadata key and value pair to set or unset. '
           'For unset, specify only the key.')
def do_qos_key(cs, args):
    """Sets or unsets specifications for a qos spec."""
    keypair = _extract_metadata(args)

    if args.action == 'set':
        cs.qos_specs.set_keys(args.qos_specs, keypair)
    elif args.action == 'unset':
        cs.qos_specs.unset_keys(args.qos_specs, list(keypair))


@utils.arg('qos_specs', metavar='<qos_specs>',
           help='ID of QoS specifications.')
@utils.service_type('volumev2')
def do_qos_get_association(cs, args):
    """Lists all associations for specified qos specs."""
    associations = cs.qos_specs.get_associations(args.qos_specs)
    _print_associations_list(associations)


@utils.arg('snapshot',
           metavar='<snapshot>',
           help='ID of snapshot for which to update metadata.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="The action. Valid values are 'set' or 'unset.'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata key and value pair to set or unset. '
           'For unset, specify only the key.')
@utils.service_type('volumev2')
def do_snapshot_metadata(cs, args):
    """Sets or deletes snapshot metadata."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        metadata = snapshot.set_metadata(metadata)
        utils.print_dict(metadata._info)
    elif args.action == 'unset':
        snapshot.delete_metadata(list(metadata.keys()))


@utils.arg('snapshot', metavar='<snapshot>',
           help='ID of snapshot.')
@utils.service_type('volumev2')
def do_snapshot_metadata_show(cs, args):
    """Shows snapshot metadata."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    utils.print_dict(snapshot._info['metadata'], 'Metadata-property')


@utils.arg('volume', metavar='<volume>',
           help='ID of volume.')
@utils.service_type('volumev2')
def do_metadata_show(cs, args):
    """Shows volume metadata."""
    volume = utils.find_volume(cs, args.volume)
    utils.print_dict(volume._info['metadata'], 'Metadata-property')


@utils.arg('volume',
           metavar='<volume>',
           help='ID of volume for which to update metadata.')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata key and value pair or pairs to update.')
@utils.service_type('volumev2')
def do_metadata_update_all(cs, args):
    """Updates volume metadata."""
    volume = utils.find_volume(cs, args.volume)
    metadata = _extract_metadata(args)
    metadata = volume.update_all_metadata(metadata)
    utils.print_dict(metadata)


@utils.arg('snapshot',
           metavar='<snapshot>',
           help='ID of snapshot for which to update metadata.')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata key and value pair to update.')
@utils.service_type('volumev2')
def do_snapshot_metadata_update_all(cs, args):
    """Updates snapshot metadata."""
    snapshot = _find_volume_snapshot(cs, args.snapshot)
    metadata = _extract_metadata(args)
    metadata = snapshot.update_all_metadata(metadata)
    utils.print_dict(metadata)


@utils.arg('volume', metavar='<volume>', help='ID of volume to update.')
@utils.arg('read_only',
           metavar='<True|true|False|false>',
           choices=['True', 'true', 'False', 'false'],
           help='Enables or disables update of volume to '
           'read-only access mode.')
@utils.service_type('volumev2')
def do_readonly_mode_update(cs, args):
    """Updates volume read-only access-mode flag."""
    volume = utils.find_volume(cs, args.volume)
    cs.volumes.update_readonly_flag(volume,
                                    strutils.bool_from_string(args.read_only))


@utils.arg('volume', metavar='<volume>', help='ID of the volume to update.')
@utils.arg('bootable',
           metavar='<True|true|False|false>',
           choices=['True', 'true', 'False', 'false'],
           help='Flag to indicate whether volume is bootable.')
@utils.service_type('volumev2')
def do_set_bootable(cs, args):
    """Update bootable status of a volume."""
    volume = utils.find_volume(cs, args.volume)
    cs.volumes.set_bootable(volume,
                            strutils.bool_from_string(args.bootable))


@utils.arg('host',
           metavar='<host>',
           help='Cinder host on which the existing volume resides')
@utils.arg('ref',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Driver-specific reference to the existing volume as '
                'key=value pairs')
@utils.arg('--source-name',
           metavar='<source-name>',
           help='Name of the volume to manage (Optional)')
@utils.arg('--source-id',
           metavar='<source-id>',
           help='ID of the volume to manage (Optional)')
@utils.arg('--name',
           metavar='<name>',
           help='Volume name (Optional, Default=None)')
@utils.arg('--description',
           metavar='<description>',
           help='Volume description (Optional, Default=None)')
@utils.arg('--volume-type',
           metavar='<volume-type>',
           help='Volume type (Optional, Default=None)')
@utils.arg('--availability-zone',
           metavar='<availability-zone>',
           help='Availability zone for volume (Optional, Default=None)')
@utils.arg('--metadata',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Metadata key=value pairs (Optional, Default=None)')
@utils.arg('--bootable',
           action='store_true',
           help='Specifies that the newly created volume should be'
                ' marked as bootable')
@utils.service_type('volumev2')
def do_manage(cs, args):
    """Manage an existing volume."""
    volume_metadata = None
    if args.metadata is not None:
        volume_metadata = _extract_metadata(args)

    # Build a dictionary of key/value pairs to pass to the API.
    ref_dict = {}
    for pair in args.ref:
        (k, v) = pair.split('=', 1)
        ref_dict[k] = v

    # The recommended way to specify an existing volume is by ID or name, and
    # have the Cinder driver look for 'source-name' or 'source-id' elements in
    # the ref structure.  To make things easier for the user, we have special
    # --source-name and --source-id CLI options that add the appropriate
    # element to the ref structure.
    #
    # Note how argparse converts hyphens to underscores.  We use hyphens in the
    # dictionary so that it is consistent with what the user specified on the
    # CLI.
    if hasattr(args, 'source_name') and \
       args.source_name is not None:
        ref_dict['source-name'] = args.source_name
    if hasattr(args, 'source_id') and \
       args.source_id is not None:
        ref_dict['source-id'] = args.source_id

    volume = cs.volumes.manage(host=args.host,
                               ref=ref_dict,
                               name=args.name,
                               description=args.description,
                               volume_type=args.volume_type,
                               availability_zone=args.availability_zone,
                               metadata=volume_metadata,
                               bootable=args.bootable)

    info = {}
    volume = cs.volumes.get(volume.id)
    info.update(volume._info)
    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of the volume to unmanage.')
@utils.service_type('volumev2')
def do_unmanage(cs, args):
    utils.find_volume(cs, args.volume).unmanage(args.volume)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of the volume to promote.')
@utils.service_type('volumev2')
def do_replication_promote(cs, args):
    """Promote a secondary volume to primary for a relationship."""
    utils.find_volume(cs, args.volume).promote(args.volume)


@utils.arg('volume', metavar='<volume>',
           help='Name or ID of the volume to reenable replication.')
@utils.service_type('volumev2')
def do_replication_reenable(cs, args):
    """Sync the secondary volume with primary for a relationship."""
    utils.find_volume(cs, args.volume).reenable(args.volume)


@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.service_type('volumev2')
def do_consisgroup_list(cs, args):
    """Lists all consistencygroups."""
    consistencygroups = cs.consistencygroups.list()

    columns = ['ID', 'Status', 'Name']
    utils.print_list(consistencygroups, columns)


@utils.arg('consistencygroup',
           metavar='<consistencygroup>',
           help='Name or ID of a consistency group.')
@utils.service_type('volumev2')
def do_consisgroup_show(cs, args):
    """Shows details of a consistency group."""
    info = dict()
    consistencygroup = _find_consistencygroup(cs, args.consistencygroup)
    info.update(consistencygroup._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('volumetypes',
           metavar='<volume-types>',
           help='Volume types.')
@utils.arg('--name',
           metavar='<name>',
           help='Name of a consistency group.')
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Description of a consistency group. Default=None.')
@utils.arg('--availability-zone',
           metavar='<availability-zone>',
           default=None,
           help='Availability zone for volume. Default=None.')
@utils.service_type('volumev2')
def do_consisgroup_create(cs, args):
    """Creates a consistency group."""

    consistencygroup = cs.consistencygroups.create(
        args.volumetypes,
        args.name,
        args.description,
        availability_zone=args.availability_zone)

    info = dict()
    consistencygroup = cs.consistencygroups.get(consistencygroup.id)
    info.update(consistencygroup._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('consistencygroup',
           metavar='<consistencygroup>', nargs='+',
           help='Name or ID of one or more consistency groups '
                'to be deleted.')
@utils.arg('--force',
           action='store_true',
           help='Allows or disallows consistency groups '
                'to be deleted. If the consistency group is empty, '
                'it can be deleted without the force flag. '
                'If the consistency group is not empty, the force '
                'flag is required for it to be deleted.',
           default=False)
@utils.service_type('volumev2')
def do_consisgroup_delete(cs, args):
    """Removes one or more consistency groups."""
    failure_count = 0
    for consistencygroup in args.consistencygroup:
        try:
            _find_consistencygroup(cs, consistencygroup).delete(args.force)
        except Exception as e:
            failure_count += 1
            print("Delete for consistency group %s failed: %s" %
                  (consistencygroup, e))
    if failure_count == len(args.consistencygroup):
        raise exceptions.CommandError("Unable to delete any of specified "
                                      "consistency groups.")


@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help='Filters results by a status. Default=None.')
@utils.arg('--consistencygroup-id',
           metavar='<consistencygroup_id>',
           default=None,
           help='Filters results by a consistency group ID. Default=None.')
@utils.service_type('volumev2')
def do_cgsnapshot_list(cs, args):
    """Lists all cgsnapshots."""
    cgsnapshots = cs.cgsnapshots.list()

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    search_opts = {
        'all_tenants': all_tenants,
        'status': args.status,
        'consistencygroup_id': args.consistencygroup_id,
    }

    cgsnapshots = cs.cgsnapshots.list(search_opts=search_opts)

    columns = ['ID', 'Status', 'Name']
    utils.print_list(cgsnapshots, columns)


@utils.arg('cgsnapshot',
           metavar='<cgsnapshot>',
           help='Name or ID of cgsnapshot.')
@utils.service_type('volumev2')
def do_cgsnapshot_show(cs, args):
    """Shows cgsnapshot details."""
    info = dict()
    cgsnapshot = _find_cgsnapshot(cs, args.cgsnapshot)
    info.update(cgsnapshot._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('consistencygroup',
           metavar='<consistencygroup>',
           help='Name or ID of a consistency group.')
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Cgsnapshot name. Default=None.')
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Cgsnapshot description. Default=None.')
@utils.service_type('volumev2')
def do_cgsnapshot_create(cs, args):
    """Creates a cgsnapshot."""
    consistencygroup = _find_consistencygroup(cs, args.consistencygroup)
    cgsnapshot = cs.cgsnapshots.create(
        consistencygroup.id,
        args.name,
        args.description)

    info = dict()
    cgsnapshot = cs.cgsnapshots.get(cgsnapshot.id)
    info.update(cgsnapshot._info)

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('cgsnapshot',
           metavar='<cgsnapshot>', nargs='+',
           help='Name or ID of one or more cgsnapshots to be deleted.')
@utils.service_type('volumev2')
def do_cgsnapshot_delete(cs, args):
    """Removes one or more cgsnapshots."""
    failure_count = 0
    for cgsnapshot in args.cgsnapshot:
        try:
            _find_cgsnapshot(cs, cgsnapshot).delete()
        except Exception as e:
            failure_count += 1
            print("Delete for cgsnapshot %s failed: %s" % (cgsnapshot, e))
    if failure_count == len(args.cgsnapshot):
        raise exceptions.CommandError("Unable to delete any of specified "
                                      "cgsnapshots.")
