import pytest

from awx.main.access import (
    InstanceGroupAccess,
    OrganizationAccess,
    InventoryAccess,
    JobTemplateAccess,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "obj_perm,allowed,readonly,partial", [("admin_role", True, True, True), ("use_role", False, True, True), ("read_role", False, True, False)]
)
def test_ig_role_base_visibility(default_instance_group, rando, obj_perm, allowed, partial, readonly):
    if obj_perm:
        getattr(default_instance_group, obj_perm).members.add(rando)

    assert readonly == InstanceGroupAccess(rando).can_read(default_instance_group)
    assert partial == InstanceGroupAccess(rando).can_use(default_instance_group)
    assert not InstanceGroupAccess(rando).can_add(default_instance_group)
    assert allowed == InstanceGroupAccess(rando).can_admin(default_instance_group)
    assert allowed == InstanceGroupAccess(rando).can_change(default_instance_group, {'name': 'New Name'})


@pytest.mark.django_db
@pytest.mark.parametrize(
    "obj_perm,subobj_perm,allowed", [('admin_role', 'use_role', True), ('admin_role', 'read_role', False), ('admin_role', 'admin_role', True)]
)
def test_ig_role_based_associability(default_instance_group, rando, organization, job_template_factory, obj_perm, subobj_perm, allowed):
    objects = job_template_factory('jt', organization=organization, project='p', inventory='i', credential='c')
    if obj_perm:
        getattr(objects.job_template, obj_perm).members.add(rando)
        getattr(objects.inventory, obj_perm).members.add(rando)
        getattr(objects.organization, obj_perm).members.add(rando)
    if subobj_perm:
        getattr(default_instance_group, subobj_perm).members.add(rando)

    assert allowed == JobTemplateAccess(rando).can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert allowed == InventoryAccess(rando).can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert allowed == OrganizationAccess(rando).can_attach(objects.organization, default_instance_group, 'instance_groups', None)


@pytest.mark.django_db
def test_ig_use_with_org_admin(default_instance_group, rando, org_admin):
    default_instance_group.use_role.members.add(rando)

    assert list(InstanceGroupAccess(org_admin).get_queryset()) != [default_instance_group]
    assert list(InstanceGroupAccess(rando).get_queryset()) == [default_instance_group]


@pytest.mark.django_db
def test_ig_normal_user_visibility(organization, default_instance_group, user):
    u = user('user', False)
    assert len(InstanceGroupAccess(u).get_queryset()) == 0
    organization.instance_groups.add(default_instance_group)
    organization.member_role.members.add(u)
    assert len(InstanceGroupAccess(u).get_queryset()) == 0


@pytest.mark.django_db
def test_ig_admin_user_visibility(organization, default_instance_group, admin, system_auditor, org_admin):
    assert len(InstanceGroupAccess(admin).get_queryset()) == 1
    assert len(InstanceGroupAccess(system_auditor).get_queryset()) == 1
    assert len(InstanceGroupAccess(org_admin).get_queryset()) == 0
    organization.instance_groups.add(default_instance_group)
    assert len(InstanceGroupAccess(org_admin).get_queryset()) == 0


@pytest.mark.django_db
def test_ig_normal_user_associability(organization, default_instance_group, user):
    u = user('user', False)
    access = OrganizationAccess(u)
    assert not access.can_attach(organization, default_instance_group, 'instance_groups', None)
    organization.instance_groups.add(default_instance_group)
    organization.member_role.members.add(u)
    assert not access.can_attach(organization, default_instance_group, 'instance_groups', None)


@pytest.mark.django_db
def test_ig_associability(organization, default_instance_group, admin, system_auditor, org_admin, org_member, job_template_factory):
    admin_access = OrganizationAccess(admin)
    auditor_access = OrganizationAccess(system_auditor)
    oadmin_access = OrganizationAccess(org_admin)
    omember_access = OrganizationAccess(org_member)
    assert admin_access.can_attach(organization, default_instance_group, 'instance_groups', None)
    assert not oadmin_access.can_attach(organization, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_attach(organization, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_attach(organization, default_instance_group, 'instance_groups', None)

    organization.instance_groups.add(default_instance_group)

    assert admin_access.can_unattach(organization, default_instance_group, 'instance_groups', None)
    assert not oadmin_access.can_unattach(organization, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_unattach(organization, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_unattach(organization, default_instance_group, 'instance_groups', None)

    objects = job_template_factory('jt', organization=organization, project='p', inventory='i', credential='c')
    admin_access = InventoryAccess(admin)
    auditor_access = InventoryAccess(system_auditor)
    oadmin_access = InventoryAccess(org_admin)
    omember_access = InventoryAccess(org_member)

    assert admin_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert not oadmin_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)

    admin_access = JobTemplateAccess(admin)
    auditor_access = JobTemplateAccess(system_auditor)
    oadmin_access = JobTemplateAccess(org_admin)
    omember_access = JobTemplateAccess(org_member)

    assert admin_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert not oadmin_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
