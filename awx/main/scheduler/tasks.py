# Python
import logging

# AWX
from awx.main.scheduler import TaskManager, TaskPrepper
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename

logger = logging.getLogger('awx.main.scheduler')


@task(queue=get_local_queuename)
def task_manager():
    logger.debug("=== Running task manager.")
    TaskManager().schedule()


@task(queue=get_local_queuename)
def task_prepper():
    logger.debug("=== Running task prepper.")
    TaskPrepper().schedule()


def run_task_manager():
    task_manager()
    task_prepper()
