# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
import json

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.cache import cache
from django.db import DatabaseError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import FixedOffset

# AWX
from awx.main.models import * # noqa

logger = logging.getLogger('awx.main.commands.run_callback_receiver')

class CallbackBrokerWorker(ConsumerMixin):

    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[Queue(settings.CALLBACK_QUEUE,
                                       Exchange(settings.CALLBACK_QUEUE, type='direct'),
                                       routing_key=settings.CALLBACK_QUEUE)],
                         accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        try:
            if "event" not in body:
                raise Exception("Payload does not have an event")
            if "job_id" not in body:
                raise Exception("Payload does not have a job_id")
            if settings.DEBUG:
                logger.info("Body: {}".format(body))
                logger.info("Message: {}".format(message))
            self.process_job_event(body)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            logger.error('Callback Task Processor Raised Exception: %r', exc)
        message.ack()

    def process_job_event(self, payload):
        # Get the correct "verbose" value from the job.
        # If for any reason there's a problem, just use 0.
        if 'ad_hoc_command_id' in payload:
            event_type_key = 'ad_hoc_command_id'
            event_object_type = AdHocCommand
        else:
            event_type_key = 'job_id'
            event_object_type = Job

        try:
            verbose = event_object_type.objects.get(id=payload[event_type_key]).verbosity
        except Exception as e:
            verbose=0
        # TODO: cache

        # Convert the datetime for the job event's creation appropriately,
        # and include a time zone for it.
        #
        # In the event of any issue, throw it out, and Django will just save
        # the current time.
        try:
            if not isinstance(payload['created'], datetime.datetime):
                payload['created'] = parse_datetime(payload['created'])
            if not payload['created'].tzinfo:
                payload['created'] = payload['created'].replace(tzinfo=FixedOffset(0))
        except (KeyError, ValueError):
            payload.pop('created', None)

        event_uuid = payload.get("uuid", '')
        parent_event_uuid = payload.get("parent_uuid", '')
        artifact_data = payload.get("artifact_data", None)

        # Sanity check: Don't honor keys that we don't recognize.
        for key in payload.keys():
            if key not in (event_type_key, 'event', 'event_data',
                           'created', 'counter', 'uuid'):
                payload.pop(key)

        try:
            # If we're not in verbose mode, wipe out any module
            # arguments.
            res = payload['event_data'].get('res', {})
            if isinstance(res, dict):
                i = res.get('invocation', {})
                if verbose == 0 and 'module_args' in i:
                    i['module_args'] = ''

            if 'ad_hoc_command_id' in payload:
                AdHocCommandEvent.objects.create(**data)
                return
            
            j = JobEvent(**payload)
            if payload['event'] == 'playbook_on_start':
                j.save()
                cache.set("{}_{}".format(payload['job_id'], event_uuid), j.id, 300)
                return
            else:
                if parent_event_uuid:
                    parent_id = cache.get("{}_{}".format(payload['job_id'], parent_event_uuid), None)
                    if parent_id is None:
                        parent_id_obj = JobEvent.objects.filter(uuid=parent_event_uuid, job_id=payload['job_id'])
                        if parent_id_obj.exists():  # Problematic if not there, means the parent hasn't been written yet... TODO
                            j.parent_id = parent_id_obj[0].id
                            print("Settings cache: {}_{} with value {}".format(payload['job_id'], parent_event_uuid, j.parent_id))
                            cache.set("{}_{}".format(payload['job_id'], parent_event_uuid), j.parent_id, 300)
                    else:
                        print("Cache hit")
                        j.parent_id = parent_id
                j.save(post_process=True)
                if event_uuid:
                    cache.set("{}_{}".format(payload['job_id'], event_uuid), j.id, 300)
        except DatabaseError as e:
            logger.error("Database Error Saving Job Event: {}".format(e))

        if artifact_data:
            try:
                self.process_artifacts(artifact_data, res, payload)
            except DatabaseError as e:
                logger.error("Database Error Saving Job Artifacts: {}".format(e))

    def process_artifacts(self, artifact_data, res, payload):
        artifact_dict = json.loads(artifact_data)
        if res and isinstance(res, dict):
            if res.get('_ansible_no_log', False):
                artifact_dict['_ansible_no_log'] = True
        if artifact_data is not None:
            parent_job = Job.objects.filter(pk=payload['job_id']).first()
            if parent_job is not None and parent_job.artifacts != artifact_dict:
                parent_job.artifacts = artifact_dict
                parent_job.save(update_fields=['artifacts'])


class Command(NoArgsCommand):
    '''
    Save Job Callback receiver (see awx.plugins.callbacks.job_event_callback)
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
    '''
    help = 'Launch the job callback receiver'

    def handle_noargs(self, **options):
        with Connection(settings.BROKER_URL) as conn:
            try:
                worker = CallbackBrokerWorker(conn)
                worker.run()
            except KeyboardInterrupt:
                print('Terminating Callback Receiver')

