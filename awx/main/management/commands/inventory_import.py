# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import glob
import json
import logging
from optparse import make_option
import os
import re
import shlex
import string
import subprocess
import sys
import time
import traceback

# PyYAML
import yaml

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import connection, transaction
from django.db.models import Q
from django.contrib.auth.models import User

# AWX
from awx.main.models import *
from awx.main.utils import ignore_inventory_computed_fields
from awx.main.signals import disable_activity_stream
from awx.main.task_engine import TaskSerializer as LicenseReader

logger = logging.getLogger('awx.main.commands.inventory_import')

LICENSE_MESSAGE = '''\
Number of licensed instances exceeded, would bring available instances to %(new_count)d, system is licensed for %(available_instances)d.
See http://www.ansible.com/renew for license extension information.'''

DEMO_LICENSE_MESSAGE = '''\
Demo mode free license count exceeded, would bring available instances to %(new_count)d, demo mode allows %(available_instances)d.
See http://www.ansible.com/renew for licensing information.'''


class MemObject(object):
    '''
    Common code shared between in-memory groups and hosts.
    '''
    
    def __init__(self, name, source_dir):
        assert name, 'no name'
        assert source_dir, 'no source dir'
        self.name = name
        self.source_dir = source_dir
    
    def load_vars(self, base_path):
        all_vars = {}
        for suffix in ('', '.yml', '.yaml', '.json'):
            path = ''.join([base_path, suffix])
            if not os.path.exists(path):
                continue
            if not os.path.isfile(path):
                continue
            vars_name = os.path.basename(os.path.dirname(path))
            logger.debug('Loading %s from %s', vars_name, path)
            try:
                v = yaml.safe_load(file(path, 'r').read())
                if hasattr(v, 'items'): # is a dict
                    all_vars.update(v)
            except yaml.YAMLError, e:
                if hasattr(e, 'problem_mark'):
                    logger.error('Invalid YAML in %s:%s col %s', path,
                                 e.problem_mark.line + 1,
                                 e.problem_mark.column + 1)
                else:
                    logger.error('Error loading YAML from %s', path)
                raise
        return all_vars


class MemGroup(MemObject):
    '''
    In-memory representation of an inventory group.
    '''

    def __init__(self, name, source_dir):
        super(MemGroup, self).__init__(name, source_dir)
        self.children = []
        self.hosts = []
        self.variables = {}
        self.parents = []
        # Used on the "all" group in place of previous global variables.
        # maps host and group names to hosts to prevent redudant additions
        self.all_hosts = {}
        self.all_groups = {}
        group_vars = os.path.join(source_dir, 'group_vars', self.name)
        self.variables = self.load_vars(group_vars)
        logger.debug('Loaded group: %s', self.name)
        
    def child_group_by_name(self, name, loader):
        if name == 'all':
            return
        logger.debug('Looking for %s as child group of %s', name, self.name)
        # slight hack here, passing in 'self' for all_group but child=True won't use it
        group = loader.get_group(name, self, child=True)
        if group:
            # don't add to child groups if already there
            for g in self.children:
                if g.name == name:
                     return g
            logger.debug('Adding child group %s to group %s', group.name, self.name)
            self.children.append(group)
        return group

    def add_child_group(self, group):
        assert group.name is not 'all', 'group name is all'
        assert isinstance(group, MemGroup), 'not MemGroup instance'
        logger.debug('Adding child group %s to parent %s', group.name, self.name)
        if group not in self.children:
            self.children.append(group)
        if not self in group.parents:
            group.parents.append(self)

    def add_host(self, host):
        assert isinstance(host, MemHost), 'not MemHost instance'
        logger.debug('Adding host %s to group %s', host.name, self.name)
        if host not in self.hosts:
            self.hosts.append(host)

    def debug_tree(self, group_names=None):
        group_names = group_names or set()
        if self.name in group_names:
            return
        logger.debug('Dumping tree for group "%s":', self.name)
        logger.debug('- Vars: %r', self.variables)
        for h in self.hosts:
            logger.debug('- Host: %s, %r',  h.name, h.variables)
        for g in self.children:
            logger.debug('- Child: %s', g.name)
        logger.debug('----')
        group_names.add(self.name)
        for g in self.children:
            g.debug_tree(group_names)


