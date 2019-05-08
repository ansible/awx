import pytest

from awx.main.access import (
    InstanceGroupAccess,
    OrganizationAccess,
    InventoryAccess,
    JobTemplateAccess,
)
from awx.main.models import Organization


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
    assert len(InstanceGroupAccess(org_admin).get_queryset()) == 1


@pytest.mark.django_db
def test_ig_normal_user_associability(organization, default_instance_group, user):
    u = user('user', False)
    access = OrganizationAccess(u)
    assert not access.can_attach(organization, default_instance_group, 'instance_groups', None)
    organization.instance_groups.add(default_instance_group)
    organization.member_role.members.add(u)
    assert not access.can_attach(organization, default_instance_group, 'instance_groups', None)


@pytest.mark.django_db
def test_access_via_two_organizations(rando, default_instance_group):
    for org_name in ['org1', 'org2']:
        org = Organization.objects.create(name=org_name)
        org.instance_groups.add(default_instance_group)
        org.admin_role.members.add(rando)
    access = InstanceGroupAccess(rando)
    assert list(access.get_queryset()) == [default_instance_group]


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

    objects = job_template_factory('jt', organization=organization, project='p',
                                   inventory='i', credential='c')
    admin_access = InventoryAccess(admin)
    auditor_access = InventoryAccess(system_auditor)
    oadmin_access = InventoryAccess(org_admin)
    omember_access = InventoryAccess(org_member)

    assert admin_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert oadmin_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_attach(objects.inventory, default_instance_group, 'instance_groups', None)

    admin_access = JobTemplateAccess(admin)
    auditor_access = JobTemplateAccess(system_auditor)
    oadmin_access = JobTemplateAccess(org_admin)
    omember_access = JobTemplateAccess(org_member)

    assert admin_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert oadmin_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert not auditor_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
    assert not omember_access.can_attach(objects.job_template, default_instance_group, 'instance_groups', None)
