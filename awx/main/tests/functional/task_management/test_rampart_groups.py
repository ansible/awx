import pytest
from unittest import mock
from datetime import timedelta
from awx.main.scheduler import TaskManager
from awx.main.models import InstanceGroup, WorkflowJob
from awx.main.tasks import apply_cluster_membership_policies


@pytest.mark.django_db
def test_multi_group_basic_job_launch(instance_factory, default_instance_group, mocker,
                                      instance_group_factory, job_template_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig1 = instance_group_factory("ig1", instances=[i1])
    ig2 = instance_group_factory("ig2", instances=[i2])
    objects1 = job_template_factory('jt1', organization='org1', project='proj1',
                                    inventory='inv1', credential='cred1',
                                    jobs=["job_should_start"])
    objects1.job_template.instance_groups.add(ig1)
    j1 = objects1.jobs['job_should_start']
    j1.status = 'pending'
    j1.save()
    objects2 = job_template_factory('jt2', organization='org2', project='proj2',
                                    inventory='inv2', credential='cred2',
                                    jobs=["job_should_still_start"])
    objects2.job_template.instance_groups.add(ig2)
    j2 = objects2.jobs['job_should_still_start']
    j2.status = 'pending'
    j2.save()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 500
        with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
            TaskManager().schedule()
            TaskManager.start_task.assert_has_calls([mock.call(j1, ig1, [], i1), mock.call(j2, ig2, [], i2)])



@pytest.mark.django_db
def test_multi_group_with_shared_dependency(instance_factory, default_instance_group, mocker,
                                            instance_group_factory, job_template_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig1 = instance_group_factory("ig1", instances=[i1])
    ig2 = instance_group_factory("ig2", instances=[i2])
    objects1 = job_template_factory('jt1', organization='org1', project='proj1',
                                    inventory='inv1', credential='cred1',
                                    jobs=["job_should_start"])
    objects1.job_template.instance_groups.add(ig1)
    p = objects1.project
    p.scm_update_on_launch = True
    p.scm_update_cache_timeout = 0
    p.scm_type = "git"
    p.scm_url = "http://github.com/ansible/ansible.git"
    p.save()
    j1 = objects1.jobs['job_should_start']
    j1.status = 'pending'
    j1.save()
    objects2 = job_template_factory('jt2', organization=objects1.organization, project=p,
                                    inventory='inv2', credential='cred2',
                                    jobs=["job_should_still_start"])
    objects2.job_template.instance_groups.add(ig2)
    j2 = objects2.jobs['job_should_still_start']
    j2.status = 'pending'
    j2.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        pu = p.project_updates.first()
        TaskManager.start_task.assert_called_once_with(pu,
                                                       default_instance_group,
                                                       [j1,j2],
                                                       default_instance_group.instances.all()[0])
        pu.finished = pu.created + timedelta(seconds=1)
        pu.status = "successful"
        pu.save()
    with mock.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()

        TaskManager.start_task.assert_any_call(j1, ig1, [], i1)
        TaskManager.start_task.assert_any_call(j2, ig2, [], i2)
        assert TaskManager.start_task.call_count == 2


@pytest.mark.django_db
def test_workflow_job_no_instancegroup(workflow_job_template_factory, default_instance_group, mocker):
    wfjt = workflow_job_template_factory('anicedayforawalk').workflow_job_template
    wfj = WorkflowJob.objects.create(workflow_job_template=wfjt)
    wfj.status = "pending"
    wfj.save()
    with mocker.patch("awx.main.scheduler.TaskManager.start_task"):
        TaskManager().schedule()
        TaskManager.start_task.assert_called_once_with(wfj, None, [], None)
        assert wfj.instance_group is None


@pytest.mark.django_db
def test_overcapacity_blocking_other_groups_unaffected(instance_factory, default_instance_group, mocker,
                                                       instance_group_factory, job_template_factory):
    i1 = instance_factory("i1")
    i1.capacity = 1000
    i1.save()
    i2 = instance_factory("i2")
    ig1 = instance_group_factory("ig1", instances=[i1])
    ig2 = instance_group_factory("ig2", instances=[i2])
    objects1 = job_template_factory('jt1', organization='org1', project='proj1',
                                    inventory='inv1', credential='cred1',
                                    jobs=["job_should_start"])
    objects1.job_template.instance_groups.add(ig1)
    j1 = objects1.jobs['job_should_start']
    j1.status = 'pending'
    j1.save()
    objects2 = job_template_factory('jt2', organization=objects1.organization, project='proj2',
                                    inventory='inv2', credential='cred2',
                                    jobs=["job_should_start", "job_should_also_start"])
    objects2.job_template.instance_groups.add(ig1)
    j1_1 = objects2.jobs['job_should_also_start']
    j1_1.status = 'pending'
    j1_1.save()
    objects3 = job_template_factory('jt3', organization='org2', project='proj3',
                                    inventory='inv3', credential='cred3',
                                    jobs=["job_should_still_start"])
    objects3.job_template.instance_groups.add(ig2)
    j2 = objects3.jobs['job_should_still_start']
    j2.status = 'pending'
    j2.save()
    objects4 = job_template_factory('jt4', organization=objects3.organization, project='proj4',
                                    inventory='inv4', credential='cred4',
                                    jobs=["job_should_not_start"])
    objects4.job_template.instance_groups.add(ig2)
    j2_1 = objects4.jobs['job_should_not_start']
    j2_1.status = 'pending'
    j2_1.save()
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 500
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_has_calls([mock.call(j1, ig1, [], i1),
                                       mock.call(j1_1, ig1, [], i1),
                                       mock.call(j2, ig2, [], i2)])
            assert mock_job.call_count == 3


@pytest.mark.django_db
def test_failover_group_run(instance_factory, default_instance_group, mocker,
                            instance_group_factory, job_template_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig1 = instance_group_factory("ig1", instances=[i1])
    ig2 = instance_group_factory("ig2", instances=[i2])
    objects1 = job_template_factory('jt1', organization='org1', project='proj1',
                                    inventory='inv1', credential='cred1',
                                    jobs=["job_should_start"])
    objects1.job_template.instance_groups.add(ig1)
    j1 = objects1.jobs['job_should_start']
    j1.status = 'pending'
    j1.save()
    objects2 = job_template_factory('jt2', organization=objects1.organization, project='proj2',
                                    inventory='inv2', credential='cred2',
                                    jobs=["job_should_start", "job_should_also_start"])
    objects2.job_template.instance_groups.add(ig1)
    objects2.job_template.instance_groups.add(ig2)
    j1_1 = objects2.jobs['job_should_also_start']
    j1_1.status = 'pending'
    j1_1.save()
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 500
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_has_calls([mock.call(j1, ig1, [], i1),
                                       mock.call(j1_1, ig2, [], i2)])
            assert mock_job.call_count == 2


@pytest.mark.django_db
def test_instance_group_basic_policies(instance_factory, instance_group_factory):
    i0 = instance_factory("i0")
    i0.managed_by_policy = False
    i0.save()
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    i4 = instance_factory("i4")
    ig0 = instance_group_factory("ig0")
    ig1 = instance_group_factory("ig1", minimum=2)
    ig2 = instance_group_factory("ig2", percentage=50)
    ig3 = instance_group_factory("ig3", percentage=50)
    ig0.policy_instance_list.append(i0.hostname)
    ig0.save()
    apply_cluster_membership_policies()
    ig0 = InstanceGroup.objects.get(id=ig0.id)
    ig1 = InstanceGroup.objects.get(id=ig1.id)
    ig2 = InstanceGroup.objects.get(id=ig2.id)
    ig3 = InstanceGroup.objects.get(id=ig3.id)
    assert len(ig0.instances.all()) == 1
    assert i0 in ig0.instances.all()
    assert len(InstanceGroup.objects.get(id=ig1.id).instances.all()) == 2
    assert i1 in ig1.instances.all()
    assert i2 in ig1.instances.all()
    assert len(InstanceGroup.objects.get(id=ig2.id).instances.all()) == 2
    assert i3 in ig2.instances.all()
    assert i4 in ig2.instances.all()
    assert len(InstanceGroup.objects.get(id=ig3.id).instances.all()) == 2
    assert i1 in ig3.instances.all()
    assert i2 in ig3.instances.all()
