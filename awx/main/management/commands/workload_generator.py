# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import pymongo
import sys
from optparse import make_option
import datetime
import json

# Django
from django.core.management.base import BaseCommand
from django.utils.timezone import now

# Mongoengine
import mongoengine

# awx
from awx.fact.models.fact import * # noqa
from awx.main.models import * # noqa

TEST_FACT_ANSIBLE = {
    "ansible_swapfree_mb" : 4092,
    "ansible_default_ipv6" : {
        
    },
    "ansible_distribution_release" : "trusty",
    "ansible_system_vendor" : "innotek GmbH",
    "ansible_os_family" : "Debian",
    "ansible_all_ipv4_addresses" : [
        "192.168.1.145"
    ],
    "ansible_lsb" : {
        "release" : "14.04",
        "major_release" : "14",
        "codename" : "trusty",
        "id" : "Ubuntu",
        "description" : "Ubuntu 14.04.2 LTS"
    },
}

TEST_FACT_PACKAGES = [
    {
        "name": "accountsservice",
        "architecture": "amd64",
        "source": "apt",
        "version": "0.6.35-0ubuntu7.1"
    },
    {
        "name": "acpid",
        "architecture": "amd64",
        "source": "apt",
        "version": "1:2.0.21-1ubuntu2"
    },
    {
        "name": "adduser",
        "architecture": "all",
        "source": "apt",
        "version": "3.113+nmu3ubuntu3"
    },
]

TEST_FACT_SERVICES = [
    {
        "source" : "upstart",
        "state" : "waiting",
        "name" : "ureadahead-other",
        "goal" : "stop"
    },
    {
        "source" : "upstart",
        "state" : "running",
        "name" : "apport",
        "goal" : "start"
    },
    {
        "source" : "upstart",
        "state" : "waiting",
        "name" : "console-setup",
        "goal" : "stop"
    },
]

TEST_FACT_FILES = [
        {
            "uid": 0, 
            "woth": False, 
            "mtime": 1436810539.5895822, 
            "inode": 525214, 
            "isgid": False, 
            "size": 0, 
            "isuid": False, 
            "isreg": True, 
            "gid": 0, 
            "ischr": False, 
            "wusr": True, 
            "xoth": False, 
            "islnk": False, 
            "nlink": 1, 
            "issock": False, 
            "rgrp": True, 
            "path": "/test/1948", 
            "xusr": False, 
            "atime": 1436810539.5895822, 
            "isdir": False, 
            "ctime": 1436810539.5895822, 
            "isblk": False, 
            "wgrp": False, 
            "xgrp": False, 
            "dev": 64768, 
            "roth": True, 
            "isfifo": False, 
            "mode": "0644", 
            "rusr": True
        }, 
        {
            "uid": 0, 
            "woth": False, 
            "mtime": 1436810540.4955823, 
            "inode": 526295, 
            "isgid": False, 
            "size": 0, 
            "isuid": False, 
            "isreg": True, 
            "gid": 0, 
            "ischr": False, 
            "wusr": True, 
            "xoth": False, 
            "islnk": False, 
            "nlink": 1, 
            "issock": False, 
            "rgrp": True, 
            "path": "/test/3029", 
            "xusr": False, 
            "atime": 1436810540.4955823, 
            "isdir": False, 
            "ctime": 1436810540.4955823, 
            "isblk": False, 
            "wgrp": False, 
            "xgrp": False, 
            "dev": 64768, 
            "roth": True, 
            "isfifo": False, 
            "mode": "0644", 
            "rusr": True
        }, 
        {
            "uid": 0, 
            "woth": False, 
            "mtime": 1436810540.5825822, 
            "inode": 526401, 
            "isgid": False, 
            "size": 0, 
            "isuid": False, 
            "isreg": True, 
            "gid": 0, 
            "ischr": False, 
            "wusr": True, 
            "xoth": False, 
            "islnk": False, 
            "nlink": 1, 
            "issock": False, 
            "rgrp": True, 
            "path": "/test/3135", 
            "xusr": False, 
            "atime": 1436810540.5825822, 
            "isdir": False, 
            "ctime": 1436810540.5825822, 
            "isblk": False, 
            "wgrp": False, 
            "xgrp": False, 
            "dev": 64768, 
            "roth": True, 
            "isfifo": False, 
            "mode": "0644", 
            "rusr": True
        }, 
]

FACT_FIXTURES = {
    'ansible': TEST_FACT_ANSIBLE,
    'packages': TEST_FACT_PACKAGES,
    'services': TEST_FACT_SERVICES,
    'files': TEST_FACT_FILES,
}

EXPERIMENT_DEFAULT = {
    "hosts": 10,
    "scan": {
        "duration" : int(525949), # 1 year
        "period": 1440 # 1 day
    },
    "modules": [
        "ansible",
        "packages",
        "services",
        "files"
    ]
}

