# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import logging
from django.conf import settings
from django.core.management.base import BaseCommand

from awx.main.models import Job, JobEvent

import zmq

logger = logging.getLogger('awx.main.commands.runner_receiver')


class Command(BaseCommand):

    help = 'Launch a receiver for Runner Events and Statuses'

    def process_payload(self, data):
        job_actual, created = Job.objects.get_or_create(runner_job_ident=data['runner_ident'])
        if created:
            job_actual.launch_type = 'external'
            job_actual.runner_job_ident = data['runner_ident']
            job_actual.name = 'External Job {}'.format(data['runner_ident'])
            job_actual.save()
            logger.debug("New Job {} created".format(job_actual.id))
        if 'status' in data:
            job_actual.status = data['status']
            job_actual.save()
            job_actual.websocket_emit_status(job_actual.status)
            logger.debug("Job {} updated to status {}".format(job_actual.id, job_actual.status))
        elif 'uuid' in data:
            logger.debug("Creating payload for job {}: {}".format(data, job_actual.id))
            data['job_id'] = job_actual.id
            je = JobEvent.create_from_data(**data)
            je.save()

    def handle(self, *args, **kwargs):
        context = zmq.Context()
        receiver = context.socket(zmq.PULL)
        receiver.bind(settings.RUNNER_RECEIVER_URL)
        logger.info("Runner Receiver bound at {}".format(settings.RUNNER_RECEIVER_URL))
        try:
            while True:
                self.process_payload(receiver.recv_json())
        except KeyboardInterrupt:
            print("Terminating Runner Receiver")
