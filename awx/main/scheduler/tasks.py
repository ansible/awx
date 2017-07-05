
# Python
import logging
import json

# Django
from django.db import transaction
from django.utils.timezone import now as tz_now
from awx.main.utils.pglock import advisory_lock

# Celery
from celery import task

# AWX
from awx.main.scheduler import TaskManager 
from django.core.cache import cache

logger = logging.getLogger('awx.main.scheduler')

# TODO: move logic to UnifiedJob model and use bind=True feature of celery.
# Would we need the request loop then? I think so. Even if we get the in-memory
# updated model, the call to schedule() may get stale data.


@task
def run_job_launch(job_id):
    TaskManager().schedule()


@task
def run_job_complete(job_id):
    TaskManager().schedule()


@task
def run_task_manager():
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()


@task
def run_fail_inconsistent_running_jobs():
    logger.debug("Running task to fail inconsistent running jobs.")
    with transaction.atomic():
        # Lock
        with advisory_lock('task_manager_lock', wait=False) as acquired:
            if acquired is False:
                return

            scheduler = TaskManager()
            celery_task_start_time = tz_now()
            active_task_queues, active_tasks = scheduler.get_active_tasks()
            cache.set("active_celery_tasks", json.dumps(active_task_queues))
            if active_tasks is None:
                # TODO: Failed to contact celery. We should surface this.
                return None

            all_running_sorted_tasks = scheduler.get_running_tasks()
            scheduler.process_celery_tasks(celery_task_start_time, active_tasks, all_running_sorted_tasks)


