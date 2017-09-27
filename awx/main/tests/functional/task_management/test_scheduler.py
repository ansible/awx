import pytest
import mock
import json
from datetime import timedelta, datetime

from django.core.cache import cache
from django.utils.timezone import now as tz_now

from awx.main.scheduler import TaskManager
from awx.main.utils import encrypt_field
from awx.main.models import (
    Job,
    Instance,
    WorkflowJob,
)


@pytest.mark.django_db
def test_single_job_scheduler_launch(default_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [])


@pytest.mark.django_db
def test_single_jt_multi_job_launch_blocks_last(default_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start", "job_should_not_start"])
    j1 = objects.jobs["job_should_start"]
    j1.status = 'pending'
    j1.save()
    j2 = objects.jobs["job_should_not_start"]
    j2.status = 'pending'
    j2.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j1, default_instance_group, [])
        j1.status = "successful"
        j1.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j2, default_instance_group, [])


@pytest.mark.django_db
def test_single_jt_multi_job_launch_allow_simul_allowed(default_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start", "job_should_not_start"])
    jt = objects.job_template
    jt.save()

    j1 = objects.jobs["job_should_start"]
    j1.allow_simultaneous = True
    j1.status = 'pending'
    j1.save()
    j2 = objects.jobs["job_should_not_start"]
    j2.allow_simultaneous = True
    j2.status = 'pending'
    j2.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_has_calls([mock.call(j1, default_instance_group, []),
                                                 mock.call(j2, default_instance_group, [])])


@pytest.mark.django_db
def test_multi_jt_capacity_blocking(default_instance_group, job_template_factory, mocker):
    objects1 = job_template_factory('jt1', organization='org1', project='proj1',
                                    inventory='inv1', credential='cred1',
                                    jobs=["job_should_start"])
    objects2 = job_template_factory('jt2', organization='org2', project='proj2',
                                    inventory='inv2', credential='cred2',
                                    jobs=["job_should_not_start"])
    j1 = objects1.jobs["job_should_start"]
    j1.status = 'pending'
    j1.save()
    j2 = objects2.jobs["job_should_not_start"]
    j2.status = 'pending'
    j2.save()
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 500
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once_with(j1, default_instance_group, [])
            j1.status = "successful"
            j1.save()
    with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
        tm.schedule()
        mock_job.assert_called_once_with(j2, default_instance_group, [])
    
    

@pytest.mark.django_db
def test_single_job_dependencies_project_launch(default_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 0
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        tm = TaskManager()
        with mock.patch.object(TaskManager, "create_project_update", wraps=tm.create_project_update) as mock_pu:
            tm.schedule()
            mock_pu.assert_called_once_with(j)
            pu = [x for x in p.project_updates.all()]
            assert len(pu) == 1
            TaskManager.start_task.assert_called_once_with(pu[0], default_instance_group, [j])
            pu[0].status = "successful"
            pu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [])


@pytest.mark.django_db
def test_single_job_dependencies_inventory_update_launch(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 0
    ii.save()
    i.inventory_sources.add(ii)
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        tm = TaskManager()
        with mock.patch.object(TaskManager, "create_inventory_update", wraps=tm.create_inventory_update) as mock_iu:
            tm.schedule()
            mock_iu.assert_called_once_with(j, ii)
            iu = [x for x in ii.inventory_updates.all()]
            assert len(iu) == 1
            TaskManager.start_task.assert_called_once_with(iu[0], default_instance_group, [j])
            iu[0].status = "successful"
            iu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [])


@pytest.mark.django_db
def test_job_dependency_with_already_updated(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 0
    ii.save()
    i.inventory_sources.add(ii)
    j.start_args = json.dumps(dict(inventory_sources_already_updated=[ii.id]))
    j.save()
    j.start_args = encrypt_field(j, field_name="start_args")
    j.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        tm = TaskManager()
        with mock.patch.object(TaskManager, "create_inventory_update", wraps=tm.create_inventory_update) as mock_iu:
            tm.schedule()
            mock_iu.assert_not_called()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [])


@pytest.mark.django_db
def test_shared_dependencies_launch(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["first_job", "second_job"])
    j1 = objects.jobs["first_job"]
    j1.status = 'pending'
    j1.save()
    j2 = objects.jobs["second_job"]
    j2.status = 'pending'
    j2.save()
    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 300
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save()

    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 300
    ii.save()
    i.inventory_sources.add(ii)

    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        pu = p.project_updates.first()
        iu = ii.inventory_updates.first()
        TaskManager.start_task.assert_has_calls([mock.call(pu, default_instance_group, [iu, j1]),
                                                 mock.call(iu, default_instance_group, [pu, j1])])
        pu.status = "successful"
        pu.finished = pu.created + timedelta(seconds=1)
        pu.save()
        iu.status = "successful"
        iu.finished = iu.created + timedelta(seconds=1)
        iu.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j1, default_instance_group, [])
        j1.status = "successful"
        j1.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j2, default_instance_group, [])
    pu = [x for x in p.project_updates.all()]
    iu = [x for x in ii.inventory_updates.all()]
    assert len(pu) == 1
    assert len(iu) == 1


@pytest.mark.django_db
def test_cleanup_interval():
    assert cache.get('last_celery_task_cleanup') is None

    TaskManager().cleanup_inconsistent_celery_tasks()
    last_cleanup = cache.get('last_celery_task_cleanup')
    assert isinstance(last_cleanup, datetime)

    TaskManager().cleanup_inconsistent_celery_tasks()
    assert cache.get('last_celery_task_cleanup') == last_cleanup


