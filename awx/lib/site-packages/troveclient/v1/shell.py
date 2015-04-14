# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

import sys
import time

try:
    import simplejson as json
except ImportError:
    import json

from troveclient import exceptions
from troveclient import utils


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
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


def _print_instance(instance):
    info = instance._info.copy()
    info['flavor'] = instance.flavor['id']
    if hasattr(instance, 'volume'):
        info['volume'] = instance.volume['size']
        if 'used' in instance.volume:
            info['volume_used'] = instance.volume['used']
    if hasattr(instance, 'ip'):
        info['ip'] = ', '.join(instance.ip)
    if hasattr(instance, 'datastore'):
        info['datastore'] = instance.datastore['type']
        info['datastore_version'] = instance.datastore['version']
    if hasattr(instance, 'configuration'):
        info['configuration'] = instance.configuration['id']
    if hasattr(instance, 'replica_of'):
        info['replica_of'] = instance.replica_of['id']
    if hasattr(instance, 'replicas'):
        replicas = [replica['id'] for replica in instance.replicas]
        info['replicas'] = ', '.join(replicas)
    info.pop('links', None)
    utils.print_dict(info)


def _print_object(obj):
    # Get rid of those ugly links
    if obj._info.get('links'):
        del(obj._info['links'])

    # Fallback to str_id for flavors, where necessary
    if hasattr(obj, 'str_id'):
        if hasattr(obj, 'id') and not obj.id:
            obj._info['id'] = obj.str_id
        del(obj._info['str_id'])

    utils.print_dict(obj._info)


def _find_instance(cs, instance):
    """Get an instance by ID."""
    return utils.find_resource(cs.instances, instance)


def _find_cluster(cs, cluster):
    """Get a cluster by ID."""
    return utils.find_resource(cs.clusters, cluster)


def _find_flavor(cs, flavor):
    """Get a flavor by ID."""
    return utils.find_resource(cs.flavors, flavor)


def _find_backup(cs, backup):
    """Get a backup by ID."""
    return utils.find_resource(cs.backups, backup)


# Flavor related calls
@utils.arg('--datastore_type', metavar='<datastore_type>',
           default=None,
           help='Type of the datastore. For eg: mysql.')
@utils.arg("--datastore_version_id", metavar="<datastore_version_id>",
           default=None, help="ID of the datastore version.")
@utils.service_type('database')
def do_flavor_list(cs, args):
    """Lists available flavors."""
    if args.datastore_type and args.datastore_version_id:
        flavors = cs.flavors.list_datastore_version_associated_flavors(
            args.datastore_type, args.datastore_version_id)
    elif not args.datastore_type and not args.datastore_version_id:
        flavors = cs.flavors.list()
    else:
        err_msg = ("Specify both <datastore_type> and <datastore_version_id>"
                   " to list datastore version associated flavors.")
        raise exceptions.CommandError(err_msg)

    # Fallback to str_id where necessary.
    _flavors = []
    for f in flavors:
        if not f.id and hasattr(f, 'str_id'):
            f.id = f.str_id
        _flavors.append(f)

    utils.print_list(_flavors, ['id', 'name', 'ram'],
                     labels={'ram': 'RAM'})


