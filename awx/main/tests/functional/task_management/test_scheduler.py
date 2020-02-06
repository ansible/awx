import pytest
from unittest import mock
import json
from datetime import timedelta

from awx.main.scheduler import TaskManager
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.utils import encrypt_field
from awx.main.models import WorkflowJobTemplate, JobTemplate, Job


@pytest.mark.django_db
def test_single_job_scheduler_launch(default_instance_group, job_template_factory, mocker):
    instance = default_instance_group.instances.all()[0]
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [], instance)


@pytest.mark.django_db
class TestJobLifeCycle:

    def run_tm(self, tm, expect_channel=None, expect_schedule=None, expect_commit=None):
        """Test helper method that takes parameters to assert against
        expect_channel - list of expected websocket emit channel message calls
        expect_schedule - list of expected calls to reschedule itself
        expect_commit - list of expected on_commit calls
        If any of these are None, then the assertion is not made.
        """
        if expect_schedule and len(expect_schedule) > 1:
            raise RuntimeError('Task manager should reschedule itself one time, at most.')
        with mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status') as mock_channel:
            with mock.patch('awx.main.utils.common._schedule_task_manager') as tm_sch:
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

    def test_task_manager_workflow_rescheduling(self, job_template_factory, inventory, project, default_instance_group):
        jt = JobTemplate.objects.create(
            allow_simultaneous=True,
            inventory=inventory,
            project=project,
            playbook='helloworld.yml'
        )
        wfjt = WorkflowJobTemplate.objects.create(name='foo')
        for i in range(2):
            wfjt.workflow_nodes.create(
                unified_job_template=jt
            )
        wj = wfjt.create_unified_job()
        assert wj.workflow_nodes.count() == 2
        wj.signal_start()
        tm = TaskManager()

        # Transitions workflow job to running
        # needs to re-schedule so it spawns jobs next round
        self.run_tm(tm, [mock.call('running')], [mock.call()])

        # Spawns jobs
        # needs re-schedule to submit jobs next round
        self.run_tm(tm, [mock.call('pending'), mock.call('pending')], [mock.call()])

        assert jt.jobs.count() == 2  # task manager spawned jobs

        # Submits jobs
        # intermission - jobs will run and reschedule TM when finished
        self.run_tm(tm, [mock.call('waiting'), mock.call('waiting')], [])

        # I am the job runner
        for job in jt.jobs.all():
            job.status = 'successful'
            job.save()

        # Finishes workflow
        # no further action is necessary, so rescheduling should not happen
        self.run_tm(tm, [mock.call('successful')], [])

    def test_task_manager_workflow_workflow_rescheduling(self):
        wfjts = [WorkflowJobTemplate.objects.create(name='foo')]
        for i in range(5):
            wfjt = WorkflowJobTemplate.objects.create(name='foo{}'.format(i))
            wfjts[-1].workflow_nodes.create(
                unified_job_template=wfjt
            )
            wfjts.append(wfjt)

        wj = wfjts[0].create_unified_job()
        wj.signal_start()
        tm = TaskManager()

        while wfjts[0].status != 'successful':
            wfjts[1].refresh_from_db()
            if wfjts[1].status == 'successful':
                # final run, no more work to do
                self.run_tm(tm, expect_schedule=[])
            else:
                self.run_tm(tm, expect_schedule=[mock.call()])
            wfjts[0].refresh_from_db()


@pytest.mark.django_db
def test_single_jt_multi_job_launch_blocks_last(default_instance_group, job_template_factory, mocker):
    instance = default_instance_group.instances.all()[0]
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
        TaskManager.start_task.assert_called_once_with(j1, default_instance_group, [], instance)
        j1.status = "successful"
        j1.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j2, default_instance_group, [], instance)


@pytest.mark.django_db
def test_single_jt_multi_job_launch_allow_simul_allowed(default_instance_group, job_template_factory, mocker):
    instance = default_instance_group.instances.all()[0]
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
        TaskManager.start_task.assert_has_calls([mock.call(j1, default_instance_group, [], instance),
                                                 mock.call(j2, default_instance_group, [], instance)])


@pytest.mark.django_db
def test_multi_jt_capacity_blocking(default_instance_group, job_template_factory, mocker):
    instance = default_instance_group.instances.all()[0]
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
            mock_job.assert_called_once_with(j1, default_instance_group, [], instance)
            j1.status = "successful"
            j1.save()
    with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
        tm.schedule()
        mock_job.assert_called_once_with(j2, default_instance_group, [], instance)


