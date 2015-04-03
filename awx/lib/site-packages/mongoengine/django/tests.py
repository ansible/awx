#coding: utf-8

from unittest import TestCase

from mongoengine import connect
from mongoengine.connection import get_db


class MongoTestCase(TestCase):
    """
    TestCase class that clear the collection between the tests
    """

    @property
    def db_name(self):
        from django.conf import settings
        return 'test_%s' % getattr(settings, 'MONGO_DATABASE_NAME', 'dummy')

    def __init__(self, methodName='runtest'):
        connect(self.db_name)
        self.db = get_db()
        super(MongoTestCase, self).__init__(methodName)

    def dropCollections(self):
        for collection in self.db.collection_names():
            if collection.startswith('system.'):
                continue
            self.db.drop_collection(collection)

    def tearDown(self):
        self.dropCollections()
