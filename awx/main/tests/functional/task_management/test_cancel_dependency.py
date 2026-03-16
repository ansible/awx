# Test file for cancel + dependency chain behavior
#
# These tests verify behavior when canceling jobs that have dependency chain
# project updates (created by DependencyManager for projects with
# scm_update_on_launch=True), and when the task manager encounters pending
# jobs with cancel_flag set.

import pytest
from unittest import mock

from awx.api.versioning import reverse
from awx.main.scheduler import TaskManager, DependencyManager
from awx.main.models import ProjectUpdate
from . import create_job


@pytest.fixture
def scm_on_launch_objects(job_template_factory):
    """Create a job template with a project configured for scm_update_on_launch."""
    objects = job_template_factory(
        'jt',
        organization='org1',
        project='proj',
        inventory='inv',
        credential='cred',
    )
    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 0
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save(skip_update=True)
    return objects


def _create_job_with_dependency(objects):
    """Create a pending job and run DependencyManager to produce its project update dependency.

    Returns (job, project_update).
    """
    j = create_job(objects.job_template, dependencies_processed=False)
    with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
        DependencyManager().schedule()
    assert j.dependent_jobs.count() == 1
    pu = j.dependent_jobs.first()
    assert isinstance(pu.get_real_instance(), ProjectUpdate)
    return j, pu


def _simulate_dependency_running(pu):
    """Transition a project update to running with fake dispatcher fields."""
    ProjectUpdate.objects.filter(pk=pu.pk).update(
        status='running',
        celery_task_id='fake-task-id',
        controller_node='test-node',
    )
    pu.refresh_from_db()


@pytest.mark.django_db
class TestCancelPropagatesToDependency:
    """When a job is canceled, its dependency project updates (linked via
    dependent_jobs M2M) should also be canceled."""

    def test_cancel_job_cancels_dependency_project_update(self, controlplane_instance_group, scm_on_launch_objects):
        """Cancel a job whose dependency project update is running and verify
        cancel_flag propagates to the dependency."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)
        _simulate_dependency_running(pu)

        j.refresh_from_db()
        assert j.can_cancel
        with mock.patch('awx.main.models.unified_jobs.UnifiedJob.cancel_dispatcher_process'):
            j.cancel()

        j.refresh_from_db()
        pu.refresh_from_db()

        assert j.cancel_flag is True
        assert pu.cancel_flag is True

    def test_get_jobs_fail_chain_includes_dependent_jobs(self, controlplane_instance_group, scm_on_launch_objects):
        """Verify that Job.get_jobs_fail_chain() includes entries
        from the dependent_jobs M2M relationship."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)

        # project_update FK is not set (only set by the runner during pre_run_hook)
        assert j.project_update_id is None

        chain = j.get_jobs_fail_chain()
        assert pu in chain


@pytest.mark.django_db
class TestCanceledDependencyFailsBlockedJob:
    """When a dependency project update is canceled or failed, the task manager
    should fail the blocked job via process_job_dep_failures."""

    def test_canceled_dependency_fails_blocked_job(self, controlplane_instance_group, scm_on_launch_objects):
        """A canceled dependency causes the blocked job to be failed with
        a 'Previous Task Canceled' explanation."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)

        ProjectUpdate.objects.filter(pk=pu.pk).update(status='canceled', cancel_flag=True)

        with mock.patch("awx.main.scheduler.TaskManager.start_task"):
            TaskManager().schedule()

        j.refresh_from_db()
        assert j.status == 'failed'
        assert 'Previous Task Canceled' in j.job_explanation

    def test_failed_dependency_fails_blocked_job(self, controlplane_instance_group, scm_on_launch_objects):
        """A failed dependency causes the blocked job to be failed with
        a 'Previous Task Failed' explanation."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)

        ProjectUpdate.objects.filter(pk=pu.pk).update(status='failed')

        with mock.patch("awx.main.scheduler.TaskManager.start_task"):
            TaskManager().schedule()

        j.refresh_from_db()
        assert j.status == 'failed'
        assert 'Previous Task Failed' in j.job_explanation


