# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from awx.main.tests.base import BaseTest, MongoDBRequired

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