@utils.arg('flavor', metavar='<flavor>', help='ID or name of the flavor.')
@utils.service_type('database')
def do_flavor_show(cs, args):
    """Shows details of a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_object(flavor)


# Instance related calls

@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help='Limit the number of results displayed.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
@utils.arg('--include-clustered', dest='include_clustered',
           action="store_true", default=False,
           help="Include instances that are part of a cluster "
                "(default false).")
@utils.service_type('database')
def do_list(cs, args):
    """Lists all the instances."""
    instances = cs.instances.list(limit=args.limit, marker=args.marker,
                                  include_clustered=args.include_clustered)

    for instance in instances:
        setattr(instance, 'flavor_id', instance.flavor['id'])
        if hasattr(instance, 'volume'):
            setattr(instance, 'size', instance.volume['size'])
        else:
            setattr(instance, 'size', '-')
        if hasattr(instance, 'datastore'):
            if instance.datastore.get('version'):
                setattr(instance, 'datastore_version',
                        instance.datastore['version'])
            setattr(instance, 'datastore', instance.datastore['type'])
    utils.print_list(instances, ['id', 'name', 'datastore',
                                 'datastore_version', 'status',
                                 'flavor_id', 'size'])


@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help='Limit the number of results displayed.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
@utils.service_type('database')
def do_cluster_list(cs, args):
    """Lists all the clusters."""
    clusters = cs.clusters.list(limit=args.limit, marker=args.marker)

    for cluster in clusters:
        setattr(cluster, 'datastore_version',
                cluster.datastore['version'])
        setattr(cluster, 'datastore', cluster.datastore['type'])
        setattr(cluster, 'task_name', cluster.task['name'])
    utils.print_list(clusters, ['id', 'name', 'datastore',
                                'datastore_version', 'task_name'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_show(cs, args):
    """Shows details of an instance."""
    instance = _find_instance(cs, args.instance)
    _print_instance(instance)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.service_type('database')
def do_cluster_show(cs, args):
    """Shows details of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    info = cluster._info.copy()
    info['datastore'] = cluster.datastore['type']
    info['datastore_version'] = cluster.datastore['version']
    info['task_name'] = cluster.task['name']
    info['task_description'] = cluster.task['description']
    del info['task']
    if hasattr(cluster, 'ip'):
        info['ip'] = ', '.join(cluster.ip)
    del info['instances']
    cluster._info = info
    _print_object(cluster)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.service_type('database')
def do_cluster_instances(cs, args):
    """Lists all instances of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = cluster._info['instances']
    for instance in instances:
        instance['flavor_id'] = instance['flavor']['id']
        if instance.get('volume'):
            instance['size'] = instance['volume']['size']
    utils.print_list(
        instances, ['id', 'name', 'flavor_id', 'size', 'status'],
        obj_is_dict=True)


@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.service_type('database')
def do_delete(cs, args):
    """Deletes an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.delete(instance)


@utils.arg('cluster', metavar='<cluster>', help='ID of the cluster.')
@utils.service_type('database')
def do_cluster_delete(cs, args):
    """Deletes a cluster."""
    cs.clusters.delete(args.cluster)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('--name',
           metavar='<name>',
           type=str,
           default=None,
           help='Name of the instance.')
@utils.arg('--configuration',
           metavar='<configuration>',
           type=str,
           default=None,
           help='ID of the configuration reference to attach.')
@utils.arg('--detach-replica-source',
           dest='detach_replica_source',
           action="store_true",
           default=False,
           help='Detach the replica instance from its replication source.')
@utils.arg('--remove_configuration',
           dest='remove_configuration',
           action="store_true",
           default=False,
           help='Drops the current configuration reference.')
