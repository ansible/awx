# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import sys
from optparse import make_option

from django.core.management.base import NoArgsCommand

from awx.main.models import (
    UnifiedJob,
    Job,
    AdHocCommand,
)
from awx.main.consumers import emit_channel_notification
from awx.api.serializers import (
    JobEventWebSocketSerializer,
    AdHocCommandEventWebSocketSerializer,
)


class Command(NoArgsCommand):

    help = 'Replay job events over websockets'

    option_list = NoArgsCommand.option_list + (
        make_option('--job_id', dest='job_id', type='int', metavar='j',
                    help='Id of the job to replay (job or adhoc)'),
    )

    def replay_job_events(self, job_id):
        try:
            unified_job = UnifiedJob.objects.get(id=job_id)
        except UnifiedJob.DoesNotExist:
            print("UnifiedJob {} not found.".format(job_id))
            sys.exit(1)

        job = unified_job.get_real_instance()
        job_events = job.job_events.order_by('created')
        serializer = None
        if type(job) is Job:
            serializer = JobEventWebSocketSerializer
        elif type(job) is AdHocCommand:
            serializer = AdHocCommandEventWebSocketSerializer
        else:
            print("Job is of type {} and replay is not yet supported.".format(type(job)))
            sys.exit(1)

        for je in job_events:
            je_serialized = serializer(je).data
            emit_channel_notification('{}-{}'.format(je_serialized['group_name'], job.id), je_serialized)

    def handle_noargs(self, **options):
        self.job_id = options.get('job_id')
        self.replay_job_events(self.job_id)
