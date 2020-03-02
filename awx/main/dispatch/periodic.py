import logging
import os
import time
from multiprocessing import Process

from django.conf import settings
from django.db import connections
from schedule import Scheduler

from awx.main.dispatch.worker import TaskWorker

logger = logging.getLogger('awx.main.dispatch.periodic')


class Scheduler(Scheduler):

    def run_continuously(self):
        idle_seconds = max(
            1,
            min(self.jobs).period.total_seconds() / 2
        )

        def run():
            ppid = os.getppid()
            logger.warn(f'periodic beat started')
            while True:
                if os.getppid() != ppid:
                    # if the parent PID changes, this process has been orphaned
                    # via e.g., segfault or sigkill, we should exit too
                    pid = os.getpid()
                    logger.warn(f'periodic beat exiting gracefully pid:{pid}')
                    raise SystemExit()
                try:
                    for conn in connections.all():
                        # If the database connection has a hiccup, re-establish a new
                        # connection
                        conn.close_if_unusable_or_obsolete()
                    self.run_pending()
                except Exception:
                    logger.exception(
                        'encountered an error while scheduling periodic tasks'
                    )
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