@utils.service_type('database')
def do_update(cs, args):
    """Updates an instance: Edits name, configuration, or replica source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, args.configuration, args.name,
                      args.detach_replica_source, args.remove_configuration)


@utils.arg('name',
           metavar='<name>',
           type=str,
           help='Name of the instance.')
@utils.arg('--size',
           metavar='<size>',
           type=int,
           default=None,
           help="Size of the instance disk volume in GB. "
                "Required when volume support is enabled.")
@utils.arg('flavor_id',
           metavar='<flavor_id>',
           help='Flavor of the instance.')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.arg('--users', metavar='<users>',
           help='Optional list of users in the form user:password.',
           nargs="+", default=[])
@utils.arg('--backup',
           metavar='<backup>',
           default=None,
           help='A backup ID.')
@utils.arg('--availability_zone',
           metavar='<availability_zone>',
           default=None,
           help='The Zone hint to give to nova.')
@utils.arg('--datastore',
           metavar='<datastore>',
           default=None,
           help='A datastore name or ID.')
@utils.arg('--datastore_version',
           metavar='<datastore_version>',
           default=None,
           help='A datastore version name or ID.')
@utils.arg('--nic',
           metavar="<net-id=net-uuid,v4-fixed-ip=ip-addr,port-id=port-uuid>",
           action='append',
           dest='nics',
           default=[],
           help="Create a NIC on the instance. "
                "Specify option multiple times to create multiple NICs. "
                "net-id: attach NIC to network with this ID "
                "(either port-id or net-id must be specified), "
                "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
                "port-id: attach NIC to port with this ID "
                "(either port-id or net-id must be specified).")
@utils.arg('--configuration',
           metavar='<configuration>',
           default=None,
           help='ID of the configuration group to attach to the instance.')
@utils.arg('--replica_of',
           metavar='<source_instance>',
           default=None,
           help='ID or name of an existing instance to replicate from.')
@utils.arg('--replica_count',
           metavar='<count>',
           type=int,
           default=1,
           help='Number of replicas to create (defaults to 1).')
@utils.service_type('database')
def do_create(cs, args):
    """Creates a new instance."""
    volume = None
    replica_of_instance = None
    if args.size:
        volume = {"size": args.size}
    restore_point = None
    if args.backup:
        restore_point = {"backupRef": args.backup}
    if args.replica_of:
        replica_of_instance = _find_instance(cs, args.replica_of)
    databases = [{'name': value} for value in args.databases]
    users = [{'name': n, 'password': p, 'databases': databases} for (n, p) in
             [z.split(':')[:2] for z in args.users]]
    nics = []
    for nic_str in args.nics:
        nic_info = dict([(k, v) for (k, v) in [z.split("=", 1)[:2] for z in
                                               nic_str.split(",")]])
        if bool(nic_info.get('net-id')) == bool(nic_info.get('port-id')):
            err_msg = ("Invalid nic argument '%s'. Nic arguments must be of "
                       "the form --nic <net-id=net-uuid,v4-fixed-ip=ip-addr,"
                       "port-id=port-uuid>, with at minimum net-id or port-id "
                       "(but not both) specified." % nic_str)
            raise exceptions.CommandError(err_msg)
        nics.append(nic_info)

    instance = cs.instances.create(args.name,
                                   args.flavor_id,
                                   volume=volume,
                                   databases=databases,
                                   users=users,
                                   restorePoint=restore_point,
                                   availability_zone=args.availability_zone,
                                   datastore=args.datastore,
                                   datastore_version=args.datastore_version,
                                   nics=nics,
                                   configuration=args.configuration,
                                   replica_of=replica_of_instance,
                                   replica_count=args.replica_count)
    _print_instance(instance)


@utils.arg('name',
           metavar='<name>',
           type=str,
           help='Name of the cluster.')
@utils.arg('datastore',
           metavar='<datastore>',
           help='A datastore name or UUID.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='A datastore version name or UUID.')
@utils.arg('--instance',
           metavar="<flavor_id=flavor_id,volume=volume>",
           action='append',
           dest='instances',
           default=[],
           help="Create an instance for the cluster.  Specify multiple "
                "times to create multiple instances.")
@utils.service_type('database')
def do_cluster_create(cs, args):
    """Creates a new cluster."""
    instances = []
    for instance_str in args.instances:
        instance_info = {}
        for z in instance_str.split(","):
            for (k, v) in [z.split("=", 1)[:2]]:
                if k == "flavor_id":
                    instance_info["flavorRef"] = v
                elif k == "volume":
                    instance_info["volume"] = {"size": v}
                else:
                    instance_info[k] = v
        if not instance_info.get('flavorRef'):
            err_msg = ("flavor_id is required. Instance arguments must be "
                       "of the form --instance <flavor_id=flavor_id,"
                       "volume=volume>.")
            raise exceptions.CommandError(err_msg)
        instances.append(instance_info)
    cluster = cs.clusters.create(args.name,
                                 args.datastore,
                                 args.datastore_version,
                                 instances=instances)
    cluster._info['task_name'] = cluster.task['name']
    cluster._info['task_description'] = cluster.task['description']
    del cluster._info['task']
    cluster._info['datastore'] = cluster.datastore['type']
    cluster._info['datastore_version'] = cluster.datastore['version']
    del cluster._info['instances']
    _print_object(cluster)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('flavor_id',
           metavar='<flavor_id>',
           help='New flavor of the instance.')
@utils.service_type('database')
def do_resize_flavor(cs, args):
    """[DEPRECATED] Please use resize-instance instead."""
    do_resize_instance(cs, args)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('flavor_id',
           metavar='<flavor_id>',
           help='New flavor of the instance.')
@utils.service_type('database')
def do_resize_instance(cs, args):
    """Resizes an instance with a new flavor."""
    instance = _find_instance(cs, args.instance)
    cs.instances.resize_instance(instance, args.flavor_id)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('size',
           metavar='<size>',
           type=int,
           default=None,
           help='New size of the instance disk volume in GB.')
@utils.service_type('database')
def do_resize_volume(cs, args):
    """Resizes the volume size of an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.resize_volume(instance, args.size)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.service_type('database')
