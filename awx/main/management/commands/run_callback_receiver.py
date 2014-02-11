# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import json
from optparse import make_option

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.utils.tzinfo import FixedOffset

# AWX
from awx.main.models import *

# ZeroMQ
import zmq

class Command(NoArgsCommand):
    '''
    Management command to run the job callback receiver
    '''

    help = 'Launch the job callback receiver'

    option_list = NoArgsCommand.option_list + (
        make_option('--port', dest='port', type='int', default=5556,
                    help='Port to listen for requests on'),)

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.run_callback_receiver')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.commit_on_success
    def process_job_event(self, data):
        print("Received data: %s" % str(data))
        event = data.get('event', '')
        if not event or 'job_id' not in data:
            return
        try:
            if not isinstance(data['created'], datetime.datetime):
                data['created'] = parse_datetime(data['created'])
            if not data['created'].tzinfo:
                data['created'] = data['created'].replace(tzinfo=FixedOffset(0))
        except (KeyError, ValueError):
            data.pop('created', None)
        if settings.DEBUG:
            print data
        for key in data.keys():
            if key not in ('job_id', 'event', 'event_data', 'created'):
                data.pop(key)
        data['play'] = data.get('event_data', {}).get('play', '').strip()
        data['task'] = data.get('event_data', {}).get('task', '').strip()
        for retry_count in xrange(11):
            try:
                if event == 'playbook_on_stats':
                    transaction.commit()
                if not JobEvent.objects.filter(**data).exists():
                    job_event = JobEvent(**data)
                    job_event.save(post_process=True)
                    if not event.startswith('runner_'):
                        transaction.commit()
                else:
                    duplicate = True
                    if settings.DEBUG:
                        print 'skipping duplicate job event %r' % data
                break
            except DatabaseError as e:
                transaction.rollback()
                logger.debug('Database error saving job event, retrying in '
                             '1 second (retry #%d): %s', retry_count + 1, e)
                time.sleep(1)
        else:
            logger.error('Failed to save job event after %d retries.',
                         retry_count)

    def run_subscriber(self, port=5556):
        print("Starting ZMQ Context")
        context = zmq.Context()
        subscriber = context.socket(zmq.REP)
        print("Starting connection")
        subscriber.bind("tcp://127.0.0.1:%s" % str(port))
        print("Listening on tcp://127.0.0.1:%s" % str(port))
        while True: # Handle signal
            message = subscriber.recv()
            subscriber.send("1")
            data = json.loads(message)
            self.process_job_event(data)

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.run_subscriber()
