# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import logging

from django.core.management.base import NoArgsCommand

from awx.main.models import * # noqa

logger = logging.getLogger('awx.main.commands.run_fact_cache_receiver')

class FactCacheReceiver(object):
    pass

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

