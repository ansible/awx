import logging
import os
import time
from multiprocessing import Process

from django.conf import settings
from django.db import connections
from schedule import Scheduler
from django_guid import set_guid
from django_guid.utils import generate_guid

from awx.main.dispatch.worker import TaskWorker
from awx.main.utils.db import set_connection_name

logger = logging.getLogger('awx.main.dispatch.periodic')


class Scheduler(Scheduler):
    def run_continuously(self):
        def run():
            ppid = os.getppid()
            logger.warning('periodic beat started')

            set_connection_name('periodic')  # set application_name to distinguish from other dispatcher processes

            while True:
                if os.getppid() != ppid:
                    # if the parent PID changes, this process has been orphaned
                    # via e.g., segfault or sigkill, we should exit too
                    pid = os.getpid()
                    logger.warning(f'periodic beat exiting gracefully pid:{pid}')
                    raise SystemExit()
                try:
                    for conn in connections.all():
                        # If the database connection has a hiccup, re-establish a new
                        # connection
                        conn.close_if_unusable_or_obsolete()
                    set_guid(generate_guid())

                    # same logic as run_pending but split up to give spacing between jobs
                    # when more than 1 job is available to run now, put spacing between them
                    # this is to spread out pressure on dispatcher worker pool,
                    # avoiding need for excess reserve workers
                    runnable_jobs = sorted(job for job in self.jobs if job.should_run)
                    for job in runnable_jobs[:-1]:
                        self._run_job(job)
                        time.sleep(0.3)
                    if runnable_jobs:
                        self._run_job(runnable_jobs[-1])

                except Exception:
                    logger.exception('encountered an error while scheduling periodic tasks')

                idle_seconds = self.idle_seconds
                if idle_seconds and idle_seconds > 0:
                    time.sleep(idle_seconds)

        process = Process(target=run)
        process.daemon = True
        process.start()


def run_continuously():
    scheduler = Scheduler()
    for task in settings.CELERYBEAT_SCHEDULE.values():
        apply_async = TaskWorker.resolve_callable(task['task']).apply_async
        total_seconds = task['schedule'].total_seconds()
        scheduler.every(total_seconds).seconds.do(apply_async)
    scheduler.run_continuously()
