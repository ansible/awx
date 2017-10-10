# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import logging
from optparse import make_option
import os
import re
import subprocess
import sys
import time
import traceback
import shutil

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.utils.encoding import smart_text

# AWX
from awx.main.models import * # noqa
from awx.main.utils import (
    ignore_inventory_computed_fields,
    check_proot_installed,
    wrap_args_with_proot,
    build_proot_temp_dir,
    get_licenser
)
from awx.main.utils.mem_inventory import MemInventory, dict_to_mem_data
from awx.main.signals import disable_activity_stream

logger = logging.getLogger('awx.main.commands.inventory_import')

LICENSE_EXPIRED_MESSAGE = '''\
License expired.
See http://www.ansible.com/renew for license extension information.'''

LICENSE_NON_EXISTANT_MESSAGE = '''\
No license.
See http://www.ansible.com/renew for license information.'''

LICENSE_MESSAGE = '''\
Number of licensed instances exceeded, would bring available instances to %(new_count)d, system is licensed for %(available_instances)d.
See http://www.ansible.com/renew for license extension information.'''

DEMO_LICENSE_MESSAGE = '''\
Demo mode free license count exceeded, would bring available instances to %(new_count)d, demo mode allows %(available_instances)d.
See http://www.ansible.com/renew for licensing information.'''


def functioning_dir(path):
    if os.path.isdir(path):
        return path
    return os.path.dirname(path)


class AnsibleInventoryLoader(object):
    '''
    Given executable `source` (directory, executable, or file) this will
    use the ansible-inventory CLI utility to convert it into in-memory
    representational objects. Example:
        /usr/bin/ansible/ansible-inventory -i hosts --list
    If it fails to find this, it uses the backported script instead
    '''

    def __init__(self, source, group_filter_re=None, host_filter_re=None, is_custom=False):
        self.source = source
        self.source_dir = functioning_dir(self.source)
        self.is_custom = is_custom
        self.tmp_private_dir = None
        self.method = 'ansible-inventory'
        self.group_filter_re = group_filter_re
        self.host_filter_re = host_filter_re

        self.is_vendored_source = False
        if self.source_dir == os.path.join(settings.BASE_DIR, 'plugins', 'inventory'):
            self.is_vendored_source = True

    def build_env(self):
        env = dict(os.environ.items())
        env['VIRTUAL_ENV'] = settings.ANSIBLE_VENV_PATH
        env['PATH'] = os.path.join(settings.ANSIBLE_VENV_PATH, "bin") + ":" + env['PATH']
        env['ANSIBLE_INVENTORY_UNPARSED_FAILED'] = '1'
        venv_libdir = os.path.join(settings.ANSIBLE_VENV_PATH, "lib")
        env.pop('PYTHONPATH', None)  # default to none if no python_ver matches
        for python_ver in ["python2.7", "python2.6"]:
            if os.path.isdir(os.path.join(venv_libdir, python_ver)):
                env['PYTHONPATH'] = os.path.join(venv_libdir, python_ver, "site-packages") + ":"
                break
        return env

    def get_base_args(self):
        # get ansible-inventory absolute path for running in bubblewrap/proot, in Popen
        for path in os.environ["PATH"].split(os.pathsep):
            potential_path = os.path.join(path.strip('"'), 'ansible-inventory')
            if os.path.isfile(potential_path) and os.access(potential_path, os.X_OK):
                logger.debug('Using system install of ansible-inventory CLI: {}'.format(potential_path))
                return [potential_path, '-i', self.source]

        # Stopgap solution for group_vars, do not use backported module for official
        # vendored cloud modules or custom scripts TODO: remove after Ansible 2.3 deprecation
        if self.is_vendored_source or self.is_custom:
            self.method = 'inventory script invocation'
            return [self.source]

        # ansible-inventory was not found, look for backported module TODO: remove after Ansible 2.3 deprecation
        abs_module_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'plugins',
            'ansible_inventory', 'backport.py'))
        self.method = 'ansible-inventory backport'

        if not os.path.exists(abs_module_path):
            raise ImproperlyConfigured('Cannot find inventory module')
        logger.debug('Using backported ansible-inventory module: {}'.format(abs_module_path))
        return [abs_module_path, '-i', self.source]

    def get_proot_args(self, cmd, env):
        cwd = os.getcwd()
        if not check_proot_installed():
            raise RuntimeError("proot is not installed but is configured for use")

        kwargs = {}
        if self.is_custom:
            # use source's tmp dir for proot, task manager will delete folder
            logger.debug("Using provided directory '{}' for isolation.".format(self.source_dir))
            kwargs['proot_temp_dir'] = self.source_dir
            cwd = self.source_dir
        else:
            # we cannot safely store tmp data in source dir or trust script contents
            if env['AWX_PRIVATE_DATA_DIR']:
                # If this is non-blank, file credentials are being used and we need access
                private_data_dir = functioning_dir(env['AWX_PRIVATE_DATA_DIR'])
                logger.debug("Using private credential data in '{}'.".format(private_data_dir))
                kwargs['private_data_dir'] = private_data_dir
            self.tmp_private_dir = build_proot_temp_dir()
            logger.debug("Using fresh temporary directory '{}' for isolation.".format(self.tmp_private_dir))
            kwargs['proot_temp_dir'] = self.tmp_private_dir
            # Run from source's location so that custom script contents are in `show_paths`
            cwd = functioning_dir(self.source)
        logger.debug("Running from `{}` working directory.".format(cwd))

        return wrap_args_with_proot(cmd, cwd, **kwargs)

    def command_to_json(self, cmd):
        data = {}
        stdout, stderr = '', ''
        env = self.build_env()

        if ((self.is_custom or 'AWX_PRIVATE_DATA_DIR' in env) and
                getattr(settings, 'AWX_PROOT_ENABLED', False)):
            cmd = self.get_proot_args(cmd, env)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate()

        if self.tmp_private_dir:
            shutil.rmtree(self.tmp_private_dir, True)
        if proc.returncode != 0 or 'file not found' in stderr:
            raise RuntimeError('%s failed (rc=%d) with stdout:\n%s\nstderr:\n%s' % (
                self.method, proc.returncode, stdout, stderr))

        for line in stderr.splitlines():
            logger.error(line)
        try:
            data = json.loads(stdout)
            if not isinstance(data, dict):
                raise TypeError('Returned JSON must be a dictionary, got %s instead' % str(type(data)))
        except:
            logger.error('Failed to load JSON from: %s', stdout)
            raise
        return data

    def load(self):
        base_args = self.get_base_args()
        logger.info('Reading Ansible inventory source: %s', self.source)
        data = self.command_to_json(base_args + ['--list'])

        # TODO: remove after we run custom scripts through ansible-inventory
        if self.is_custom and '_meta' not in data or 'hostvars' not in data['_meta']:
            # Invoke the executable once for each host name we've built up
            # to set their variables
            data.setdefault('_meta', {})
            data['_meta'].setdefault('hostvars', {})
            logger.warning('Re-calling script for hostvars individually.')
            for group_name, group_data in data.iteritems():
                if group_name == '_meta':
                    continue

                if isinstance(group_data, dict):
                    group_host_list = group_data.get('hosts', [])
                elif isinstance(group_data, list):
                    group_host_list = group_data
                else:
                    logger.warning('Group data for "%s" is not a dict or list',
                                   group_name)
                    group_host_list = []

                for hostname in group_host_list:
                    logger.debug('Obtaining hostvars for %s' % hostname.encode('utf-8'))
                    hostdata = self.command_to_json(
                        base_args + ['--host', hostname.encode("utf-8")]
                    )
                    if isinstance(hostdata, dict):
                        data['_meta']['hostvars'][hostname] = hostdata
                    else:
                        logger.warning(
                            'Expected dict of vars for host "%s" when '
                            'calling with `--host`, got %s instead',
                            k, str(type(data))
                        )

        logger.info('Processing JSON output...')
        inventory = MemInventory(
            group_filter_re=self.group_filter_re, host_filter_re=self.host_filter_re)
        inventory = dict_to_mem_data(data, inventory=inventory)

        return inventory


