import pytest
from unittest import mock

from awx.main.models import AdHocCommand, InventoryUpdate, JobTemplate, Job
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.ha import Instance, InstanceGroup
from awx.main.tasks.system import apply_cluster_membership_policies
from awx.api.versioning import reverse

from django.utils.timezone import now


@pytest.mark.django_db
def test_default_tower_instance_group(default_instance_group, job_factory):
    assert default_instance_group in job_factory().preferred_instance_groups


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ('execution', 'control'))
@pytest.mark.parametrize('active', (True, False))
def test_get_cleanup_task_kwargs_active_jobs(node_type, active):
    instance = Instance.objects.create(hostname='foobar', node_type=node_type)
    job_kwargs = dict()
    job_kwargs['controller_node' if node_type == 'control' else 'execution_node'] = instance.hostname
    job_kwargs['status'] = 'running' if active else 'successful'

    job = Job.objects.create(**job_kwargs)
    kwargs = instance.get_cleanup_task_kwargs()

    if active:
        assert kwargs['exclude_strings'] == [f'awx_{job.pk}_']
    else:
        assert 'exclude_strings' not in kwargs


@pytest.mark.django_db
class TestPolicyTaskScheduling:
    """Tests make assertions about when the policy task gets scheduled"""

    @pytest.mark.parametrize(
        'field, value, expect',
        [
            ('name', 'foo-bar-foo-bar', False),
            ('policy_instance_percentage', 35, True),
            ('policy_instance_minimum', 3, True),
            ('policy_instance_list', ['bar?'], True),
            ('modified', now(), False),
        ],
    )
    def test_policy_task_ran_for_ig_when_needed(self, instance_group_factory, field, value, expect):
        # always run on instance group creation
        with mock.patch('awx.main.models.ha.schedule_policy_task') as mock_policy:
            ig = InstanceGroup.objects.create(name='foo')
        mock_policy.assert_called_once()
        # selectively run on instance group modification
        with mock.patch('awx.main.models.ha.schedule_policy_task') as mock_policy:
            setattr(ig, field, value)
            ig.save()
        if expect:
            mock_policy.assert_called_once()
        else:
            mock_policy.assert_not_called()

    @pytest.mark.parametrize(
        'field, value, expect',
        [
            ('hostname', 'foo-bar-foo-bar', True),
            ('managed_by_policy', False, True),
            ('enabled', False, False),
            ('capacity_adjustment', 0.42, True),
            ('capacity', 42, False),
        ],
    )
    def test_policy_task_ran_for_instance_when_needed(self, instance_group_factory, field, value, expect):
        # always run on instance group creation
        with mock.patch('awx.main.models.ha.schedule_policy_task') as mock_policy:
            inst = Instance.objects.create(hostname='foo')
        mock_policy.assert_called_once()
        # selectively run on instance group modification
        with mock.patch('awx.main.models.ha.schedule_policy_task') as mock_policy:
            setattr(inst, field, value)
            inst.save()
        if expect:
            mock_policy.assert_called_once()
        else:
            mock_policy.assert_not_called()


@pytest.mark.django_db
def test_instance_dup(org_admin, organization, project, instance_factory, instance_group_factory, get, system_auditor, instance):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")

    ig_all = instance_group_factory("all", instances=[i1, i2, i3])
    ig_dup = instance_group_factory("duplicates", instances=[i1])
    project.organization.instance_groups.add(ig_all, ig_dup)
    actual_num_instances = Instance.objects.count()
    list_response = get(reverse('api:instance_list'), user=system_auditor)
    api_num_instances_auditor = list(list_response.data.items())[0][1]

    list_response2 = get(reverse('api:instance_list'), user=org_admin)
    api_num_instances_oa = list(list_response2.data.items())[0][1]

    assert api_num_instances_auditor == actual_num_instances
    # Note: The org_admin will not see the default 'tower' node
    # (instance fixture) because it is not in its group, as expected
    assert api_num_instances_oa == (actual_num_instances - 1)


