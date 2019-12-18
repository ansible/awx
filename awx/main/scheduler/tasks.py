
# Python
import logging

# AWX
from awx.main.scheduler import TaskManager
from awx.main.dispatch.publish import task
from awx.main.utils.db import migration_in_progress_check_or_relase

logger = logging.getLogger('awx.main.scheduler')


@task()
def run_task_manager():
    if migration_in_progress_check_or_relase():
        logger.debug("Not running task manager because migration is in progress.")
        return
    logger.debug("Running Tower task manager.")
    TaskManager().schedule()
