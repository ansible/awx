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
