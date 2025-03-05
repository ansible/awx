import time
import logging

from awx.main.dispatch import get_task_queuename
from awx.main.dispatch.publish import task


logger = logging.getLogger(__name__)


@task(queue=get_task_queuename)
def sleep_task(seconds=10, log=False):
    if log:
        logger.info('starting sleep_task')
    time.sleep(seconds)
    if log:
        logger.info('finished sleep_task')