def do_restart(cs, args):
    """Restarts an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.restart(instance)

# Replication related commands


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_detach_replica(cs, args):
    """Detaches a replica instance from its replication source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, detach_replica_source=True)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_promote_to_replica_source(cs, args):
    """Promotes a replica to be the new replica source of its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.promote_to_replica_source(instance)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_eject_replica_source(cs, args):
    """Ejects a replica source from its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.eject_replica_source(instance)

# Backup related commands


@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('database')
def do_backup_show(cs, args):
    """Shows details of a backup."""
    backup = _find_backup(cs, args.backup)
    _print_object(backup)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.service_type('database')
def do_backup_list_instance(cs, args):
    """Lists available backups for an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.instances.backups(instance, limit=args.limit)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.instances.backups(instance, marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'name', 'status',
                               'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='Name or ID of the datastore to list backups for.')
@utils.service_type('database')
def do_backup_list(cs, args):
    """Lists available backups."""
    wrapper = cs.backups.list(limit=args.limit, datastore=args.datastore)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.backups.list(marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'instance_id', 'name',
                               'status', 'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('database')
def do_backup_delete(cs, args):
    """Deletes a backup."""
    cs.backups.delete(args.backup)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of the backup.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the backup.')
@utils.arg('--parent', metavar='<parent>', default=None,
           help='Optional ID of the parent backup to perform an'
           ' incremental backup from.')
@utils.service_type('database')
def do_backup_create(cs, args):
    """Creates a backup of an instance."""
    instance = _find_instance(cs, args.instance)
    backup = cs.backups.create(args.name, instance,
                               description=args.description,
                               parent_id=args.parent)
    _print_object(backup)


@utils.arg('name', metavar='<name>', help='Name of the backup.')
@utils.arg('backup', metavar='<backup>',
           help='Backup ID of the source backup.',
           default=None)
@utils.arg('--region', metavar='<region>', help='Region where the source '
                                                'backup resides.',
           default=None)
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the backup.')
@utils.service_type('database')
def do_backup_copy(cs, args):
    """Creates a backup from another backup."""
    if args.backup:
        backup_ref = {"id": args.backup,
                      "region": args.region}
    else:
        backup_ref = None
    backup = cs.backups.create(args.name, instance=None,
                               description=args.description,
                               parent_id=None, backup=backup_ref,)
    _print_object(backup)


# Database related actions

@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of the database.')
@utils.arg('--character_set', metavar='<character_set>',
           default=None,
           help='Optional character set for database.')
@utils.arg('--collate', metavar='<collate>', default=None,
           help='Optional collation type for database.')
@utils.service_type('database')
def do_database_create(cs, args):
    """Creates a database on an instance."""
    instance = _find_instance(cs, args.instance)
    database_dict = {'name': args.name}
    if args.collate:
        database_dict['collate'] = args.collate
    if args.character_set:
        database_dict['character_set'] = args.character_set
    cs.databases.create(instance,
                        [database_dict])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_database_list(cs, args):
    """Lists available databases on an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.databases.list(instance)
    databases = wrapper.items
    while (wrapper.next):
        wrapper = cs.databases.list(instance, marker=wrapper.next)
        databases += wrapper.items

    utils.print_list(databases, ['name'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.arg('database', metavar='<database>', help='Name of the database.')
@utils.service_type('database')
def do_database_delete(cs, args):
    """Deletes a database from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.databases.delete(instance, args.database)


# User related actions

@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('password', metavar='<password>', help='Password of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_create(cs, args):
    """Creates a user on an instance."""
    instance = _find_instance(cs, args.instance)
    databases = [{'name': value} for value in args.databases]
    user = {'name': args.name, 'password': args.password,
            'databases': databases}
    if args.host:
        user['host'] = args.host
    cs.users.create(instance, [user])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_user_list(cs, args):
    """Lists the users for an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.users.list(instance)
    users = wrapper.items
    while (wrapper.next):
        wrapper = cs.users.list(instance, marker=wrapper.next)
        users += wrapper.items
    for user in users:
        db_names = [db['name'] for db in user.databases]
        user.databases = ', '.join(db_names)
    utils.print_list(users, ['name', 'host', 'databases'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_delete(cs, args):
    """Deletes a user from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.users.delete(instance, args.name, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_show(cs, args):
    """Shows details of a user of an instance."""
    instance = _find_instance(cs, args.instance)
    user = cs.users.get(instance, args.name, hostname=args.host)
    _print_object(user)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_show_access(cs, args):
    """Shows access details of a user of an instance."""
    instance = _find_instance(cs, args.instance)
    access = cs.users.list_access(instance, args.name, hostname=args.host)
    utils.print_list(access, ['name'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('--new_name', metavar='<new_name>', default=None,
           help='Optional new name of user.')
@utils.arg('--new_password', metavar='<new_password>', default=None,
           help='Optional new password of user.')
@utils.arg('--new_host', metavar='<new_host>', default=None,
           help='Optional new host of user.')
@utils.service_type('database')
def do_user_update_attributes(cs, args):
    """Updates a user's attributes on an instance.
    At least one optional argument must be provided.
    """
    instance = _find_instance(cs, args.instance)
    new_attrs = {}
    if args.new_name:
        new_attrs['name'] = args.new_name
    if args.new_password:
        new_attrs['password'] = args.new_password
    if args.new_host:
        new_attrs['host'] = args.new_host
    cs.users.update_attributes(instance, args.name,
                               newuserattr=new_attrs, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('databases', metavar='<databases>',
           help='List of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_grant_access(cs, args):
    """Grants access to a database(s) for a user."""
    instance = _find_instance(cs, args.instance)
    cs.users.grant(instance, args.name,
                   args.databases, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('database', metavar='<database>', help='A single database.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_revoke_access(cs, args):
    """Revokes access to a database for a user."""
    instance = _find_instance(cs, args.instance)
    cs.users.revoke(instance, args.name,
                    args.database, hostname=args.host)


# Limits related commands

@utils.service_type('database')
def do_limit_list(cs, args):
    """Lists the limits for a tenant."""
    limits = cs.limits.list()
    # Pop the first one, its absolute limits
    absolute = limits.pop(0)
    _print_object(absolute)
    utils.print_list(limits, ['value', 'verb', 'remaining', 'unit'])


# Root related commands

@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_root_enable(cs, args):
    """Enables root for an instance and resets if already exists."""
    instance = _find_instance(cs, args.instance)
    root = cs.root.create(instance)
    utils.print_dict({'name': root[0], 'password': root[1]})


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_root_show(cs, args):
    """Gets status if root was ever enabled for an instance."""
    instance = _find_instance(cs, args.instance)
    root = cs.root.is_root_enabled(instance)
    utils.print_dict({'is_root_enabled': root.rootEnabled})


# security group related functions

@utils.service_type('database')
def do_secgroup_list(cs, args):
    """Lists all security groups."""
    wrapper = cs.security_groups.list()
    sec_grps = wrapper.items
    while (wrapper.next):
        wrapper = cs.security_groups.list()
        sec_grps += wrapper.items

    utils.print_list(sec_grps, ['id', 'name', 'instance_id'])


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID')
@utils.service_type('database')
def do_secgroup_show(cs, args):
    """Shows details of a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    del sec_grp._info['rules']
    _print_object(sec_grp)


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID.')
@utils.arg('cidr', metavar='<cidr>', help='CIDR address.')
@utils.service_type('database')
def do_secgroup_add_rule(cs, args):
    """Creates a security group rule."""
    rules = cs.security_group_rules.create(
        args.security_group, args.cidr)

    utils.print_list(rules, [
        'id', 'security_group_id', 'protocol',
        'from_port', 'to_port', 'cidr', 'created'], obj_is_dict=True)


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID.')
@utils.service_type('database')
def do_secgroup_list_rules(cs, args):
    """Lists all rules for a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    rules = sec_grp._info['rules']
    utils.print_list(
        rules, ['id', 'protocol', 'from_port', 'to_port', 'cidr'],
        obj_is_dict=True)


@utils.arg('security_group_rule', metavar='<security_group_rule>',
           help='Name of security group rule.')
@utils.service_type('database')
def do_secgroup_delete_rule(cs, args):
    """Deletes a security group rule."""
    cs.security_group_rules.delete(args.security_group_rule)


@utils.service_type('database')
def do_datastore_list(cs, args):
    """Lists available datastores."""
    datastores = cs.datastores.list()
    utils.print_list(datastores, ['id', 'name'])


@utils.arg('datastore', metavar='<datastore>',
           help='ID of the datastore.')
@utils.service_type('database')
def do_datastore_show(cs, args):
    """Shows details of a datastore."""
    datastore = cs.datastores.get(args.datastore)
    if hasattr(datastore, 'default_version'):
        datastore._info['default_version'] = getattr(datastore,
                                                     'default_version')
    _print_object(datastore)


@utils.arg('datastore', metavar='<datastore>',
           help='ID or name of the datastore.')
@utils.service_type('database')
def do_datastore_version_list(cs, args):
    """Lists available versions for a datastore."""
    datastore_versions = cs.datastore_versions.list(args.datastore)
    utils.print_list(datastore_versions, ['id', 'name'])


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version', metavar='<datastore_version>',
           help='ID or name of the datastore version.')
@utils.service_type('database')
def do_datastore_version_show(cs, args):
    """Shows details of a datastore version."""
    if args.datastore:
        datastore_version = cs.datastore_versions.get(args.datastore,
                                                      args.datastore_version)
    elif utils.is_uuid_like(args.datastore_version):
        datastore_version = cs.datastore_versions.get_by_uuid(
            args.datastore_version)
    else:
        raise exceptions.NoUniqueMatch('The datastore name or id is required'
                                       ' to retrieve a datastore version'
                                       ' by name.')
    _print_object(datastore_version)


# configuration group related functions

@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('configuration',
           metavar='<configuration>',
           type=str,
           help='ID of the configuration group to attach to the instance.')
@utils.service_type('database')
def do_configuration_attach(cs, args):
    """Attaches a configuration group to an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.modify(instance, args.configuration)


@utils.arg('name', metavar='<name>', help='Name of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.arg('--datastore', metavar='<datastore>',
           help='Datastore assigned to the configuration group. Required if '
                'default datastore is not configured.')
@utils.arg('--datastore_version', metavar='<datastore_version>',
           help='Datastore version ID assigned to the configuration group.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the configuration group.')
@utils.service_type('database')
def do_configuration_create(cs, args):
    """Creates a configuration group."""
    config_grp = cs.configurations.create(
        args.name,
        args.values,
        description=args.description,
        datastore=args.datastore,
        datastore_version=args.datastore_version)
    config_grp._info['values'] = json.dumps(config_grp.values)
    _print_object(config_grp)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.service_type('database')
def do_configuration_default(cs, args):
    """Shows the default configuration of an instance."""
    instance = _find_instance(cs, args.instance)
    configs = cs.instances.configuration(instance)
    utils.print_dict(configs._info['configuration'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_delete(cs, args):
    """Deletes a configuration group."""
    cs.configurations.delete(args.configuration_group)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.service_type('database')
def do_configuration_detach(cs, args):
    """Detaches a configuration group from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.modify(instance)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore to list configuration '
                'parameters for. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='Datastore version name or ID assigned to the '
                'configuration group.')
@utils.arg('parameter', metavar='<parameter>',
           help='Name of the configuration parameter.')
@utils.service_type('database')
def do_configuration_parameter_show(cs, args):
    """Shows details of a configuration parameter."""
    if args.datastore:
        param = cs.configuration_parameters.get_parameter(
            args.datastore,
            args.datastore_version,
            args.parameter)
    elif utils.is_uuid_like(args.datastore_version):
        param = cs.configuration_parameters.get_parameter_by_version(
            args.datastore_version,
            args.parameter)
    _print_object(param)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore to list configuration '
                'parameters for. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='Datastore version name or ID assigned to the '
                'configuration group.')
@utils.service_type('database')
def do_configuration_parameter_list(cs, args):
    """Lists available parameters for a configuration group."""
    if args.datastore:
        params = cs.configuration_parameters.parameters(
            args.datastore,
            args.datastore_version)
    elif utils.is_uuid_like(args.datastore_version):
        params = cs.configuration_parameters.parameters_by_version(
            args.datastore_version)
    else:
        raise exceptions.NoUniqueMatch('The datastore name or id is required'
                                       ' to retrieve the parameters for the'
                                       ' configuration group by name.')
    utils.print_list(params, ['name', 'type', 'min_size', 'max_size',
                              'restart_required'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.service_type('database')
def do_configuration_patch(cs, args):
    """Patches a configuration group."""
    cs.configurations.edit(args.configuration_group,
                           args.values)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_instances(cs, args):
    """Lists all instances associated with a configuration group."""
    params = cs.configurations.instances(args.configuration_group)
    utils.print_list(params, ['id', 'name'])


@utils.service_type('database')
def do_configuration_list(cs, args):
    """Lists all configuration groups."""
    config_grps = cs.configurations.list()
    utils.print_list(config_grps, [
        'id', 'name', 'description',
        'datastore_name', 'datastore_version_name'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_show(cs, args):
    """Shows details of a configuration group."""
    config_grp = cs.configurations.get(args.configuration_group)
    config_grp._info['values'] = json.dumps(config_grp.values)

    del config_grp._info['datastore_version_id']
    _print_object(config_grp)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.arg('--name', metavar='<name>', default=None,
           help='Name of the configuration group.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the configuration group.')
@utils.service_type('database')
def do_configuration_update(cs, args):
    """Updates a configuration group."""
    cs.configurations.update(args.configuration_group,
                             args.values,
                             args.name,
                             args.description)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.service_type('database')
def do_metadata_list(cs, args):
    """Shows all metadata for instance <id>."""
    result = cs.metadata.list(args.instance_id)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.arg('key', metavar='<key>', help='key to display')
@utils.service_type('database')
def do_metadata_show(cs, args):
    """Shows metadata entry for key <key> and instance <id>."""
    result = cs.metadata.show(args.instance_id, args.key)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.arg('key', metavar='<key>', help='Key to replace')
@utils.arg('value', metavar='<value>',
           help='New value to assign to <key>')
@utils.service_type('database')
def do_metadata_edit(cs, args):
    """Replaces metadata value with a new one, this is non-destructive."""
    cs.metadata.edit(args.instance_id, args.key, args.value)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.arg('key', metavar='<key>', help='Key to update')
@utils.arg('newkey', metavar='<newkey>', help='New key')
@utils.arg('value', metavar='<value>', help='Value to assign to <newkey>')
@utils.service_type('database')
def do_metadata_update(cs, args):
    """Updates metadata, this is destructive."""
    cs.metadata.update(args.instance_id, args.key, args.newkey, args.value)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.arg('key', metavar='<key>', help='Key for assignment')
@utils.arg('value', metavar='<value>', help='Value to assign to <key>')
@utils.service_type('database')
def do_metadata_create(cs, args):
    """Creates metadata in the database for instance <id>."""
    result = cs.metadata.create(args.instance_id, args.key, args.value)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance')
@utils.arg('key', metavar='<key>', help='Metadata key to delete')
@utils.service_type('database')
def do_metadata_delete(cs, args):
    """Deletes metadata for instance <id>."""
    cs.metadata.delete(args.instance_id, args.key)


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='Name of the datastore configuration parameter.')
# @utils.arg('restart_required', metavar='<restart_required>',
#            help='Flags the instance to require a restart if this '
#                 'configuration parameter is new or changed.')
# @utils.arg('data_type', metavar='<data_type>',
#            help='Data type of the datastore configuration parameter.')
# @utils.arg('--max_size', metavar='<max_size>',
#            help='Maximum size of the datastore configuration parameter.')
# @utils.arg('--min_size', metavar='<min_size>',
#            help='Minimum size of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_create(cs, args):
#     """Create datastore configuration parameter"""
#     cs.mgmt_config_params.create(
#         args.datastore_version,
#         args.name,
#         args.restart_required,
#         args.data_type,
#         args.max_size,
#         args.min_size,
#     )


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='Name of the datastore configuration parameter.')
# @utils.arg('restart_required', metavar='<restart_required>',
#            help='Sets the datastore configuration parameter if it '
#                 'requires a restart or not.')
# @utils.arg('data_type', metavar='<data_type>',
#            help='Data type of the datastore configuration parameter.')
# @utils.arg('--max_size', metavar='<max_size>',
#            help='Maximum size of the datastore configuration parameter.')
# @utils.arg('--min_size', metavar='<min_size>',
#            help='Minimum size of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_modify(cs, args):
#     """Modify datastore configuration parameter"""
#     cs.mgmt_config_params.modify(
#         args.datastore_version,
#         args.name,
#         args.restart_required,
#         args.data_type,
#         args.max_size,
#         args.min_size,
#     )


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='UUID of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_delete(cs, args):
#     """Modify datastore configuration parameter"""
#     cs.mgmt_config_params.delete(
#         args.datastore_version,
#         args.name,
#     )
