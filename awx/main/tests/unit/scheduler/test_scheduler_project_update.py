
# Python
import pytest
from datetime import timedelta

# Django
from django.utils.timezone import now as tz_now

# awx
from awx.main.scheduler.partial import (
    JobDict,
    ProjectUpdateDict,
)
from awx.main.scheduler import Scheduler

# TODO: wherever get_latest_rpoject_update_task() is stubbed and returns a
# ProjectUpdateDict. We should instead return a ProjectUpdateLatestDict()
# For now, this is ok since the fields on deviate that much.

@pytest.fixture
def epoch():
    return tz_now()


@pytest.fixture
def scheduler_factory(mocker, epoch):
    def fn(tasks=[], latest_project_updates=[], create_project_update=None):
        sched = Scheduler()
        sched.capacity_total = 999999999

        sched.graph.get_now = lambda: epoch

        mocker.patch.object(sched, 'get_tasks', return_value=tasks)
        mocker.patch.object(sched, 'get_latest_project_update_tasks', return_value=latest_project_updates)
        mocker.patch.object(sched, 'create_project_update', return_value=create_project_update)
        mocker.patch.object(sched, 'start_task')
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
def pending_job(epoch):
    return JobDict({ 
        'id': 1, 
        'status': 'pending', 
        'job_template_id': 1, 
        'project_id': 1, 
        'inventory_id': 1,
        'launch_type': 'manual', 
        'allow_simultaneous': False, 
        'created': epoch - timedelta(seconds=99), 
        'celery_task_id': '', 
        'project__scm_update_on_launch': True, 
        'forks': 5 
    })

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

class TestStartProjectUpdate():
    def test(self, scheduler_factory, pending_project_update):
        scheduler = scheduler_factory(tasks=[pending_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_project_update)
        assert scheduler.create_project_update.call_count == 0

    '''
    Explicit project update should always run. They should not use cache logic.
    '''
    def test_cache_oblivious(self, scheduler_factory, successful_project_update, pending_project_update):
        scheduler = scheduler_factory(tasks=[pending_project_update],
                                      latest_project_updates=[successful_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_project_update)
        assert scheduler.create_project_update.call_count == 0


class TestCreateDependentProjectUpdate():

    def test(self, scheduler_factory, pending_job, waiting_project_update):
        scheduler = scheduler_factory(tasks=[pending_job], 
                                      create_project_update=waiting_project_update)

        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])

    def test_cache_hit(self, scheduler_factory, pending_job, successful_project_update):
        scheduler = scheduler_factory(tasks=[successful_project_update, pending_job], 
                                      latest_project_updates=[successful_project_update])
        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_job)

    def test_cache_miss(self, scheduler_factory, pending_job, successful_project_update_cache_expired, waiting_project_update):
        scheduler = scheduler_factory(tasks=[successful_project_update_cache_expired, pending_job], 
                                      latest_project_updates=[successful_project_update_cache_expired], 
                                      create_project_update=waiting_project_update)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])

    def test_last_update_failed(self, scheduler_factory, pending_job, failed_project_update, waiting_project_update):
        scheduler = scheduler_factory(tasks=[failed_project_update, pending_job], 
                                      latest_project_updates=[failed_project_update], 
                                      create_project_update=waiting_project_update)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])


class TestJobBlockedOnProjectUpdate():
    def test(self, scheduler_factory, pending_job, waiting_project_update):
        scheduler = scheduler_factory(tasks=[waiting_project_update, pending_job],
                                      latest_project_updates=[waiting_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

    def test_project_running(self, scheduler_factory, pending_job, running_project_update):
        scheduler = scheduler_factory(tasks=[running_project_update, pending_job])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

class TestProjectUpdateBlocked():
    def test(self, scheduler_factory, running_project_update, pending_project_update):
        scheduler = scheduler_factory(tasks=[running_project_update, pending_project_update],
                                      latest_project_updates=[running_project_update])
        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

