import pytest

from awx.main.access import (
    LabelAccess,
)

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
def test_label_access_admin(label, user):
    '''can_change because I am an admin of that org'''
    a = user('admin', False)
    label.organization.admin_role.members.add(a)

    access = LabelAccess(user('admin', False))
    assert access.can_read(label)
    assert access.can_change(label, None)
    assert access.can_delete(label)

@pytest.mark.django_db
def test_label_access_user(label, user):
    access = LabelAccess(user('user', False))
    label.organization.member_role.members.add(user('user', False))

    assert access.can_read(label)
    assert not access.can_change(label, None)
    assert not access.can_delete(label)

