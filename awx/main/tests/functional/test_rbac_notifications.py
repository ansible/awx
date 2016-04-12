import pytest

from awx.main.access import NotifierAccess

@pytest.mark.django_db
def test_notifier_get_queryset_orgmember(notifier, user):
    access = NotifierAccess(user('user', False))
    notifier.organization.member_role.members.add(user('user', False))
    assert access.get_queryset().count() == 0

@pytest.mark.django_db
def test_notifier_get_queryset_nonorgmember(notifier, user):
    access = NotifierAccess(user('user', False))
    assert access.get_queryset().count() == 0

@pytest.mark.django_db
def test_notifier_get_queryset_su(notifier, user):
    access = NotifierAccess(user('user', True))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_notifier_get_queryset_orgadmin(notifier, user):
    access = NotifierAccess(user('admin', False))
    notifier.organization.admin_role.members.add(user('admin', False))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_notifier_access_superuser(notifier, user, notifier_factory):
    access = NotifierAccess(user('admin', True))
    assert access.can_read(notifier)
    assert access.can_change(notifier, None)
    assert access.can_delete(notifier)
    nf = notifier_factory("test-orphaned")
    nf.organization = None
    nf.save()
    assert access.can_read(nf)
    assert access.can_change(nf, None)
    assert access.can_delete(nf)

@pytest.mark.django_db
def test_notifier_access_admin(notifier, user, organization_factory, notifier_factory):
    adm = user('admin', False)
    other_org = organization_factory('other')
    present_org = organization_factory('present')
    notifier.organization.admin_role.members.add(adm)
    present_org.admin_role.members.add(adm)

    access = NotifierAccess(user('admin', False))
    assert not access.can_change(notifier, {'organization': other_org.id})
    assert access.can_read(notifier)
    assert access.can_change(notifier, None)
    assert access.can_change(notifier, {'organization': present_org.id})
    assert access.can_delete(notifier)
    nf = notifier_factory("test-orphaned")
    nf.organization = None
    nf.save()
    assert not access.can_read(nf)
    assert not access.can_change(nf, None)
    assert not access.can_delete(nf)

@pytest.mark.django_db
def test_notifier_access_org_user(notifier, user):
    u = user('normal', False)
    notifier.organization.member_role.members.add(u)
    access = NotifierAccess(user('normal', False))
    assert not access.can_read(notifier)
    assert not access.can_change(notifier, None)
    assert not access.can_delete(notifier)