class MemHost(MemObject):
    '''
    In-memory representation of an inventory host.
    '''

    def __init__(self, name, source_dir, port=None):
        super(MemHost, self).__init__(name, source_dir)
        self.variables = {}
        self.instance_id = None
        self.name = name
        if port:
            self.variables['ansible_ssh_port'] = port
        host_vars = os.path.join(source_dir, 'host_vars', name)
        self.variables.update(self.load_vars(host_vars))
        logger.debug('Loaded host: %s', self.name)


class BaseLoader(object):
    '''
    Common functions for an inventory loader from a given source.
    '''

    def __init__(self, source, all_group=None, group_filter_re=None, host_filter_re=None):
        self.source = source
        self.source_dir = os.path.dirname(self.source)
        self.all_group = all_group or MemGroup('all', self.source_dir)
        self.group_filter_re = group_filter_re
        self.host_filter_re = host_filter_re
        self.ipv6_port_re = re.compile(r'^\[([A-Fa-f0-9:]{3,})\]:(\d+?)$')

    def get_host(self, name):
        '''
        Return a MemHost instance from host name, creating if needed.  If name
        contains brackets, they will NOT be interpreted as a host pattern.
        '''
        m = self.ipv6_port_re.match(name)
        if m:
            host_name = m.groups()[0]
            port = int(m.groups()[1])
        elif name.count(':') == 1:
            host_name = name.split(':')[0]
            try:
                port = int(name.split(':')[1])
            except (ValueError, UnicodeDecodeError):
                logger.warning(u'Invalid port "%s" for host "%s"',
                               name.split(':')[1], host_name)
                port = None
        else:
            host_name = name
            port = None
        if self.host_filter_re and not self.host_filter_re.match(host_name):
            logger.debug('Filtering host %s', host_name)
            return None
        host = None
        if not host_name in self.all_group.all_hosts:
            host = MemHost(host_name, self.source_dir, port)
            self.all_group.all_hosts[host_name] = host
        return self.all_group.all_hosts[host_name]

    def get_hosts(self, name):
        '''
        Return iterator over one or more MemHost instances from host name or
        host pattern.
        '''
        def iternest(*args):
            if args:
                for i in args[0]:
                    for j in iternest(*args[1:]):
                        yield ''.join([str(i), j])
            else:
                yield ''
        if self.ipv6_port_re.match(name):
            yield self.get_host(name)
            return
        pattern_re = re.compile(r'(\[(?:(?:\d+\:\d+)|(?:[A-Za-z]\:[A-Za-z]))(?:\:\d+)??\])')
        iters = []
        for s in re.split(pattern_re, name):
            if re.match(pattern_re, s):
                start, end, step = (s[1:-1] + ':1').split(':')[:3]
                mapfunc = str
                if start in string.ascii_letters:
                    istart = string.ascii_letters.index(start)
                    iend = string.ascii_letters.index(end) + 1
                    if istart >= iend:
                        raise ValueError('invalid host range specified')
                    seq = string.ascii_letters[istart:iend:int(step)]
                else:
                    if start[0] == '0' and len(start) > 1:
                        if len(start) != len(end):
                            raise ValueError('invalid host range specified')
                        mapfunc = lambda x: str(x).zfill(len(start))
                    seq = xrange(int(start), int(end) + 1, int(step))
                iters.append(map(mapfunc, seq))
            elif re.search(r'[\[\]]', s):
                raise ValueError('invalid host range specified')
            elif s:
                iters.append([s])
        for iname in iternest(*iters):
            yield self.get_host(iname)

    def get_group(self, name, all_group=None, child=False):
        '''
        Return a MemGroup instance from group name, creating if needed.
        '''
        all_group = all_group or self.all_group
        if name == 'all':
            return all_group
        if self.group_filter_re and not self.group_filter_re.match(name):
            logger.debug('Filtering group %s', name)
            return None
        if not name in self.all_group.all_groups:
            group = MemGroup(name, self.source_dir) 
            if not child:
                all_group.add_child_group(group)
            self.all_group.all_groups[name] = group
        return self.all_group.all_groups[name]

    def load(self):
        raise NotImplementedError


