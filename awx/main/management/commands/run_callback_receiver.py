# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import os
import sys
import datetime
import logging
import json
import signal
import time
from optparse import make_option
from multiprocessing import Process

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, DatabaseError
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.utils.tzinfo import FixedOffset

# AWX
from awx.main.models import *

# ZeroMQ
import zmq

MAX_REQUESTS = 20000

class CallbackReceiver(object):

    def __init__(self):
        self.parent_mappings = {}

    def run_subscriber(self, consumer_port, queue_port, use_workers=True):
        def shutdown_handler(active_workers):
            def _handler(signum, frame):
                for active_worker in active_workers:
                    active_worker.terminate()
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum) # Rethrow signal, this time without catching it
            return _handler
        def check_pre_handle(data):
            event = data.get('event', '')
            if event == 'playbook_on_play_start':
                return True
            return False

        consumer_context = zmq.Context()
        consumer_subscriber = consumer_context.socket(zmq.REP)
        consumer_subscriber.bind(consumer_port)

        queue_context = zmq.Context()
        queue_publisher = queue_context.socket(zmq.PUSH)
        queue_publisher.bind(queue_port)

        if use_workers:
            w = Process(target=self.callback_worker, args=(queue_port,))
            w.daemon = True
            w.start()

            signal.signal(signal.SIGINT, shutdown_handler([w]))
            signal.signal(signal.SIGTERM, shutdown_handler([w]))
            if settings.DEBUG:
                print 'Started worker'
        elif settings.DEBUG:
            print 'Started callback receiver (no workers)'

        message_number = 0
        while True: # Handle signal
            message = consumer_subscriber.recv_json()
            message_number += 1
            if not use_workers:
                self.process_job_event(message)
            else:
                queue_publisher.send_json(message)
                if message_number >= MAX_REQUESTS:
                    message_number = 0
                    print("Recycling worker process")
                    w.join()
                    w = Process(target=self.callback_worker, args=(queue_port,))
                    w.daemon = True
                    w.start()
            consumer_subscriber.send("1")

    # NOTE: This cache doesn't work too terribly well but it can help prevent database queries
    # we may want to use something like memcached here instead
    def process_parent_cache(self, job_id, event_object):
        if event_object.event not in ('playbook_on_start', 'playbook_on_play_start', 'playbook_on_setup', 'playbook_on_task_start'):
            return
        if job_id not in self.parent_mappings:
            self.parent_mappings[job_id] = {}
        if event_object.event not in self.parent_mappings[job_id]:
            self.parent_mappings[job_id][event_object.event] = {event_object.id: event_object}
        else:
            self.parent_mappings[job_id][event_object.event][event_object.id] = event_object

    def find_parent(self, job_id, event_object):
        if job_id not in self.parent_mappings:
            return None
        job_parent_mappings = self.parent_mappings[job_id]
        search_events = set()
        if event_object.event in ('playbook_on_play_start', 'playbook_on_stats',
                                  'playbook_on_vars_prompt'):
            search_events.add('playbook_on_start')
        elif event_object.event in ('playbook_on_notify', 'playbook_on_setup',
                                    'playbook_on_task_start',
                                    'playbook_on_no_hosts_matched',
                                    'playbook_on_no_hosts_remaining',
                                    'playbook_on_import_for_host',
                                    'playbook_on_not_import_for_host'):
            search_events.add('playbook_on_play_start')
        elif event_object.event.startswith('runner_on_'):
            search_events.add('playbook_on_setup')
            search_events.add('playbook_on_task_start')
        potential_events = []
        for event_type in search_events:
            potential_events.extend([e for e in self.parent_mappings[job_id][event_type].values()] if \
                                    event_type in self.parent_mappings[job_id] else [])
        potential_events = sorted(potential_events, cmp=lambda x,y: y.id-x.id)
        if len(potential_events) > 0:
            return potential_events[0]
        return None

    def check_purge_parent_cache(self, job_id, event_object):
        if event_object.event == 'playbook_on_stats':
            del(self.parent_mappings[job_id])

    @transaction.commit_on_success
    def process_job_event(self, data):
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
        for retry_count in xrange(11):
            try:
                if event == 'playbook_on_stats':
                    transaction.commit()
                job_event = JobEvent(**data)
                job_event.parent = self.find_parent(data['job_id'], job_event)
                job_event.save(post_process=True)
                self.process_parent_cache(data['job_id'], job_event)
                self.check_purge_parent_cache(data['job_id'], job_event)
                if not event.startswith('runner_'):
                    transaction.commit()
                break
            except DatabaseError as e:
                transaction.rollback()
                print('Database error saving job event, retrying in '
                      '1 second (retry #%d): %s', retry_count + 1, e)
                time.sleep(1)
        else:
            print('Failed to save job event after %d retries.',
                  retry_count)

    def callback_worker(self, port):
        messages_processed = 0
        pool_context = zmq.Context()
        pool_subscriber = pool_context.socket(zmq.PULL)
        pool_subscriber.connect(port)
        while True:
            message = pool_subscriber.recv_json()
            self.process_job_event(message)
            messages_processed += 1
            if messages_processed >= MAX_REQUESTS:
                print("Shutting down message receiver")
                pool_subscriber.close()
                sys.exit(0)

class Command(NoArgsCommand):
    '''
    Save Job Callback receiver (see awx.plugins.callbacks.job_event_callback)
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
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

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        consumer_port = settings.CALLBACK_CONSUMER_PORT
        queue_port = settings.CALLBACK_QUEUE_PORT
        cr = CallbackReceiver()
        try:
            cr.run_subscriber(consumer_port, queue_port)
        except KeyboardInterrupt:
            pass

