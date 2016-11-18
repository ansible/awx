# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
from threading import Thread
from datetime import datetime

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

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


class FactBrokerWorker(ConsumerMixin):

    def __init__(self, connection):
        self.connection = connection
        self.timestamp = None

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[Queue(settings.FACT_QUEUE,
                                       Exchange(settings.FACT_QUEUE, type='direct'),
                                       routing_key=settings.FACT_QUEUE)],
                         accept=['json'],
                         callbacks=[self.process_fact_message])]

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

    def process_fact_message(self, body, message):
        print body
        print type(body)
        hostname = body['host']
        inventory_id = body['inventory_id']
        facts_data = body['facts']
        date_key = body['date_key']

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


class Command(NoArgsCommand):
    '''
    Save Fact Event packets to the database as emitted from a Tower Scan Job
    '''
    help = 'Launch the Fact Cache Receiver'

    def handle_noargs(self, **options):
        with Connection(settings.BROKER_URL) as conn:
            try:
                worker = FactBrokerWorker(conn)
                worker.run()
            except KeyboardInterrupt:
                pass

