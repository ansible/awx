
# Python
import logging

# Django
from django.db import transaction
from django.db.utils import DatabaseError

# Celery
from celery import task

# AWX
from awx.main.models import Instance
from awx.main.scheduler import Scheduler

logger = logging.getLogger('awx.main.scheduler')

# TODO: move logic to UnifiedJob model and use bind=True feature of celery.
# Would we need the request loop then? I think so. Even if we get the in-memory
# updated model, the call to schedule() may get stale data.

@task
def run_job_launch(job_id):
    Scheduler().schedule()

@task
def run_job_complete(job_id):
    Scheduler().schedule()

@task
def run_scheduler():
    Scheduler().schedule()

@task
def run_fail_inconsistent_running_jobs():
    return
    print("run_fail_inconsistent_running_jobs() running")
    with transaction.atomic():
        # Lock
        try:
            Instance.objects.select_for_update(nowait=True).all()[0]
            scheduler = Scheduler()
            active_tasks = scheduler.get_activate_tasks()
            if active_tasks is None:
                return None

            all_sorted_tasks = scheduler.get_tasks()
            scheduler.process_celery_tasks(active_tasks, all_sorted_tasks)
        except DatabaseError:
            return

