import pytest
import mock

from awx.main.models import AdHocCommand, InventoryUpdate, Job, JobTemplate, ProjectUpdate, Instance
from awx.main.tasks import apply_cluster_membership_policies
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_default_tower_instance_group(default_instance_group, job_factory):
    assert default_instance_group in job_factory().preferred_instance_groups


@pytest.mark.django_db
def test_instance_dup(org_admin, organization, project, instance_factory, instance_group_factory, get, system_auditor):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    ig_all = instance_group_factory("all", instances=[i1, i2, i3])
    ig_dup = instance_group_factory("duplicates", instances=[i1])
    project.organization.instance_groups.add(ig_all, ig_dup)
    actual_num_instances = Instance.objects.active_count()
    list_response = get(reverse('api:instance_list'), user=system_auditor)
    api_num_instances_auditor = list_response.data.items()[0][1]

    list_response2 = get(reverse('api:instance_list'), user=org_admin)
    api_num_instances_oa = list_response2.data.items()[0][1]

    assert actual_num_instances == api_num_instances_auditor
    # Note: The org_admin will not see the default 'tower' node because it is not in it's group, as expected
    assert api_num_instances_oa == (actual_num_instances - 1)


@pytest.mark.django_db
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_few_instances(mock, instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    ig_1 = instance_group_factory("ig1", percentage=25)
    ig_2 = instance_group_factory("ig2", percentage=25)
    ig_3 = instance_group_factory("ig3", percentage=25)
    ig_4 = instance_group_factory("ig4", percentage=25)
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i1 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i1 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i1 in ig_4.instances.all()
    i2 = instance_factory("i2")
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()
    assert len(ig_3.instances.all()) == 1
    assert i1 in ig_3.instances.all()
    assert len(ig_4.instances.all()) == 1
    assert i2 in ig_4.instances.all()


@pytest.mark.django_db
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_distribution_round_up(mock, instance_factory, instance_group_factory):
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
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_distribution_uneven(mock, instance_factory, instance_group_factory):
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
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_distribution_even(mock, instance_factory, instance_group_factory):
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
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_distribution_simultaneous(mock, instance_factory, instance_group_factory):
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
@mock.patch('awx.main.tasks.handle_ha_toplogy_changes', return_value=None)
def test_policy_instance_list_manually_managed(mock, instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    ig_1 = instance_group_factory("ig1", percentage=100, minimum=2)
    ig_2 = instance_group_factory("ig2")
    ig_2.policy_instance_list = [i2.hostname]
    ig_2.save()
    apply_cluster_membership_policies()
    assert len(ig_1.instances.all()) == 1
    assert i1 in ig_1.instances.all()
    assert i2 not in ig_1.instances.all()
    assert len(ig_2.instances.all()) == 1
    assert i2 in ig_2.instances.all()


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
def test_instance_group_capacity(instance_factory, instance_group_factory):
    i1 = instance_factory("i1")
    i2 = instance_factory("i2")
    i3 = instance_factory("i3")
    ig_all = instance_group_factory("all", instances=[i1, i2, i3])
    assert ig_all.capacity == 300
    ig_single = instance_group_factory("single", instances=[i1])
    assert ig_single.capacity == 100


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

    def test_inventory_update_instance_groups(self, instance_group_factory, inventory_source, default_instance_group):
        iu = InventoryUpdate.objects.create(inventory_source=inventory_source)
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

    def test_project_update_instance_groups(self, instance_group_factory, project, default_instance_group):
        pu = ProjectUpdate.objects.create(project=project)
        assert pu.preferred_instance_groups == [default_instance_group]
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        project.organization.instance_groups.add(ig_org)
        assert pu.preferred_instance_groups == [ig_org]
        project.instance_groups.add(ig_tmp)
        assert pu.preferred_instance_groups == [ig_tmp, ig_org]

    def test_job_instance_groups(self, instance_group_factory, inventory, project, default_instance_group):
        jt = JobTemplate.objects.create(inventory=inventory, project=project)
        job = Job.objects.create(inventory=inventory, job_template=jt, project=project)
        assert job.preferred_instance_groups == [default_instance_group]
        ig_org = instance_group_factory("OrgIstGrp", [default_instance_group.instances.first()])
        ig_inv = instance_group_factory("InvIstGrp", [default_instance_group.instances.first()])
        ig_tmp = instance_group_factory("TmpIstGrp", [default_instance_group.instances.first()])
        project.organization.instance_groups.add(ig_org)
        inventory.instance_groups.add(ig_inv)
        assert job.preferred_instance_groups == [ig_inv, ig_org]
        job.job_template.instance_groups.add(ig_tmp)
        assert job.preferred_instance_groups == [ig_tmp, ig_inv, ig_org]
