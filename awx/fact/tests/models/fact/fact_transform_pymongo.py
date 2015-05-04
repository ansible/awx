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

__all__ = ['FactSerializePymongoTest', 'FactDeserializePymongoTest',]

class FactPymongoBaseTest(BaseFactTest):
    def setUp(self):
        super(FactPymongoBaseTest, self).setUp()
        # TODO: get host settings from config
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db2 = self.client[settings.MONGO_DB]

    def _create_fact(self):
        fact = {}
        fact[self.k] = self.v
        q = {
            'hostname': 'blah'
        }
        h = self.db['fact_host'].insert(q)
        q = { 
            'host': h,
            'module': 'blah',
            'timestamp': datetime.now(),
            'fact': fact
        }
        f = self.db['fact'].insert(q)
        return f

    def check_transform(self, id):
        raise RuntimeError("Must override")

    def create_dot_fact(self):
        self.k = 'this.is.a.key'
        self.v = 'this.is.a.value'

        self.k_uni = 'this\uff0Eis\uff0Ea\uff0Ekey'

        return self._create_fact()

    def create_dollar_fact(self):
        self.k = 'this$is$a$key'
        self.v = 'this$is$a$value'

        self.k_uni = 'this\uff04is\uff04a\uff04key'

        return self._create_fact()

class FactSerializePymongoTest(FactPymongoBaseTest):
    def check_transform(self, id):
        q = {
            '_id': id
        }
        f = self.db2.fact.find_one(q)
        self.assertIn(self.k_uni, f['fact'])
        self.assertEqual(f['fact'][self.k_uni], self.v)

    # Ensure key . are being transformed to the equivalent unicode into the database
    def test_key_transform_dot(self):
        f = self.create_dot_fact()
        self.check_transform(f)

    # Ensure key $ are being transformed to the equivalent unicode into the database
    def test_key_transform_dollar(self):
        f = self.create_dollar_fact()
        self.check_transform(f)

class FactDeserializePymongoTest(FactPymongoBaseTest):
    def check_transform(self, id):
        q = {
            '_id': id
        }
        f = self.db.fact.find_one(q)
        self.assertIn(self.k, f['fact'])
        self.assertEqual(f['fact'][self.k], self.v)

    def test_key_transform_dot(self):
        f = self.create_dot_fact()
        self.check_transform(f)

    def test_key_transform_dollar(self):
        f = self.create_dollar_fact()
        self.check_transform(f)
