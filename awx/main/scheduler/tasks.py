
# Python
import logging

# Celery
from celery import Task, shared_task

# AWX
from awx.main.scheduler import TaskManager

logger = logging.getLogger('awx.main.scheduler')

# TODO: move logic to UnifiedJob model and use bind=True feature of celery.
# Would we need the request loop then? I think so. Even if we get the in-memory
# updated model, the call to schedule() may get stale data.


class LogErrorsTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.exception('Task {} encountered exception.'.format(self.name), exc_info=exc)
        super(LogErrorsTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@shared_task(base=LogErrorsTask)
def run_job_launch(job_id):
    TaskManager().schedule()


@shared_task(base=LogErrorsTask)
def run_job_complete(job_id):
    TaskManager().schedule()


@shared_task(base=LogErrorsTask)
def run_task_manager():
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()
