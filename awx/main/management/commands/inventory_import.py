# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import sys
from optparse import make_option

# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

# AWX
from awx.main.models import *

LOGGER = None

class ImportException(object):

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

        group_vars = os.path.join(inventory_base, 'group_vars', name)
        if os.path.exists(group_vars):
            LOGGER.debug("loading group_vars")
            self.variables = yaml.load(open(group_vars).read())

    def child_group_by_name(self, grp_name):
        LOGGER.debug("looking for child group: %s" % grp_name)
        if grp_name == 'all':
            return
        for x in self.child_groups:
            if x.name == grp_name:
                 return x
        grp = MemGroup(grp_name, self.inventory_base)       
        LOGGER.debug("adding child group %s to group %s" % (grp.name, self.name))
        self.child_groups.append(grp)
        return grp

    def add_child_group(self, grp):
        assert grp.name is not 'all'

        LOGGER.debug("adding child group %s to group %s" % (grp.name, self.name))
 
        assert type(grp) == MemGroup
        if grp not in self.child_groups:
            self.child_groups.append(grp)
        if not self in grp.parents:
            grp.parents.append(self)

    def add_host(self, host):
        LOGGER.debug("adding host %s to group %s" % (host.name, self.name))
       
        assert type(host) == MemHost
        if host not in self.hosts:
            self.hosts.append(host)

    def set_variables(self, values):
        LOGGER.debug("setting variables %s on group %s" % (values, self.name))
        self.variables = values

    def debug_tree(self):
        LOGGER.debug("debugging tree of group (%s)" % self.name)
 
        print "group: %s, %s" % (self.name, self.variables)
        for x in self.child_groups:
            print "   child: %s" % (x.name)
        for x in self.hosts:
            print "   host: %s, %s" % (x.name, x.variables)

        print "---"
        for x in self.child_groups:
            x.debug_tree()

class MemHost(object):

    def __init__(self, name, inventory_base):
        LOGGER.debug("adding host name: %s" % name)
        assert name is not None
        assert inventory_base is not None

        # set ansible_ssh_port if ":" in name
        self.name = name
        self.variables = {}
        self.inventory_base = inventory_base
      
        if name.find(":") != -1:
            tokens = name.split(":")
            self.name = tokens[0]
            self.variables['ansible_ssh_port'] = tokens[1]

        if "[" in name:
            raise ImportException("block ranges like host[0:50].example.com are not yet supported by the importer")

        host_vars = os.path.join(inventory_base, 'host_vars', name)
        if os.path.exists(host_vars):
            LOGGER.debug("loading host_vars")
            self.variables = yaml.load(open(host_vars).read())
    
    def set_variables(self, values):
        LOGGER.debug("setting variables %s on host %s" % (values, self.name))
        self.variables = values

class DirectoryLoader(object):

    def __init__(self):
        LOGGER.debug("processing directory")
        pass

    def load(self, src, all_group):
        self.inventory_base = dirname

        # now go through converts and use IniLoader or ExecutableJsonLoader
        # as needed but pass them in the inventory_base or src so group_vars can load

class IniLoader(object):

    
    def __init__(self, inventory_base=None):
        LOGGER.debug("processing ini")
        self.inventory_base = inventory_base
        self.group_names = {}

    def get_group(self, name, all_group):
        group = None
        if name == 'all':
            return all_group
        if not name in self.group_names:
            group = MemGroup(name, self.inventory_base)
            all_group.add_child_group(group)
            self.group_names[name] = group
        else:
            group = self.group_names[name]
        return group

    def load(self, src, all_group):
        LOGGER.debug("loading: %s on %s" % (src, all_group))

        if self.inventory_base is None:
            self.inventory_base = os.path.dirname(src)  

        data = open(src).read()
        lines = data.split("\n")
        group = all_group
        input_mode = 'host'

        for line in lines:
            if line.find("#"):
                 tokens = line.split("#")
                 line = tokens[0]

            if line.startswith("["):
                 # mode change, possible new group name
                 line = line.replace("[","").replace("]","").lstrip().rstrip()
                 if line.find(":vars") != -1:
                     input_mode = 'vars'
                     line = line.replace(":vars","")
                     group = self.get_group(line, all_group)
                 elif line.find(":children") != -1:
                     input_mode = 'children' 
                     line = line.replace(":children","")
                     group = self.get_group(line, all_group)
                 else:
                     input_mode = 'host'
                     group = self.get_group(line, all_group)
            else:
                 # add a host or variable to the existing group/host
                 line = line.lstrip().rstrip()
                 if line == "":
                     continue
                 tokens = shlex.split(line)

                 if input_mode == 'host':
                     new_host = MemHost(tokens[0], self.inventory_base)
                     if len(tokens) > 1:
                         variables = {}
                         for t in tokens[1:]:
                             (k,v) = t.split("=",1)
                             new_host.variables[k] = v
                     group.add_host(new_host) 

                 elif input_mode == 'children':
                     group.child_group_by_name(line)
                 elif input_mode == 'vars':
                     for t in tokens:
                         (k, v) = t.split("=", 1)
                         group.variables[k] = v
     
                                           


            # TODO: expansion patterns are probably not going to be supported

 
        


