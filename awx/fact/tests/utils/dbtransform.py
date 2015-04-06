# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import datetime
from mongoengine import connect

# Django
from django.conf import settings

# AWX
from awx.main.tests.base import BaseTest, MongoDBRequired
from awx.fact.models.fact import * # noqa

__all__ = ['DBTransformTest']

class DBTransformTest(BaseTest, MongoDBRequired):
    def setUp(self):
        super(DBTransformTest, self).setUp()

        # Create a db connection that doesn't have the transformation registered
        # Note: this goes through pymongo not mongoengine
        self.client = connect(settings.MONGO_DB)
        self.db = self.client[settings.MONGO_DB]

    def _create_fact(self):
        fact = {}
        fact[self.k] = self.v
        h = FactHost(hostname='blah')
        h.save()
        f = Fact(host=h,module='blah',timestamp=datetime.now(),fact=fact)
        f.save()
        return f

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

    def check_unicode(self, f):
        f_raw = self.db.fact.find_one(id=f.id)
        self.assertIn(self.k_uni, f_raw['fact'])
        self.assertEqual(f_raw['fact'][self.k_uni], self.v)

    # Ensure key . are being transformed to the equivalent unicode into the database
    def test_key_transform_dot_unicode_in_storage(self):
        f = self.create_dot_fact()
        self.check_unicode(f)

    # Ensure key $ are being transformed to the equivalent unicode into the database
    def test_key_transform_dollar_unicode_in_storage(self):
        f = self.create_dollar_fact()
        self.check_unicode(f)

    def check_transform(self):
        f = Fact.objects.all()[0]
        self.assertIn(self.k, f.fact)
        self.assertEqual(f.fact[self.k], self.v)

    def test_key_transform_dot_on_retreive(self):
        self.create_dot_fact()
        self.check_transform()

    def test_key_transform_dollar_on_retreive(self):
        self.create_dollar_fact()
        self.check_transform()
