# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from django.utils.timezone import now

# Django
from django.conf import settings
import django

# MongoEngine
from mongoengine.connection import get_db, ConnectionError

# AWX
from awx.fact.models.fact import * # noqa

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


class MongoDBRequired(django.test.TestCase):
    def setUp(self):
        # Drop mongo database
        try:
            self.db = get_db()
            self.db.connection.drop_database(settings.MONGO_DB)
        except ConnectionError:
            self.skipTest('MongoDB connection failed')

class BaseFactTestMixin(MongoDBRequired):
    pass

class BaseFactTest(BaseFactTestMixin, MongoDBRequired):
    pass

class FactScanBuilder(object):

    def __init__(self):
        self.facts_data = {}
        self.hostname_data = []

        self.host_objs = []
        self.fact_objs = []
        self.version_objs = []
        self.timestamps = []

    def add_fact(self, module, facts):
        self.facts_data[module] = facts

    def add_hostname(self, hostname):
        self.hostname_data.append(hostname)

    def build(self, scan_count, host_count):
        if len(self.facts_data) == 0:
            raise RuntimeError("No fact data to build populate scans. call add_fact()")
        if (len(self.hostname_data) > 0 and len(self.hostname_data) != host_count):
            raise RuntimeError("Registered number of hostnames %d does not match host_count %d" % (len(self.hostname_data), host_count))

        if len(self.hostname_data) == 0:
            self.hostname_data = ['hostname_%s' % i for i in range(0, host_count)]

        self.host_objs = [FactHost(hostname=hostname).save() for hostname in self.hostname_data]

        for i in range(0, scan_count):
            scan = {}
            scan_version = {}
            timestamp = now().replace(year=2015 - i, microsecond=0)
            for module in self.facts_data:
                fact_objs = []
                version_objs = []
                for host in self.host_objs:
                    (fact_obj, version_obj) = Fact.add_fact(timestamp=timestamp, 
                                                            host=host, 
                                                            module=module, 
                                                            fact=self.facts_data[module])
                    fact_objs.append(fact_obj)
                    version_objs.append(version_obj)
                scan[module] = fact_objs
                scan_version[module] = version_objs
            self.fact_objs.append(scan)
            self.version_objs.append(scan_version)
            self.timestamps.append(timestamp)


    def get_scan(self, index, module=None):
        res = None
        res = self.fact_objs[index]
        if module:
            res = res[module]
        return res

    def get_scans(self, index_start=None, index_end=None):
        if index_start is None:
            index_start = 0
        if index_end is None:
            index_end = len(self.fact_objs)
        return self.fact_objs[index_start:index_end]

    def get_scan_version(self, index, module=None):
        res = None
        res = self.version_objs[index]
        if module:
            res = res[module]
        return res

    def get_scan_versions(self, index_start=None, index_end=None):
        if index_start is None:
            index_start = 0
        if index_end is None:
            index_end = len(self.version_objs)
        return self.version_objs[index_start:index_end]

    def get_hostname(self, index):
        return self.host_objs[index].hostname
        
    def get_hostnames(self, index_start=None, index_end=None):
        if index_start is None:
            index_start = 0
        if index_end is None:
            index_end = len(self.host_objs)

        return [self.host_objs[i].hostname for i in range(index_start, index_end)]


    def get_scan_count(self):
        return len(self.fact_objs)

    def get_host_count(self):
        return len(self.host_objs)

    def get_timestamp(self, index):
        return self.timestamps[index]

    def get_timestamps(self, index_start=None, index_end=None):
        if not index_start:
            index_start = 0
        if not index_end:
            len(self.timestamps)
        return self.timestamps[index_start:index_end]