class ExecutableJsonLoader(object):

    def __init__(self, inventory_base=None):

        LOGGER.debug("processing executable JSON source")
        self.inventory_base = inventory_base

    def load(self, src, all_group):

        LOGGER.debug("loading %s onto %s" % (src, all_group))
        if self.inventory_base is None:
            self.inventory_base = os.path.dirname(src)

class GenericLoader(object):
    def __init__(self, src):

        LOGGER.debug("preparing loaders")


        LOGGER.debug("analyzing type of source")
        if not os.path.exists(src):
            LOGGER.debug("source missing")
            raise ImportException("source does not exist")
        if os.path.isdir(src):
            self.memGroup = memGroup = MemGroup('all', src)
            DirectoryLoader().load(src, memGroup)
        elif os.access(src, os.X_OK):
            self.memGroup = memGroup = MemGroup('all', os.path.basename(src))
            ExecutableJsonLoader().load(src, memGroup)
        else:
            self.memGroup = memGroup = MemGroup('all', os.path.basename(src))
            IniLoader().load(src, memGroup)

        LOGGER.debug("loading process complete")


    def result(self):
        return self.memGroup

class Command(BaseCommand):
    '''
    Management command to import directory, INI, or dynamic inventory
    '''

    help = 'Import or sync external inventory sources'
    args = '[<appname>, <appname.ModelName>, ...]'

    option_list = BaseCommand.option_list + (
        make_option('--inventory-name', dest='inventory_name', type='str', default=None, metavar='n',
                    help='name of inventory source to sync'),
        make_option('--inventory-id', dest='inventory_id', type='int', default=None, metavar='i',
                    help='inventory id to sync'),
        make_option('--overwrite', dest='overwrite', action='store_true', metavar="o",
                    default=False, help='overwrite the destination'),
        make_option('--overwite-vars', dest='overwrite_vars', action='store_true', metavar="V",
                    default=False, help='overwrite (rather than merge) variables'),
        make_option('--keep-vars', dest='keep_vars', action='store_true', metavar="k",
                    default=False, help='use database variables if set'),
        make_option('--source', dest='source', type='str', default=None, metavar='s',
                    help='inventory directory, file, or script to load'),
    )

    #def get_models(self, model):
    #    if not model._meta.abstract:
    #        yield model
    #    for sub in model.__subclasses__():
    #        for submodel in self.get_models(sub):
    #            yield submodel

    #def cleanup_model(self, model):
    #    name_field = None
    #    active_field = None
    #    for field in model._meta.fields:
    #        if field.name in ('name', 'username'):
    #            name_field = field.name
    #        if field.name in ('is_active', 'active'):
    #            active_field = field.name
    #    if not name_field:
    #        self.logger.warning('skipping model %s, no name field', model)
    #        return
    #    if not active_field:
    #        self.logger.warning('skipping model %s, no active field', model)
    #        return
    #    qs = model.objects.filter(**{
    #        active_field: False,
    #        '%s__startswith' % name_field: '_deleted_',
    #    })
    #    self.logger.debug('cleaning up model %s', model)
    #    for instance in qs:
    #        dt = parse_datetime(getattr(instance, name_field).split('_')[2])
    #        if not dt:
    #            self.logger.warning('unable to find deleted timestamp in %s '
    #                                'field', name_field)
    #        elif dt >= self.cutoff:
    #            action_text = 'would skip' if self.dry_run else 'skipping'
    #            self.logger.debug('%s %s', action_text, instance)
    #        else:
    #            action_text = 'would delete' if self.dry_run else 'deleting'
    #            self.logger.info('%s %s', action_text, instance)
    #            if not self.dry_run:
    #                instance.delete()

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        global LOGGER
        LOGGER = self.logger = logging.getLogger('awx.main.commands.cleanup_deleted')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.commit_on_success
    def handle(self, *args, **options):
        
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()

        name = options.get('inventory_name', None)
        id   = options.get('inventory_id', None)
        overwrite = options.get('overwrite', False)
        overwrite_vars = options.get('overwrite_vars', False)
        keep_vars = options.get('keep_vars', False)
        source = options.get('source', None)

        LOGGER.debug("name=%s" % name)
        LOGGER.debug("id=%s" % id)

        if name is None and id is None:
            self.logger.error("--inventory-name and --inventory-id are mutually exclusive")
            sys.exit(1)
        if name is None and id is None:
            self.logger.error("--inventory-name or --inventory-id are required")
            sys.exit(1)
        if (overwrite or overwrite_vars) and keep_vars:
            self.logger.error("--overwrite/--overwrite-vars and --keep-vars are mutually exclusive")
            sys.exit(1)
        if not source:
            self.logger.error("--source is required")
            sys.exit(1)

        LOGGER.debug("preparing loader")

        loader = GenericLoader(source)
        memGroup = loader.result()

        LOGGER.debug("debugging loaded result")
        memGroup.debug_tree()

        # now that memGroup is correct and supports JSON executables, INI, and trees
        # now merge and/or overwrite with the database itself!


        #self.days = int(options.get('days', 90))
        #self.dry_run = bool(options.get('dry_run', False))
        ## FIXME: Handle args to select models.
        #self.cutoff = now() - datetime.timedelta(days=self.days)
        #self.cleanup_model(User)
        #for model in self.get_models(PrimordialModel):
        #    self.cleanup_model(model)