class IniLoader(BaseLoader):
    '''
    Loader to read inventory from an INI-formatted text file.
    '''
    
    def load(self):
        logger.info('Reading INI source: %s', self.source)
        group = self.all_group
        input_mode = 'host'
        for line in file(self.source, 'r'):
            line = line.split('#')[0].strip()
            if not line:
                continue
            elif line.startswith('[') and line.endswith(']'):
                # Mode change, possible new group name
                line = line[1:-1].strip()
                if line.endswith(':vars'):
                    input_mode = 'vars'
                    line = line[:-5]
                elif line.endswith(':children'):
                    input_mode = 'children'
                    line = line[:-9]
                else:
                    input_mode = 'host'
                group = self.get_group(line)
            elif group:
                # If group is None, we are skipping this group and shouldn't
                # capture any children/variables/hosts under it.
                # Add hosts with inline variables, or variables/children to
                # an existing group.
                tokens = shlex.split(line)
                if input_mode == 'host':
                    for host in self.get_hosts(tokens[0]):
                        if not host:
                            continue
                        if len(tokens) > 1:
                            for t in tokens[1:]:
                                k,v = t.split('=', 1)
                                host.variables[k] = v
                        group.add_host(host) 
                elif input_mode == 'children':
                    group.child_group_by_name(line, self)
                elif input_mode == 'vars':
                    for t in tokens:
                        k, v = t.split('=', 1)
                        group.variables[k] = v
            # TODO: expansion patterns are probably not going to be supported.  YES THEY ARE!


# from API documentation:
#
# if called with --list, inventory outputs like so:
#        
# {
#    "databases"   : {
#        "hosts"   : [ "host1.example.com", "host2.example.com" ],
#        "vars"    : {
#            "a"   : true
#        }
#    },
#    "webservers"  : [ "host2.example.com", "host3.example.com" ],
#    "atlanta"     : {
#        "hosts"   : [ "host1.example.com", "host4.example.com", "host5.example.com" ],
#        "vars"    : {
#            "b"   : false
#        },
#        "children": [ "marietta", "5points" ],
#    },
#    "marietta"    : [ "host6.example.com" ],
#    "5points"     : [ "host7.example.com" ]
# }
#
# if called with --host <host_record_name> outputs JSON for that host


class ExecutableJsonLoader(BaseLoader):

    def command_to_json(self, cmd):
        data = {}
        stdout, stderr = '', ''
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError('%r failed (rc=%d) with output: %s' % (cmd, proc.returncode, stderr))
            data = json.loads(stdout)
            if not isinstance(data, dict):
                raise TypeError('Returned JSON must be a dictionary, got %s instead' % str(type(data)))
        except:
            logger.error('Failed to load JSON from: %s', stdout)
            raise
        return data

    def load(self):
        logger.info('Reading executable JSON source: %s', self.source)
        data = self.command_to_json([self.source, '--list'])
        _meta = data.pop('_meta', {})

        for k,v in data.iteritems():
            group = self.get_group(k)
            if not group:
                continue

            # Load group hosts/vars/children from a dictionary.
            if isinstance(v, dict):
                # Process hosts within a group.
                hosts = v.get('hosts', {})
                if isinstance(hosts, dict):
                    for hk, hv in hosts.iteritems():
                        host = self.get_host(hk)
                        if not host:
                            continue
                        if isinstance(hv, dict):
                            host.variables.update(hv)
                        else:
                            self.logger.warning('Expected dict of vars for '
                                                'host "%s", got %s instead',
                                                hk, str(type(hv)))
                        group.add_host(host)
                elif isinstance(hosts, (list, tuple)):
                    for hk in hosts:
                        host = self.get_host(hk)
                        if not host:
                            continue
                        group.add_host(host)
                else:
                    logger.warning('Expected dict or list of "hosts" for '
                                   'group "%s", got %s instead', k,
                                   str(type(hosts)))
                # Process group variables.
                vars = v.get('vars', {})
                if isinstance(vars, dict):
                    group.variables.update(vars)
                else:
                    self.logger.warning('Expected dict of vars for '
                                        'group "%s", got %s instead',
                                        k, str(type(vars)))
                # Process child groups.
                children = v.get('children', [])
                if isinstance(children, (list, tuple)):
                    for c in children:
                        child = self.get_group(c, self.all_group, child=True)
                        if child:
                            group.add_child_group(child)
                else:
                    self.logger.warning('Expected list of children for '
                                        'group "%s", got %s instead',
                                        k, str(type(children)))

            # Load host names from a list.
            elif isinstance(v, (list, tuple)):
                for h in v:
                    host = self.get_host(h)
                    if not host:
                        continue
                    group.add_host(host)
            else:
                logger.warning('')
                self.logger.warning('Expected dict or list for group "%s", '
                                    'got %s instead', k, str(type(v)))

            if k != 'all':
                self.all_group.add_child_group(group)

        # Invoke the executable once for each host name we've built up
        # to set their variables
        for k,v in self.all_group.all_hosts.iteritems():
            if 'hostvars' not in _meta:
                data = self.command_to_json([self.source, '--host', k])
            else:
                data = _meta['hostvars'].get(k, {})
            if isinstance(data, dict):
                v.variables.update(data)
            else:
                self.logger.warning('Expected dict of vars for '
                                    'host "%s", got %s instead',
                                    k, str(type(data)))


