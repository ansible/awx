import pytest

from awx.main.access import (
    LabelAccess,
)

from rest_framework.exceptions import ParseError

@pytest.mark.django_db
def test_label_get_queryset_user(label, user):
    access = LabelAccess(user('user', False))
    label.organization.member_role.members.add(user('user', False))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_label_get_queryset_su(label, user):
    access = LabelAccess(user('user', True))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_label_access(label, user):
    access = LabelAccess(user('user', False))
    assert not access.can_read(label)

@pytest.mark.django_db
def test_label_access_superuser(label, user):
    access = LabelAccess(user('admin', True))

    assert access.can_read(label)
    assert access.can_change(label, None)
    assert access.can_delete(label)

@pytest.mark.django_db
def test_label_access_admin(label, user, organization_factory):
    '''can_change because I am an admin of that org'''
    a = user('admin', False)
    org_no_members = organization_factory("no_members")
    org_members = organization_factory("has_members")

    label.organization.admin_role.members.add(a)
    org_members.admin_role.members.add(a)

    access = LabelAccess(user('admin', False))
    assert not access.can_change(label, {'organization': org_no_members.id})
    assert access.can_read(label)
    assert access.can_change(label, None)
    assert access.can_change(label, {'organization': org_members.id})
    assert access.can_delete(label)

@pytest.mark.django_db
def test_label_access_user(label, user):
    access = LabelAccess(user('user', False))
    label.organization.member_role.members.add(user('user', False))

    with pytest.raises(ParseError):
        access.can_add({'organization': None})
    assert not access.can_change(label, None)
    assert not access.can_delete(label)

    assert access.can_read(label)
    assert access.can_add({'organization': label.organization.id})

