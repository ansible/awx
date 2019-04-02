import pytest

from awx.main.models import Organization
from awx.main.access import (
    NotificationTemplateAccess,
    NotificationAccess,
    JobTemplateAccess,
    ProjectAccess,
    WorkflowJobTemplateAccess,
    OrganizationAccess,
    InventorySourceAccess
)


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
def test_notification_template_get_queryset_notificationadmin(notification_template, user):
    access = NotificationTemplateAccess(user('admin', False))
    notification_template.organization.notification_admin_role.members.add(user('admin', False))
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_notification_template_get_queryset_org_auditor(notification_template, org_auditor):
    access = NotificationTemplateAccess(org_auditor)
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_notification_template_access_superuser(notification_template_factory):
    nf_objects = notification_template_factory('test-orphaned', organization='test', superusers=['admin'])
    admin = nf_objects.superusers.admin
    nf = nf_objects.notification_template

    access = NotificationTemplateAccess(admin)
    assert access.can_read(nf)
    assert access.can_change(nf, None)
    assert access.can_delete(nf)

    nf.organization = None
    nf.save()

    assert access.can_read(nf)
    assert access.can_change(nf, None)
    assert access.can_delete(nf)


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["present.admin_role:admin", "present.notification_admin_role:admin"])
def test_notification_template_access_admin(role, organization_factory, notification_template_factory):
    other_objects = organization_factory('other')
    present_objects = organization_factory('present',
                                           users=['admin'],
                                           notification_templates=['test-notification'],
                                           roles=[role])

    notification_template = present_objects.notification_templates.test_notification
    other_org = other_objects.organization
    present_org = present_objects.organization
    admin = present_objects.users.admin

    access = NotificationTemplateAccess(admin)
    assert not access.can_change(notification_template, {'organization': other_org.id})
    assert access.can_read(notification_template)
    assert access.can_change(notification_template, None)
    assert access.can_change(notification_template, {'organization': present_org.id})
    assert access.can_delete(notification_template)

    nf = notification_template_factory("test-orphaned")
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


@pytest.mark.django_db
def test_notificaiton_template_orphan_access_org_admin(notification_template, organization, org_admin):
    notification_template.organization = None
    access = NotificationTemplateAccess(org_admin)
    assert not access.can_change(notification_template, {'organization': organization.id})


@pytest.mark.django_db
def test_notification_access_get_queryset_org_admin(notification, org_admin):
    access = NotificationAccess(org_admin)
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_notification_access_get_queryset_org_auditor(notification, org_auditor):
    access = NotificationAccess(org_auditor)
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_notification_access_system_admin(notification, admin):
    access = NotificationAccess(admin)
    assert access.can_read(notification)
    assert access.can_delete(notification)


@pytest.mark.django_db
def test_system_auditor_JT_attach(system_auditor, job_template, notification_template):
    job_template.admin_role.members.add(system_auditor)
    access = JobTemplateAccess(system_auditor)
    assert not access.can_attach(
        job_template, notification_template, 'notification_templates_success',
        {'id': notification_template.id})


@pytest.mark.django_db
@pytest.mark.parametrize("org_role,expect", [
    ('admin_role', True),
    ('notification_admin_role', True),
    ('workflow_admin_role', False),
    ('auditor_role', False),
    ('member_role', False)
])
def test_org_role_JT_attach(rando, job_template, project, workflow_job_template, inventory_source,
                            notification_template, org_role, expect):
    getattr(notification_template.organization, org_role).members.add(rando)
    kwargs = dict(
        sub_obj=notification_template,
        relationship='notification_templates_success',
        data={'id': notification_template.id}
    )
    job_template.admin_role.members.add(rando)
    assert JobTemplateAccess(rando).can_attach(job_template, **kwargs) is expect
    project.admin_role.members.add(rando)
    assert ProjectAccess(rando).can_attach(project, **kwargs) is expect
    workflow_job_template.admin_role.members.add(rando)
    assert workflow_job_template.organization == notification_template.organization
    assert WorkflowJobTemplateAccess(rando).can_attach(workflow_job_template, **kwargs) is expect
    second_organization = Organization.objects.create(name='fooooorg')
    second_organization.admin_role.members.add(rando)
    assert OrganizationAccess(rando).can_attach(second_organization, **kwargs) is expect
    inventory_source.inventory.admin_role.members.add(rando)
    assert InventorySourceAccess(rando).can_attach(inventory_source, **kwargs) is expect


@pytest.mark.django_db
def test_notification_access_org_admin(notification, org_admin):
    access = NotificationAccess(org_admin)
    assert access.can_read(notification)
    assert access.can_delete(notification)


@pytest.mark.django_db
def test_notification_access_org_auditor(notification, org_auditor):
    access = NotificationAccess(org_auditor)
    assert access.can_read(notification)
    assert not access.can_delete(notification)