def load_inventory_source(source, all_group=None, group_filter_re=None,
                          host_filter_re=None, exclude_empty_groups=False):
    '''
    Load inventory from given source directory or file.
    '''
    # Sanity check: We need the "azure" module to be titled "windows_azure.py",
    # because it depends on the "azure" package from PyPI, and naming the
    # module the same way makes the importer sad.
    source = source.replace('azure', 'windows_azure')

    logger.debug('Analyzing type of source: %s', source)
    original_all_group = all_group
    if not os.path.exists(source):
        raise IOError('Source does not exist: %s' % source)
    source = os.path.join(os.getcwd(), os.path.dirname(source),
                          os.path.basename(source))
    source = os.path.normpath(os.path.abspath(source))
    if os.path.isdir(source):
        all_group = all_group or MemGroup('all', source)
        for filename in glob.glob(os.path.join(source, '*')):
            if filename.endswith(".ini") or os.path.isdir(filename):
                continue
            load_inventory_source(filename, all_group, group_filter_re,
                                  host_filter_re)
    else:
        all_group = all_group or MemGroup('all', os.path.dirname(source))
        if os.access(source, os.X_OK):
            ExecutableJsonLoader(source, all_group, group_filter_re, host_filter_re).load()
        else:
            IniLoader(source, all_group, group_filter_re, host_filter_re).load()

    logger.debug('Finished loading from source: %s', source)
    # Exclude groups that are completely empty.
    if original_all_group is None and exclude_empty_groups:
        for name, group in all_group.all_groups.items():
            if not group.children and not group.hosts and not group.variables:
                logger.debug('Removing empty group %s', name)
                for parent in group.parents:
                    if group in parent.children:
                        parent.children.remove(group)
                del all_group.all_groups[name]
    if original_all_group is None:
        logger.info('Loaded %d groups, %d hosts', len(all_group.all_groups),
                    len(all_group.all_hosts))
    return all_group


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
        make_option('--source', dest='source', type='str', default=None,
                    metavar='s', help='inventory directory, file, or script '
                    'to load'),
        make_option('--enabled-var', dest='enabled_var', type='str',
                    default=None, metavar='v', help='host variable used to '
                    'set/clear enabled flag when host is online/offline'),
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
                    'specifies the unique, immutable instance ID'),
    )

    def init_logging(self):
        log_levels = dict(enumerate([logging.WARNING, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.inventory_import')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        class Formatter(logging.Formatter):
            def format(self, record):
                record.relativeSeconds = record.relativeCreated / 1000.0
                return logging.Formatter.format(self, record)
        formatter = Formatter('%(relativeSeconds)9.3f %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

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
            self.inventory = Inventory.objects.filter(active=True).get(**q)
        except Inventory.DoesNotExist:
            raise CommandError('Inventory with %s = %s cannot be found' % q.items()[0])
        except Inventory.MultipleObjectsReturned:
            raise CommandError('Inventory with %s = %s returned multiple results' % q.items()[0])
        self.logger.info('Updating inventory %d: %s' % (self.inventory.pk,
                                                        self.inventory.name))

        # Load inventory source if specified via environment variable (when
        # inventory_import is called from an InventoryUpdate task).
        inventory_source_id = os.getenv('INVENTORY_SOURCE_ID', None)
        if inventory_source_id:
            try:
                self.inventory_source = InventorySource.objects.get(pk=inventory_source_id,
                                                                    inventory=self.inventory,
                                                                    active=True)
            except InventorySource.DoesNotExist:
                raise CommandError('Inventory source with id=%s not found' % \
                                   inventory_source_id)
            self.inventory_update = None
        # Otherwise, create a new inventory source to capture this invocation
        # via command line.
        else:
            with ignore_inventory_computed_fields():
                self.inventory_source, created = InventorySource.objects.get_or_create(
                    inventory=self.inventory,
                    group=None,
                    source='file',
                    source_path=os.path.abspath(self.source),
                    overwrite=self.overwrite,
                    overwrite_vars=self.overwrite_vars,
                    active=True,
                )
                self.inventory_update = self.inventory_source.create_inventory_update(
                    job_args=json.dumps(sys.argv),
                    job_env=dict(os.environ.items()),
                    job_cwd=os.getcwd(),
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
            if self.inventory_source.group:
                host_qs = self.inventory_source.group.all_hosts
            else:
                host_qs = self.inventory.hosts.all()
            host_qs = host_qs.filter(active=True, instance_id='',
                                     variables__contains=self.instance_id_var)
            for host in host_qs:
                instance_id = host.variables_dict.get(self.instance_id_var, '')
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
                instance_id = mem_host.variables.get(self.instance_id_var, '')
                if not instance_id:
                    self.logger.warning('Host "%s" has no "%s" variable',
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
        if self.inventory_source.group:
            hosts_qs = self.inventory_source.group.all_hosts
            # FIXME: Also include hosts from inventory_source.managed_hosts?
        else:
            hosts_qs = self.inventory.hosts.filter(active=True)
        # Build list of all host pks, remove all that should not be deleted.
        del_host_pks = set(hosts_qs.values_list('pk', flat=True))
        if self.instance_id_var:
            all_instance_ids = self.mem_instance_id_map.keys()
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
                host.mark_inactive()
                self.logger.info('Deleted host "%s"', host_name)
        if settings.SQL_DEBUG:
            self.logger.warning('host deletions took %d queries for %d hosts',
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
        if self.inventory_source.group:
            groups_qs = self.inventory_source.group.all_children
            # FIXME: Also include groups from inventory_source.managed_groups?
        else:
            groups_qs = self.inventory.groups.filter(active=True)
        # Build list of all group pks, remove those that should not be deleted.
        del_group_pks = set(groups_qs.values_list('pk', flat=True))
        all_group_names = self.all_group.all_groups.keys()
        for offset in xrange(0, len(all_group_names), self._batch_size):
            group_names = all_group_names[offset:(offset + self._batch_size)]
            for group_pk in groups_qs.filter(name__in=group_names).values_list('pk', flat=True):
                del_group_pks.discard(group_pk)
        # Now delete all remaining groups in batches.
        all_del_pks = sorted(list(del_group_pks))
        for offset in xrange(0, len(all_del_pks), self._batch_size):
            del_pks = all_del_pks[offset:(offset + self._batch_size)]
            for group in groups_qs.filter(pk__in=del_pks):
                group_name = group.name
                group.mark_inactive(recompute=False)
                self.logger.info('Group "%s" deleted', group_name)
        if settings.SQL_DEBUG:
            self.logger.warning('group deletions took %d queries for %d groups',
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
        if self.inventory_source.group:
            db_groups = self.inventory_source.group.all_children
        else:
            db_groups = self.inventory.groups.filter(active=True)
        for db_group in db_groups:
            # Delete child group relationships not present in imported data.
            db_children = db_group.children.filter(active=True)
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
                    self.logger.info('Group "%s" removed from group "%s"',
                                     db_child.name, db_group.name)
            # FIXME: Inventory source group relationships
            # Delete group/host relationships not present in imported data.
            db_hosts = db_group.hosts.filter(active=True)
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
                    if db_host not in db_group.hosts.filter(active=True):
                        continue
                    db_group.hosts.remove(db_host)
                    self.logger.info('Host "%s" removed from group "%s"',
                                     db_host.name, db_group.name)
        if settings.SQL_DEBUG:
            self.logger.warning('group-group and group-host deletions took %d queries for %d relationships',
                                len(connection.queries) - queries_before,
                                group_group_count + group_host_count)

    def _update_inventory(self):
        '''
        Update/overwrite variables from "all" group.  If importing from a
        cloud source attached to a specific group, variables will be set on
        the base group, otherwise they will be set on the whole inventory.
        '''
        if self.inventory_source.group:
            all_obj = self.inventory_source.group
            all_obj.inventory_sources.add(self.inventory_source)
            all_name = 'group "%s"' % all_obj.name
        else:
            all_obj = self.inventory
            all_name = 'inventory'
        db_variables = all_obj.variables_dict
        if self.overwrite_vars or self.overwrite:
            db_variables = self.all_group.variables
        else:
            db_variables.update(self.all_group.variables)
        if db_variables != all_obj.variables_dict:
            all_obj.variables = json.dumps(db_variables)
            all_obj.save(update_fields=['variables'])
            if self.overwrite_vars or self.overwrite:
                self.logger.info('%s variables replaced from "all" group', all_name.capitalize())
            else:
                self.logger.info('%s variables updated from "all" group', all_name.capitalize())
        else:
            self.logger.info('%s variables unmodified', all_name.capitalize())

    def _create_update_groups(self):
        '''
        For each group in the local list, create it if it doesn't exist in the
        database.  Otherwise, update/replace database variables from the
        imported data.  Associate with the inventory source group if importing
        from cloud inventory source.
        '''
        if settings.SQL_DEBUG:
            queries_before = len(connection.queries)
        inv_src_group = self.inventory_source.group
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
                if self.overwrite_vars or self.overwrite:
                    db_variables = mem_group.variables
                else:
                    db_variables.update(mem_group.variables)
                if db_variables != group.variables_dict:
                    group.variables = json.dumps(db_variables)
                    group.save(update_fields=['variables'])
                    if self.overwrite_vars or self.overwrite:
                        self.logger.info('Group "%s" variables replaced', group.name)
                    else:
                        self.logger.info('Group "%s" variables updated', group.name)
                else:
                    self.logger.info('Group "%s" variables unmodified', group.name)
                existing_group_names.add(group.name)
                if inv_src_group and inv_src_group != group and group.name in root_group_names:
                    self._batch_add_m2m(inv_src_group.children, group)
                self._batch_add_m2m(self.inventory_source.groups, group)
        for group_name in all_group_names:
            if group_name in existing_group_names:
                continue
            mem_group = self.all_group.all_groups[group_name]
            group = self.inventory.groups.create(name=group_name, variables=json.dumps(mem_group.variables), description='imported')
            # Access auto one-to-one attribute to create related object.
            #group.inventory_source
            InventorySource.objects.create(group=group, inventory=self.inventory, name=('%s (%s)' % (group_name, self.inventory.name)))
            self.logger.info('Group "%s" added', group.name)
            if inv_src_group and group_name in root_group_names:
                self._batch_add_m2m(inv_src_group.children, group)
            self._batch_add_m2m(self.inventory_source.groups, group)
        if inv_src_group:
            self._batch_add_m2m(inv_src_group.children, flush=True)
        self._batch_add_m2m(self.inventory_source.groups, flush=True)
        if settings.SQL_DEBUG:
            self.logger.warning('group updates took %d queries for %d groups',
                                len(connection.queries) - queries_before,
                                len(self.all_group.all_groups))

    def _update_db_host_from_mem_host(self, db_host, mem_host):
        # Update host variables.
        db_variables = db_host.variables_dict
        if self.overwrite_vars or self.overwrite:
            db_variables = mem_host.variables
        else:
            db_variables.update(mem_host.variables)
        update_fields = []
        if db_variables != db_host.variables_dict:
            db_host.variables = json.dumps(db_variables)
            update_fields.append('variables')
        # Update host enabled flag.
        enabled = None
        if self.enabled_var and self.enabled_var in mem_host.variables:
            value = mem_host.variables[self.enabled_var]
            if self.enabled_value is not None:
                enabled = bool(unicode(self.enabled_value) == unicode(value))
            else:
                enabled = bool(value)
        if enabled is not None and db_host.enabled != enabled:
            db_host.enabled = enabled
            update_fields.append('enabled')
        # Update host name.
        if mem_host.name != db_host.name:
            old_name = db_host.name
            db_host.name = mem_host.name
            update_fields.append('name')
        # Update host instance_id.
        if self.instance_id_var:
            instance_id = mem_host.variables.get(self.instance_id_var, '')
        else:
            instance_id = ''
        if instance_id != db_host.instance_id:
            old_instance_id = db_host.instance_id
            db_host.instance_id = instance_id
            update_fields.append('instance_id')
        # Update host and display message(s) on what changed.
        if update_fields:
            db_host.save(update_fields=update_fields)
        if 'name' in update_fields:
            self.logger.info('Host renamed from "%s" to "%s"', old_name, mem_host.name)
        if 'instance_id' in update_fields:
            if old_instance_id:
                self.logger.info('Host "%s" instance_id updated', mem_host.name)
            else:
                self.logger.info('Host "%s" instance_id added', mem_host.name)
        if 'variables' in update_fields:
            if self.overwrite_vars or self.overwrite:
                self.logger.info('Host "%s" variables replaced', mem_host.name)
            else:
                self.logger.info('Host "%s" variables updated', mem_host.name)
        else:
            self.logger.info('Host "%s" variables unmodified', mem_host.name)
        if 'enabled' in update_fields:
            if enabled:
                self.logger.info('Host "%s" is now enabled', mem_host.name)
            else:
                self.logger.info('Host "%s" is now disabled', mem_host.name)
        if self.inventory_source.group:
            self._batch_add_m2m(self.inventory_source.group.hosts, db_host)
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
            instance_id = ''
            mem_host_name_map[k] = v
            if self.instance_id_var:
                instance_id = v.variables.get(self.instance_id_var, '')
            if instance_id in self.db_instance_id_map:
                mem_host_pk_map[self.db_instance_id_map[instance_id]] = v
            elif instance_id:
                mem_host_instance_id_map[instance_id] = v

        # Update all existing hosts where we know the PK based on instance_id.
        all_host_pks = sorted(mem_host_pk_map.keys())
        for offset in xrange(0, len(all_host_pks), self._batch_size):
            host_pks = all_host_pks[offset:(offset + self._batch_size)]
            for db_host in self.inventory.hosts.filter(active=True, pk__in=host_pks):
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
            for db_host in self.inventory.hosts.filter(active=True, instance_id__in=instance_ids):
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
            for db_host in self.inventory.hosts.filter(active=True, name__in=host_names):
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
                              name=mem_host_name, description='imported')
            enabled = None
            if self.enabled_var and self.enabled_var in mem_host.variables:
                value = mem_host.variables[self.enabled_var]
                if self.enabled_value is not None:
                    enabled = bool(unicode(self.enabled_value) == unicode(value))
                else:
                    enabled = bool(value)
                host_attrs['enabled'] = enabled
            if self.instance_id_var:
                instance_id = mem_host.variables.get(self.instance_id_var, '')
                host_attrs['instance_id'] = instance_id
            db_host = self.inventory.hosts.create(**host_attrs)
            if enabled is False:
                self.logger.info('Host "%s" added (disabled)', mem_host_name)
            else:
                self.logger.info('Host "%s" added', mem_host_name)
            if self.inventory_source.group:
                self._batch_add_m2m(self.inventory_source.group.hosts, db_host)
            self._batch_add_m2m(self.inventory_source.hosts, db_host)

        if self.inventory_source.group:
            self._batch_add_m2m(self.inventory_source.group.hosts, flush=True)
        self._batch_add_m2m(self.inventory_source.hosts, flush=True)

        if settings.SQL_DEBUG:
            self.logger.warning('host updates took %d queries for %d hosts',
                                len(connection.queries) - queries_before,
                                len(self.all_group.all_hosts))

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
                child_names = set([g.name for g in mem_group.children])
                db_children_qs = self.inventory.groups.filter(name__in=child_names)
                # FIXME: May fail unit tests when len(child_names) > 1000.
                for db_child in db_children_qs.filter(children__id=db_group.id):
                    self.logger.info('Group "%s" already child of group "%s"', db_child.name, db_group.name)
                for db_child in db_children_qs.exclude(children__id=db_group.id):
                    self._batch_add_m2m(db_group.children, db_child)
                    self.logger.info('Group "%s" added as child of "%s"', db_child.name, db_group.name)
                self._batch_add_m2m(db_group.children, flush=True)
        if settings.SQL_DEBUG:
            self.logger.warning('Group-group updates took %d queries for %d group-group relationships',
                                len(connection.queries) - queries_before, group_group_count)

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
                        self.logger.info('Host "%s" already in group "%s"', db_host.name, db_group.name)
                    for db_host in db_hosts_qs.exclude(groups__id=db_group.id):
                        self._batch_add_m2m(db_group.hosts, db_host)
                        self.logger.info('Host "%s" added to group "%s"', db_host.name, db_group.name)
                all_instance_ids = sorted([h.instance_id for h in mem_group.hosts if h.instance_id])
                for offset2 in xrange(0, len(all_instance_ids), self._batch_size):
                    instance_ids = all_instance_ids[offset2:(offset2 + self._batch_size)]
                    db_hosts_qs = self.inventory.hosts.filter(instance_id__in=instance_ids)
                    for db_host in db_hosts_qs.filter(groups__id=db_group.id):
                        self.logger.info('Host "%s" already in group "%s"', db_host.name, db_group.name)
                    for db_host in db_hosts_qs.exclude(groups__id=db_group.id):
                        self._batch_add_m2m(db_group.hosts, db_host)
                        self.logger.info('Host "%s" added to group "%s"', db_host.name, db_group.name)
                self._batch_add_m2m(db_group.hosts, flush=True)
        if settings.SQL_DEBUG:
            self.logger.warning('Group-host updates took %d queries for %d group-host relationships',
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
        reader = LicenseReader()
        license_info = reader.from_file()
        available_instances = license_info.get('available_instances', 0)
        free_instances = license_info.get('free_instances', 0)
        time_remaining = license_info.get('time_remaining', 0)
        new_count = Host.objects.active_count()
        if time_remaining <= 0 and not license_info.get('demo', False):
            self.logger.error('License has expired')
            raise CommandError("License has expired!")
        if free_instances < 0:
            d = {
                'new_count': new_count,
                'available_instances': available_instances,
            }
            if license_info.get('demo', False):
                self.logger.error(DEMO_LICENSE_MESSAGE % d)
            else:
                self.logger.error(LICENSE_MESSAGE % d)
            raise CommandError('License count exceeded!')

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.inventory_name = options.get('inventory_name', None)
        self.inventory_id = options.get('inventory_id', None)
        self.overwrite = bool(options.get('overwrite', False))
        self.overwrite_vars = bool(options.get('overwrite_vars', False))
        self.keep_vars = bool(options.get('keep_vars', False))
        self.source = options.get('source', None)
        self.enabled_var = options.get('enabled_var', None)
        self.enabled_value = options.get('enabled_value', None)
        self.group_filter = options.get('group_filter', None) or r'^.+$'
        self.host_filter = options.get('host_filter', None) or r'^.+$'
        self.exclude_empty_groups = bool(options.get('exclude_empty_groups', False))
        self.instance_id_var = options.get('instance_id_var', None)

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

        self.check_license()
        begin = time.time()
        self.load_inventory_from_database()

        status, tb, exc = 'error', '', None
        try:
            if settings.SQL_DEBUG:
                queries_before = len(connection.queries)

            # Update inventory update for this command line invocation.
            with ignore_inventory_computed_fields():
                iu = self.inventory_update
                if iu and iu.status != 'running':
                    with transaction.atomic():
                        self.inventory_update.status = 'running'
                        self.inventory_update.save()

            # Load inventory from source.
            self.all_group = load_inventory_source(self.source, None,
                                                   self.group_filter_re,
                                                   self.host_filter_re,
                                                   self.exclude_empty_groups)
            self.all_group.debug_tree()

            # Ensure that this is managed as an atomic SQL transaction,
            # and thus properly rolled back if there is an issue.
            with transaction.atomic():
                # Merge/overwrite inventory into database.
                if settings.SQL_DEBUG:
                    self.logger.warning('loading into database...')
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
                        self.logger.warning('update computed fields took %d queries',
                                            len(connection.queries) - queries_before2)
                self.check_license()
     
                if self.inventory_source.group:
                    inv_name = 'group "%s"' % (self.inventory_source.group.name)
                else:
                    inv_name = '"%s" (id=%s)' % (self.inventory.name,
                                                 self.inventory.id)
                if settings.SQL_DEBUG:
                    self.logger.warning('Inventory import completed for %s in %0.1fs',
                                        inv_name, time.time() - begin)
                else:
                    self.logger.info('Inventory import completed for %s in %0.1fs',
                                     inv_name, time.time() - begin)
                status = 'successful'

            # If we're in debug mode, then log the queries and time
            # used to do the operation.
            if settings.SQL_DEBUG:
                queries_this_import = connection.queries[queries_before:]
                sqltime = sum(float(x['time']) for x in queries_this_import)
                self.logger.warning('Inventory import required %d queries '
                                 'taking %0.3fs', len(queries_this_import),
                                 sqltime)
        except Exception, e:
            if isinstance(e, KeyboardInterrupt):
                status = 'canceled'
                exc = e
            elif isinstance(e, CommandError):
                exc = e
            else:
                tb = traceback.format_exc()
                exc = e
            if self.inventory_update:
                transaction.rollback()

        if self.inventory_update:
            with ignore_inventory_computed_fields():
                self.inventory_update = InventoryUpdate.objects.get(pk=self.inventory_update.pk)
                self.inventory_update.result_traceback = tb
                self.inventory_update.status = status
                self.inventory_update.save(update_fields=['status', 'result_traceback'])
            
        if exc and isinstance(exc, CommandError):
            sys.exit(1)
        elif exc:
            raise
