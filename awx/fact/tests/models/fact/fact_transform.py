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
from awx.fact.tests.base import BaseFactTest

__all__ = ['FactTransformTest', 'FactTransformUpdateTest',]

TEST_FACT_PACKAGES_WITH_DOTS = [
    {
        "name": "acpid3.4",
        "version": "1:2.0.21-1ubuntu2",
        "deeper.key": "some_value"
    },
    {
        "name": "adduser.2",
        "source": "apt",
        "version": "3.113+nmu3ubuntu3"
    },
    {
        "what.ever." : {
            "shallowish.key": "some_shallow_value"
        }
    }
]

TEST_FACT_PACKAGES_WITH_DOLLARS = [
    {
        "name": "acpid3$4",
        "version": "1:2.0.21-1ubuntu2",
        "deeper.key": "some_value"
    },
    {
        "name": "adduser$2",
        "source": "apt",
        "version": "3.113+nmu3ubuntu3"
    },
    {
        "what.ever." : {
            "shallowish.key": "some_shallow_value"
        }
    }
]
class FactTransformTest(BaseFactTest):
    def setUp(self):
        super(FactTransformTest, self).setUp()
        # TODO: get host settings from config
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db2 = self.client[settings.MONGO_DB]

        self.timestamp = datetime.now().replace(microsecond=0)

    def setup_create_fact_dot(self):
        self.host = FactHost(hostname='hosty').save()
        self.f = Fact(timestamp=self.timestamp, module='packages', fact=TEST_FACT_PACKAGES_WITH_DOTS, host=self.host)
        self.f.save()

    def setup_create_fact_dollar(self):
        self.host = FactHost(hostname='hosty').save()
        self.f = Fact(timestamp=self.timestamp, module='packages', fact=TEST_FACT_PACKAGES_WITH_DOLLARS, host=self.host)
        self.f.save()

    def test_fact_with_dot_serialized(self):
        self.setup_create_fact_dot()

        q = {
            '_id': self.f.id
        }

        # Bypass mongoengine and pymongo transform to get record
        f_dict = self.db2['fact'].find_one(q)
        self.assertIn('what\uff0Eever\uff0E', f_dict['fact'][2])

    def test_fact_with_dot_serialized_pymongo(self):
        #self.setup_create_fact_dot()

        host = FactHost(hostname='hosty').save()
        f = self.db['fact'].insert({ 
            'hostname': 'hosty',
            'fact': TEST_FACT_PACKAGES_WITH_DOTS,
            'timestamp': self.timestamp,
            'host': host.id,
            'module': 'packages',
        })

        q = {
            '_id': f
        }
        # Bypass mongoengine and pymongo transform to get record
        f_dict = self.db2['fact'].find_one(q)
        self.assertIn('what\uff0Eever\uff0E', f_dict['fact'][2])

    def test_fact_with_dot_deserialized_pymongo(self):
        self.setup_create_fact_dot()

        q = {
            '_id': self.f.id
        }
        f_dict = self.db['fact'].find_one(q)
        self.assertIn('what.ever.', f_dict['fact'][2])

    def test_fact_with_dot_deserialized(self):
        self.setup_create_fact_dot()

        f = Fact.objects.get(id=self.f.id)
        self.assertIn('what.ever.', f.fact[2])

class FactTransformUpdateTest(BaseFactTest):
    pass
