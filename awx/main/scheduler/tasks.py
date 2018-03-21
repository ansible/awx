
# Python
import logging

# AWX
from awx.main.scheduler import TaskManager
from awx.main.models.tasks import lazy_task

logger = logging.getLogger('awx.main.scheduler')


@lazy_task()
def run_task_manager():
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()