# damn you python 2.6
def timedelta_total_seconds(timedelta):
    return (
        timedelta.microseconds + 0.0 +
        (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6

class Experiment(object):
    def __init__(self, exp, fact_fixtures, raw_db, mongoengine_db):
        self.db = raw_db
        self.enginedb = mongoengine_db

        for module in exp['modules']:
            if module not in fact_fixtures:
                raise RuntimeError("Module %s fixture not found in %s" % (module, fact_fixtures))

        # Setup experiment from experiment params
        self.fact_fixtures = fact_fixtures
        self.host_count = exp['hosts']
        self.scans_total = int(exp['scan']['duration'] / exp['scan']['period']) # round down
        self.scan_end = int(timedelta_total_seconds((datetime.datetime(2015,1,1) - datetime.datetime(1970,1,1))) / 60)
        self.scan_start = self.scan_end - exp['scan']['duration']
        self.scan_period = exp['scan']['period']
        self.modules = exp['modules']

        # Changing vars
        self.scan_time_last = self.scan_start
        self.scan_time = self.scan_start

        # 
        self.user = None
        self.org = None
        self.inv = None
        self.hosts = []

    @property
    def scan_datetime(self):
        return datetime.datetime.fromtimestamp(self.scan_time * 60)

    def _delete_tower_metadata(self):
        invs = Inventory.objects.filter(name='sys_tracking_inventory')
        org = Organization.objects.filter(name='sys_tracking_organization')
        if invs:
            for inv in invs:
                for host in inv.hosts.all():
                    host.delete()
            invs.delete()
        org.delete()
        User.objects.filter(username='boberson').delete()

    '''
    Create an org and an inventory
    '''
    def _create_tower_metadata(self):
        self.user = User.objects.create_user('boberson', "%s@example.com", 'scoobasteve')
        self.org = Organization.objects.create(
            name='sys_tracking_organization',
            description='The system tracking organization is serious about seriousness.',
            created_by=self.user,
        )
        self.org.admins.add(self.user)
        self.inv = self.org.inventories.create(
            name='sys_tracking_inventory',
            created_by=self.user,
        )
        for x in range(0, self.host_count):
            host = self.inv.hosts.create(name='hostname_%s.doesnotexist.ansible.com' % x,
                                         inventory=self.inv)
            self.hosts.append(host)

    def generate_workload(self):
        time_start = now()
        print("Started at: %s" % time_start)

        # TODO only call delete if --dropdb ??
        self._delete_tower_metadata()

        print("Creating needed tower models (i.e. org, inventory, etc.)")
        self._create_tower_metadata()
        print("Generating workload ")

        scan_time_backup = self.scan_time
        for host_i in range(0, self.host_count):
            # Reset scan time
            self.scan_time = scan_time_backup
            sys.stdout.write('.')
            sys.stdout.flush()
            host = FactHost(hostname='hostname_%s.doesnotexist.ansible.com' % host_i, inventory_id=self.inv.pk).save()
            for scan_i in range(0, self.scans_total):
                for module in self.modules:
                    Fact.add_fact(self.scan_datetime, host=host, module=module, fact=self.fact_fixtures[module])

                    self.scan_time_last = self.scan_time
                    self.scan_time += self.scan_period
        time_end = now()
        print("")
        print("Finished at: %s" % time_end)
        print("Total runtime: %s seconds" % timedelta_total_seconds(time_end - time_start))

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--drop', dest='drop', action='store_true', default=False, 
                    help='Drop collections before generating workload.'),
        make_option('--experiment', dest='experiment', action='store', default=None,
                    help='experiment config file defining the params'),
        make_option('--host', dest='host', action='store', type='string', default='localhost',
                    help='mongodb host'),
        make_option('--username', dest='username', action='store', type='string', default=None,
                    help='mongodb username'),
        make_option('--password', dest='password', action='store', type='string', default=None,
                    help='mongodb password'),
        make_option('--port', dest='port', action='store', type='int', default=27017,
                    help='mongodb port'),
        make_option('--db', dest='db', action='store', type='string', default='system_tracking_workload',
                    help='mongodb database name'),
        make_option('--quite', dest='quite', action='store_true', default=False,
                    help='Surpress the printing of large results.'),
        make_option('--silent', dest='silent', action='store_true', default=False,
                    help='Surpress the printing of ALL results.'),
    )

    def handle(self, *args, **options):
        # TODO: load experiment from file, json
        if options['experiment']:
            f = open(options['experiment'])
            exp = json.loads(f.read())
        else:
            exp = EXPERIMENT_DEFAULT
        print("Experiment settings\n%s\n" % exp)

        self.client = pymongo.MongoClient(options['host'], options['port'])
        db = self.client[options['db']]

        connection_params = dict((k, options[k]) for k in ['host', 'port', 'username', 'password'])

        mongoengine.connection.disconnect()
        enginedb = mongoengine.connection.connect(options['db'], **connection_params)
        if options['drop']:
            enginedb.drop_database(options['db'])

        self.experiment = Experiment(exp, FACT_FIXTURES, db, enginedb)
        self.experiment.generate_workload()

