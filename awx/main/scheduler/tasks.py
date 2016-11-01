
# Python
import logging

# Django
from django.db import transaction
from django.db.utils import DatabaseError

# Celery
from celery import task

# AWX
from awx.main.models import Instance
from awx.main.scheduler import TaskManager 

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
def run_scheduler():
    TaskManager().schedule()

@task
def run_fail_inconsistent_running_jobs():
    with transaction.atomic():
        # Lock
        try:
            Instance.objects.select_for_update(nowait=True).all()[0]
            scheduler = TaskManager()
            active_tasks = scheduler.get_active_tasks()

            if active_tasks is None:
                # TODO: Failed to contact celery. We should surface this.
                return None

            all_running_sorted_tasks = scheduler.get_running_tasks()
            scheduler.process_celery_tasks(active_tasks, all_running_sorted_tasks)
        except DatabaseError:
            return

