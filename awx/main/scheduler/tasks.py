
# Python
import logging

# AWX
from awx.main.scheduler import TaskManager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename

logger = logging.getLogger('awx.main.scheduler')


@task(queue=get_local_queuename)
def run_task_manager():
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()
