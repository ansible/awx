# AWX
from awx.main.analytics.subsystem_metrics import Metrics
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename


@task(queue=get_task_queuename)
def send_subsystem_metrics():
    Metrics().send_metrics()
