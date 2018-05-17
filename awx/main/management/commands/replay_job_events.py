# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import sys
import time
import json

from django.utils import timezone
from django.core.management.base import BaseCommand

from awx.main.models import (
    UnifiedJob,
    Job,
    AdHocCommand,
    ProjectUpdate,
    InventoryUpdate,
    SystemJob
)
from awx.main.consumers import emit_channel_notification
from awx.api.serializers import (
    JobEventWebSocketSerializer,
    AdHocCommandEventWebSocketSerializer,
    ProjectUpdateEventWebSocketSerializer,
    InventoryUpdateEventWebSocketSerializer,
    SystemJobEventWebSocketSerializer
)


class ReplayJobEvents():

    recording_start = None
    replay_start = None

    def now(self):
        return timezone.now()

    def start(self, first_event_created):
        self.recording_start = first_event_created
        self.replay_start = self.now()

    def lateness(self, now, created):
        time_passed = now - self.recording_start
        job_event_time = created - self.replay_start

        return (time_passed - job_event_time).total_seconds()

    def get_job(self, job_id):
        try:
            unified_job = UnifiedJob.objects.get(id=job_id)
        except UnifiedJob.DoesNotExist:
            print("UnifiedJob {} not found.".format(job_id))
            sys.exit(1)

        return unified_job.get_real_instance()

    def sleep(self, seconds):
        time.sleep(seconds)

    def replay_elapsed(self):
        return (self.now() - self.replay_start)

    def recording_elapsed(self, created):
        return (created - self.recording_start)

    def replay_offset(self, created, speed):
        return self.replay_elapsed().total_seconds() - (self.recording_elapsed(created).total_seconds() * (1.0 / speed))

    def get_job_events(self, job):
        if type(job) is Job:
            job_events = job.job_events.order_by('created')
        elif type(job) is AdHocCommand:
            job_events = job.ad_hoc_command_events.order_by('created')
        elif type(job) is ProjectUpdate:
            job_events = job.project_update_events.order_by('created')
        elif type(job) is InventoryUpdate:
            job_events = job.inventory_update_events.order_by('created')
        elif type(job) is SystemJob:
            job_events = job.system_job_events.order_by('created')
        if job_events.count() == 0:
            raise RuntimeError("No events for job id {}".format(job.id))
        return job_events

    def get_serializer(self, job):
        if type(job) is Job:
            return JobEventWebSocketSerializer
        elif type(job) is AdHocCommand:
            return AdHocCommandEventWebSocketSerializer
        elif type(job) is ProjectUpdate:
            return ProjectUpdateEventWebSocketSerializer
        elif type(job) is InventoryUpdate:
            return InventoryUpdateEventWebSocketSerializer
        elif type(job) is SystemJob:
            return SystemJobEventWebSocketSerializer
        else:
            raise RuntimeError("Job is of type {} and replay is not yet supported.".format(type(job)))
            sys.exit(1)

    def run(self, job_id, speed=1.0, verbosity=0, skip=0):
        stats = {
            'events_ontime': {
                'total': 0,
                'percentage': 0,
            },
            'events_late': {
                'total': 0,
                'percentage': 0,
                'lateness_total': 0,
                'lateness_average': 0,
            },
            'events_total': 0,
            'events_distance_total': 0,
            'events_distance_average': 0,
            'recording_start': 0,
            'recording_end': 0,
            'recording_duration': 0,
            'replay_start': 0,
            'replay_end': 0,
            'replay_duration': 0,
        }
        try:
            job = self.get_job(job_id)
            job_events = self.get_job_events(job)
            serializer = self.get_serializer(job)
        except RuntimeError as e:
            print("{}".format(e.message))
            sys.exit(1)

        je_previous = None
        for n, je_current in enumerate(job_events):
            if n < skip:
                continue

            if not je_previous:
                stats['recording_start'] = je_current.created
                self.start(je_current.created)
                stats['replay_start'] = self.replay_start
                je_previous = je_current

            je_serialized = serializer(je_current).data
            emit_channel_notification('{}-{}'.format(je_serialized['group_name'], job.id), je_serialized)

            replay_offset = self.replay_offset(je_previous.created, speed)
            recording_diff = (je_current.created - je_previous.created).total_seconds() * (1.0 / speed)
            stats['events_distance_total'] += recording_diff
            if verbosity >= 3:
                print("recording: next job in {} seconds".format(recording_diff))
            if replay_offset >= 0:
                replay_diff = recording_diff - replay_offset
                
                if replay_diff > 0:
                    stats['events_ontime']['total'] += 1
                    if verbosity >= 3:
                        print("\treplay: sleep for {} seconds".format(replay_diff))
                    self.sleep(replay_diff)
                else:
                    stats['events_late']['total'] += 1
                    stats['events_late']['lateness_total'] += (replay_diff * -1)
                    if verbosity >= 3:
                        print("\treplay: too far behind to sleep {} seconds".format(replay_diff))
            else:
                replay_offset = self.replay_offset(je_current.created, speed)
                stats['events_late']['lateness_total'] += (replay_offset * -1)
                stats['events_late']['total'] += 1
                if verbosity >= 3:
                    print("\treplay: behind by {} seconds".format(replay_offset))

            stats['events_total'] += 1
            je_previous = je_current

        if stats['events_total'] > 2:
            stats['replay_end'] = self.now()
            stats['replay_duration'] = (stats['replay_end'] - stats['replay_start']).total_seconds()
            stats['replay_start'] = stats['replay_start'].isoformat()
            stats['replay_end'] = stats['replay_end'].isoformat()

            stats['recording_end'] = je_current.created
            stats['recording_duration'] = (stats['recording_end'] - stats['recording_start']).total_seconds()
            stats['recording_start'] = stats['recording_start'].isoformat()
            stats['recording_end'] = stats['recording_end'].isoformat()

            stats['events_ontime']['percentage'] = (stats['events_ontime']['total'] / float(stats['events_total'])) * 100.00
            stats['events_late']['percentage'] = (stats['events_late']['total'] / float(stats['events_total'])) * 100.00
            stats['events_distance_average'] = stats['events_distance_total'] / stats['events_total']
            stats['events_late']['lateness_average'] = stats['events_late']['lateness_total'] / stats['events_late']['total']
        else:
            stats = {'events_total': stats['events_total']}

        if verbosity >= 2:
            print(json.dumps(stats, indent=4, sort_keys=True))


class Command(BaseCommand):

    help = 'Replay job events over websockets ordered by created on date.'

    def add_arguments(self, parser):
        parser.add_argument('--job_id', dest='job_id', type=int, metavar='j',
                            help='Id of the job to replay (job or adhoc)')
        parser.add_argument('--speed', dest='speed', type=int, metavar='s',
                            help='Speedup factor.')
        parser.add_argument('--skip', dest='skip', type=int, metavar='k',
                            help='Number of events to skip.')

    def handle(self, *args, **options):
        job_id = options.get('job_id')
        speed = options.get('speed') or 1
        verbosity = options.get('verbosity') or 0
        skip = options.get('skip') or 0

        replayer = ReplayJobEvents()
        replayer.run(job_id, speed, verbosity, skip)