@pytest.mark.django_db
def test_policy_instance_few_instances(instance_factory, instance_group_factory):
    # we need to use node_type=execution because node_type=hybrid will implicitly
    # create the controlplane execution group if it doesn't already exist
    i1 = instance_factory("i1", node_type='execution')
    ig_1 = instance_group_factory("ig1", percentage=25)
    ig_2 = instance_group_factory("ig2", percentage=25)
    ig_3 = instance_group_factory("ig3", percentage=25)
    ig_4 = instance_group_factory("ig4", percentage=25)

    count = ActivityStream.objects.count()

    apply_cluster_membership_policies()
    # running apply_cluster_membership_policies shouldn't spam the activity stream
    assert ActivityStream.objects.count() == count

    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i1 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i1 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i1 in ig_4.instances.all()

    i2 = instance_factory("i2", node_type='execution')
    count += 1
    apply_cluster_membership_policies()
    assert ActivityStream.objects.count() == count

    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i1 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i2 in ig_4.instances.all()


@pytest.mark.django_db
def test_policy_instance_distribution_round_up(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    i4 = instance_factory("i4")
    i5 = instance_factory("i5")
    ig_1 = instance_group_factory("ig1", percentage=79)
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 4
    assert set([i1, i2, i3, i4]) == set(ig_1.instances.all())
    assert i5 not in ig_1.instances.all()


@pytest.mark.django_db
def test_policy_instance_distribution_uneven(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    ig_1 = instance_group_factory("ig1", percentage=25)
    ig_2 = instance_group_factory("ig2", percentage=25)
    ig_3 = instance_group_factory("ig3", percentage=25)
    ig_4 = instance_group_factory("ig4", percentage=25)
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i3 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i1 in ig_4.instances.all()


@pytest.mark.django_db
def test_policy_instance_distribution_even(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    i4 = instance_factory("i4")
    ig_1 = instance_group_factory("ig1", percentage=25)
    ig_2 = instance_group_factory("ig2", percentage=25)
    ig_3 = instance_group_factory("ig3", percentage=25)
    ig_4 = instance_group_factory("ig4", percentage=25)
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i3 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i4 in ig_4.instances.all()
    ig_1.policy_instance_minimum = 2
    ig_1.save()
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 2
    assert i1 in ig_1.instances.all()
    assert i2 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i3 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i4 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i1 in ig_4.instances.all()


@pytest.mark.django_db
def test_policy_instance_distribution_simultaneous(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    i4 = instance_factory("i4")
    ig_1 = instance_group_factory("ig1", percentage=25, minimum=2)
    ig_2 = instance_group_factory("ig2", percentage=25)
    ig_3 = instance_group_factory("ig3", percentage=25)
    ig_4 = instance_group_factory("ig4", percentage=25)
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 2
    assert i1 in ig_1.instances.all()
    assert i2 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i3 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i4 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i1 in ig_4.instances.all()


@pytest.mark.django_db
def test_policy_instance_list_manually_assigned(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig_1 = instance_group_factory("ig1", percentage=100, minimum=2)
    ig_2 = instance_group_factory("ig2")
    ig_2.policy_instance_list = [i2.hostname]
    ig_2.save()
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 2
    assert i1 in ig_1.instances.all()
    assert i2 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()


@pytest.mark.django_db
def test_policy_instance_list_explicitly_pinned(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig_1 = instance_group_factory("ig1", percentage=100, minimum=2)
    ig_2 = instance_group_factory("ig2")
    ig_2.policy_instance_list = [i2.hostname]
    ig_2.save()

    # without being marked as manual, i2 will be picked up by ig_1
    apply_cluster_membership_policies()
    assert set(ig_1.instances.all()) == set([i1, i2])
    assert set(ig_2.instances.all()) == set([i2])

    i2.managed_by_policy = False
    i2.save()

    # after marking as manual, i2 no longer available for ig_1
    apply_cluster_membership_policies()
    assert set(ig_1.instances.all()) == set([i1])
    assert set(ig_2.instances.all()) == set([i2])


@pytest.mark.django_db
def test_control_plane_policy_exception(controlplane_instance_group):
    controlplane_instance_group.policy_instance_percentage = 100
    controlplane_instance_group.policy_instance_minimum = 2
    controlplane_instance_group.save()
    Instance.objects.create(hostname='foo-1', node_type='execution')
    apply_cluster_membership_policies()
    assert 'foo-1' not in [inst.hostname for inst in controlplane_instance_group.instances.all()]


@pytest.mark.django_db
def test_normal_instance_group_policy_exception():
    ig = InstanceGroup.objects.create(name='bar', policy_instance_percentage=100, policy_instance_minimum=2)
    Instance.objects.create(hostname='foo-1', node_type='control')
    apply_cluster_membership_policies()
    assert 'foo-1' not in [inst.hostname for inst in ig.instances.all()]


@pytest.mark.django_db
def test_percentage_as_fraction_of_execution_nodes():
    """
    If an instance requests 50 percent of instances, then those should be 50 percent
    of available execution nodes (1 out of 2), as opposed to 50 percent
    of all available nodes (2 out of 4) which include unusable control nodes
    """
    ig = InstanceGroup.objects.create(name='bar', policy_instance_percentage=50)
    for i in range(2):
        Instance.objects.create(hostname=f'foo-{i}', node_type='control')
    for i in range(2):
        Instance.objects.create(hostname=f'bar-{i}', node_type='execution')
    apply_cluster_membership_policies()
    assert ig.instances.count() == 1
    assert ig.instances.first().hostname.startswith('bar-')


@pytest.mark.django_db
def test_basic_instance_group_membership(instance_group_factory, default_instance_group, job_factory):
    j = job_factory()
    ig = instance_group_factory("basicA", [default_instance_group.instances.first()])
    j.job_template.instance_groups.add(ig)
    assert ig in j.preferred_instance_groups
    assert default_instance_group not in j.preferred_instance_groups


@pytest.mark.django_db
def test_inherited_instance_group_membership(instance_group_factory, default_instance_group, job_factory, project, inventory):
    j = job_factory()
    j.project = project
    j.inventory = inventory
    ig_org = instance_group_factory("basicA", [default_instance_group.instances.first()])
    ig_inv = instance_group_factory("basicB", [default_instance_group.instances.first()])
    j.project.organization.instance_groups.add(ig_org)
    j.inventory.instance_groups.add(ig_inv)
    assert ig_org in j.preferred_instance_groups
    assert ig_inv in j.preferred_instance_groups
    assert default_instance_group not in j.preferred_instance_groups


@pytest.mark.django_db
def test_global_instance_groups_as_defaults(controlplane_instance_group, default_instance_group, job_factory):
    j = job_factory()
    assert j.preferred_instance_groups == [default_instance_group, controlplane_instance_group]


@pytest.mark.django_db
def test_mixed_group_membership(instance_factory, instance_group_factory):
    for i in range(5):
        instance_factory("i{}".format(i))
    ig_1 = instance_group_factory("ig1", percentage=60)
    ig_2 = instance_group_factory("ig2", minimum=3)
    ig_3 = instance_group_factory("ig3", minimum=1, percentage=60)
    apply_cluster_membership_policies()
    for group in (ig_1, ig_2, ig_3):
        assert len(group.instances.all()) == 3


@pytest.mark.django_db
def test_instance_group_capacity(instance_factory, instance_group_factory):
    node_capacity = 100
    i1 = instance_factory("i1", capacity=node_capacity)
    i2 = instance_factory("i2", capacity=node_capacity)
    i3 = instance_factory("i3", capacity=node_capacity)
    ig_all = instance_group_factory("all", instances=[i1, i2, i3])
    assert ig_all.capacity == node_capacity * 3
    ig_single = instance_group_factory("single", instances=[i1])
    assert ig_single.capacity == node_capacity


@pytest.mark.django_db
def test_health_check_clears_errors():
    instance = Instance.objects.create(hostname='foo-1', enabled=True, capacity=0, errors='something went wrong')
    data = dict(version='ansible-runner-4.2', cpu=782, memory=int(39e9), uuid='asdfasdfasdfasdfasdf', errors='')
    instance.save_health_data(**data)
    for k, v in data.items():
        assert getattr(instance, k) == v


@pytest.mark.django_db
def test_health_check_oh_no():
    instance = Instance.objects.create(hostname='foo-2', enabled=True, capacity=52, cpu=8, memory=int(40e9))
    instance.save_health_data('', 0, 0, errors='This it not a real instance!')
    assert instance.capacity == instance.cpu_capacity == 0
    assert instance.errors == 'This it not a real instance!'


@pytest.mark.django_db
def test_errors_field_alone():
    instance = Instance.objects.create(hostname='foo-1', enabled=True, node_type='hop')

    instance.save_health_data(errors='Node went missing!')
    assert instance.errors == 'Node went missing!'
    assert instance.capacity == 0
    assert instance.memory == instance.mem_capacity == 0
    assert instance.cpu == instance.cpu_capacity == 0

    instance.save_health_data(errors='')
    assert not instance.errors
    assert instance.capacity == 0
    assert instance.memory == instance.mem_capacity == 0
    assert instance.cpu == instance.cpu_capacity == 0


@pytest.mark.django_db
class TestInstanceGroupOrdering:
    def test_ad_hoc_instance_groups(self, instance_group_factory, inventory, default_instance_group):
        ad_hoc = AdHocCommand.objects.create(inventory=inventory)
        assert ad_hoc.preferred_instance_groups == [default_instance_group]
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        inventory.organization.instance_groups.add(ig_org)
        assert ad_hoc.preferred_instance_groups == [ig_org]
        inventory.instance_groups.add(ig_inv)
        assert ad_hoc.preferred_instance_groups == [ig_inv, ig_org]
        inventory.prevent_instance_group_fallback = True
        assert ad_hoc.preferred_instance_groups == [ig_inv]

    def test_inventory_update_instance_groups(self, instance_group_factory, inventory_source, default_instance_group):
        iu = InventoryUpdate.objects.create(inventory_source=inventory_source, source=inventory_source.source)
        assert iu.preferred_instance_groups == [default_instance_group]
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        inventory_source.inventory.organization.instance_groups.add(ig_org)
        inventory_source.inventory.instance_groups.add(ig_inv)
        assert iu.preferred_instance_groups == [ig_inv, ig_org]
        inventory_source.instance_groups.add(ig_tmp)
        # API does not allow setting IGs on inventory source, so ignore those
        assert iu.preferred_instance_groups == [ig_inv, ig_org]
        inventory_source.inventory.prevent_instance_group_fallback = True
        assert iu.preferred_instance_groups == [ig_inv]

    def test_job_instance_groups(self, instance_group_factory, inventory, project, default_instance_group):
        jt = JobTemplate.objects.create(inventory=inventory, project=project)
        job = jt.create_unified_job()
        assert job.preferred_instance_groups == [default_instance_group]
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        project.organization.instance_groups.add(ig_org)
        inventory.instance_groups.add(ig_inv)
        assert job.preferred_instance_groups == [ig_inv, ig_org]
        job.job_template.instance_groups.add(ig_tmp)
        assert job.preferred_instance_groups == [ig_tmp, ig_inv, ig_org]

    def test_job_instance_groups_cache_default(self, instance_group_factory, inventory, project, default_instance_group):
        jt = JobTemplate.objects.create(inventory=inventory, project=project)
        job = jt.create_unified_job()
        print(job.preferred_instance_groups_cache)
        print(default_instance_group)
        assert job.preferred_instance_groups_cache == [default_instance_group.id]

    def test_job_instance_groups_cache_default_additional_items(self, instance_group_factory, inventory, project, default_instance_group):
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        project.organization.instance_groups.add(ig_org)
        inventory.instance_groups.add(ig_inv)
        jt = JobTemplate.objects.create(inventory=inventory, project=project)
        jt.instance_groups.add(ig_tmp)
        job = jt.create_unified_job()
        assert job.preferred_instance_groups_cache == [ig_tmp.id, ig_inv.id, ig_org.id]

    def test_job_instance_groups_cache_prompt(self, instance_group_factory, inventory, project, default_instance_group):
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        project.organization.instance_groups.add(ig_org)
        inventory.instance_groups.add(ig_inv)
        jt = JobTemplate.objects.create(inventory=inventory, project=project)
        job = jt.create_unified_job(instance_groups=[ig_tmp])
        assert job.preferred_instance_groups_cache == [ig_tmp.id]
