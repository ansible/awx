import datetime
from unittest import mock
from django.utils.timezone import now as tz_now
import pytest
from django.test import override_settings

from awx.main.models import InstanceGroup, Job, WorkflowJob, Instance
from awx.main.dispatch import reaper
from awx.main.dispatch.reaper import (
    reset_orphaned_waiting_jobs,
    reap_orphaned_jobs,
    get_orphaned_running_jobs_query,
    startup_reaping,
    reap_job,
)
from awx.main.tasks import system
from dispatcherd.publish import task

'''
Prevent logger.<warn, debug, error> calls from triggering database operations
'''


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=mock.PropertyMock)
    m.return_value = []


def restricted(a, b):
    raise AssertionError("This code should not run because it isn't decorated with @task")


@task()
def add(a, b):
    return a + b


class BaseTask(object):
    def add(self, a, b):
        return add(a, b)


class Restricted(object):
    def run(self, a, b):
        raise AssertionError("This code should not run because it isn't decorated with @task")


@task()
class Adder(BaseTask):
    def run(self, a, b):
        return super(Adder, self).add(a, b)


@task(queue='hard-math')
def multiply(a, b):
    return a * b


yesterday = tz_now() - datetime.timedelta(days=1)
minute = tz_now() - datetime.timedelta(seconds=120)
now = tz_now()