def load_inventory_source(source, group_filter_re=None,
                          host_filter_re=None, exclude_empty_groups=False,
                          is_custom=False):
    '''
    Load inventory from given source directory or file.
    '''
    # Sanity check: We sanitize these module names for our API but Ansible proper doesn't follow
    # good naming conventions
    source = source.replace('satellite6.py', 'foreman.py')
    source = source.replace('vmware.py', 'vmware_inventory.py')
    if not os.path.exists(source):
        raise IOError('Source does not exist: %s' % source)
    source = os.path.join(os.getcwd(), os.path.dirname(source),
                          os.path.basename(source))
    source = os.path.normpath(os.path.abspath(source))

    inventory = AnsibleInventoryLoader(
        source=source,
        group_filter_re=group_filter_re,
        host_filter_re=host_filter_re,
        is_custom=is_custom).load()

    logger.debug('Finished loading from source: %s', source)
    # Exclude groups that are completely empty.
    if exclude_empty_groups:
        inventory.delete_empty_groups()
    logger.info('Loaded %d groups, %d hosts', len(inventory.all_group.all_groups),
                len(inventory.all_group.all_hosts))
    return inventory.all_group


class Command(NoArgsCommand):
    '''
    Management command to import inventory from a directory, ini file, or
    dynamic inventory script.
    '''

    help = 'Import or sync external inventory sources'

    option_list = NoArgsCommand.option_list + (
        make_option('--inventory-name', dest='inventory_name', type='str',
                    default=None, metavar='n',
                    help='name of inventory to sync'),
        make_option('--inventory-id', dest='inventory_id', type='int',
                    default=None, metavar='i', help='id of inventory to sync'),
        make_option('--overwrite', dest='overwrite', action='store_true',
                    metavar="o", default=False,
                    help='overwrite the destination hosts and groups'),
        make_option('--overwrite-vars', dest='overwrite_vars',
                    action='store_true', metavar="V", default=False,
                    help='overwrite (rather than merge) variables'),
        make_option('--keep-vars', dest='keep_vars', action='store_true',
                    metavar="k", default=False,
                    help='use database variables if set'),
        make_option('--custom', dest='custom', action='store_true',
                    metavar="c", default=False,
                    help='this is a custom inventory script'),
        make_option('--source', dest='source', type='str', default=None,
                    metavar='s', help='inventory directory, file, or script '
                    'to load'),
        make_option('--enabled-var', dest='enabled_var', type='str',
                    default=None, metavar='v', help='host variable used to '
                    'set/clear enabled flag when host is online/offline, may '
                    'be specified as "foo.bar" to traverse nested dicts.'),
        make_option('--enabled-value', dest='enabled_value', type='str',
                    default=None, metavar='v', help='value of host variable '
                    'specified by --enabled-var that indicates host is '
                    'enabled/online.'),
        make_option('--group-filter', dest='group_filter', type='str',
                    default=None, metavar='regex', help='regular expression '
                    'to filter group name(s); only matches are imported.'),
        make_option('--host-filter', dest='host_filter', type='str',
                    default=None, metavar='regex', help='regular expression '
                    'to filter host name(s); only matches are imported.'),
        make_option('--exclude-empty-groups', dest='exclude_empty_groups',
                    action='store_true', default=False, help='when set, '
                    'exclude all groups that have no child groups, hosts, or '
                    'variables.'),
        make_option('--instance-id-var', dest='instance_id_var', type='str',
                    default=None, metavar='v', help='host variable that '
                    'specifies the unique, immutable instance ID, may be '
                    'specified as "foo.bar" to traverse nested dicts.'),
    )

    def set_logging_level(self):
        log_levels = dict(enumerate([logging.WARNING, logging.INFO,
                                     logging.DEBUG, 0]))
        logger.setLevel(log_levels.get(self.verbosity, 0))

    def _get_instance_id(self, from_dict, default=''):
        '''
        Retrieve the instance ID from the given dict of host variables.

        The instance ID variable may be specified as 'foo.bar', in which case
        the lookup will traverse into nested dicts, equivalent to:

        from_dict.get('foo', {}).get('bar', default)
        '''
        instance_id = default
        if getattr(self, 'instance_id_var', None):
            for key in self.instance_id_var.split('.'):
                if not hasattr(from_dict, 'get'):
                    instance_id = default
                    break
                instance_id = from_dict.get(key, default)
                from_dict = instance_id
        return smart_text(instance_id)

    def _get_enabled(self, from_dict, default=None):
        '''
        Retrieve the enabled state from the given dict of host variables.

        The enabled variable may be specified as 'foo.bar', in which case
        the lookup will traverse into nested dicts, equivalent to:

        from_dict.get('foo', {}).get('bar', default)
        '''
        enabled = default
        if getattr(self, 'enabled_var', None):
            default = object()
            for key in self.enabled_var.split('.'):
                if not hasattr(from_dict, 'get'):
                    enabled = default
                    break
                enabled = from_dict.get(key, default)
                from_dict = enabled
            if enabled is not default:
                enabled_value = getattr(self, 'enabled_value', None)
                if enabled_value is not None:
                    enabled = bool(unicode(enabled_value) == unicode(enabled))
                else:
                    enabled = bool(enabled)
        return enabled

    def load_inventory_from_database(self):
        '''
        Load inventory and related objects from the database.
        '''
        # Load inventory object based on name or ID.
        if self.inventory_id:
            q = dict(id=self.inventory_id)
        else:
            q = dict(name=self.inventory_name)
        try:
            self.inventory = Inventory.objects.get(**q)
        except Inventory.DoesNotExist:
            raise CommandError('Inventory with %s = %s cannot be found' % q.items()[0])
        except Inventory.MultipleObjectsReturned:
            raise CommandError('Inventory with %s = %s returned multiple results' % q.items()[0])
        logger.info('Updating inventory %d: %s' % (self.inventory.pk,
                                                   self.inventory.name))

        # Load inventory source if specified via environment variable (when
        # inventory_import is called from an InventoryUpdate task).
        inventory_source_id = os.getenv('INVENTORY_SOURCE_ID', None)
        inventory_update_id = os.getenv('INVENTORY_UPDATE_ID', None)
        if inventory_source_id:
            try:
                self.inventory_source = InventorySource.objects.get(pk=inventory_source_id,
                                                                    inventory=self.inventory)
            except InventorySource.DoesNotExist:
                raise CommandError('Inventory source with id=%s not found' %
                                   inventory_source_id)
            try:
                self.inventory_update = InventoryUpdate.objects.get(pk=inventory_update_id)
            except InventoryUpdate.DoesNotExist:
                raise CommandError('Inventory update with id=%s not found' %
                                   inventory_update_id)
        # Otherwise, create a new inventory source to capture this invocation
        # via command line.
        else:
            with ignore_inventory_computed_fields():
                self.inventory_source, created = InventorySource.objects.get_or_create(
                    inventory=self.inventory,
                    source='file',
                    source_path=os.path.abspath(self.source),
                    overwrite=self.overwrite,
                    overwrite_vars=self.overwrite_vars,
                )
                self.inventory_update = self.inventory_source.create_inventory_update(
                    job_args=json.dumps(sys.argv),
                    job_env=dict(os.environ.items()),
                    job_cwd=os.getcwd(),
                    _eager_fields=dict(
                        execution_node=settings.CLUSTER_HOST_ID,
                        instance_group=InstanceGroup.objects.get(name='tower'))
                )

        # FIXME: Wait or raise error if inventory is being updated by another
        # source.

    def _batch_add_m2m(self, related_manager, *objs, **kwargs):
        key = (related_manager.instance.pk, related_manager.through._meta.db_table)
        flush = bool(kwargs.get('flush', False))
        if not hasattr(self, '_batch_add_m2m_cache'):
            self._batch_add_m2m_cache = {}
        cached_objs = self._batch_add_m2m_cache.setdefault(key, [])
        cached_objs.extend(objs)
        if len(cached_objs) > self._batch_size or flush:
            if len(cached_objs):
                related_manager.add(*cached_objs)
            self._batch_add_m2m_cache[key] = []

    def _build_db_instance_id_map(self):
        '''
        Find any hosts in the database without an instance_id set that may
        still have one available via host variables.
        '''
        self.db_instance_id_map = {}
        if self.instance_id_var:
            host_qs = self.inventory_source.hosts.all()
            host_qs = host_qs.filter(instance_id='',
                                     variables__contains=self.instance_id_var.split('.')[0])
            for host in host_qs:
                instance_id = self._get_instance_id(host.variables_dict)
                if not instance_id:
                    continue
                self.db_instance_id_map[instance_id] = host.pk

    def _build_mem_instance_id_map(self):
        '''
        Update instance ID for each imported host and define a mapping of
        instance IDs to MemHost instances.
        '''
        self.mem_instance_id_map = {}
        if self.instance_id_var:
            for mem_host in self.all_group.all_hosts.values():
                instance_id = self._get_instance_id(mem_host.variables)
                if not instance_id:
                    logger.warning('Host "%s" has no "%s" variable',
                                   mem_host.name, self.instance_id_var)
                    continue
                mem_host.instance_id = instance_id
                self.mem_instance_id_map[instance_id] = mem_host.name

    def _delete_hosts(self):
        '''
        For each host in the database that is NOT in the local list, delete
        it. When importing from a cloud inventory source attached to a
        specific group, only delete hosts beneath that group.  Delete each
        host individually so signal handlers will run.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        hosts_qs = self.inventory_source.hosts
        # Build list of all host pks, remove all that should not be deleted.
        del_host_pks = set(hosts_qs.values_list('pk', flat=True))
        if self.instance_id_var:
            all_instance_ids = self.mem_instance_id_map.keys()
            instance_ids = []
            for offset in xrange(0, len(all_instance_ids), self._batch_size):
                instance_ids = all_instance_ids[offset:(offset + self._batch_size)]
                for host_pk in hosts_qs.filter(instance_id__in=instance_ids).values_list('pk', flat=True):
                    del_host_pks.discard(host_pk)
            for host_pk in set([v for k,v in self.db_instance_id_map.items() if k in instance_ids]):
                del_host_pks.discard(host_pk)
            all_host_names = list(set(self.mem_instance_id_map.values()) - set(self.all_group.all_hosts.keys()))
        else:
            all_host_names = self.all_group.all_hosts.keys()
        for offset in xrange(0, len(all_host_names), self._batch_size):
            host_names = all_host_names[offset:(offset + self._batch_size)]
            for host_pk in hosts_qs.filter(name__in=host_names).values_list('pk', flat=True):
                del_host_pks.discard(host_pk)
        # Now delete all remaining hosts in batches.
        all_del_pks = sorted(list(del_host_pks))
        for offset in xrange(0, len(all_del_pks), self._batch_size):
            del_pks = all_del_pks[offset:(offset + self._batch_size)]
            for host in hosts_qs.filter(pk__in=del_pks):
                host_name = host.name
                host.delete()
                logger.info('Deleted host "%s"', host_name)
        if settings.SQL_DEBUG:
            logger.warning('host deletions took %d queries for %d hosts',
                           len(connection.queries) - queries_before,
                           len(all_del_pks))

    def _delete_groups(self):
        '''
        # If overwrite is set, for each group in the database that is NOT in
        # the local list, delete it. When importing from a cloud inventory
        # source attached to a specific group, only delete children of that
        # group.  Delete each group individually so signal handlers will run.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        groups_qs = self.inventory_source.groups.all()
        # Build list of all group pks, remove those that should not be deleted.
        del_group_pks = set(groups_qs.values_list('pk', flat=True))
        all_group_names = self.all_group.all_groups.keys()
        for offset in xrange(0, len(all_group_names), self._batch_size):
            group_names = all_group_names[offset:(offset + self._batch_size)]
            for group_pk in groups_qs.filter(name__in=group_names).values_list('pk', flat=True):
                del_group_pks.discard(group_pk)
        if self.inventory_source.deprecated_group_id in del_group_pks:  # TODO: remove in 3.3
            logger.warning(
                'Group "%s" from v1 API is not deleted by overwrite',
                self.inventory_source.deprecated_group.name
            )
            del_group_pks.discard(self.inventory_source.deprecated_group_id)
        # Now delete all remaining groups in batches.
        all_del_pks = sorted(list(del_group_pks))
        for offset in xrange(0, len(all_del_pks), self._batch_size):
            del_pks = all_del_pks[offset:(offset + self._batch_size)]
            for group in groups_qs.filter(pk__in=del_pks):
                group_name = group.name
                with ignore_inventory_computed_fields():
                    group.delete()
                logger.info('Group "%s" deleted', group_name)
        if settings.SQL_DEBUG:
            logger.warning('group deletions took %d queries for %d groups',
                           len(connection.queries) - queries_before,
                           len(all_del_pks))

    def _delete_group_children_and_hosts(self):
        '''
        Clear all invalid child relationships for groups and all invalid host
        memberships.  When importing from a cloud inventory source attached to
        a specific group, only clear relationships for hosts and groups that
        are beneath the inventory source group.
        '''
        # FIXME: Optimize performance!
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        group_group_count = 0
        group_host_count = 0
        db_groups = self.inventory_source.groups
        for db_group in db_groups.all():
            if self.inventory_source.deprecated_group_id == db_group.id:  # TODO: remove in 3.3
                logger.info(
                    'Group "%s" from v1 API child group/host connections preserved',
                    db_group.name
                )
                continue
            # Delete child group relationships not present in imported data.
            db_children = db_group.children
            db_children_name_pk_map = dict(db_children.values_list('name', 'pk'))
            mem_children = self.all_group.all_groups[db_group.name].children
            for mem_group in mem_children:
                db_children_name_pk_map.pop(mem_group.name, None)
            del_child_group_pks = list(set(db_children_name_pk_map.values()))
            for offset in xrange(0, len(del_child_group_pks), self._batch_size):
                child_group_pks = del_child_group_pks[offset:(offset + self._batch_size)]
                for db_child in db_children.filter(pk__in=child_group_pks):
                    group_group_count += 1
                    db_group.children.remove(db_child)
                    logger.info('Group "%s" removed from group "%s"',
                                db_child.name, db_group.name)
            # FIXME: Inventory source group relationships
            # Delete group/host relationships not present in imported data.
            db_hosts = db_group.hosts
            del_host_pks = set(db_hosts.values_list('pk', flat=True))
            mem_hosts = self.all_group.all_groups[db_group.name].hosts
            all_mem_host_names = [h.name for h in mem_hosts if not h.instance_id]
            for offset in xrange(0, len(all_mem_host_names), self._batch_size):
                mem_host_names = all_mem_host_names[offset:(offset + self._batch_size)]
                for db_host_pk in db_hosts.filter(name__in=mem_host_names).values_list('pk', flat=True):
                    del_host_pks.discard(db_host_pk)
            all_mem_instance_ids = [h.instance_id for h in mem_hosts if h.instance_id]
            for offset in xrange(0, len(all_mem_instance_ids), self._batch_size):
                mem_instance_ids = all_mem_instance_ids[offset:(offset + self._batch_size)]
                for db_host_pk in db_hosts.filter(instance_id__in=mem_instance_ids).values_list('pk', flat=True):
                    del_host_pks.discard(db_host_pk)
            all_db_host_pks = [v for k,v in self.db_instance_id_map.items() if k in all_mem_instance_ids]
            for db_host_pk in all_db_host_pks:
                del_host_pks.discard(db_host_pk)
            del_host_pks = list(del_host_pks)
            for offset in xrange(0, len(del_host_pks), self._batch_size):
                del_pks = del_host_pks[offset:(offset + self._batch_size)]
                for db_host in db_hosts.filter(pk__in=del_pks):
                    group_host_count += 1
                    if db_host not in db_group.hosts.all():
                        continue
                    db_group.hosts.remove(db_host)
                    logger.info('Host "%s" removed from group "%s"',
                                db_host.name, db_group.name)
        if settings.SQL_DEBUG:
            logger.warning('group-group and group-host deletions took %d queries for %d relationships',
                           len(connection.queries) - queries_before,
                           group_group_count + group_host_count)

    def _update_inventory(self):
        '''
        Update/overwrite variables from "all" group.  If importing from a
        cloud source attached to a specific group, variables will be set on
        the base group, otherwise they will be set on the whole inventory.
        '''
        # FIXME: figure out how "all" variables are handled in the new inventory source system
        all_obj = self.inventory
        all_name = 'inventory'
        db_variables = all_obj.variables_dict
        if self.overwrite_vars:
            db_variables = self.all_group.variables
        else:
            db_variables.update(self.all_group.variables)
        if db_variables != all_obj.variables_dict:
            all_obj.variables = json.dumps(db_variables)
            all_obj.save(update_fields=['variables'])
            if self.overwrite_vars:
                logger.info('%s variables replaced from "all" group', all_name.capitalize())
            else:
                logger.info('%s variables updated from "all" group', all_name.capitalize())
        else:
            logger.info('%s variables unmodified', all_name.capitalize())

    def _create_update_groups(self):
        '''
        For each group in the local list, create it if it doesn't exist in the
        database.  Otherwise, update/replace database variables from the
        imported data.  Associate with the inventory source group if importing
        from cloud inventory source.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        all_group_names = sorted(self.all_group.all_groups.keys())
        root_group_names = set()
        for k,v in self.all_group.all_groups.items():
            if not v.parents:
                root_group_names.add(k)
            if len(v.parents) == 1 and v.parents[0].name == 'all':
                root_group_names.add(k)
        existing_group_names = set()
        for offset in xrange(0, len(all_group_names), self._batch_size):
            group_names = all_group_names[offset:(offset + self._batch_size)]
            for group in self.inventory.groups.filter(name__in=group_names):
                mem_group = self.all_group.all_groups[group.name]
                db_variables = group.variables_dict
                if self.overwrite_vars:
                    db_variables = mem_group.variables
                else:
                    db_variables.update(mem_group.variables)
                if db_variables != group.variables_dict:
                    group.variables = json.dumps(db_variables)
                    group.save(update_fields=['variables'])
                    if self.overwrite_vars:
                        logger.info('Group "%s" variables replaced', group.name)
                    else:
                        logger.info('Group "%s" variables updated', group.name)
                else:
                    logger.info('Group "%s" variables unmodified', group.name)
                existing_group_names.add(group.name)
                self._batch_add_m2m(self.inventory_source.groups, group)
        for group_name in all_group_names:
            if group_name in existing_group_names:
                continue
            mem_group = self.all_group.all_groups[group_name]
            group = self.inventory.groups.update_or_create(
                name=group_name,
                defaults={
                    'variables':json.dumps(mem_group.variables),
                    'description':'imported'
                }
            )[0]
            logger.info('Group "%s" added', group.name)
            self._batch_add_m2m(self.inventory_source.groups, group)
        self._batch_add_m2m(self.inventory_source.groups, flush=True)
        if settings.SQL_DEBUG:
            logger.warning('group updates took %d queries for %d groups',
                           len(connection.queries) - queries_before,
                           len(self.all_group.all_groups))

    def _update_db_host_from_mem_host(self, db_host, mem_host):
        # Update host variables.
        db_variables = db_host.variables_dict
        if self.overwrite_vars:
            db_variables = mem_host.variables
        else:
            db_variables.update(mem_host.variables)
        update_fields = []
        if db_variables != db_host.variables_dict:
            db_host.variables = json.dumps(db_variables)
            update_fields.append('variables')
        # Update host enabled flag.
        enabled = self._get_enabled(mem_host.variables)
        if enabled is not None and db_host.enabled != enabled:
            db_host.enabled = enabled
            update_fields.append('enabled')
        # Update host name.
        if mem_host.name != db_host.name:
            old_name = db_host.name
            db_host.name = mem_host.name
            update_fields.append('name')
        # Update host instance_id.
        instance_id = self._get_instance_id(mem_host.variables)
        if instance_id != db_host.instance_id:
            old_instance_id = db_host.instance_id
            db_host.instance_id = instance_id
            update_fields.append('instance_id')
        # Update host and display message(s) on what changed.
        if update_fields:
            db_host.save(update_fields=update_fields)
        if 'name' in update_fields:
            logger.info('Host renamed from "%s" to "%s"', old_name, mem_host.name)
        if 'instance_id' in update_fields:
            if old_instance_id:
                logger.info('Host "%s" instance_id updated', mem_host.name)
            else:
                logger.info('Host "%s" instance_id added', mem_host.name)
        if 'variables' in update_fields:
            if self.overwrite_vars:
                logger.info('Host "%s" variables replaced', mem_host.name)
            else:
                logger.info('Host "%s" variables updated', mem_host.name)
        else:
            logger.info('Host "%s" variables unmodified', mem_host.name)
        if 'enabled' in update_fields:
            if enabled:
                logger.info('Host "%s" is now enabled', mem_host.name)
            else:
                logger.info('Host "%s" is now disabled', mem_host.name)
        self._batch_add_m2m(self.inventory_source.hosts, db_host)

    def _create_update_hosts(self):
        '''
        For each host in the local list, create it if it doesn't exist in the
        database.  Otherwise, update/replace database variables from the
        imported data.  Associate with the inventory source group if importing
        from cloud inventory source.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        host_pks_updated = set()
        mem_host_pk_map = {}
        mem_host_instance_id_map = {}
        mem_host_name_map = {}
        mem_host_names_to_update = set(self.all_group.all_hosts.keys())
        for k,v in self.all_group.all_hosts.iteritems():
            mem_host_name_map[k] = v
            instance_id = self._get_instance_id(v.variables)
            if instance_id in self.db_instance_id_map:
                mem_host_pk_map[self.db_instance_id_map[instance_id]] = v
            elif instance_id:
                mem_host_instance_id_map[instance_id] = v

        # Update all existing hosts where we know the PK based on instance_id.
        all_host_pks = sorted(mem_host_pk_map.keys())
        for offset in xrange(0, len(all_host_pks), self._batch_size):
            host_pks = all_host_pks[offset:(offset + self._batch_size)]
            for db_host in self.inventory.hosts.filter( pk__in=host_pks):
                if db_host.pk in host_pks_updated:
                    continue
                mem_host = mem_host_pk_map[db_host.pk]
                self._update_db_host_from_mem_host(db_host, mem_host)
                host_pks_updated.add(db_host.pk)
                mem_host_names_to_update.discard(mem_host.name)

        # Update all existing hosts where we know the instance_id.
        all_instance_ids = sorted(mem_host_instance_id_map.keys())
        for offset in xrange(0, len(all_instance_ids), self._batch_size):
            instance_ids = all_instance_ids[offset:(offset + self._batch_size)]
            for db_host in self.inventory.hosts.filter( instance_id__in=instance_ids):
                if db_host.pk in host_pks_updated:
                    continue
                mem_host = mem_host_instance_id_map[db_host.instance_id]
                self._update_db_host_from_mem_host(db_host, mem_host)
                host_pks_updated.add(db_host.pk)
                mem_host_names_to_update.discard(mem_host.name)

        # Update all existing hosts by name.
        all_host_names = sorted(mem_host_name_map.keys())
        for offset in xrange(0, len(all_host_names), self._batch_size):
            host_names = all_host_names[offset:(offset + self._batch_size)]
            for db_host in self.inventory.hosts.filter( name__in=host_names):
                if db_host.pk in host_pks_updated:
                    continue
                mem_host = mem_host_name_map[db_host.name]
                self._update_db_host_from_mem_host(db_host, mem_host)
                host_pks_updated.add(db_host.pk)
                mem_host_names_to_update.discard(mem_host.name)

        # Create any new hosts.
        for mem_host_name in sorted(mem_host_names_to_update):
            mem_host = self.all_group.all_hosts[mem_host_name]
            host_attrs = dict(variables=json.dumps(mem_host.variables),
                              description='imported')
            enabled = self._get_enabled(mem_host.variables)
            if enabled is not None:
                host_attrs['enabled'] = enabled
            if self.instance_id_var:
                instance_id = self._get_instance_id(mem_host.variables)
                host_attrs['instance_id'] = instance_id
            db_host = self.inventory.hosts.update_or_create(name=mem_host_name, defaults=host_attrs)[0]
            if enabled is False:
                logger.info('Host "%s" added (disabled)', mem_host_name)
            else:
                logger.info('Host "%s" added', mem_host_name)
            self._batch_add_m2m(self.inventory_source.hosts, db_host)

        self._batch_add_m2m(self.inventory_source.hosts, flush=True)

        if settings.SQL_DEBUG:
            logger.warning('host updates took %d queries for %d hosts',
                           len(connection.queries) - queries_before,
                           len(self.all_group.all_hosts))

    @transaction.atomic
    def _create_update_group_children(self):
        '''
        For each imported group, create all parent-child group relationships.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        all_group_names = sorted([k for k,v in self.all_group.all_groups.iteritems() if v.children])
        group_group_count = 0
        for offset in xrange(0, len(all_group_names), self._batch_size):
            group_names = all_group_names[offset:(offset + self._batch_size)]
            for db_group in self.inventory.groups.filter(name__in=group_names):
                mem_group = self.all_group.all_groups[db_group.name]
                group_group_count += len(mem_group.children)
                all_child_names = sorted([g.name for g in mem_group.children])
                for offset2 in xrange(0, len(all_child_names), self._batch_size):
                    child_names = all_child_names[offset2:(offset2 + self._batch_size)]
                    db_children_qs = self.inventory.groups.filter(name__in=child_names)
                    for db_child in db_children_qs.filter(children__id=db_group.id):
                        logger.info('Group "%s" already child of group "%s"', db_child.name, db_group.name)
                    for db_child in db_children_qs.exclude(children__id=db_group.id):
                        self._batch_add_m2m(db_group.children, db_child)
                    logger.info('Group "%s" added as child of "%s"', db_child.name, db_group.name)
                self._batch_add_m2m(db_group.children, flush=True)
        if settings.SQL_DEBUG:
            logger.warning('Group-group updates took %d queries for %d group-group relationships',
                           len(connection.queries) - queries_before, group_group_count)

    @transaction.atomic
    def _create_update_group_hosts(self):
        # For each host in a mem group, add it to the parent(s) to which it
        # belongs.
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        all_group_names = sorted([k for k,v in self.all_group.all_groups.iteritems() if v.hosts])
        group_host_count = 0
        for offset in xrange(0, len(all_group_names), self._batch_size):
            group_names = all_group_names[offset:(offset + self._batch_size)]
            for db_group in self.inventory.groups.filter(name__in=group_names):
                mem_group = self.all_group.all_groups[db_group.name]
                group_host_count += len(mem_group.hosts)
                all_host_names = sorted([h.name for h in mem_group.hosts if not h.instance_id])
                for offset2 in xrange(0, len(all_host_names), self._batch_size):
                    host_names = all_host_names[offset2:(offset2 + self._batch_size)]
                    db_hosts_qs = self.inventory.hosts.filter(name__in=host_names)
                    for db_host in db_hosts_qs.filter(groups__id=db_group.id):
                        logger.info('Host "%s" already in group "%s"', db_host.name, db_group.name)
                    for db_host in db_hosts_qs.exclude(groups__id=db_group.id):
                        self._batch_add_m2m(db_group.hosts, db_host)
                        logger.info('Host "%s" added to group "%s"', db_host.name, db_group.name)
                all_instance_ids = sorted([h.instance_id for h in mem_group.hosts if h.instance_id])
                for offset2 in xrange(0, len(all_instance_ids), self._batch_size):
                    instance_ids = all_instance_ids[offset2:(offset2 + self._batch_size)]
                    db_hosts_qs = self.inventory.hosts.filter(instance_id__in=instance_ids)
                    for db_host in db_hosts_qs.filter(groups__id=db_group.id):
                        logger.info('Host "%s" already in group "%s"', db_host.name, db_group.name)
                    for db_host in db_hosts_qs.exclude(groups__id=db_group.id):
                        self._batch_add_m2m(db_group.hosts, db_host)
                        logger.info('Host "%s" added to group "%s"', db_host.name, db_group.name)
                self._batch_add_m2m(db_group.hosts, flush=True)
        if settings.SQL_DEBUG:
            logger.warning('Group-host updates took %d queries for %d group-host relationships',
                           len(connection.queries) - queries_before, group_host_count)

    def load_into_database(self):
        '''
        Load inventory from in-memory groups to the database, overwriting or
        merging as appropriate.
        '''
        # FIXME: Attribute changes to superuser?
        # Perform __in queries in batches (mainly for unit tests using SQLite).
        self._batch_size = 500
        self._build_db_instance_id_map()
        self._build_mem_instance_id_map()
        if self.overwrite:
            self._delete_hosts()
            self._delete_groups()
            self._delete_group_children_and_hosts()
        self._update_inventory()
        self._create_update_groups()
        self._create_update_hosts()
        self._create_update_group_children()
        self._create_update_group_hosts()

    def check_license(self):
        license_info = get_licenser().validate()
        if license_info.get('license_key', 'UNLICENSED') == 'UNLICENSED':
            logger.error(LICENSE_NON_EXISTANT_MESSAGE)
            raise CommandError('No license found!')
        elif license_info.get('license_type', 'UNLICENSED') == 'open':
            return
        available_instances = license_info.get('available_instances', 0)
        free_instances = license_info.get('free_instances', 0)
        time_remaining = license_info.get('time_remaining', 0)
        new_count = Host.objects.active_count()
        if time_remaining <= 0 and not license_info.get('demo', False):
            logger.error(LICENSE_EXPIRED_MESSAGE)
            raise CommandError("License has expired!")
        if free_instances < 0:
            d = {
                'new_count': new_count,
                'available_instances': available_instances,
            }
            if license_info.get('demo', False):
                logger.error(DEMO_LICENSE_MESSAGE % d)
            else:
                logger.error(LICENSE_MESSAGE % d)
            raise CommandError('License count exceeded!')

    def mark_license_failure(self, save=True):
        self.inventory_update.license_error = True
        self.inventory_update.save(update_fields=['license_error'])

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.set_logging_level()
        self.inventory_name = options.get('inventory_name', None)
        self.inventory_id = options.get('inventory_id', None)
        self.overwrite = bool(options.get('overwrite', False))
        self.overwrite_vars = bool(options.get('overwrite_vars', False))
        self.keep_vars = bool(options.get('keep_vars', False))
        self.is_custom = bool(options.get('custom', False))
        self.source = options.get('source', None)
        self.enabled_var = options.get('enabled_var', None)
        self.enabled_value = options.get('enabled_value', None)
        self.group_filter = options.get('group_filter', None) or r'^.+$'
        self.host_filter = options.get('host_filter', None) or r'^.+$'
        self.exclude_empty_groups = bool(options.get('exclude_empty_groups', False))
        self.instance_id_var = options.get('instance_id_var', None)

        self.celery_invoked = False if os.getenv('INVENTORY_SOURCE_ID', None) is None else True

        # Load inventory and related objects from database.
        if self.inventory_name and self.inventory_id:
            raise CommandError('--inventory-name and --inventory-id are mutually exclusive')
        elif not self.inventory_name and not self.inventory_id:
            raise CommandError('--inventory-name or --inventory-id is required')
        if (self.overwrite or self.overwrite_vars) and self.keep_vars:
            raise CommandError('--overwrite/--overwrite-vars and --keep-vars are mutually exclusive')
        if not self.source:
            raise CommandError('--source is required')
        try:
            self.group_filter_re = re.compile(self.group_filter)
        except re.error:
            raise CommandError('invalid regular expression for --group-filter')
        try:
            self.host_filter_re = re.compile(self.host_filter)
        except re.error:
            raise CommandError('invalid regular expression for --host-filter')

        '''
        TODO: Remove this deprecation when we remove support for rax.py
        '''
        if self.source == "rax.py":
            logger.info("Rackspace inventory sync is Deprecated in Tower 3.1.0 and support for Rackspace will be removed in a future release.")

        begin = time.time()
        self.load_inventory_from_database()

        try:
            self.check_license()
        except CommandError as e:
            self.mark_license_failure(save=True)
            raise e

        status, tb, exc = 'error', '', None
        try:
            if settings.SQL_DEBUG:
                queries_before = len(connection.queries)

            # Update inventory update for this command line invocation.
            with ignore_inventory_computed_fields():
                iu = self.inventory_update
                if iu.status != 'running':
                    with transaction.atomic():
                        self.inventory_update.status = 'running'
                        self.inventory_update.save()

            # Load inventory from source.
            self.all_group = load_inventory_source(self.source,
                                                   self.group_filter_re,
                                                   self.host_filter_re,
                                                   self.exclude_empty_groups,
                                                   self.is_custom)
            if settings.DEBUG:
                # depending on inventory source, this output can be
                # *exceedingly* verbose - crawling a deeply nested
                # inventory/group data structure and printing metadata about
                # each host and its memberships
                #
                # it's easy for this scale of data to overwhelm pexpect,
                # (and it's likely only useful for purposes of debugging the
                # actual inventory import code), so only print it if we have to:
                # https://github.com/ansible/ansible-tower/issues/7414#issuecomment-321615104
                self.all_group.debug_tree()

            with batch_role_ancestor_rebuilding():
                # Ensure that this is managed as an atomic SQL transaction,
                # and thus properly rolled back if there is an issue.
                with transaction.atomic():
                    # Merge/overwrite inventory into database.
                    if settings.SQL_DEBUG:
                        logger.warning('loading into database...')
                    with ignore_inventory_computed_fields():
                        if getattr(settings, 'ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC', True):
                            self.load_into_database()
                        else:
                            with disable_activity_stream():
                                self.load_into_database()
                        if settings.SQL_DEBUG:
                            queries_before2 = len(connection.queries)
                        self.inventory.update_computed_fields()
                        if settings.SQL_DEBUG:
                            logger.warning('update computed fields took %d queries',
                                           len(connection.queries) - queries_before2)
                    try:
                        self.check_license()
                    except CommandError as e:
                        self.mark_license_failure(save=True)
                        raise e

                    if settings.SQL_DEBUG:
                        logger.warning('Inventory import completed for %s in %0.1fs',
                                       self.inventory_source.name, time.time() - begin)
                    else:
                        logger.info('Inventory import completed for %s in %0.1fs',
                                    self.inventory_source.name, time.time() - begin)
                    status = 'successful'

            # If we're in debug mode, then log the queries and time
            # used to do the operation.
            if settings.SQL_DEBUG:
                queries_this_import = connection.queries[queries_before:]
                sqltime = sum(float(x['time']) for x in queries_this_import)
                logger.warning('Inventory import required %d queries '
                               'taking %0.3fs', len(queries_this_import),
                               sqltime)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                status = 'canceled'
                exc = e
            elif isinstance(e, CommandError):
                exc = e
            else:
                tb = traceback.format_exc()
                exc = e
            transaction.rollback()

        if self.celery_invoked is False:
            with ignore_inventory_computed_fields():
                self.inventory_update = InventoryUpdate.objects.get(pk=self.inventory_update.pk)
                self.inventory_update.result_traceback = tb
                self.inventory_update.status = status
                self.inventory_update.save(update_fields=['status', 'result_traceback'])

        if exc and isinstance(exc, CommandError):
            sys.exit(1)
        elif exc:
            raise
