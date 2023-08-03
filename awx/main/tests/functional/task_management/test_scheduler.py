import pytest
from unittest import mock
import json
from datetime import timedelta

from awx.main.scheduler import TaskManager, DependencyManager, WorkflowManager
from awx.main.utils import encrypt_field
from awx.main.models import WorkflowJobTemplate, JobTemplate, Job
from awx.main.models.ha import Instance
from . import create_job
from django.conf import settings


@pytest.mark.django_db
def test_single_job_scheduler_launch(hybrid_instance, controlplane_instance_group, job_template_factory, mocker):
    instance = controlplane_instance_group.instances.all()[0]
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    j = create_job(objects.job_template)
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, controlplane_instance_group, instance)


@pytest.mark.django_db
class TestJobLifeCycle:
    def run_tm(self, tm, expect_channel=None, expect_schedule=None, expect_commit=None):
        """Test helper method that takes parameters to assert against
        expect_channel - list of expected websocket emit channel message calls
        expect_schedule - list of expected calls to reschedule itself
        expect_commit - list of expected on_commit calls
        If any of these are None, then the assertion is not made.
        """
        with mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status') as mock_channel:
            with mock.patch('awx.main.utils.common.ScheduleManager._schedule') as tm_sch:
                # Job are ultimately submitted in on_commit hook, but this will not
                # actually run, because it waits until outer transaction, which is the test
                # itself in this case
                with mock.patch('django.db.connection.on_commit') as mock_commit:
                    tm.schedule()
                    if expect_channel is not None:
                        assert mock_channel.mock_calls == expect_channel
                    if expect_schedule is not None:
                        assert tm_sch.mock_calls == expect_schedule
                    if expect_commit is not None:
                        assert mock_commit.mock_calls == expect_commit

    def test_task_manager_workflow_rescheduling(self, job_template_factory, inventory, project, controlplane_instance_group):
        jt = JobTemplate.objects.create(allow_simultaneous=True, inventory=inventory, project=project, playbook='helloworld.yml')
        wfjt = WorkflowJobTemplate.objects.create(name='foo')
        for i in range(2):
            wfjt.workflow_nodes.create(unified_job_template=jt)
        wj = wfjt.create_unified_job()
        assert wj.workflow_nodes.count() == 2
        wj.signal_start()

        # Transitions workflow job to running
        # needs to re-schedule so it spawns jobs next round
        self.run_tm(TaskManager(), [mock.call('running')])

        # Spawns jobs
        # needs re-schedule to submit jobs next round
        self.run_tm(WorkflowManager(), [mock.call('pending'), mock.call('pending')])

        assert jt.jobs.count() == 2  # task manager spawned jobs

        # Submits jobs
        # intermission - jobs will run and reschedule TM when finished
        self.run_tm(DependencyManager())  # flip dependencies_processed to True
        self.run_tm(TaskManager())
        # I am the job runner
        for job in jt.jobs.all():
            job.status = 'successful'
            job.save()

        # Finishes workflow
        # no further action is necessary, so rescheduling should not happen
        self.run_tm(WorkflowManager(), [mock.call('successful')])

    def test_task_manager_workflow_workflow_rescheduling(self, controlplane_instance_group):
        wfjts = [WorkflowJobTemplate.objects.create(name='foo')]
        for i in range(5):
            wfjt = WorkflowJobTemplate.objects.create(name='foo{}'.format(i))
            wfjts[-1].workflow_nodes.create(unified_job_template=wfjt)
            wfjts.append(wfjt)

        wj = wfjts[0].create_unified_job()
        wj.signal_start()

        attempts = 10
        while wfjts[0].status != 'successful' and attempts > 0:
            self.run_tm(TaskManager())
            self.run_tm(WorkflowManager())
            wfjts[0].refresh_from_db()
            attempts -= 1

    def test_control_and_execution_instance(self, project, system_job_template, job_template, inventory_source, control_instance, execution_instance):
        assert Instance.objects.count() == 2

        pu = project.create_unified_job()
        sj = system_job_template.create_unified_job()
        job = job_template.create_unified_job()
        inv_update = inventory_source.create_unified_job()

        all_ujs = (pu, sj, job, inv_update)
        for uj in all_ujs:
            uj.signal_start()

        DependencyManager().schedule()
        tm = TaskManager()
        self.run_tm(tm)

        for uj in all_ujs:
            uj.refresh_from_db()
            assert uj.status == 'waiting'

        for uj in (pu, sj):  # control plane jobs
            assert uj.capacity_type == 'control'
            assert [uj.execution_node, uj.controller_node] == [control_instance.hostname, control_instance.hostname], uj
        for uj in (job, inv_update):  # user-space jobs
            assert uj.capacity_type == 'execution'
            assert [uj.execution_node, uj.controller_node] == [execution_instance.hostname, control_instance.hostname], uj

    @pytest.mark.django_db
    def test_job_fails_to_launch_when_no_control_capacity(self, job_template, control_instance_low_capacity, execution_instance):
        enough_capacity = job_template.create_unified_job()
        insufficient_capacity = job_template.create_unified_job()
        all_ujs = [enough_capacity, insufficient_capacity]
        for uj in all_ujs:
            uj.signal_start()

        DependencyManager().schedule()
        # There is only enough control capacity to run one of the jobs so one should end up in pending and the other in waiting
        tm = TaskManager()
        self.run_tm(tm)

        for uj in all_ujs:
            uj.refresh_from_db()
        assert enough_capacity.status == 'waiting'
        assert insufficient_capacity.status == 'pending'
        assert [enough_capacity.execution_node, enough_capacity.controller_node] == [
            execution_instance.hostname,
            control_instance_low_capacity.hostname,
        ], enough_capacity

    @pytest.mark.django_db
    def test_hybrid_capacity(self, job_template, hybrid_instance):
        enough_capacity = job_template.create_unified_job()
        insufficient_capacity = job_template.create_unified_job()
        expected_task_impact = enough_capacity.task_impact + settings.AWX_CONTROL_NODE_TASK_IMPACT
        all_ujs = [enough_capacity, insufficient_capacity]
        for uj in all_ujs:
            uj.signal_start()

        DependencyManager().schedule()
        # There is only enough control capacity to run one of the jobs so one should end up in pending and the other in waiting
        tm = TaskManager()
        self.run_tm(tm)

        for uj in all_ujs:
            uj.refresh_from_db()
        assert enough_capacity.status == 'waiting'
        assert insufficient_capacity.status == 'pending'
        assert [enough_capacity.execution_node, enough_capacity.controller_node] == [
            hybrid_instance.hostname,
            hybrid_instance.hostname,
        ], enough_capacity
        assert expected_task_impact == hybrid_instance.consumed_capacity

    @pytest.mark.django_db
    def test_project_update_capacity(self, project, hybrid_instance, instance_group_factory, controlplane_instance_group):
        pu = project.create_unified_job()
        instance_group_factory(name='second_ig', instances=[hybrid_instance])
        expected_task_impact = pu.task_impact + settings.AWX_CONTROL_NODE_TASK_IMPACT
        pu.signal_start()

        tm = TaskManager()
        self.run_tm(tm)

        pu.refresh_from_db()
        assert pu.status == 'waiting'
        assert [pu.execution_node, pu.controller_node] == [
            hybrid_instance.hostname,
            hybrid_instance.hostname,
        ], pu
        assert expected_task_impact == hybrid_instance.consumed_capacity
        # The hybrid node is in both instance groups, but the project update should
        # always get assigned to the controlplane
        assert pu.instance_group.name == settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME
        pu.status = 'successful'
        pu.save()
        assert hybrid_instance.consumed_capacity == 0


