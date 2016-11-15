
# Python
import pytest
from datetime import timedelta

# Django
from django.utils.timezone import now as tz_now

# awx
from awx.main.scheduler.partial import (
    JobDict,
    ProjectUpdateDict,
    InventoryUpdateDict,
    InventorySourceDict,
)
from awx.main.scheduler import TaskManager


@pytest.fixture
def epoch():
    return tz_now()

@pytest.fixture
def scheduler_factory(mocker, epoch):
    mocker.patch('awx.main.models.Instance.objects.total_capacity', return_value=10000)

    def fn(tasks=[], inventory_sources=[], latest_project_updates=[], latest_inventory_updates=[], create_project_update=None, create_inventory_update=None):
        sched = TaskManager()

        sched.graph.get_now = lambda: epoch

        def no_create_inventory_update(task, ignore):
            raise RuntimeError("create_inventory_update should not be called")

        def no_create_project_update(task):
            raise RuntimeError("create_project_update should not be called")

        mocker.patch.object(sched, 'get_tasks', return_value=tasks)
        mocker.patch.object(sched, 'get_running_workflow_jobs', return_value=[])
        mocker.patch.object(sched, 'get_inventory_source_tasks', return_value=inventory_sources)
        mocker.patch.object(sched, 'get_latest_project_update_tasks', return_value=latest_project_updates)
        mocker.patch.object(sched, 'get_latest_inventory_update_tasks', return_value=latest_inventory_updates)
        create_project_update_mock = mocker.patch.object(sched, 'create_project_update', return_value=create_project_update)
        create_inventory_update_mock = mocker.patch.object(sched, 'create_inventory_update', return_value=create_inventory_update)
        mocker.patch.object(sched, 'start_task')

        if not create_project_update:
            create_project_update_mock.side_effect = no_create_project_update
        if not create_inventory_update:
            create_inventory_update_mock.side_effect = no_create_inventory_update
        return sched
    return fn

@pytest.fixture
def project_update_factory(epoch):
    def fn():
        return ProjectUpdateDict({
            'id': 1,
            'created': epoch - timedelta(seconds=100),
            'project_id': 1,
            'project__scm_update_cache_timeout': 0,
            'celery_task_id': '',
            'launch_type': 'dependency',
            'project__scm_update_on_launch': True,
        })
    return fn

@pytest.fixture
def pending_project_update(project_update_factory):
    project_update = project_update_factory()
    project_update['status'] = 'pending'
    return project_update

@pytest.fixture
def waiting_project_update(epoch, project_update_factory):
    project_update = project_update_factory()
    project_update['status'] = 'waiting'
    return project_update

@pytest.fixture
def running_project_update(epoch, project_update_factory):
    project_update = project_update_factory()
    project_update['status'] = 'running'
    return project_update

@pytest.fixture
def successful_project_update(epoch, project_update_factory):
    project_update = project_update_factory()
    project_update['finished'] = epoch - timedelta(seconds=90)
    project_update['status'] = 'successful'
    return project_update

@pytest.fixture
def successful_project_update_cache_expired(epoch, project_update_factory):
    project_update = project_update_factory()

    project_update['status'] = 'successful'
    project_update['created'] = epoch - timedelta(seconds=120)
    project_update['finished'] = epoch - timedelta(seconds=110)
    project_update['project__scm_update_cache_timeout'] = 1
    return project_update

@pytest.fixture
def failed_project_update(epoch, project_update_factory):
    project_update = project_update_factory()
    project_update['finished'] = epoch - timedelta(seconds=90)
    project_update['status'] = 'failed'
    return project_update

@pytest.fixture
def inventory_update_factory(epoch):
    def fn():
        return InventoryUpdateDict({
            'id': 1,
            'created': epoch - timedelta(seconds=101),
            'inventory_id': 1,
            'celery_task_id': '',
            'status': 'pending',
            'launch_type': 'dependency',
            'inventory_source_id': 1,
            'inventory_source__inventory_id': 1,
        })
    return fn

@pytest.fixture
def inventory_update_latest_factory(epoch):
    def fn():
        return InventoryUpdateDict({
            'id': 1,
            'created': epoch - timedelta(seconds=101),
            'inventory_id': 1,
            'celery_task_id': '',
            'status': 'pending',
            'launch_type': 'dependency',
            'inventory_source_id': 1,
            'finished': None,
        })
    return fn

@pytest.fixture
def inventory_update_latest(inventory_update_latest_factory):
    return inventory_update_latest_factory()

@pytest.fixture
def successful_inventory_update_latest(inventory_update_latest_factory):
    iu = inventory_update_latest_factory()
    iu['status'] = 'successful'
    iu['finished'] = iu['created'] + timedelta(seconds=10)
    return iu

@pytest.fixture
def failed_inventory_update_latest(inventory_update_latest_factory):
    iu = inventory_update_latest_factory()
    iu['status'] = 'failed'
    return iu

@pytest.fixture
def pending_inventory_update(epoch, inventory_update_factory):
    inventory_update = inventory_update_factory()
    inventory_update['status'] = 'pending'
    return inventory_update

@pytest.fixture
def waiting_inventory_update(epoch, inventory_update_factory):
    inventory_update = inventory_update_factory()
    inventory_update['status'] = 'waiting'
    return inventory_update

@pytest.fixture
def failed_inventory_update(epoch, inventory_update_factory):
    inventory_update = inventory_update_factory()
    inventory_update['status'] = 'failed'
    return inventory_update

@pytest.fixture
def running_inventory_update(epoch, inventory_update_factory):
    inventory_update = inventory_update_factory()
    inventory_update['status'] = 'running'
    return inventory_update

@pytest.fixture
def successful_inventory_update(epoch, inventory_update_factory):
    inventory_update = inventory_update_factory()
    inventory_update['finished'] = epoch - timedelta(seconds=90)
    inventory_update['status'] = 'successful'
    return inventory_update


'''
Job
'''
@pytest.fixture
def job_factory(epoch):
    def fn(id=1, project__scm_update_on_launch=True, inventory__inventory_sources=[], allow_simultaneous=False):
        return JobDict({ 
            'id': id,
            'status': 'pending', 
            'job_template_id': 1, 
            'project_id': 1, 
            'inventory_id': 1,
            'launch_type': 'manual', 
            'allow_simultaneous': allow_simultaneous,
            'created': epoch - timedelta(seconds=99), 
            'celery_task_id': '', 
            'project__scm_update_on_launch': project__scm_update_on_launch, 
            'inventory__inventory_sources': inventory__inventory_sources,
            'forks': 5 
        })
    return fn

@pytest.fixture
def pending_job(job_factory):
    job = job_factory()
    job['status'] = 'pending'
    return job

@pytest.fixture
def running_job(job_factory):
    job = job_factory()
    job['status'] = 'running'
    return job


'''
Inventory id -> [InventorySourceDict, ...]
'''
@pytest.fixture
def inventory_source_factory():
    def fn(id=1):
        return InventorySourceDict({
            'id': id,
        })
    return fn

@pytest.fixture
def inventory_id_sources(inventory_source_factory):
    return [
        (1, [
            inventory_source_factory(id=1),
            inventory_source_factory(id=2),
        ]),
    ]

