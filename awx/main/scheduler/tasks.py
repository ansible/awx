
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
    '''
    # Wait for job to exist.
    # The job is created in a transaction then the message is created, but
    # the transaction may not have completed.

    # FIXME: We could generate the message in a Django signal handler.
    # OR, we could call an explicit commit in the view and then send the 
    # message.

    retries = 10
    retry = 0
    while not UnifiedJob.objects.filter(id=job_id).exists():
        time.sleep(0.3)
        
        if retry >= retries:
            logger.error("Failed to process 'job_launch' message for job %d" % job_id)
            # ack the message so we don't build up the queue.
            #
            # The job can still be chosen to run during tower startup or 
            # when another job is started or completes
            return
        retry += 1

    # "Safe" to get the job now since it exists.
    # Really, there is a race condition from exists to get

    # TODO: while not loop should call get wrapped in a try except
    #job = UnifiedJob.objects.get(id=job_id)
    '''

    Scheduler().schedule()

@task
def run_job_complete(job_id):
    '''
    # TODO: use list of finished status from jobs.py or unified_jobs.py
    finished_status = ['successful', 'error', 'failed', 'completed']
    q = UnifiedJob.objects.filter(id=job_id)

    # Ensure that the job is updated in the database before we call to
    # schedule the next job.
    retries = 10
    retry = 0
    while True:
        # Job not found, most likely deleted. That's fine
        if not q.exists():
            logger.warn("Failed to find job '%d' while processing 'job_complete' message. Presume that it was deleted." % job_id)
            break

        job = q[0]
        if job.status in finished_status:
            break

        time.sleep(0.3)
        
        if retry >= retries:
            logger.error("Expected job status '%s' to be one of '%s' while processing 'job_complete' message." % (job.status, finished_status))
            return
        retry += 1
    '''

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

