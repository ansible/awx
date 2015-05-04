# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from datetime import datetime

# Django
from django.conf import settings

# Pymongo
import pymongo

# AWX
from awx.fact.models.fact import * # noqa
from .base import BaseFactTest

__all__ = ['FactTransformTest', 'FactTransformUpdateTest',]

TEST_FACT_DATA = {
    'hostname': 'hostname1',
    'add_fact_data': {
        'timestamp': datetime.now(),
        'host': None,
        'module': 'packages',
        'fact': {
            "acpid3.4": [
                {
                    "version": "1:2.0.21-1ubuntu2",
                    "deeper.key": "some_value"
                }
            ],
            "adduser.2": [
                {
                    "source": "apt",
                    "version": "3.113+nmu3ubuntu3"
                }
            ],
            "what.ever." : {
                "shallowish.key": "some_shallow_value"
            }
        },
    }
}
# Strip off microseconds because mongo has less precision
BaseFactTest.normalize_timestamp(TEST_FACT_DATA)

class FactTransformTest(BaseFactTest):
    def setUp(self):
        super(FactTransformTest, self).setUp()
        # TODO: get host settings from config
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db2 = self.client[settings.MONGO_DB]

        self.create_host_document(TEST_FACT_DATA)

    def setup_create_fact_dot(self):
        self.data = TEST_FACT_DATA
        self.f = Fact(**TEST_FACT_DATA['add_fact_data'])
        self.f.save()

    def setup_create_fact_dollar(self):
        self.data = TEST_FACT_DATA
        self.f = Fact(**TEST_FACT_DATA['add_fact_data'])
        self.f.save()

    def test_fact_with_dot_serialized(self):
        self.setup_create_fact_dot()

        q = {
            '_id': self.f.id
        }

        # Bypass mongoengine and pymongo transform to get record
        f_dict = self.db2['fact'].find_one(q)
        self.assertIn('acpid3\uff0E4', f_dict['fact'])

    def test_fact_with_dot_serialized_pymongo(self):
        #self.setup_create_fact_dot()

        f = self.db['fact'].insert({ 
            'hostname': TEST_FACT_DATA['hostname'],
            'fact': TEST_FACT_DATA['add_fact_data']['fact'],
            'timestamp': TEST_FACT_DATA['add_fact_data']['timestamp'],
            'host': TEST_FACT_DATA['add_fact_data']['host'].id,
            'module': TEST_FACT_DATA['add_fact_data']['module']
        })

        q = {
            '_id': f
        }
        # Bypass mongoengine and pymongo transform to get record
        f_dict = self.db2['fact'].find_one(q)
        self.assertIn('acpid3\uff0E4', f_dict['fact'])

    def test_fact_with_dot_deserialized_pymongo(self):
        self.setup_create_fact_dot()

        q = {
            '_id': self.f.id
        }
        f_dict = self.db['fact'].find_one(q)
        self.assertIn('acpid3.4', f_dict['fact'])

    def test_fact_with_dot_deserialized(self):
        self.setup_create_fact_dot()

        f = Fact.objects.get(id=self.f.id)
        self.assertIn('acpid3.4', f.fact)

class FactTransformUpdateTest(BaseFactTest):
    pass
