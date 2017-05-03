import pytest


@pytest.mark.django_db
def test_default_tower_instance_group(default_instance_group, job_factory):
    assert default_instance_group in job_factory().preferred_instance_groups


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
