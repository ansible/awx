
# Python
import logging

# AWX
from awx.main.scheduler import TaskManager
from awx.main.dispatch.publish import task

logger = logging.getLogger('awx.main.scheduler')


@task()
def run_job_launch(job_id):
    TaskManager().schedule()


@task()
def run_job_complete(job_id):
    TaskManager().schedule()


@task()
def run_task_manager():
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()
