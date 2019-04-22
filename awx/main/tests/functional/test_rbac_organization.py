from unittest import mock
import pytest

from awx.main.access import (
    BaseAccess,
    OrganizationAccess,
)


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_admin(cl, organization, user):
    '''can_change because I am an admin of that org'''
    a = user('admin', False)
    organization.admin_role.members.add(a)
    organization.member_role.members.add(user('user', False))

    access = OrganizationAccess(a)
    assert access.can_change(organization, None)
    assert access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 1
    assert len(org.member_role.members.all()) == 1


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_organization_access_user(cl, organization, user):
    access = OrganizationAccess(user('user', False))
    organization.member_role.members.add(user('user', False))

    assert not access.can_change(organization, None)
    assert not access.can_delete(organization)

    org = access.get_queryset()[0]
    assert len(org.admin_role.members.all()) == 0
    assert len(org.member_role.members.all()) == 1


@pytest.mark.django_db
@pytest.mark.parametrize('ext_auth', [True, False])
def test_org_resource_role(ext_auth, organization, rando, org_admin):
    with mock.patch('awx.main.access.settings') as settings_mock:
        settings_mock.MANAGE_ORGANIZATION_AUTH = ext_auth
        access = OrganizationAccess(org_admin)

        assert access.can_attach(organization, rando, 'member_role.members') == ext_auth
        organization.member_role.members.add(rando)
        assert access.can_unattach(organization, rando, 'member_role.members') == ext_auth
