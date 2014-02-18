# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import json
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

def run_subscriber(consumer_port, queue_port, use_workers=True):

    consumer_context = zmq.Context()
    consumer_subscriber = consumer_context.socket(zmq.PULL)
    consumer_subscriber.bind(consumer_port)

    queue_context = zmq.Context()
    queue_publisher = queue_context.socket(zmq.PUSH)
    queue_publisher.bind(queue_port)

    if use_workers:
        workers = []
        for idx in range(4):
            w = Worker(queue_port)
            w.start()
            workers.append(w)

    while True: # Handle signal
        message = consumer_subscriber.recv_json()
        if use_workers:
            queue_publisher.send_json(message)
        else:
            process_job_event(message)


@transaction.commit_on_success
def process_job_event(data):
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
            job_event = JobEvent(**data)
            job_event.save(post_process=True)
            if not event.startswith('runner_'):
                transaction.commit()
            break
        except DatabaseError as e:
            transaction.rollback()
            logger.debug('Database error saving job event, retrying in '
                          '1 second (retry #%d): %s', retry_count + 1, e)
            time.sleep(1)
    else:
        logger.error('Failed to save job event after %d retries.',
                     retry_count)


class Worker(Process):
    '''
    Process to validate and store save job events received via zeromq
    '''

    def __init__(self, port):
        self.port = port

    def run(self):
        print("Starting worker")
        pool_context = zmq.Context()
        pool_subscriber = pool_context.socket(zmq.PULL)
        pool_subscriber.connect(self.port)
        while True:
            message = pool_subscriber.recv_json()
            process_job_event(message)

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
        run_subscriber(consumer_port, queue_port)
