# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Django
from django.core.management.base import BaseCommand

# AWX
from awx.main.models import UnifiedJob


class Command(BaseCommand):
    '''
    Emits some simple statistics suitable for external monitoring
    '''

    help = 'Display some simple statistics'

    def add_arguments(self, parser):
        parser.add_argument('--stat',
                            action='store',
                            dest='stat',
                            type=str,
                            default="jobs_running",
                            help='Select which stat to get information for')

    def job_stats(self, state):
        return UnifiedJob.objects.filter(status=state).count()

    def handle(self, *args, **options):
        if options['stat'].startswith("jobs_"):
            self.stdout.write(str(self.job_stats(options['stat'][5:])))
        else:
            self.stdout.write("Supported stats:  jobs_{state}")