@pytest.mark.django_db
class TestJobReaper(object):
    @pytest.mark.parametrize(
        'status, execution_node, controller_node, modified, fail',
        [
            ('running', '', '', None, False),  # running, not assigned to the instance
            ('running', 'awx', '', None, True),  # running, has the instance as its execution_node
            ('running', '', 'awx', None, True),  # running, has the instance as its controller_node
        ],
    )
    def test_should_reap(self, status, fail, execution_node, controller_node, modified):
        i = Instance(hostname='awx')
        i.save()
        j = Job(
            status=status,
            execution_node=execution_node,
            controller_node=controller_node,
            start_args='SENSITIVE',
        )
        j.save()
        if modified:
            # we have to edit the modification time _without_ calling save()
            # (because .save() overwrites it to _now_)
            Job.objects.filter(id=j.id).update(modified=modified)
        reaper.reap(i)
        job = Job.objects.first()
        if fail:
            assert job.status == 'failed'
            assert 'marked as failed' in job.job_explanation
            assert job.start_args == ''
        else:
            assert job.status == status

    def test_waiting_job_sent_back_to_pending(self):
        this_inst = Instance(hostname='awx')
        this_inst.save()
        lost_inst = Instance(hostname='lost', node_type=Instance.Types.EXECUTION, node_state=Instance.States.UNAVAILABLE)
        lost_inst.save()
        job = Job.objects.create(status='waiting', controller_node=lost_inst.hostname, execution_node='lost')

        system._heartbeat_handle_lost_instances([lost_inst], this_inst)

        # Simulate what the background task would do
        reset_orphaned_waiting_jobs()

        job.refresh_from_db()

        assert job.status == 'pending'
        assert job.controller_node == ''
        assert job.execution_node == ''

    @pytest.mark.parametrize(
        'excluded_uuids, fail, started',
        [
            (['abc123'], False, None),
            ([], False, None),
            ([], True, minute),
        ],
    )
    def test_do_not_reap_excluded_uuids(self, excluded_uuids, fail, started):
        """Modified Test to account for ref_time in reap()"""
        i = Instance(hostname='awx')
        i.save()
        j = Job(
            status='running',
            execution_node='awx',
            controller_node='',
            start_args='SENSITIVE',
            celery_task_id='abc123',
        )
        j.save()
        if started:
            Job.objects.filter(id=j.id).update(started=started)

        # if the UUID is excluded, don't reap it
        reaper.reap(i, excluded_uuids=excluded_uuids, ref_time=now)
        job = Job.objects.first()

        if fail:
            assert job.status == 'failed'
            assert 'marked as failed' in job.job_explanation
            assert job.start_args == ''
        else:
            assert job.status == 'running'

    def test_workflow_does_not_reap(self):
        i = Instance(hostname='awx')
        i.save()
        j = WorkflowJob(status='running', execution_node='awx')
        j.save()
        reaper.reap(i)

        assert WorkflowJob.objects.first().status == 'running'

    def test_should_not_reap_new(self):
        """
        This test is designed specifically to ensure that jobs that are launched after the dispatcher has provided a list of UUIDs aren't reaped.
        It is very racy and this test is designed with that in mind
        """
        i = Instance(hostname='awx')
        # ref_time is set to 10 seconds in the past to mimic someone launching a job in the heartbeat window.
        ref_time = tz_now() - datetime.timedelta(seconds=10)
        # creating job at current time
        job = Job.objects.create(status='running', controller_node=i.hostname)
        reaper.reap(i, ref_time=ref_time)
        # explictly refreshing from db to ensure up to date cache
        job.refresh_from_db()
        assert job.started > ref_time
        assert job.status == 'running'
        assert job.job_explanation == ''

    def test_waiting_job_reset_when_controller_node_deprovisioned(self):
        """When a controller pod is replaced (e.g. K8s rollout), waiting jobs
        assigned to the now-gone controller_node should be reset to pending
        by the task manager so they can be re-dispatched."""
        live_inst = Instance(hostname='awx-task-live', node_type='control')
        live_inst.save()
        # No instance record for 'awx-task-dead' — it was already deprovisioned
        job = Job.objects.create(status='waiting', controller_node='awx-task-dead', execution_node='')

        # Simulate what the background task would do
        reset_orphaned_waiting_jobs()

        job.refresh_from_db()
        assert job.status == 'pending'
        assert job.controller_node == ''
        assert job.execution_node == ''

    @pytest.mark.parametrize('node_type', ['control', 'hybrid'])
    def test_waiting_job_not_reset_when_controller_node_alive(self, node_type):
        """Waiting jobs on a live control or hybrid node should not be touched."""
        live_inst = Instance(hostname='awx-task-live', node_type=node_type)
        live_inst.save()
        job = Job.objects.create(status='waiting', controller_node='awx-task-live', execution_node='')

        # Simulate what the background task would do
        reset_orphaned_waiting_jobs()

        job.refresh_from_db()
        assert job.status == 'waiting'
        assert job.controller_node == 'awx-task-live'

    def test_reap_orphaned_jobs_background_task(self):
        """Test the reap_orphaned_jobs background task reaps running jobs on orphaned execution nodes."""
        exec_inst = Instance(hostname='exec-live', node_type='execution')
        exec_inst.save()

        orphaned_job = Job.objects.create(
            status='running',
            execution_node='exec-orphaned',
            controller_node='',
            start_args='SENSITIVE',
        )
        valid_job = Job.objects.create(
            status='running',
            execution_node='exec-live',
            controller_node='',
        )

        reap_orphaned_jobs()

        orphaned_job.refresh_from_db()
        valid_job.refresh_from_db()

        assert orphaned_job.status == 'failed'
        assert 'not a registered instance' in orphaned_job.job_explanation
        assert orphaned_job.start_args == ''
        assert valid_job.status == 'running'

    def test_get_orphaned_running_jobs_query(self):
        """Test that get_orphaned_running_jobs_query filters correctly."""
        exec_inst = Instance(hostname='exec-live', node_type='execution')
        exec_inst.save()

        orphaned = Job.objects.create(status='running', execution_node='exec-orphaned', controller_node='')
        valid = Job.objects.create(status='running', execution_node='exec-live', controller_node='')
        not_running = Job.objects.create(status='pending', execution_node='exec-orphaned', controller_node='')
        workflow = WorkflowJob.objects.create(status='running', execution_node='exec-orphaned', controller_node='')

        valid_nodes = ['exec-live']
        qs = get_orphaned_running_jobs_query(valid_nodes)

        result_ids = set(qs.values_list('id', flat=True))
        assert orphaned.id in result_ids
        assert valid.id not in result_ids
        assert not_running.id not in result_ids
        assert workflow.id not in result_ids

    def test_reset_orphaned_waiting_jobs_background_task(self):
        """Test the reset_orphaned_waiting_jobs background task resets waiting jobs on orphaned controller nodes."""
        ctrl_inst = Instance(hostname='ctrl-live', node_type='control')
        ctrl_inst.save()

        orphaned_job = Job.objects.create(
            status='waiting',
            controller_node='ctrl-orphaned',
            execution_node='',
        )
        valid_job = Job.objects.create(
            status='waiting',
            controller_node='ctrl-live',
            execution_node='',
        )
        pending_job = Job.objects.create(
            status='pending',
            controller_node='ctrl-orphaned',
            execution_node='',
        )

        reset_orphaned_waiting_jobs()

        orphaned_job.refresh_from_db()
        valid_job.refresh_from_db()
        pending_job.refresh_from_db()

        assert orphaned_job.status == 'pending'
        assert orphaned_job.controller_node == ''
        assert orphaned_job.execution_node == ''
        assert valid_job.status == 'waiting'
        assert pending_job.status == 'pending'

    def test_startup_reaping(self, mocker):
        """Test startup_reaping reaps running jobs on the controller node at startup."""
        inst = Instance(hostname='awx-controller')
        inst.save()

        mocker.patch('awx.main.models.Instance.objects.my_hostname', return_value='awx-controller')

        job1 = Job.objects.create(status='running', controller_node='awx-controller', start_args='SENSITIVE')
        job2 = Job.objects.create(status='running', controller_node='other', start_args='SENSITIVE')
        job3 = Job.objects.create(status='failed', controller_node='awx-controller')

        startup_reaping()

        job1.refresh_from_db()
        job2.refresh_from_db()
        job3.refresh_from_db()

        assert job1.status == 'failed'
        assert 'at system start up' in job1.job_explanation
        assert job1.start_args == ''
        assert job2.status == 'running'
        assert job3.status == 'failed'

    def test_reap_job_updates_status(self):
        """Test reap_job marks a running job as failed and clears sensitive data."""
        job = Job.objects.create(
            status='running',
            start_args='SENSITIVE_DATA',
            job_explanation='Some prior explanation.',
        )

        reap_job(job, 'failed', job_explanation='Task was lost')

        job.refresh_from_db()
        assert job.status == 'failed'
        assert job.start_args == ''
        assert 'Some prior explanation' in job.job_explanation
        assert 'Task was lost' in job.job_explanation

    def test_reap_job_does_not_reap_non_running(self):
        """Test reap_job does not modify jobs that are not running or waiting."""
        job = Job.objects.create(status='failed', start_args='SENSITIVE')
        original_args = job.start_args

        reap_job(job, 'failed', job_explanation='Should not apply')

        job.refresh_from_db()
        assert job.status == 'failed'
        assert job.start_args == original_args

    def test_reap_orphaned_jobs_skips_container_group_task(self):
        """Container group tasks on orphaned nodes should not be reaped."""
        exec_inst = Instance(hostname='exec-live', node_type='execution')
        exec_inst.save()
        cg = InstanceGroup.objects.create(name='container-group', is_container_group=True)

        cg_job = Job.objects.create(
            status='running',
            execution_node='exec-orphaned',
            controller_node='',
            start_args='SENSITIVE',
        )
        cg_job.instance_group = cg
        cg_job.save(update_fields=['instance_group'])

        normal_job = Job.objects.create(
            status='running',
            execution_node='exec-orphaned',
            controller_node='',
            start_args='SENSITIVE',
        )

        reap_orphaned_jobs()

        cg_job.refresh_from_db()
        normal_job.refresh_from_db()

        assert cg_job.status == 'running', 'Container group task should not be reaped'
        assert cg_job.start_args != ''
        assert normal_job.status == 'failed'
        assert 'not a registered instance' in normal_job.job_explanation

    def test_heartbeat_handle_lost_instances_marks_offline(self, mocker):
        """Test _heartbeat_handle_lost_instances marks lost control instances offline and triggers task manager."""
        this_inst = Instance(hostname='awx-alive', node_type='control')
        this_inst.save()
        lost_inst = Instance(hostname='awx-lost', node_type='control', node_state=Instance.States.READY)
        lost_inst.save()

        schedule_mock = mocker.patch('awx.main.utils.ScheduleTaskManager')

        system._heartbeat_handle_lost_instances([lost_inst], this_inst)

        lost_inst.refresh_from_db()
        assert lost_inst.node_state == Instance.States.UNAVAILABLE
        schedule_mock.return_value.schedule.assert_called_once()

    @override_settings(AWX_AUTO_DEPROVISION_INSTANCES=True)
    def test_heartbeat_handle_lost_instances_deprovisioned(self, mocker):
        """Test _heartbeat_handle_lost_instances auto-deprovisions control nodes when enabled."""
        this_inst = Instance(hostname='awx-alive', node_type='control')
        this_inst.save()
        lost_inst = Instance(hostname='awx-lost', node_type='control')
        lost_inst.save()

        schedule_mock = mocker.patch('awx.main.utils.ScheduleTaskManager')

        system._heartbeat_handle_lost_instances([lost_inst], this_inst)

        assert not Instance.objects.filter(hostname='awx-lost').exists()
        schedule_mock.return_value.schedule.assert_called_once()
