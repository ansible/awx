# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import glob
import json
import logging
from optparse import make_option
import os
import shlex
import subprocess
import sys
import traceback

# PyYAML
import yaml

# Django
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User

# AWX
from awx.main.models import *
from awx.main.licenses import LicenseReader

logger = logging.getLogger('awx.main.commands.inventory_import')

class ImportException(BaseException):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Import Error: %s" % msg

class MemGroup(object):

    def __init__(self, name, inventory_base):

        assert inventory_base is not None
        self.inventory_base = inventory_base

        self.name = name
        self.child_groups = []
        self.hosts = []
        self.variables = {}
        self.parents = []
        # Used on the "all" group in place of previous global variables.
        # maps host and group names to hosts to prevent redudant additions
        self.host_names = {}
        self.group_names = {}

        group_vars = os.path.join(inventory_base, 'group_vars', name)
        if os.path.exists(group_vars):
            logger.debug("loading group_vars")
            self.variables = yaml.load(open(group_vars).read())

    def child_group_by_name(self, grp_name, loader):
        logger.debug("looking for child group: %s" % grp_name)
        if grp_name == 'all':
            return
        # slight hack here, passing in 'self' for all_group but child=True won't use it
        grp = loader.get_group(grp_name, self, child=True)
        # don't add to child groups if already there
        for x in self.child_groups:
            if x.name == grp_name:
                 return x
        logger.debug("adding child group %s to group %s" % (grp.name, self.name))
        self.child_groups.append(grp)
        return grp

    def add_child_group(self, grp):
        assert grp.name is not 'all'

        logger.debug("adding child group %s to group %s" % (grp.name, self.name))
 
        assert type(grp) == MemGroup
        if grp not in self.child_groups:
            self.child_groups.append(grp)
        if not self in grp.parents:
            grp.parents.append(self)

    def add_host(self, host):
        logger.debug("adding host %s to group %s" % (host.name, self.name))
       
        assert type(host) == MemHost
        if host not in self.hosts:
            self.hosts.append(host)

    def debug_tree(self):
        logger.debug("describing tree of group (%s)" % self.name)
 
        logger.debug("group: %s, %s" % (self.name, self.variables))
        for x in self.child_groups:
            logger.debug("   child: %s" % (x.name))
        for x in self.hosts:
            logger.debug("   host: %s, %s" % (x.name, x.variables))

        logger.debug("---")
        for x in self.child_groups:
            x.debug_tree()

class MemHost(object):

    def __init__(self, name, inventory_base):
        logger.debug("adding host name: %s" % name)
        assert name is not None
        assert inventory_base is not None

        # set ansible_ssh_port if ":" in name
        self.name = name
        self.variables = {}
        self.inventory_base = inventory_base
      
        if ':' in name:
            tokens = name.split(":")
            self.name = tokens[0]
            self.variables['ansible_ssh_port'] = int(tokens[1])

        if "[" in name:
            raise ImportException("block ranges like host[0:50].example.com are not yet supported by the importer")

        host_vars = os.path.join(inventory_base, 'host_vars', name)
        if os.path.exists(host_vars):
            logger.debug("loading host_vars")
            self.variables.update(yaml.load(open(host_vars).read()))
    
class BaseLoader(object):

    def __init__(self, inventory_base=None, all_group=None):
        self.inventory_base = inventory_base
        self.all_group = all_group

    def get_host(self, name):
        host_name = name.split(':')[0]
        host = None
        if not host_name in self.all_group.host_names:
            host = MemHost(name, self.inventory_base)
            self.all_group.host_names[host_name] = host
        return self.all_group.host_names[host_name]

    def get_group(self, name, all_group=None, child=False):
        all_group = all_group or self.all_group
        if name == 'all':
            return all_group
        if not name in self.all_group.group_names:
            group = MemGroup(name, self.inventory_base) 
            if not child:
                all_group.add_child_group(group)
            self.all_group.group_names[name] = group
        return self.all_group.group_names[name]

    def load(self, src):
        raise NotImplementedError

