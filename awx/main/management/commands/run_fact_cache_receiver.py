# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
from threading import Thread
from datetime import datetime

# Django
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.utils import timezone

# AWX
from awx.main.models.fact import Fact
from awx.main.models.inventory import Host
from awx.main.socket_queue import Socket

logger = logging.getLogger('awx.main.commands.run_fact_cache_receiver')

class FactCacheReceiver(object):
    def __init__(self):
        self.timestamp = None

    def _determine_module(self, facts):
        # Symantically determine the module type
        if len(facts) == 1:
            return facts.iterkeys().next()
        return 'ansible'

    def _extract_module_facts(self, module, facts):
        if module in facts:
            f = facts[module]
            return f
        return facts

    def process_facts(self, facts):
        module = self._determine_module(facts)
        facts = self._extract_module_facts(module, facts)
        return (module, facts)

    def process_fact_message(self, message):
        hostname = message['host']
        inventory_id = message['inventory_id']
        facts_data = message['facts']
        date_key = message['date_key']

        # TODO: in ansible < v2 module_setup is emitted for "smart" fact caching.
        # ansible v2 will not emit this message. Thus, this can be removed at that time.
        if 'module_setup' in facts_data and len(facts_data) == 1:
            logger.info('Received module_setup message')
            return None

        try:
            host_obj = Host.objects.get(name=hostname, inventory__id=inventory_id)
        except Fact.DoesNotExist:
            logger.warn('Failed to intake fact. Host does not exist <hostname, inventory_id> <%s, %s>' % (hostname, inventory_id))
            return
        except Fact.MultipleObjectsReturned:
            logger.warn('Database inconsistent. Multiple Hosts found for <hostname, inventory_id> <%s, %s>.' % (hostname, inventory_id))
            return None
        except Exception as e:
            logger.error("Exception communicating with Fact Cache Database: %s" % str(e))
            return None

        (module_name, facts) = self.process_facts(facts_data)
        self.timestamp = datetime.fromtimestamp(date_key, timezone.utc)

        # Update existing Fact entry
        try:
            fact_obj = Fact.objects.get(host__id=host_obj.id, module=module_name, timestamp=self.timestamp)
            fact_obj.facts = facts
            fact_obj.save()
            logger.info('Updated existing fact <%s>' % (fact_obj.id))
        except Fact.DoesNotExist:
            # Create new Fact entry
            fact_obj = Fact.add_fact(host_obj.id, module_name, self.timestamp, facts)
            logger.info('Created new fact <fact_id, module> <%s, %s>' % (fact_obj.id, module_name))
        return fact_obj

    def run_receiver(self, use_processing_threads=True):
        with Socket('fact_cache', 'r') as facts:
            for message in facts.listen():
                if 'host' not in message or 'facts' not in message or 'date_key' not in message:
                    logger.warn('Received invalid message %s' % message)
                    continue
                logger.info('Received message %s' % message)
                if use_processing_threads:
                    wt = Thread(target=self.process_fact_message, args=(message,))
                    wt.start()
                else:
                    self.process_fact_message(message)

class Command(NoArgsCommand):
    '''
    blah blah
    '''
    help = 'Launch the Fact Cache Receiver'

    def handle_noargs(self, **options):
        fcr = FactCacheReceiver()
        fact_cache_port = settings.FACT_CACHE_PORT
        logger.info('Listening on port http://0.0.0.0:' + str(fact_cache_port))
        try:
            fcr.run_receiver()
        except KeyboardInterrupt:
            pass

