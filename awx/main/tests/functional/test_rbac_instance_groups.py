import pytest

from awx.main.access import (
    InstanceGroupAccess,
    OrganizationAccess,
    InventoryAccess,
    JobTemplateAccess,
)
from awx.main.models import Organization


@pytest.mark.django_db
def test_ig_read_user_visibility(default_instance_group, user, organization, job_template_factory):
    u = user('test', False)
    objects = job_template_factory('jt', organization=organization, project='p', inventory='i', credential='c')
    role = default_instance_group.read_role
    role.members.add(u)
    access = InstanceGroupAccess(u)
    jtaccess = JobTemplateAccess(u)
    assert not jtaccess.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert access.can_read(default_instance_group)
    assert not access.can_use(default_instance_group)
    assert not access.can_add(default_instance_group)
    assert not access.can_admin(default_instance_group)
    assert not access.can_change(default_instance_group, {'name': 'New description.'})


@pytest.mark.django_db
def test_ig_use_role_user_visibility(default_instance_group, user):
    u = user('test', False)
    role = default_instance_group.use_role
    role.members.add(u)
    access = InstanceGroupAccess(u)
    assert access.can_read(default_instance_group)
    assert access.can_use(default_instance_group)
    assert not access.can_add(default_instance_group)
    assert not access.can_admin(default_instance_group)
    assert not access.can_change(default_instance_group, {'name': 'New description.'})


@pytest.mark.django_db
def test_ig_role_based_associability(default_instance_group, user, organization, job_template_factory):
    objects = job_template_factory('jt', organization=organization, project='p', inventory='i', credential='c')

    ig_read = user('reader', False)
    ig_use = user('use', False)
    ig_admin = user('admin', False)

    read_role = default_instance_group.read_role
    admin_role = default_instance_group.admin_role
    use_role = default_instance_group.use_role

    read_role.members.add(ig_read)
    use_role.members.add(ig_use)
    admin_role.members.add(ig_admin)

    read_access = JobTemplateAccess(ig_read)
    use_access = JobTemplateAccess(ig_use)
    admin_access = JobTemplateAccess(ig_admin)

    assert not read_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert use_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert admin_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)

    read_access = InventoryAccess(ig_read)
    use_access = InventoryAccess(ig_use)
    admin_access = InventoryAccess(ig_admin)

    assert not read_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert use_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert admin_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)


@pytest.mark.django_db
def test_ig_use_with_org_admin(default_instance_group, rando, admin):
    org = Organization.objects.create(name='org1')

    use_role = default_instance_group.use_role
    use_role.members.add(rando)
    admin_role = org.admin_role
    org_admin_role = org.admin_role
    org_admin_role.members.add(admin)
    admin_role.members.add(rando)

    admin_access = InstanceGroupAccess(admin)
    access = InstanceGroupAccess(rando)

    assert list(admin_access.get_queryset()) == [default_instance_group]
    assert list(access.get_queryset()) == [default_instance_group]


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
