# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Python
import os
import sys
import datetime
import logging
import signal
import time
from multiprocessing import Process, Queue
from Queue import Empty as QueueEmpty

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import transaction, DatabaseError
from django.utils.dateparse import parse_datetime
from django.utils.tzinfo import FixedOffset
from django.db import connection

# AWX
from awx.main.models import * # noqa
from awx.main.socket import Socket

logger = logging.getLogger('awx.main.commands.run_callback_receiver')

WORKERS = 4

class CallbackReceiver(object):
    def __init__(self):
        self.parent_mappings = {}

    def run_subscriber(self, use_workers=True):
        def shutdown_handler(active_workers):
            def _handler(signum, frame):
                try:
                    for active_worker in active_workers:
                        active_worker.terminate()
                    signal.signal(signum, signal.SIG_DFL)
                    os.kill(os.getpid(), signum) # Rethrow signal, this time without catching it
                except Exception:
                    # TODO: LOG
                    pass
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
                queue_actual = Queue(settings.JOB_EVENT_MAX_QUEUE_SIZE)
                w = Process(target=self.callback_worker, args=(queue_actual, idx,))
                w.start()
                if settings.DEBUG:
                    logger.info('Started worker %s' % str(idx))
                worker_queues.append([0, queue_actual, w])
        elif settings.DEBUG:
            logger.warn('Started callback receiver (no workers)')

        main_process = Process(
            target=self.callback_handler,
            args=(use_workers, worker_queues,)
        )
        main_process.daemon = True
        main_process.start()

        signal.signal(signal.SIGINT, shutdown_handler([p[2] for p in worker_queues] + [main_process]))
        signal.signal(signal.SIGTERM, shutdown_handler([p[2] for p in worker_queues] + [main_process]))
        while True:
            workers_changed = False
            idx = 0
            for queue_worker in worker_queues:
                if not queue_worker[2].is_alive():
                    logger.warn("Worker %s was not alive, restarting" % str(queue_worker))
                    workers_changed = True
                    queue_worker[2].join()
                    w = Process(target=self.callback_worker, args=(queue_worker[1], idx,))
                    w.daemon = True
                    w.start()
                    signal.signal(signal.SIGINT, shutdown_handler([w]))
                    signal.signal(signal.SIGTERM, shutdown_handler([w]))
                    queue_worker[2] = w
                idx += 1
            if workers_changed:
                signal.signal(signal.SIGINT, shutdown_handler([p[2] for p in worker_queues] + [main_process]))
                signal.signal(signal.SIGTERM, shutdown_handler([p[2] for p in worker_queues] + [main_process]))
            if not main_process.is_alive():
                logger.error("Main process is not alive")
                for queue_worker in worker_queues:
                    queue_worker[2].terminate()
                break
            time.sleep(0.1)

    def write_queue_worker(self, preferred_queue, worker_queues, message):
        queue_order = sorted(range(WORKERS), cmp=lambda x, y: -1 if x==preferred_queue else 0)
        for queue_actual in queue_order:
            try:
                worker_actual = worker_queues[queue_actual]
                worker_actual[1].put(message, block=True, timeout=2)
                worker_actual[0] += 1
                return queue_actual
            except Exception:
                logger.warn("Could not write to queue %s" % preferred_queue)
                continue
        return None

    def callback_handler(self, use_workers, worker_queues):
        total_messages = 0
        last_parent_events = {}
        with Socket('callbacks', 'r') as callbacks:
            for message in callbacks.listen():
                total_messages += 1
                if 'ad_hoc_command_id' in message:
                    self.process_ad_hoc_event(message)
                elif not use_workers:
                    self.process_job_event(message)
                else:
                    job_parent_events = last_parent_events.get(message['job_id'], {})
                    if message['event'] in ('playbook_on_play_start', 'playbook_on_stats', 'playbook_on_vars_prompt'):
                        parent = job_parent_events.get('playbook_on_start', None)
                    elif message['event'] in ('playbook_on_notify',
                                              'playbook_on_setup',
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
                        list_parents = sorted(filter(lambda x: x is not None, list_parents), cmp=lambda x, y: y.id - x.id)
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

                        actual_queue = self.write_queue_worker(total_messages % WORKERS, worker_queues, message)
                        # NOTE: It might be better to recycle the entire callback receiver process if one or more of the queues are too full
                        # the drawback is that if we under extremely high load we may be legitimately taking a while to process messages
                        if actual_queue is None:
                            logger.error("All queues full!")
                            sys.exit(1)
                    last_parent_events[message['job_id']] = job_parent_events

    @transaction.atomic
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
        # If we get a database error of some kind, bail out.
        try:
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
            # Log the error and bail out.
            logger.error('Database error saving job event: %s', e)
        return None

    @transaction.atomic
    def process_ad_hoc_event(self, data):
        # Sanity check: Do we need to do anything at all?
        event = data.get('event', '')
        if not event or 'ad_hoc_command_id' not in data:
            return

        # Get the correct "verbose" value from the job.
        # If for any reason there's a problem, just use 0.
        try:
            verbose = AdHocCommand.objects.get(id=data['ad_hoc_command_id']).verbosity
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
            if key not in ('ad_hoc_command_id', 'event', 'event_data',
                           'created', 'counter'):
                data.pop(key)

        # Save any modifications to the ad hoc command event to the database.
        # If we get a database error of some kind, bail out.
        try:
            # If we're not in verbose mode, wipe out any module
            # arguments. FIXME: Needed for adhoc?
            res = data['event_data'].get('res', {})
            if isinstance(res, dict):
                i = res.get('invocation', {})
                if verbose == 0 and 'module_args' in i:
                    i['module_args'] = ''

            # Create a new AdHocCommandEvent object.
            ad_hoc_command_event = AdHocCommandEvent.objects.create(**data)

            # Retrun the ad hoc comamnd event object.
            return ad_hoc_command_event
        except DatabaseError as e:
            # Log the error and bail out.
            logger.error('Database error saving ad hoc command event: %s', e)
        return None

    def callback_worker(self, queue_actual, idx):
        messages_processed = 0
        while True:
            try:
                message = queue_actual.get(block=True, timeout=1)
            except QueueEmpty:
                continue
            except Exception, e:
                logger.error("Exception on listen socket, restarting: " + str(e))
                break
            self.process_job_event(message)
            messages_processed += 1
            if messages_processed >= settings.JOB_EVENT_RECYCLE_THRESHOLD:
                logger.info("Shutting down message receiver")
                break

class Command(NoArgsCommand):
    '''
    Save Job Callback receiver (see awx.plugins.callbacks.job_event_callback)
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
    '''
    help = 'Launch the job callback receiver'

    def handle_noargs(self, **options):
        cr = CallbackReceiver()
        try:
            cr.run_subscriber()
        except KeyboardInterrupt:
            pass