class IniLoader(BaseLoader):
    
    def __init__(self, inventory_base=None, all_group=None):
        super(IniLoader, self).__init__(inventory_base, all_group)
        logger.debug("processing ini")

    def load(self, src):
        logger.debug("loading: %s on %s" % (src, self.all_group))

        if self.inventory_base is None:
            self.inventory_base = os.path.dirname(src)  

        data = open(src).read()
        lines = data.split("\n")
        group = self.all_group
        input_mode = 'host'

        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue
            elif line.startswith("["):
                 # mode change, possible new group name
                 line = line.replace("[","").replace("]","").lstrip().rstrip()
                 if line.find(":vars") != -1:
                     input_mode = 'vars'
                     line = line.replace(":vars","")
                     group = self.get_group(line)
                 elif line.find(":children") != -1:
                     input_mode = 'children' 
                     line = line.replace(":children","")
                     group = self.get_group(line)
                 else:
                     input_mode = 'host'
                     group = self.get_group(line)
            else:
                 # add a host or variable to the existing group/host
                 tokens = shlex.split(line)

                 if input_mode == 'host':
                     new_host = self.get_host(tokens[0])
                     if len(tokens) > 1:
                         variables = {}
                         for t in tokens[1:]:
                             (k,v) = t.split("=",1)
                             new_host.variables[k] = v
                     group.add_host(new_host) 

                 elif input_mode == 'children':
                     group.child_group_by_name(line, self)
                 elif input_mode == 'vars':
                     for t in tokens:
                         (k, v) = t.split("=", 1)
                         group.variables[k] = v
     
            # TODO: expansion patterns are probably not going to be supported

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

    def __init__(self, inventory_base=None, all_group=None):
        super(ExecutableJsonLoader, self).__init__(inventory_base, all_group)
        logger.debug("processing executable JSON source")
        self.child_group_names = {}

    def command_to_json(self, cmd):
        data = {}
        stdout, stderr = '', ''
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise Exception("%s list failed %s with output: %s" % (cmd, stderr, proc.returncode))
            data = json.loads(stdout)
        except:
            traceback.print_exc()
            raise Exception("failed to load JSON output: %s" % stdout)
        assert type(data) == dict
        return data

    def load(self, src):

        logger.debug("loading %s onto %s" % (src, self.all_group))

        if self.inventory_base is None:
            self.inventory_base = os.path.dirname(src)

        data = self.command_to_json([src, "--list"])

        group = None
        _meta = data.pop('_meta', {})

        for (k,v) in data.iteritems():
 
            group = self.get_group(k)

            if type(v) == dict:

                # process hosts
                host_details = v.get('hosts', None)
                if host_details is not None:
                    if type(host_details) == dict:
                        for (hk, hv) in host_details.iteritems():
                             host = self.get_host(hk)
                             host.variables.update(hv)
                             group.add_host(host)
                    if type(host_details) == list:
                        for hk in host_details:
                            host = self.get_host(hk)
                            group.add_host(host)

                # process variables
                vars = v.get('vars', None)
                if vars is not None:
                    group.variables.update(vars)

                # process child groups
                children_details = v.get('children', None)
                if children_details is not None:
                    for x in children_details:
                        child = self.get_group(x, self.inventory_base, child=True)
                        group.add_child_group(child)
                        self.child_group_names[x] = child

            if type(v) in (tuple, list):
               for x in v:
                   host = self.get_host(x)
                   group.add_host(host)

            if k != 'all':
                self.all_group.add_child_group(group)
           

        # then we invoke the executable once for each host name we've built up
        # to set their variables
        for (k,v) in self.all_group.host_names.iteritems():
            if 'hostvars' not in _meta:
                data = self.command_to_json([src, "--host", k])
            else:
                data = _meta['hostvars'].get(k, {})
            v.variables.update(data)


