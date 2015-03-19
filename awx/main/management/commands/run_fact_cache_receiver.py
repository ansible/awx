# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import logging

from django.core.management.base import NoArgsCommand

from awx.main.models import * # noqa
from awx.main.socket import Socket

from pymongo import MongoClient

logger = logging.getLogger('awx.main.commands.run_fact_cache_receiver')

from pymongo.son_manipulator import SONManipulator
 
class KeyTransform(SONManipulator):
    """Transforms keys going to database and restores them coming out.

    This allows keys with dots in them to be used (but does break searching on
    them unless the find command also uses the transform.

    Example & test:
        # To allow `.` (dots) in keys
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost")
        db = client['delete_me']
        db.add_son_manipulator(KeyTransform(".", "_dot_"))
        db['mycol'].remove()
        db['mycol'].update({'_id': 1}, {'127.0.0.1': 'localhost'}, upsert=True,
                           manipulate=True)
        print db['mycol'].find().next()
        print db['mycol'].find({'127_dot_0_dot_0_dot_1': 'localhost'}).next()

    Note: transformation could be easily extended to be more complex.
    """
 
    def __init__(self, replace, replacement):
        self.replace = replace
        self.replacement = replacement
 
    def transform_key(self, key):
        """Transform key for saving to database."""
        return key.replace(self.replace, self.replacement)
 
    def revert_key(self, key):
        """Restore transformed key returning from database."""
        return key.replace(self.replacement, self.replace)
 
    def transform_incoming(self, son, collection):
        """Recursively replace all keys that need transforming."""
        for (key, value) in son.items():
            if self.replace in key:
                if isinstance(value, dict):
                    son[self.transform_key(key)] = self.transform_incoming(
                        son.pop(key), collection)
                else:
                    son[self.transform_key(key)] = son.pop(key)
            elif isinstance(value, dict):  # recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son
 
    def transform_outgoing(self, son, collection):
        return son

class FactCacheReceiver(object):

    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        
    def process_fact_message(self, message):
        host = message['host'].replace(".", "_")
        facts = message['facts']
        date_key = message['date_key']
        host_db = self.client.host_facts
        host_db.add_son_manipulator(KeyTransform(".", "_"))
        host_db.add_son_manipulator(KeyTransform("$", "_"))
        host_collection = host_db[host]
        facts.update(dict(tower_host=host, datetime=date_key))
        rec = host_collection.find({"datetime": date_key})
        if rec.count():
            this_fact = rec.next()
            this_fact.update(facts)
            host_collection.save(this_fact)
        else:
            host_collection.insert(facts)

    def run_receiver(self):
        with Socket('fact_cache', 'r') as facts:
            for message in facts.listen():
                if 'host' not in message or 'facts' not in message or 'date_key' not in message:
                    continue
                self.process_fact_message(message)

class Command(NoArgsCommand):
    '''
    blah blah
    '''
    help = 'Launch the Fact Cache Receiver'

    def handle_noargs(self, **options):
        fcr = FactCacheReceiver()
        try:
            fcr.run_receiver()
        except KeyboardInterrupt:
            pass

