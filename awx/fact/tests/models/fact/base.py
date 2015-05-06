# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from awx.main.tests.base import BaseTest, MongoDBRequired
from copy import deepcopy
from datetime import datetime

# AWX
from awx.fact.models.fact import * # noqa

'''
Helper functions (i.e. create_host_document) expect the structure:
{
    'hostname': 'hostname1',
    'add_fact_data': {
        'timestamp': datetime.now(),
        'host': None,
        'module': 'packages',
        'fact': ...
    }
}
'''
class BaseFactTest(BaseTest, MongoDBRequired):

    @staticmethod
    def _normalize_timestamp(timestamp):
        return timestamp.replace(microsecond=0)

    @staticmethod
    def normalize_timestamp(data):
        data['add_fact_data']['timestamp'] = BaseFactTest._normalize_timestamp(data['add_fact_data']['timestamp'])

    def create_host_document(self, data):
        data['add_fact_data']['host'] = FactHost(hostname=data['hostname']).save()

    def create_fact_scans(self, data, host_count=1, scan_count=1):
        timestamps = []
        self.fact_data = []
        self.fact_objs = []
        self.hostnames = [FactHost(hostname='%s_%s' % (data['hostname'], i)).save() for i in range(0, host_count)]
        for i in range(0, scan_count):
            self.fact_data.append([])
            self.fact_objs.append([])
            for j in range(0, host_count):
                data = deepcopy(data)
                t = datetime.now().replace(year=2015 - i, microsecond=0)
                data['add_fact_data']['timestamp'] = t
                data['add_fact_data']['host'] = self.hostnames[j]
                (f, v) = Fact.add_fact(**data['add_fact_data'])
                timestamps.append(t)

                self.fact_data[i].append(data)
                self.fact_objs[i].append(f)

        return timestamps