def load_generic(src):
    logger.debug("analyzing type of source")
    if not os.path.exists(src):
        logger.debug("source missing")
        raise CommandError("source does not exist")
    if os.path.isdir(src):
        all_group = MemGroup('all', src)
        for f in glob.glob("%s/*" % src):
            if f.endswith(".ini"):
                # config files for inventory scripts should be ignored
                continue 
            if not os.path.isdir(f):
                if os.access(f, os.X_OK):
                    ExecutableJsonLoader(None, all_group).load(f)
                else:
                    IniLoader(None, all_group).load(f)
    elif os.access(src, os.X_OK):
        all_group = MemGroup('all', os.path.dirname(src))
        ExecutableJsonLoader(None, all_group).load(src)
    else:
        all_group = MemGroup('all', os.path.dirname(src))
        IniLoader(None, all_group).load(src)

    logger.debug("loading process complete")
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
    )

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.inventory_import')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
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
            self.inventory = Inventory.objects.get(**q)
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
                                                               inventory=self.inventory)
            except InventorySource.DoesNotExist:
                raise CommandError('Inventory source with id=%s not found' % \
                                   inventory_source_id)
            self.inventory_update = None
        # Otherwise, create a new inventory source to capture this invocation
        # via command line.
        else:
            self.inventory_source, created = InventorySource.objects.get_or_create(
                inventory=self.inventory,
                group=None,
                source='file',
                source_path=os.path.abspath(self.source),
                overwrite=self.overwrite,
                overwrite_vars=self.overwrite_vars,
            )
            self.inventory_update = self.inventory_source.inventory_updates.create(
                job_args=json.dumps(sys.argv),
                job_env=dict(os.environ.items()),
                job_cwd=os.getcwd(),
            )

        # FIXME: Wait or raise error if inventory is being updated by another
        # source.

    def load_into_database(self):
        '''
        Load inventory from in-memory groups to the database, overwriting or
        merging as appropriate.
        '''

        # If overwrite is set, for each host in the database that is NOT in
        # the local list, delete it. When importing from a cloud inventory
        # source attached to a specific group, only delete hosts beneath that
        # group.  Delete each host individually so signal handlers will run.
        if self.overwrite:
            self.logger.debug('deleting any hosts not in the remote source')
            if self.inventory_source.group:
                del_hosts = self.inventory_source.group.all_hosts
                # FIXME: Also include hosts from inventory_source.managed_hosts?
            else:
                del_hosts = self.inventory.hosts.all()
            del_hosts = del_hosts.exclude(name__in=self.all_group.host_names.keys())
            for host in del_hosts:
                host.delete()

        # If overwrite is set, for each group in the database that is NOT in
        # the local list, delete it. When importing from a cloud inventory
        # source attached to a specific group, only delete children of that
        # group.  Delete each group individually so signal handlers will run.
        if self.overwrite:
            self.logger.debug('deleting any groups not in the remote source')
            if self.inventory_source.group:
                del_groups = self.inventory_source.group.all_children
                # FIXME: Also include groups from inventory_source.managed_groups?
            else:
                del_groups = self.inventory.groups.all()
            del_groups = del_groups.exclude(name__in=self.all_group.group_names.keys())
            for group in del_groups:
                group.delete()

        # If overwrite is set, clear all invalid child relationships for groups
        # and all invalid host memberships.  When importing from a cloud
        # inventory source attached to a specific group, only clear
        # relationships for hosts and groups that are beneath the inventory
        # source group.
        if self.overwrite:
            self.logger.info("clearing any child relationships to rebuild from remote source")
            if self.inventory_source.group:
                db_groups = self.inventory_source.group.all_children
            else:
                db_groups = self.inventory.groups.all()

            for db_group in db_groups:
                db_kids = db_group.children.all()
                mem_kids = self.all_group.group_names[db_group.name].child_groups
                mem_kid_names = [ k.name for k in mem_kids ]
                for db_kid in db_kids:
                    if db_kid.name not in mem_kid_names:
                        self.logger.debug("removing non-DB kid: %s" % (db_kid.name))
                        db_group.children.remove(db_kid)

                db_hosts = db_group.hosts.all()
                mem_hosts = self.all_group.group_names[db_group.name].hosts
                mem_host_names = [ h.name for h in mem_hosts ]
                for db_host in db_hosts:
                    if db_host.name not in mem_host_names:
                        self.logger.debug("removing non-DB host: %s" % (db_host.name))
                        db_group.hosts.remove(db_host)

        # Update/overwrite variables from "all" group.  If importing from a
        # cloud source attached to a specific group, variables will be set on
        # the base group, otherwise they will be set on the inventory.
        if self.inventory_source.group:
            all_obj = self.inventory_source.group
            all_obj.inventory_sources.add(self.inventory_source)
        else:
            all_obj = self.inventory
        db_variables = all_obj.variables_dict
        mem_variables = self.all_group.variables
        if self.overwrite_vars or self.overwrite:
            self.logger.info('replacing inventory variables from "all" group')
            db_variables = mem_variables
        else:
            self.logger.info('updating inventory variables from "all" group')
            db_variables.update(mem_variables)
        all_obj.variables = json.dumps(db_variables)
        all_obj.save(update_fields=['variables'])

        # FIXME: Attribute changes to superuser?

        # For each group in the local list, create it if it doesn't exist in
        # the database.  Otherwise, update/replace database variables from the
        # imported data.  Associate with the inventory source group if
        # importing from cloud inventory source.
        for k,v in self.all_group.group_names.iteritems():
            variables = json.dumps(v.variables)
            defaults = dict(variables=variables, description='imported')
            group, created = self.inventory.groups.get_or_create(name=k,
                                                                 defaults=defaults)
            if created:
                self.logger.info('inserting new group %s' % k)
            else:
                self.logger.info('updating existing group %s' % k)
                db_variables = group.variables_dict
                mem_variables = v.variables
                if self.overwrite_vars or self.overwrite:
                    db_variables = mem_variables
                else:
                    db_variables.update(mem_variables)
                group.variables = json.dumps(db_variables)
                group.save(update_fields=['variables'])
            if self.inventory_source.group:
                self.inventory_source.group.children.add(group)
            group.inventory_sources.add(self.inventory_source)

        # For each host in the local list, create it if it doesn't exist in
        # the database.  Otherwise, update/replace database variables from the
        # imported data.  Associate with the inventory source group if
        # importing from cloud inventory source.
        for k,v in self.all_group.host_names.iteritems():
            variables = json.dumps(v.variables)
            defaults = dict(variables=variables, description='imported')
            host, created = self.inventory.hosts.get_or_create(name=k,
                                                               defaults=defaults)
            if created:
                self.logger.info('inserting new host %s' % k)
            else:
                self.logger.info('updating existing host %s' % k)
                db_variables = host.variables_dict
                mem_variables = v.variables
                if self.overwrite_vars or self.overwrite:
                    db_variables = mem_variables
                else:
                    db_variables.update(mem_variables)
                host.variables = json.dumps(db_variables)
                host.save(update_fields=['variables'])
            if self.inventory_source.group:
                self.inventory_source.group.hosts.add(host)
            host.inventory_sources.add(self.inventory_source)
            host.update_computed_fields(False, False)

        # for each host in a mem group, add it to the parents to which it belongs
        for (k,v) in self.all_group.group_names.iteritems():
            self.logger.info("adding parent arrangements for %s" % k)
            db_group = Group.objects.get(name=k, inventory__pk=self.inventory.pk)
            mem_hosts = v.hosts
            for h in mem_hosts:
                db_host = Host.objects.get(name=h.name, inventory__pk=self.inventory.pk)
                db_group.hosts.add(db_host)
                self.logger.debug("*** ADDING %s to %s ***" % (db_host, db_group))
  
        # for each group, draw in child group arrangements
        for (k,v) in self.all_group.group_names.iteritems():
            db_group = Group.objects.get(inventory=self.inventory, name=k)
            for mem_child_group in v.child_groups:
                db_child = Group.objects.get(inventory=self.inventory, name=mem_child_group.name)
                db_group.children.add(db_child)

    def check_license(self):
        reader = LicenseReader()
        license_info = reader.from_file()
        available_instances = license_info.get('available_instances', 0)
        free_instances = license_info.get('free_instances', 0)
        new_count = Host.objects.filter(active=True).count()
        if free_instances < 0:
            if license_info.get('demo', False):
                raise CommandError("demo mode free license count exceeded, would bring available instances to %s, demo mode allows %s, see http://ansibleworks.com/ansibleworks-awx for licensing information" % (new_count, available_instances))
            else:
                raise CommandError("number of licensed instances exceeded, would bring available instances to %s, system is licensed for %s, see http://ansibleworks.com/ansibleworks-awx for license extension information" % (new_count, available_instances))

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.inventory_name = options.get('inventory_name', None)
        self.inventory_id = options.get('inventory_id', None)
        self.overwrite = bool(options.get('overwrite', False))
        self.overwrite_vars = bool(options.get('overwrite_vars', False))
        self.keep_vars = bool(options.get('keep_vars', False))
        self.source = options.get('source', None)

        # Load inventory and related objects from database.
        if self.inventory_name and self.inventory_id:
            raise CommandError('--inventory-name and --inventory-id are mutually exclusive')
        elif not self.inventory_name and not self.inventory_id:
            raise CommandError('--inventory-name or --inventory-id is required')
        if (self.overwrite or self.overwrite_vars) and self.keep_vars:
            raise CommandError('--overwrite/--overwrite-vars and --keep-vars are mutually exclusive')
        if not self.source:
            raise CommandError('--source is required')

        self.load_inventory_from_database()

        status, tb, exc = 'error', '', None
        try:
            # Update inventory update for this command line invocation.
            if self.inventory_update:
                self.inventory_update.status = 'running'
                self.inventory_update.save()
                transaction.commit()

            self.logger.debug('preparing to load from %s' % self.source)
            self.all_group = load_generic(self.source)
            self.logger.debug('debugging loaded result:')
            self.all_group.debug_tree()

            # now that memGroup is correct and supports JSON executables, INI, and trees
            # now merge and/or overwrite with the database itself!

            self.load_into_database()
            self.check_license()
 
            self.logger.info("inventory import complete, %s, id=%s" % \
                             (self.inventory.name, self.inventory.id))
            status = 'successful'
        except Exception, e:
            if isinstance(e, KeyboardInterrupt):
                status = 'canceled'
                exc = e
            else:
                tb = traceback.format_exc()
                exc = e
            if self.inventory_update:
                transaction.rollback()

        if self.inventory_update:
            self.inventory_update = InventoryUpdate.objects.get(pk=self.inventory_update.pk)
            self.inventory_update.result_traceback = tb
            self.inventory_update.status = status
            self.inventory_update.save(update_fields=['status', 'result_traceback'])
            transaction.commit()
            
        if exc:
            raise exc
