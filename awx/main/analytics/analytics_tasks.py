# Python
import logging

# AWX
from awx.main.analytics.subsystem_metrics import Metrics
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename

logger = logging.getLogger('awx.main.scheduler')


@task(queue=get_task_queuename)
def send_subsystem_metrics():
    Metrics().send_metrics()
