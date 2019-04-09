# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import asyncio
import logging
import json
from django.conf import settings
from django.core.management.base import BaseCommand

from awx.main.models import Job, JobEvent


logger = logging.getLogger('awx.main.commands.runner_receiver')


class RunnerClientProtocol(asyncio.Protocol):

    def __init__(self, loop):
        self.transport = None
        self.loop = loop

    def connection_made(self, transport):
        self.transport = transport
        print("Connection from {}".format(transport.get_extra_info('peername')))

    async def process_payload(self, data):
        job_actual, created = Job.objects.get_or_create(runner_job_ident=data['runner_ident'])
        if created:
            job_actual.launch_type = 'external'
            job_actual.runner_job_ident = data['runner_ident']
            job_actual.name = 'External Job {}'.format(data['runner_ident'])
            job_actual.save()
            print("New Job {} created".format(job_actual.id))
        if 'status' in data:
            job_actual.status = data['status']
            job_actual.save()
            job_actual.websocket_emit_status(job_actual.status)
            print("Job {} updated to status {}".format(job_actual.id, job_actual.status))
        elif 'uuid' in data:
            print("Creating payload for job {}: {}".format(data, job_actual.id))
            data['job_id'] = job_actual.id
            je = JobEvent.create_from_data(**data)
            je.save()

    def data_received(self, data):
        print("Data received from {}".format(self.transport.get_extra_info('peername')))
        self.loop.create_task(self.process_payload(json.loads(data)))


class Command(BaseCommand):

    help = 'Launch a receiver for Runner Events and Statuses'

    def handle(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        proto = RunnerClientProtocol(loop)
        listener = loop.create_server(lambda: proto,
                                      '0.0.0.0', settings.RUNNER_RECEIVER_PORT)
        loop.create_task(listener)
        logger.info("Runner Receiver bound at 0.0.0.0:{}".format(settings.RUNNER_RECEIVER_PORT))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.stop()
