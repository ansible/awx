# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import logging

from django.core.management.base import NoArgsCommand

from awx.main.models import * # noqa
from awx.main.socket import Socket

from pymongo import MongoClient

logger = logging.getLogger('awx.main.commands.run_fact_cache_receiver')

class FactCacheReceiver(object):

    def __init__(self):
        self.client = MongoClient('localhost', 27017)

    def process_fact_message(self, message):
        host = message['host']
        facts = message['facts']
        date_key = message['date_key']
        host_db = self.client.host_facts
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
                print("Message received: " + str(message))
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

