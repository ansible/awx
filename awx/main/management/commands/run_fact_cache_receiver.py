# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
from datetime import datetime

# Django
from django.core.management.base import NoArgsCommand
from django.conf import settings

# AWX
from awx.fact.models.fact import * # noqa
from awx.main.socket import Socket

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
            return

        try:
            host = FactHost.objects.get(hostname=hostname, inventory_id=inventory_id)
        except FactHost.DoesNotExist:
            logger.info('Creating new host <hostname, inventory_id> <%s, %s>' % (hostname, inventory_id))
            host = FactHost(hostname=hostname, inventory_id=inventory_id)
            host.save()
            logger.info('Created new host <%s>' % (host.id))
        except FactHost.MultipleObjectsReturned:
            query = "db['fact_host'].find(hostname=%s, inventory_id=%s)" % (hostname, inventory_id)
            logger.warn('Database inconsistent. Multiple FactHost "%s" exist. Try the query %s to find the records.' % (hostname, query))
            return
        except Exception, e:
            logger.error("Exception communicating with Fact Cache Database: %s" % str(e))
            return

        (module, facts) = self.process_facts(facts_data)
        self.timestamp = datetime.fromtimestamp(date_key, None)

        try:
            # Update existing Fact entry
            version_obj = FactVersion.objects.get(timestamp=self.timestamp, host=host, module=module)
            Fact.objects(id=version_obj.fact.id).update_one(fact=facts)
            logger.info('Updated existing fact <%s>' % (version_obj.fact.id))
        except FactVersion.DoesNotExist:
            # Create new Fact entry
            (fact_obj, version_obj) = Fact.add_fact(self.timestamp, facts, host, module)
            logger.info('Created new fact <fact, fact_version> <%s, %s>' % (fact_obj.id, version_obj.id))

    def run_receiver(self):
        with Socket('fact_cache', 'r') as facts:
            for message in facts.listen():
                if 'host' not in message or 'facts' not in message or 'date_key' not in message:
                    logger.warn('Received invalid message %s' % message)
                    continue
                logger.info('Received message %s' % message)
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

