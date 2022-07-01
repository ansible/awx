# Python
import logging

# Django
from django.conf import settings

# AWX
from awx import MODE
from awx.main.scheduler import TaskManager, DependencyManager, WorkflowManager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename

logger = logging.getLogger('awx.main.scheduler')


@task(queue=get_local_queuename)
def task_manager():
    prefix = 'task'
    if MODE == 'development' and settings.AWX_DISABLE_TASK_MANAGERS:
        logger.debug(f"Not running {prefix} manager, AWX_DISABLE_TASK_MANAGERS is True. Trigger with GET to /api/debug/{prefix}_manager/")
        return

    TaskManager().schedule()


@task(queue=get_local_queuename)
def dependency_manager():
    prefix = 'dependency'
    if MODE == 'development' and settings.AWX_DISABLE_TASK_MANAGERS:
        logger.debug(f"Not running {prefix} manager, AWX_DISABLE_TASK_MANAGERS is True. Trigger with GET to /api/debug/{prefix}_manager/")
        return
    DependencyManager().schedule()


@task(queue=get_local_queuename)
def workflow_manager():
    prefix = 'workflow'
    if MODE == 'development' and settings.AWX_DISABLE_TASK_MANAGERS:
        logger.debug(f"Not running {prefix} manager, AWX_DISABLE_TASK_MANAGERS is True. Trigger with GET to /api/debug/{prefix}_manager/")
        return
    WorkflowManager().schedule()


def run_task_manager():
    if MODE == 'development' and settings.AWX_DISABLE_TASK_MANAGERS:
        logger.debug(f"Not running task managers, AWX_DISABLE_TASK_MANAGERS is True. Trigger with GET to /api/debug/{prefix}_manager/")
        return
    task_manager()
    dependency_manager()
    workflow_manager()
