# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import sys
from optparse import make_option
import subprocess
import traceback
import glob
import exceptions

# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

# AWX
from awx.main.models import *
from awx.main.licenses import LicenseReader

LOGGER = None

# maps host and group names to hosts to prevent redudant additions
group_names = {}
host_names = {}

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

        group_vars = os.path.join(inventory_base, 'group_vars', name)
        if os.path.exists(group_vars):
            LOGGER.debug("loading group_vars")
            self.variables = yaml.load(open(group_vars).read())

    def child_group_by_name(self, grp_name, loader):
        LOGGER.debug("looking for child group: %s" % grp_name)
        if grp_name == 'all':
            return
        # slight hack here, passing in 'self' for all_group but child=True won't use it
        grp = loader.get_group(grp_name, self, child=True)
        # don't add to child groups if already there
        for x in self.child_groups:
            if x.name == grp_name:
                 return x
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

class BaseLoader(object):

    def get_host(self, name):
        if ":" in name:
            tokens = name.split(":")
            name = tokens[0]
        global host_names
        host = None
        if not name in host_names:
            host = MemHost(name, self.inventory_base)
            host_names[name] = host
        return host_names[name]

    def get_group(self, name, all_group, child=False):
        global group_names
        if name == 'all':
            return all_group
        if not name in group_names:
            group = MemGroup(name, self.inventory_base) 
            if not child:
                all_group.add_child_group(group)
            group_names[name] = group
        return group_names[name]

