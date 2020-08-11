import pytest

from awx.main.access import (
    LabelAccess,
)


@pytest.mark.django_db
def test_label_get_queryset_user(label, user):
    u = user('user', False)
    access = LabelAccess(u)
    label.organization.member_role.members.add(u)
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_label_get_queryset_su(label, user):
    access = LabelAccess(user('user', True))
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_label_read_access(label, user):
    access = LabelAccess(user('user', False))
    assert not access.can_read(label)
    label.organization.member_role.members.add(user('user', False))
    assert access.can_read(label)


@pytest.mark.django_db
def test_label_jt_read_access(label, user, job_template):
    access = LabelAccess(user('user', False))
    assert not access.can_read(label)
    job_template.read_role.members.add(user('user', False))
    job_template.labels.add(label)
    assert access.can_read(label)


@pytest.mark.django_db
def test_label_access_superuser(label, user):
    access = LabelAccess(user('admin', True))

    assert access.can_read(label)
    assert access.can_change(label, None)
    assert access.can_delete(label)


@pytest.mark.django_db
def test_label_access_admin(organization_factory):
    '''can_change because I am an admin of that org'''
    no_members = organization_factory("no_members")
    members = organization_factory("has_members",
                                   users=['admin'],
                                   labels=['test'])

    label = members.labels.test
    admin = members.users.admin
    members.organization.admin_role.members.add(admin)

    access = LabelAccess(admin)
    assert not access.can_change(label, {'organization': no_members.organization.id})
    assert access.can_read(label)
    assert access.can_change(label, None)
    assert access.can_change(label, {'organization': members.organization.id})
    assert access.can_delete(label)


@pytest.mark.django_db
def test_label_access_user(label, user):
    access = LabelAccess(user('user', False))
    label.organization.member_role.members.add(user('user', False))

    assert not access.can_add({'organization': None})
    assert not access.can_change(label, None)
    assert not access.can_delete(label)

    assert access.can_read(label)
    assert access.can_add({'organization': label.organization.id})
