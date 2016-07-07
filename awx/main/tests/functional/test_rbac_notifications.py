import pytest

from awx.main.access import NotificationTemplateAccess

@pytest.mark.django_db
def test_notification_template_get_queryset_orgmember(notification_template, user):
    access = NotificationTemplateAccess(user('user', False))
    notification_template.organization.member_role.members.add(user('user', False))
    assert access.get_queryset().count() == 0

@pytest.mark.django_db
def test_notification_template_get_queryset_nonorgmember(notification_template, user):
    access = NotificationTemplateAccess(user('user', False))
    assert access.get_queryset().count() == 0

@pytest.mark.django_db
def test_notification_template_get_queryset_su(notification_template, user):
    access = NotificationTemplateAccess(user('user', True))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_notification_template_get_queryset_orgadmin(notification_template, user):
    access = NotificationTemplateAccess(user('admin', False))
    notification_template.organization.admin_role.members.add(user('admin', False))
    assert access.get_queryset().count() == 1

@pytest.mark.django_db
def test_notification_template_access_superuser(notification_template, user, notification_template_factory):
    access = NotificationTemplateAccess(user('admin', True))
    assert access.can_read(notification_template)
    assert access.can_change(notification_template, None)
    assert access.can_delete(notification_template)
    nf = notification_template_factory("test-orphaned")
    nf.organization = None
    nf.save()
    assert access.can_read(nf)
    assert access.can_change(nf, None)
    assert access.can_delete(nf)

@pytest.mark.django_db
def test_notification_template_access_admin(notification_template, user, organization_factory, notification_template_factory):
    adm = user('admin', False)
    other_org = organization_factory('other')
    present_org = organization_factory('present')
    notification_template.organization.admin_role.members.add(adm)
    present_org.admin_role.members.add(adm)

    access = NotificationTemplateAccess(user('admin', False))
    assert not access.can_change(notification_template, {'organization': other_org.id})
    assert access.can_read(notification_template)
    assert access.can_change(notification_template, None)
    assert access.can_change(notification_template, {'organization': present_org.id})
    assert access.can_delete(notification_template)
    nf = notification_template_factory("test-orphaned")
    nf.organization = None
    nf.save()
    assert not access.can_read(nf)
    assert not access.can_change(nf, None)
    assert not access.can_delete(nf)

@pytest.mark.django_db
def test_notification_template_access_org_user(notification_template, user):
    u = user('normal', False)
    notification_template.organization.member_role.members.add(u)
    access = NotificationTemplateAccess(user('normal', False))
    assert not access.can_read(notification_template)
    assert not access.can_change(notification_template, None)
    assert not access.can_delete(notification_template)