class IniLoader(BaseLoader):
    
    def __init__(self, inventory_base=None):
        LOGGER.debug("processing ini")
        self.inventory_base = inventory_base

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

    def __init__(self, inventory_base=None):

        LOGGER.debug("processing executable JSON source")
        self.inventory_base = inventory_base
        self.child_group_names = {}

    def command_to_json(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        if proc.returncode != 0:
            raise ImportException("%s list failed %s with output: %s" % (src, stderr, proc.returncode))
        data = {}
        try:
            data = json.loads(stdout)
        except:
            traceback.print_exc()
            raise Exception("failed to load JSON output: %s" % stdout)
        assert type(data) == dict
        return data

    def load(self, src, all_group):

        LOGGER.debug("loading %s onto %s" % (src, all_group))

        if self.inventory_base is None:
            self.inventory_base = os.path.dirname(src)

        data = self.command_to_json([src, "--list"])

        print "RAW: %s" % data

        group = None

        for (k,v) in data.iteritems():
 
            group = self.get_group(k, all_group)

            print "TYPE %s => %s" % (k, v)

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
                            print "?? getting host: %s" % hk
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
               print "<><><><><><><><><><><><><><><><>><><><> GOT A LIST: %s" % (v) 
               for x in v:
                   print ">>>>>>>>> ADDING HOST FROM AN EXECUTABLE LIST = %s to %s" % (x, group.name)
                   host = self.get_host(x)
                   group.add_host(host)

            all_group.add_child_group(group)
           

        # then we invoke the executable once for each host name we've built up
        # to set their variables
        global host_names
        for (k,v) in host_names.iteritems():
            data = self.command_to_json([src, "--host", k])
            v.variables.update(data)


class GenericLoader(object):

    def __init__(self, src):

        LOGGER.debug("preparing loaders")


        LOGGER.debug("analyzing type of source")
        if not os.path.exists(src):
            LOGGER.debug("source missing")
            raise ImportException("source does not exist")
        if os.path.isdir(src):
            self.memGroup = memGroup = MemGroup('all', src)
            for f in glob.glob("%s/*" % src):
                if f.endswith(".ini"):
                    # config files for inventory scripts should be ignored
                    pass
                if not os.path.isdir(f):
                    if os.access(f, os.X_OK):
                        ExecutableJsonLoader().load(f, memGroup)
                    else:
                        IniLoader().load(f, memGroup)
        elif os.access(src, os.X_OK):
            self.memGroup = memGroup = MemGroup('all', os.path.dirname(src))
            ExecutableJsonLoader().load(src, memGroup)
        else:
            self.memGroup = memGroup = MemGroup('all', os.path.dirname(src))
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
        make_option('--overwrite-vars', dest='overwrite_vars', action='store_true', metavar="V",
                    default=False, help='overwrite (rather than merge) variables'),
        make_option('--keep-vars', dest='keep_vars', action='store_true', metavar="k",
                    default=False, help='use database variables if set'),
        make_option('--source', dest='source', type='str', default=None, metavar='s',
                    help='inventory directory, file, or script to load'),
    )

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        global LOGGER
        LOGGER = self.logger = logging.getLogger('awx.main.commands.inventory_import')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.commit_on_success
    def handle(self, *args, **options):
        try:
            self.main(args, options)
        except ImportException, ie:
            print ie.msg

    def main(self, args, options):
        
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()

        name           = options.get('inventory_name', None)
        id             = options.get('inventory_id', None)
        overwrite      = options.get('overwrite', False)
        overwrite_vars = options.get('overwrite_vars', False)
        keep_vars      = options.get('keep_vars', False)
        source         = options.get('source', None)

        LOGGER.debug("name=%s" % name)
        LOGGER.debug("id=%s" % id)

        if name is not None and id is not None:
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

        if id:
            inventory = Inventory.objects.filter(pk=id)
        else:
            inventory = Inventory.objects.filter(name=name)
        count = inventory.count()
        if count != 1:
            raise ImportException("%d inventory objects matched, expected 1" % count)        
        inventory = inventory.all()[0]

        print "MODIFYING INVENTORY: %s" % inventory.name

        # if overwrite is set, for each host in the database but NOT in the local
        # list, delete it
        if overwrite:
            LOGGER.info("deleting any hosts not in the remote source: %s" % host_names.keys())
            Host.objects.exclude(name__in = host_names.keys()).filter(inventory=inventory).delete()

        # if overwrite is set, for each group in the database but NOT in the local
        # list, delete it
        if overwrite:
            LOGGER.info("deleting any groups not in the remote source")
            Group.objects.exclude(name__in = group_names.keys()).filter(inventory=inventory).delete()

        # if overwrite is set, throw away all invalid child relationships for groups
        if overwrite:
            LOGGER.info("clearing any child relationships to rebuild from remote source")
            db_groups = Group.objects.filter(inventory=inventory)

            for db_group in db_groups:
                 db_kids = db_group.children.all()
                 mem_kids = group_names[db_group.name].child_groups
                 mem_kid_names = [ k.name for k in mem_kids ]
                 removed = False
                 for db_kid in db_kids:
                     if db_kid.name not in mem_kid_names:
                         removed = True
                         print "DEBUG: removing non-DB kid: %s" % (db_kid.name)
                         db_group.children.remove(db_kid)
                 if removed:
                     db_group.save()


        # this will be slightly inaccurate, but attribute to first superuser.
        user = User.objects.filter(is_superuser=True)[0]

        db_groups = Group.objects.filter(inventory=inventory)
        db_hosts  = Host.objects.filter(inventory=inventory)
        db_group_names = [ g.name for g in db_groups ]
        db_host_names  = [ h.name for h in db_hosts  ] 

        # for each group not in the database but in the local list, create it
        for (k,v) in group_names.iteritems():
            if k not in db_group_names:
                variables = json.dumps(v.variables)
                LOGGER.info("inserting new group %s" % k)
                host = Group.objects.create(inventory=inventory, name=k, variables=variables, created_by=user,
                   description="imported")                
                host.save()

        # for each host not in the database but in the local list, create it
        for (k,v) in host_names.iteritems():
            if k not in db_host_names:
                variables = json.dumps(v.variables)
                LOGGER.info("inserting new host %s" % k)
                group = Host.objects.create(inventory=inventory, name=k, variables=variables, created_by=user,
                    description="imported")
                group.save()

        # if overwrite is set, clear any host membership on all hosts that should not exist
        if overwrite:
            LOGGER.info("purging host group memberships")
            db_groups = Group.objects.filter(inventory=inventory)

            for db_group in db_groups:
                 db_hosts = db_group.hosts.all()
                 mem_hosts = group_names[db_group.name].hosts
                 mem_host_names = [ h.name for h in mem_hosts ]
                 removed = False
                 for db_host in db_hosts:
                     if db_host.name not in mem_host_names:
                         removed = True
                         print "DEBUG: removing non-DB host: %s" % (db_host.name)
                         db_group.hosts.remove(db_host)
                 if removed:
                     db_group.save()


        # for each host in a mem group, add it to the parents to which it belongs
        # FIXME: confirm Django is ok with calling add twice and not making two rows
        for (k,v) in group_names.iteritems():
            LOGGER.info("adding parent arrangements for %s" % k)
            db_group = Group.objects.get(name=k, inventory__pk=inventory.pk)
            mem_hosts = v.hosts
            for h in mem_hosts:
                db_host = Host.objects.get(name=h.name, inventory__pk=inventory.pk)
                db_group.hosts.add(db_host)
                print "*** ADDING %s to %s ***" % (db_host, db_group) 
            db_group.save()

        def variable_mangler(model, mem_hash, overwrite, overwrite_vars):
            db_collection = model.objects.filter(inventory=inventory)
            for obj in db_collection:
               if obj.name in mem_hash:
                   mem_group = mem_hash[obj.name]
                   db_variables = json.loads(obj.variables)
                   mem_variables = mem_group.variables
                   if overwrite_vars or overwrite:
                       db_variables = mem_variables
                   else:
                       db_variables.update(mem_variables)
                   db_variables = json.dumps(db_variables)
                   obj.variables = db_variables
                   obj.save()

        variable_mangler(Group, group_names, overwrite, overwrite_vars)
        variable_mangler(Host,  host_names,  overwrite, overwrite_vars)
  
        # for each group, draw in child group arrangements
        # FIXME: confirm django add behavior as above
        for (k,v) in group_names.iteritems():
            db_group = Group.objects.get(inventory=inventory, name=k)
            for mem_child_group in v.child_groups:
                db_child = Group.objects.get(inventory=inventory, name=mem_child_group.name)
                db_group.children.add(db_child)
            db_group.save()

        reader = LicenseReader()
        license_info = reader.from_file()
        available_instances = license_info.get('available_instances', 0)
        free_instances = license_info.get('free_instances', 0)
        new_count = Host.objects.filter(active=True).count()
        if free_instances < 0:
            if license_info.get('demo', False):
                raise ImportError("demo mode free license count exceeded, would bring available instances to %s, demo mode allows %s, see http://ansibleworks.com/ansibleworks-awx for licensing information" % (new_count, available_instances))
            else:
                raise ImportError("number of licensed instances exceeded, would bring available instances to %s, system is licensed for %s, see http://ansibleworks.com/ansibleworks-awx for license extension information" % (new_count, available_instances))
 
        LOGGER.info("inventory import complete, %s, id=%s" % (inventory.name, inventory.id))


