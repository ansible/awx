# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
from datetime import datetime

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

# Django
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.utils import timezone

# AWX
from awx.main.models.jobs import Job
from awx.main.models.fact import Fact
from awx.main.models.inventory import Host
from awx.main.models.base import PERM_INVENTORY_SCAN

logger = logging.getLogger('awx.main.commands.run_fact_cache_receiver')
analytics_logger = logging.getLogger('awx.analytics.system_tracking')


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

    def _do_fact_scan_create_update(self, host_obj, module_name, facts, timestamp):
        try:
            fact_obj = Fact.objects.get(host__id=host_obj.id, module=module_name, timestamp=timestamp)
            fact_obj.facts = facts
            fact_obj.save()
            logger.info('Updated existing fact <%s>' % (fact_obj.id))
        except Fact.DoesNotExist:
            # Create new Fact entry
            fact_obj = Fact.add_fact(host_obj.id, module_name, self.timestamp, facts)
            logger.info('Created new fact <fact_id, module> <%s, %s>' % (fact_obj.id, module_name))
            analytics_logger.info('Received message with fact data', extra=dict(
                module_name=module_name, facts_data=facts))
        return fact_obj

    def _do_gather_facts_update(self, host_obj, module_name, facts, timestamp):
        host_obj.update_ansible_facts(module=module_name, facts=facts, timestamp=self.timestamp)
        return host_obj

    def process_fact_message(self, body, message):
        hostname = body['host']
        inventory_id = body['inventory_id']
        job_id = body.get('job_id', -1)
        facts_data = body['facts']
        date_key = body['date_key']

        is_fact_scan = False
        job = None

        '''
        In Tower < 3.2 we neglected to ack the incoming message.
        In Tower 3.2 we add the job_id parameter.
        To account for this, we need to fail gracefully when the job is not
        found.
        '''

        try: 
            job = Job.objects.get(id=job_id)
            is_fact_scan = True if job.job_type == PERM_INVENTORY_SCAN else False
        except Job.DoesNotExist:
            logger.warn('Failed to find job %s while processing facts' % job_id)
            message.ack()
            return None

        try:
            host_obj = Host.objects.get(name=hostname, inventory__id=inventory_id)
        except Fact.DoesNotExist:
            logger.warn('Failed to intake fact. Host does not exist <hostname, inventory_id> <%s, %s>' % (hostname, inventory_id))
            message.ack()
            return None
        except Fact.MultipleObjectsReturned:
            logger.warn('Database inconsistent. Multiple Hosts found for <hostname, inventory_id> <%s, %s>.' % (hostname, inventory_id))
            message.ack()
            return None
        except Exception as e:
            logger.error("Exception communicating with Fact Cache Database: %s" % str(e))
            message.ack()
            return None

        (module_name, facts) = self.process_facts(facts_data)
        self.timestamp = datetime.fromtimestamp(date_key, timezone.utc)

        ret = None
        # Update existing Fact entry
        if is_fact_scan is True:
            ret = self._do_fact_scan_create_update(host_obj, module_name, facts, self.timestamp)

        if job.store_facts is True:
            self._do_gather_facts_update(host_obj, module_name, facts, self.timestamp)

        message.ack()
        return ret


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

