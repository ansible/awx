# Python
import logging

# AWX
from awx.main.scheduler import TaskManager, DependencyManager, WorkflowManager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename

logger = logging.getLogger('awx.main.scheduler')


@task(queue=get_local_queuename)
def task_manager():
    TaskManager().schedule()


@task(queue=get_local_queuename)
def dependency_manager():
    DependencyManager().schedule()


@task(queue=get_local_queuename)
def workflow_manager():
    WorkflowManager().schedule()


def run_task_manager():
    task_manager()
    dependency_manager()
    workflow_manager()
