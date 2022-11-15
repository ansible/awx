from pathlib import Path
import socket

from django.db import connection
from django.core.management.base import BaseCommand
from django.conf import settings

from awx.main.tasks.callback import RunnerCallback
from awx.main.models import Job, JobHostSummary
from awx.main.constants import ACTIVE_STATES

import ansible_runner


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('job_id', type=int)

    def handle(self, *args, **options):
        runner_callback = RunnerCallback(model=Job)
        job = Job.objects.get(pk=options['job_id'])
        runner_callback.instance = job
        runner_callback.job_created = str(job.created)

        job.job_events.all().delete()
        JobHostSummary.objects.filter(job_id=job.id).delete()

        if job.status in ACTIVE_STATES:
            raise RuntimeError(f"Job must not be in an active state {ACTIVE_STATES} when running this command.")

        if settings.RECEPTOR_RELEASE_WORK:
            raise RuntimeError("To use this command, set RECEPTOR_RELEASE_WORK to False.")

        if settings.AWX_CLEANUP_PATHS:
            raise RuntimeError("To use this command, set AWX_CLEANUP_PATHS to False.")

        hostname = socket.gethostname()

        if hostname != job.controller_node:
            raise RuntimeError(f"This command must be run from {job.controller_node}.")

        resultfile = Path(f"/tmp/receptor/{hostname}/{job.work_unit_id}/stdout")

        with open(resultfile) as f:
            ansible_runner.interface.run(
                streamer='process',
                quiet=True,
                _input=f,
                event_handler=runner_callback.event_handler,
                finished_callback=runner_callback.finished_callback,
                status_handler=runner_callback.status_handler,
                private_data_dir=job.job_env['AWX_PRIVATE_DATA_DIR'],
            )