@pytest.mark.django_db
class TestCancelWithApiAndTaskManager:
    """End-to-end tests using API cancel endpoint + task manager."""

    def test_cancel_job_via_api_cancels_dependency(self, controlplane_instance_group, scm_on_launch_objects, post, admin_user):
        """Cancel a pending job via the API cancel endpoint and verify the
        dependency project update is also canceled."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)
        _simulate_dependency_running(pu)

        url = reverse('api:job_cancel', kwargs={'pk': j.pk})
        with mock.patch('awx.main.models.unified_jobs.UnifiedJob.cancel_dispatcher_process'):
            post(url, user=admin_user, expect=202)

        j.refresh_from_db()
        pu.refresh_from_db()

        assert j.cancel_flag is True
        assert pu.cancel_flag is True

    def test_cancel_job_dep_canceled_then_task_manager_fails_job(self, controlplane_instance_group, scm_on_launch_objects, post, admin_user):
        """Cancel a job while its dependency is running. The cancel propagates
        to the dependency. When the task manager runs, it sees the canceled
        dependency and fails the job with 'Previous Task Canceled'."""
        j, pu = _create_job_with_dependency(scm_on_launch_objects)
        _simulate_dependency_running(pu)

        url = reverse('api:job_cancel', kwargs={'pk': j.pk})
        with mock.patch('awx.main.models.unified_jobs.UnifiedJob.cancel_dispatcher_process'):
            post(url, user=admin_user, expect=202)

        j.refresh_from_db()
        pu.refresh_from_db()
        assert j.cancel_flag is True
        assert pu.cancel_flag is True

        # Simulate the project update finishing as canceled
        ProjectUpdate.objects.filter(pk=pu.pk).update(status='canceled')

        with mock.patch("awx.main.scheduler.TaskManager.start_task") as mock_start:
            TaskManager().schedule()

        j.refresh_from_db()
        assert j.status == 'failed'
        assert 'Previous Task Canceled' in j.job_explanation
        assert not mock_start.called


@pytest.mark.django_db
class TestTaskManagerCancelsPendingJobsWithCancelFlag:
    """When the task manager encounters pending jobs that have cancel_flag set,
    it should transition them directly to canceled status."""

    def test_pending_job_with_cancel_flag_is_canceled(self, controlplane_instance_group, job_template_factory):
        """A pending job with cancel_flag=True is transitioned to canceled
        by the task manager without being started."""
        objects = job_template_factory(
            'jt',
            organization='org1',
            project='proj',
            inventory='inv',
            credential='cred',
        )
        j = create_job(objects.job_template)
        j.cancel_flag = True
        j.save(update_fields=['cancel_flag'])

        with mock.patch("awx.main.scheduler.TaskManager.start_task") as mock_start:
            TaskManager().schedule()

        j.refresh_from_db()
        assert j.status == 'canceled'
        assert 'canceled before it started' in j.job_explanation
        assert not mock_start.called

    def test_pending_job_without_cancel_flag_is_not_canceled(self, controlplane_instance_group, job_template_factory):
        """A normal pending job without cancel_flag should not be canceled
        by the task manager (sanity check)."""
        objects = job_template_factory(
            'jt',
            organization='org1',
            project='proj',
            inventory='inv',
            credential='cred',
        )
        j = create_job(objects.job_template)

        with mock.patch("awx.main.scheduler.TaskManager.start_task"):
            TaskManager().schedule()

        j.refresh_from_db()
        assert j.status != 'canceled'

    def test_multiple_pending_jobs_with_cancel_flag_bulk_canceled(self, controlplane_instance_group, job_template_factory):
        """Multiple pending jobs with cancel_flag=True are all transitioned
        to canceled in a single task manager cycle."""
        objects = job_template_factory(
            'jt',
            organization='org1',
            project='proj',
            inventory='inv',
            credential='cred',
        )
        jt = objects.job_template
        jt.allow_simultaneous = True
        jt.save()

        jobs = []
        for _ in range(3):
            j = create_job(jt)
            j.cancel_flag = True
            j.save(update_fields=['cancel_flag'])
            jobs.append(j)

        with mock.patch("awx.main.scheduler.TaskManager.start_task") as mock_start:
            TaskManager().schedule()

        for j in jobs:
            j.refresh_from_db()
            assert j.status == 'canceled', f"Job {j.id} should be canceled but is {j.status}"
            assert 'canceled before it started' in j.job_explanation
        assert not mock_start.called
