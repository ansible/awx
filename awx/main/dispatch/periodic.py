import logging
import threading
import time

from django.conf import settings
from django.db import connections
from schedule import Scheduler

from awx.main.dispatch.worker import TaskWorker

logger = logging.getLogger('awx.main.dispatch.periodic')


class Scheduler(Scheduler):

    def run_continuously(self):
        cease_continuous_run = threading.Event()
        idle_seconds = max(
            1,
            min(self.jobs).period.total_seconds() / 2
        )

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
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
                logger.debug('periodic thread exiting...')

        thread = ScheduleThread()
        thread.daemon = True
        thread.start()
        return cease_continuous_run


def run_continuously():
    scheduler = Scheduler()
    for task in settings.CELERYBEAT_SCHEDULE.values():
        apply_async = TaskWorker.resolve_callable(task['task']).apply_async
        total_seconds = task['schedule'].total_seconds()
        scheduler.every(total_seconds).seconds.do(apply_async)
    return scheduler.run_continuously()
