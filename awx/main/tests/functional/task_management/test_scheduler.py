import pytest
from unittest import mock

from awx.main.scheduler import TaskManager, DependencyManager, WorkflowManager
from awx.main.models import WorkflowJobTemplate, JobTemplate
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
def test_multi_jt_capacity_blocking(hybrid_instance, job_template_factory):
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
def test_single_job_dependencies_project_launch(job_template_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    p = objects.project
    p.scm_update_on_launch = True
    p.save(skip_update=True)

    j = objects.job_template.create_unified_job()
    j.signal_start()
    assert j.dependencies_processed is False
    assert j.status == 'pending'

    deps = list(j.dependent_jobs.all())
    assert len(deps) == 1
    pu = deps[0]
    assert pu.project == p
    assert pu.status == 'pending'

    pu.status = 'successful'
    pu.save(update_fields=['status'])
    DependencyManager().schedule()
    j.refresh_from_db()
    assert j.dependencies_processed is True


@pytest.mark.django_db
def test_single_job_dependencies_inventory_update_launch(job_template_factory, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')

    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 0
    ii.save()
    i.inventory_sources.add(ii)

    j = objects.job_template.create_unified_job()
    j.signal_start()
    assert j.dependencies_processed is False
    assert j.status == 'pending'
    deps = list(j.dependent_jobs.all())
    assert len(deps) == 1
    inv_update = deps[0]

    inv_update.status = 'successful'
    inv_update.save()
    DependencyManager().schedule()
    j.refresh_from_db()
    assert j.dependencies_processed is True


@pytest.mark.django_db
def test_inventory_update_launches_project_update(scm_inventory_source):
    ii = scm_inventory_source
    project = scm_inventory_source.source_project
    project.scm_update_on_launch = True
    project.save()

    iu = ii.create_unified_job()
    iu.signal_start()
    assert iu.dependencies_processed is False
    assert iu.status == 'pending'
    deps = list(iu.dependent_jobs.all())
    assert len(deps) == 1
    pu = deps[0]

    pu.status = 'successful'
    pu.save()
    DependencyManager().schedule()
    iu.refresh_from_db()
    assert iu.dependencies_processed is True


@pytest.mark.django_db
def test_job_dependency_with_already_updated(job_template_factory, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')

    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 0
    ii.save()
    i.inventory_sources.add(ii)

    iu = ii.create_unified_job(_eager_fields={'status': 'successful'})

    j = objects.job_template.create_unified_job(available_deps=[iu])

    DependencyManager().schedule()
    assert list(j.dependent_jobs.all()) == [iu]


@pytest.mark.django_db
def test_shared_dependencies_launch(job_template_factory, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    objects.job_template.allow_simultaneous = True
    objects.job_template.save()

    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 300
    p.save()

    i = objects.inventory
    ii = inventory_source_factory("ec2")
    ii.source = "ec2"
    ii.update_on_launch = True
    ii.update_cache_timeout = 300
    ii.save()
    i.inventory_sources.add(ii)

    j1 = objects.job_template.create_unified_job()
    j1.signal_start()
    j2 = objects.job_template.create_unified_job()
    j2.signal_start()
    pu = p.project_updates.first()
    iu = ii.inventory_updates.first()
    assert set([iu, pu]) == set(j1.dependent_jobs.all()) == set(j2.dependent_jobs.all())
    assert list(p.project_updates.all()) == [pu]
    assert list(ii.inventory_updates.all()) == [iu]

    DependencyManager().schedule()
    for j in (j1, j2):
        j.refresh_from_db()
        assert j.status == 'pending'
        assert j.dependencies_processed is False

    for uj in (pu, iu):
        uj.status = 'successful'
        uj.save()

    DependencyManager().schedule()
    for j in (j1, j2):
        j.refresh_from_db()
        assert j.dependencies_processed

    j3 = objects.job_template.create_unified_job()
    assert set(j3.dependent_jobs.all()) == set([iu, pu])  # dependencies all inside cache timeout


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
def test_generate_dependencies_with_no_dependencies(job_template_factory):
    """We should continue to advance a job (to be ran) if it actually has no dependencies"""
    objects = job_template_factory('jt', organization='org1')

    job = objects.job_template.create_unified_job()
    job.signal_start()
    job.dependencies_processed = True
    job.save()

    DependencyManager().schedule()
    job.refresh_from_db()
    assert job.dependencies_processed