class TestReaper():
    @pytest.fixture
    def all_jobs(self, mocker):
        now = tz_now()

        Instance.objects.create(hostname='host1', capacity=100)
        Instance.objects.create(hostname='host2', capacity=100)
        Instance.objects.create(hostname='host3_split', capacity=100)
        Instance.objects.create(hostname='host4_offline', capacity=0)

        j1 = Job.objects.create(status='pending', execution_node='host1')
        j2 = Job.objects.create(status='waiting', celery_task_id='considered_j2')
        j3 = Job.objects.create(status='waiting', celery_task_id='considered_j3')
        j3.modified = now - timedelta(seconds=60)
        j3.save(update_fields=['modified'])
        j4 = Job.objects.create(status='running', celery_task_id='considered_j4', execution_node='host1')
        j5 = Job.objects.create(status='waiting', celery_task_id='reapable_j5')
        j5.modified = now - timedelta(seconds=60)
        j5.save(update_fields=['modified'])
        j6 = Job.objects.create(status='waiting', celery_task_id='considered_j6')
        j6.modified = now - timedelta(seconds=60)
        j6.save(update_fields=['modified'])
        j7 = Job.objects.create(status='running', celery_task_id='considered_j7', execution_node='host2')
        j8 = Job.objects.create(status='running', celery_task_id='reapable_j7', execution_node='host2')
        j9 = Job.objects.create(status='waiting', celery_task_id='reapable_j8')
        j9.modified = now - timedelta(seconds=60)
        j9.save(update_fields=['modified'])
        j10 = Job.objects.create(status='running', celery_task_id='host3_j10', execution_node='host3_split')

        j11 = Job.objects.create(status='running', celery_task_id='host4_j11', execution_node='host4_offline')

        j12 = WorkflowJob.objects.create(status='running', celery_task_id='workflow_job', execution_node='host1')

        js = [j1, j2, j3, j4, j5, j6, j7, j8, j9, j10, j11, j12]
        for j in js:
            j.save = mocker.Mock(wraps=j.save)
            j.websocket_emit_status = mocker.Mock()
        return js

    @pytest.fixture
    def considered_jobs(self, all_jobs):
        return all_jobs[2:7] + [all_jobs[10]]

    @pytest.fixture
    def running_tasks(self, all_jobs):
        return {
            'host1': [all_jobs[3]],
            'host2': [all_jobs[7], all_jobs[8]],
            'host3_split': [all_jobs[9]],
            'host4_offline': [all_jobs[10]],
        }

    @pytest.fixture
    def waiting_tasks(self, all_jobs):
        return [all_jobs[2], all_jobs[4], all_jobs[5], all_jobs[8]]

    @pytest.fixture
    def reapable_jobs(self, all_jobs):
        return [all_jobs[4], all_jobs[7], all_jobs[10]]

    @pytest.fixture
    def unconsidered_jobs(self, all_jobs):
        return all_jobs[0:1] + all_jobs[5:7]

    @pytest.fixture
    def active_tasks(self):
        return ([], {
            'host1': ['considered_j2', 'considered_j3', 'considered_j4',],
            'host2': ['considered_j6', 'considered_j7'],
        })

    @pytest.mark.django_db
    @mock.patch('awx.main.tasks._send_notification_templates')
    @mock.patch.object(TaskManager, 'get_active_tasks', lambda self: ([], []))
    def test_cleanup_inconsistent_task(self, notify, active_tasks, considered_jobs, reapable_jobs, running_tasks, waiting_tasks, mocker):
        tm = TaskManager()

        tm.get_running_tasks = mocker.Mock(return_value=(running_tasks, waiting_tasks))
        tm.get_active_tasks = mocker.Mock(return_value=active_tasks)
        
        tm.cleanup_inconsistent_celery_tasks()
        
        for j in considered_jobs:
            if j not in reapable_jobs:
                j.save.assert_not_called()

        assert notify.call_count == 4
        notify.assert_has_calls([mock.call(j, 'failed') for j in reapable_jobs], any_order=True)

        for j in reapable_jobs:
            j.websocket_emit_status.assert_called_once_with('failed')
            assert j.status == 'failed'
            assert j.job_explanation == (
                'Task was marked as running in Tower but was not present in Celery, so it has been marked as failed.'
            )

    @pytest.mark.django_db
    def test_get_running_tasks(self, all_jobs):
        tm = TaskManager()

        # Ensure the query grabs the expected jobs
        execution_nodes_jobs, waiting_jobs = tm.get_running_tasks()
        assert 'host1' in execution_nodes_jobs
        assert 'host2' in execution_nodes_jobs
        assert 'host3_split' in execution_nodes_jobs

        assert all_jobs[3] in execution_nodes_jobs['host1']

        assert all_jobs[6] in execution_nodes_jobs['host2']
        assert all_jobs[7] in execution_nodes_jobs['host2']
        
        assert all_jobs[9] in execution_nodes_jobs['host3_split']

        assert all_jobs[10] in execution_nodes_jobs['host4_offline']

        assert all_jobs[11] not in execution_nodes_jobs['host1']

        assert all_jobs[2] in waiting_jobs
        assert all_jobs[4] in waiting_jobs
        assert all_jobs[5] in waiting_jobs
        assert all_jobs[8] in waiting_jobs