@pytest.mark.django_db
def test_single_jt_multi_job_launch_blocks_last(job_template_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    j1 = create_job(objects.job_template)
    j2 = create_job(objects.job_template)

    TaskManager().schedule()
    j1.refresh_from_db()
    j2.refresh_from_db()
    assert j1.status == "waiting"
    assert j2.status == "pending"

    # mimic running j1 to unblock j2
    j1.status = "successful"
    j1.save()
    TaskManager().schedule()

    j2.refresh_from_db()
    assert j2.status == "waiting"


@pytest.mark.django_db
def test_single_jt_multi_job_launch_allow_simul_allowed(job_template_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    jt = objects.job_template
    jt.allow_simultaneous = True
    jt.save()
    j1 = create_job(objects.job_template)
    j2 = create_job(objects.job_template)
    TaskManager().schedule()
    j1.refresh_from_db()
    j2.refresh_from_db()
    assert j1.status == "waiting"
    assert j2.status == "waiting"


@pytest.mark.django_db
def test_multi_jt_capacity_blocking(hybrid_instance, job_template_factory, mocker):
    instance = hybrid_instance
    controlplane_instance_group = instance.rampart_groups.first()
    objects1 = job_template_factory('jt1', organization='org1', project='proj1', inventory='inv1', credential='cred1')
    objects2 = job_template_factory('jt2', organization='org2', project='proj2', inventory='inv2', credential='cred2')
    j1 = create_job(objects1.job_template)
    j2 = create_job(objects2.job_template)
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 505
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once_with(j1, controlplane_instance_group, instance)
            j1.status = "successful"
            j1.save()
    with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
        tm.schedule()
        mock_job.assert_called_once_with(j2, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_max_concurrent_jobs_ig_capacity_blocking(hybrid_instance, job_template_factory, mocker):
    """When max_concurrent_jobs of an instance group is more restrictive than capacity of instances, enforce max_concurrent_jobs."""
    instance = hybrid_instance
    controlplane_instance_group = instance.rampart_groups.first()
    # We will expect only 1 job to be started
    controlplane_instance_group.max_concurrent_jobs = 1
    controlplane_instance_group.save()
    num_jobs = 3
    jobs = []
    for i in range(num_jobs):
        jobs.append(
            create_job(job_template_factory(f'jt{i}', organization=f'org{i}', project=f'proj{i}', inventory=f'inv{i}', credential=f'cred{i}').job_template)
        )
    tm = TaskManager()
    task_impact = 1

    # Sanity check that multiple jobs would run if not for the max_concurrent_jobs setting.
    assert task_impact * num_jobs < controlplane_instance_group.capacity
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = task_impact
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once()
            jobs[0].status = 'running'
            jobs[0].controller_node = instance.hostname
            jobs[0].execution_node = instance.hostname
            jobs[0].instance_group = controlplane_instance_group
            jobs[0].save()

    # while that job is running, we should not start another job
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = task_impact
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_not_called()
    # now job is done, we should start one of the two other jobs
    jobs[0].status = 'successful'
    jobs[0].save()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = task_impact
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once()


@pytest.mark.django_db
def test_max_forks_ig_capacity_blocking(hybrid_instance, job_template_factory, mocker):
    """When max_forks of an instance group is less than the capacity of instances, enforce max_forks."""
    instance = hybrid_instance
    controlplane_instance_group = instance.rampart_groups.first()
    controlplane_instance_group.max_forks = 15
    controlplane_instance_group.save()
    task_impact = 10
    num_jobs = 2
    # Sanity check that 2 jobs would run if not for the max_forks setting.
    assert controlplane_instance_group.max_forks < controlplane_instance_group.capacity
    assert task_impact * num_jobs > controlplane_instance_group.max_forks
    assert task_impact * num_jobs < controlplane_instance_group.capacity
    for i in range(num_jobs):
        create_job(job_template_factory(f'jt{i}', organization=f'org{i}', project=f'proj{i}', inventory=f'inv{i}', credential=f'cred{i}').job_template)
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = task_impact
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once()


@pytest.mark.django_db
def test_single_job_dependencies_project_launch(controlplane_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    instance = controlplane_instance_group.instances.all()[0]
    j = create_job(objects.job_template, dependencies_processed=False)
    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 0
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save(skip_update=True)
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        dm = DependencyManager()
        dm.schedule()
        pu = [x for x in p.project_updates.all()]
        assert len(pu) == 1
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(pu[0], controlplane_instance_group, instance)
        pu[0].status = "successful"
        pu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_single_job_dependencies_inventory_update_launch(controlplane_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    instance = controlplane_instance_group.instances.all()[0]
    j = create_job(objects.job_template, dependencies_processed=False)
    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 0
    ii.save()
    i.inventory_sources.add(ii)
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        dm = DependencyManager()
        dm.schedule()
        assert ii.inventory_updates.count() == 1
        iu = [x for x in ii.inventory_updates.all()]
        assert len(iu) == 1
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(iu[0], controlplane_instance_group, instance)
        iu[0].status = "successful"
        iu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_inventory_update_launches_project_update(controlplane_instance_group, scm_inventory_source):
    ii = scm_inventory_source
    project = scm_inventory_source.source_project
    project.scm_update_on_launch = True
    project.save()
    iu = ii.create_inventory_update()
    iu.status = "pending"
    iu.save()
    assert project.project_updates.count() == 0
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        dm = DependencyManager()
        dm.schedule()
    assert project.project_updates.count() == 1


@pytest.mark.django_db
def test_job_dependency_with_already_updated(controlplane_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    instance = controlplane_instance_group.instances.all()[0]
    j = create_job(objects.job_template, dependencies_processed=False)
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
        dm = DependencyManager()
        dm.schedule()
        assert ii.inventory_updates.count() == 0
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_shared_dependencies_launch(controlplane_instance_group, job_template_factory, mocker, inventory_source_factory):
    instance = controlplane_instance_group.instances.all()[0]
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    objects.job_template.allow_simultaneous = True
    objects.job_template.save()
    j1 = create_job(objects.job_template, dependencies_processed=False)
    j2 = create_job(objects.job_template, dependencies_processed=False)
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
        DependencyManager().schedule()
        TaskManager().schedule()
        pu = p.project_updates.first()
        iu = ii.inventory_updates.first()
        TaskManager.start_task.assert_has_calls(
            [mock.call(iu, controlplane_instance_group, instance), mock.call(pu, controlplane_instance_group, instance)], any_order=True
        )
        pu.status = "successful"
        pu.finished = pu.created + timedelta(seconds=1)
        pu.save()
        iu.status = "successful"
        iu.finished = iu.created + timedelta(seconds=1)
        iu.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_has_calls(
            [mock.call(j1, controlplane_instance_group, instance), mock.call(j2, controlplane_instance_group, instance)], any_order=True
        )
    pu = [x for x in p.project_updates.all()]
    iu = [x for x in ii.inventory_updates.all()]
    assert len(pu) == 1
    assert len(iu) == 1


@pytest.mark.django_db
def test_job_not_blocking_project_update(controlplane_instance_group, job_template_factory):
    instance = controlplane_instance_group.instances.all()[0]
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    job = objects.job_template.create_unified_job()
    job.instance_group = controlplane_instance_group
    job.dependencies_process = True
    job.status = "running"
    job.save()

    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        proj = objects.project
        project_update = proj.create_project_update()
        project_update.instance_group = controlplane_instance_group
        project_update.status = "pending"
        project_update.save()
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(project_update, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_job_not_blocking_inventory_update(controlplane_instance_group, job_template_factory, inventory_source_factory):
    instance = controlplane_instance_group.instances.all()[0]
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred', jobs=["job"])
    job = objects.jobs["job"]
    job.instance_group = controlplane_instance_group
    job.status = "running"
    job.save()

    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        inv = objects.inventory
        inv_source = inventory_source_factory("ec2")
        inv_source.source = "ec2"
        inv.inventory_sources.add(inv_source)
        inventory_update = inv_source.create_inventory_update()
        inventory_update.instance_group = controlplane_instance_group
        inventory_update.status = "pending"
        inventory_update.save()

        DependencyManager().schedule()
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(inventory_update, controlplane_instance_group, instance)


@pytest.mark.django_db
def test_generate_dependencies_only_once(job_template_factory):
    objects = job_template_factory('jt', organization='org1')

    job = objects.job_template.create_job()
    job.status = "pending"
    job.name = "job_gen_dep"
    job.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        # job starts with dependencies_processed as False
        assert not job.dependencies_processed
        # run one cycle of ._schedule() to generate dependencies
        DependencyManager().schedule()

        # make sure dependencies_processed is now True
        job = Job.objects.filter(name="job_gen_dep")[0]
        assert job.dependencies_processed

        # Run ._schedule() again, but make sure .generate_dependencies() is not
        # called with job in the argument list
        dm = DependencyManager()
        dm.generate_dependencies = mock.MagicMock(return_value=[])
        dm.schedule()
        dm.generate_dependencies.assert_not_called()
