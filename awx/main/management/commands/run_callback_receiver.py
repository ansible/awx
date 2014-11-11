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
from multiprocessing import Process, Queue

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, DatabaseError
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.utils.tzinfo import FixedOffset
from django.db import connection 

# AWX
from awx.main.models import *

# ZeroMQ
import zmq

MAX_REQUESTS = 10000
WORKERS = 4

class CallbackReceiver(object):

    def __init__(self):
        self.parent_mappings = {}

    def print_log(self, message):
        print("[%s] %s" % (now().isoformat(), message))

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

        worker_queues = []

        if use_workers:
            connection.close()
            for idx in range(WORKERS):
                queue_actual = Queue()
                w = Process(target=self.callback_worker, args=(queue_actual,))
                w.start()

                signal.signal(signal.SIGINT, shutdown_handler([w]))
                signal.signal(signal.SIGTERM, shutdown_handler([w]))
                if settings.DEBUG:
                    self.print_log('Started worker %s' % str(idx))
                worker_queues.append([0, queue_actual, w])
        elif settings.DEBUG:
            self.print_log('Started callback receiver (no workers)')

        main_process = Process(target=self.callback_handler, args=(use_workers, consumer_port, worker_queues,))
        main_process.daemon = True
        main_process.start()

        signal.signal(signal.SIGINT, shutdown_handler([main_process]))
        signal.signal(signal.SIGTERM, shutdown_handler([main_process]))

        while True:
            for queue_worker in worker_queues:
                if not queue_worker[2].is_alive():
                    queue_worker[2].join()
                    w = Process(target=self.callback_worker, args=(queue_worker[1],))
                    w.daemon = True
                    w.start()
                    signal.signal(signal.SIGINT, shutdown_handler([w]))
                    signal.signal(signal.SIGTERM, shutdown_handler([w]))
                    queue_worker[2] = w
            if not main_process.is_alive():
                sys.exit(1)
            time.sleep(0.1)

    def callback_handler(self, use_workers, consumer_port, worker_queues):
        message_number = 0
        total_messages = 0
        last_parent_events = {}
        self.consumer_context = zmq.Context()
        self.consumer_subscriber = self.consumer_context.socket(zmq.REP)
        self.consumer_subscriber.bind(consumer_port)

        while True: # Handle signal
            message = self.consumer_subscriber.recv_json()
            total_messages += 1
            if not use_workers:
                self.process_job_event(message)
            else:
                job_parent_events = last_parent_events.get(message['job_id'], {})
                if message['event'] in ('playbook_on_play_start', 'playbook_on_stats', 'playbook_on_vars_prompt'):
                    parent = job_parent_events.get('playbook_on_start', None)
                elif message['event'] in ('playbook_on_notify', 'playbook_on_setup',
                                        'playbook_on_task_start',
                                        'playbook_on_no_hosts_matched',
                                        'playbook_on_no_hosts_remaining',
                                        'playbook_on_import_for_host',
                                        'playbook_on_not_import_for_host'):
                    parent = job_parent_events.get('playbook_on_play_start', None)
                elif message['event'].startswith('runner_on_'):
                    list_parents = []
                    list_parents.append(job_parent_events.get('playbook_on_setup', None))
                    list_parents.append(job_parent_events.get('playbook_on_task_start', None))
                    list_parents = sorted(filter(lambda x: x is not None, list_parents), cmp=lambda x, y: y.id-x.id)
                    parent = list_parents[0] if len(list_parents) > 0 else None
                else:
                    parent = None
                if parent is not None:
                    message['parent'] = parent.id
                if 'created' in message:
                    del(message['created'])
                if message['event'] in ('playbook_on_start', 'playbook_on_play_start',
                                        'playbook_on_setup', 'playbook_on_task_start'):
                    job_parent_events[message['event']] = self.process_job_event(message)
                else:
                    if message['event'] == 'playbook_on_stats':
                        job_parent_events = {}
                    queue_actual_worker = worker_queues[total_messages % WORKERS]
                    queue_actual_worker[0] += 1
                    queue_actual_worker[1].put(message)
                    if queue_actual_worker[0] >= MAX_REQUESTS:
                        queue_actual_worker[0] = 0
                        # print("Recycling worker process")
                        # queue_actual_worker[2].join()
                        # connection.close()
                        # w = Process(target=self.callback_worker, args=(queue_actual_worker[1],))
                        # w.daemon = True
                        # w.start()

                        # signal.signal(signal.SIGINT, shutdown_handler([w]))
                        # signal.signal(signal.SIGTERM, shutdown_handler([w]))

                        # queue_actual_worker[2] = w
                last_parent_events[message['job_id']] = job_parent_events
            self.consumer_subscriber.send("1")

    def process_job_event(self, data):
        # Sanity check: Do we need to do anything at all?
        event = data.get('event', '')
        parent_id = data.get('parent', None)
        if not event or 'job_id' not in data:
            return

        # Get the correct "verbose" value from the job.
        # If for any reason there's a problem, just use 0.
        try:
            verbose = Job.objects.get(id=data['job_id']).verbosity
        except Exception, e:
            verbose = 0

        # Convert the datetime for the job event's creation appropriately,
        # and include a time zone for it.
        #
        # In the event of any issue, throw it out, and Django will just save
        # the current time.
        try:
            if not isinstance(data['created'], datetime.datetime):
                data['created'] = parse_datetime(data['created'])
            if not data['created'].tzinfo:
                data['created'] = data['created'].replace(tzinfo=FixedOffset(0))
        except (KeyError, ValueError):
            data.pop('created', None)

        # Print the data to stdout if we're in DEBUG mode.
        if settings.DEBUG:
            print data

        # Sanity check: Don't honor keys that we don't recognize.
        for key in data.keys():
            if key not in ('job_id', 'event', 'event_data',
                           'created', 'counter'):
                data.pop(key)

        # Save any modifications to the job event to the database.
        # If we get a database error of some kind, try again.
        for retry_count in xrange(11):
            try:
                with transaction.atomic():
                    # If we're not in verbose mode, wipe out any module
                    # arguments.
                    res = data['event_data'].get('res', {})
                    if isinstance(res, dict):
                        i = res.get('invocation', {})
                        if verbose == 0 and 'module_args' in i:
                            i['module_args'] = ''

                    # Create a new JobEvent object.
                    job_event = JobEvent(**data)
                    if parent_id is not None:
                        job_event.parent = JobEvent.objects.get(id=parent_id)
                    job_event.save(post_process=True)

                    # Retrun the job event object.
                    return job_event
            except DatabaseError as e:
                # Log the error and try again.
                self.print_log('Database error saving job event, retrying in '
                               '1 second (retry #%d): %s', retry_count + 1, e)
                time.sleep(1)

        # We failed too many times, and are giving up.
        self.print_log('Failed to save job event after %d retries.', retry_count)
        return None

    def callback_worker(self, queue_actual):
        messages_processed = 0
        while True:
            message = queue_actual.get()
            self.process_job_event(message)
            messages_processed += 1
            if messages_processed >= MAX_REQUESTS:
                self.print_log("Shutting down message receiver")
                break

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