@pytest.mark.django_db
def test_single_job_dependencies_project_launch(default_instance_group, job_template_factory, mocker):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    instance = default_instance_group.instances.all()[0]
    j = objects.jobs["job_should_start"]
    j.status = 'pending'
    j.save()
    p = objects.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 0
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save(skip_update=True)
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        tm = TaskManager()
        with mock.patch.object(TaskManager, "create_project_update", wraps=tm.create_project_update) as mock_pu:
            tm.schedule()
            mock_pu.assert_called_once_with(j)
            pu = [x for x in p.project_updates.all()]
            assert len(pu) == 1
            TaskManager.start_task.assert_called_once_with(pu[0], default_instance_group, [j], instance)
            pu[0].status = "successful"
            pu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [], instance)


@pytest.mark.django_db
def test_single_job_dependencies_inventory_update_launch(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    instance = default_instance_group.instances.all()[0]
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
            TaskManager.start_task.assert_called_once_with(iu[0], default_instance_group, [j], instance)
            iu[0].status = "successful"
            iu[0].save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [], instance)


@pytest.mark.django_db
def test_job_dependency_with_already_updated(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job_should_start"])
    instance = default_instance_group.instances.all()[0]
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
        TaskManager.start_task.assert_called_once_with(j, default_instance_group, [], instance)


@pytest.mark.django_db
def test_shared_dependencies_launch(default_instance_group, job_template_factory, mocker, inventory_source_factory):
    instance = default_instance_group.instances.all()[0]
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
        TaskManager.start_task.assert_has_calls([mock.call(iu, default_instance_group, [j1, j2, pu], instance),
                                                mock.call(pu, default_instance_group, [j1, j2, iu], instance)])
        pu.status = "successful"
        pu.finished = pu.created + timedelta(seconds=1)
        pu.save()
        iu.status = "successful"
        iu.finished = iu.created + timedelta(seconds=1)
        iu.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j1, default_instance_group, [], instance)
        j1.status = "successful"
        j1.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(j2, default_instance_group, [], instance)
    pu = [x for x in p.project_updates.all()]
    iu = [x for x in ii.inventory_updates.all()]
    assert len(pu) == 1
    assert len(iu) == 1


@pytest.mark.django_db
def test_job_not_blocking_project_update(default_instance_group, job_template_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job"])
    job = objects.jobs["job"]
    job.instance_group = default_instance_group
    job.status = "running"
    job.save()

    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        task_manager = TaskManager()
        task_manager._schedule()

        proj = objects.project
        project_update = proj.create_project_update()
        project_update.instance_group = default_instance_group
        project_update.status = "pending"
        project_update.save()
        assert not task_manager.is_job_blocked(project_update)

        dependency_graph = DependencyGraph(None)
        dependency_graph.add_job(job)
        assert not dependency_graph.is_job_blocked(project_update)


@pytest.mark.django_db
def test_job_not_blocking_inventory_update(default_instance_group, job_template_factory, inventory_source_factory):
    objects = job_template_factory('jt', organization='org1', project='proj',
                                   inventory='inv', credential='cred',
                                   jobs=["job"])
    job = objects.jobs["job"]
    job.instance_group = default_instance_group
    job.status = "running"
    job.save()

    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        task_manager = TaskManager()
        task_manager._schedule()

        inv = objects.inventory
        inv_source = inventory_source_factory("ec2")
        inv_source.source = "ec2"
        inv.inventory_sources.add(inv_source)
        inventory_update = inv_source.create_inventory_update()
        inventory_update.instance_group = default_instance_group
        inventory_update.status = "pending"
        inventory_update.save()

        assert not task_manager.is_job_blocked(inventory_update)

        dependency_graph = DependencyGraph(None)
        dependency_graph.add_job(job)
        assert not dependency_graph.is_job_blocked(inventory_update)


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
        TaskManager()._schedule()

        # make sure dependencies_processed is now True
        job = Job.objects.filter(name="job_gen_dep")[0]
        assert job.dependencies_processed

        # Run ._schedule() again, but make sure .generate_dependencies() is not
        # called with job in the argument list
        tm = TaskManager()
        tm.generate_dependencies = mock.MagicMock()
        tm._schedule()

        # .call_args is tuple, (positional_args, kwargs), [0][0] then is
        # the first positional arg, i.e. the first argument of
        # .generate_dependencies()
        assert tm.generate_dependencies.call_args[0][0] == []
