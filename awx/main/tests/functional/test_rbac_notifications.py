import pytest

from awx.main.models import Organization, Project
from awx.main.access import (
    NotificationTemplateAccess,
    NotificationAccess,
    JobTemplateAccess
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

    nf = notification_template_factory("test-orphaned").notification_template
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
    nt_organization = Organization.objects.create(name='organization just for the notification template')
    notification_template.organization = nt_organization
    notification_template.save()
    getattr(notification_template.organization, org_role).members.add(rando)
    kwargs = dict(
        sub_obj=notification_template,
        relationship='notification_templates_success',
        data={'id': notification_template.id}
    )
    permissions = {}
    expected_permissions = {}
    organization = Organization.objects.create(name='objective organization')

    for resource in (organization, job_template, project, workflow_job_template, inventory_source):
        permission_resource = resource
        if resource == inventory_source:
            permission_resource = inventory_source.inventory
        getattr(permission_resource, 'admin_role').members.add(rando)
        model_name = resource.__class__.__name__
        permissions[model_name] = rando.can_access(resource.__class__, 'attach', resource, **kwargs)
        expected_permissions[model_name] = expect

    assert permissions == expected_permissions


@pytest.mark.django_db
def test_organization_NT_attach_permission(rando, notification_template):
    notification_template.organization.notification_admin_role.members.add(rando)
    target_organization = Organization.objects.create(name='objective organization')
    target_organization.workflow_admin_role.members.add(rando)
    assert not rando.can_access(Organization, 'attach', obj=target_organization, sub_obj=notification_template,
                                relationship='notification_templates_success', data={})
    target_organization.auditor_role.members.add(rando)
    assert rando.can_access(Organization, 'attach', obj=target_organization, sub_obj=notification_template,
                            relationship='notification_templates_success', data={})


@pytest.mark.django_db
def test_project_NT_attach_permission(rando, notification_template):
    notification_template.organization.notification_admin_role.members.add(rando)
    project = Project.objects.create(
        name='objective project',
        organization=Organization.objects.create(name='foo')
    )
    project.update_role.members.add(rando)
    assert not rando.can_access(Project, 'attach', obj=project, sub_obj=notification_template,
                                relationship='notification_templates_success', data={})
    project.admin_role.members.add(rando)
    assert rando.can_access(Project, 'attach', obj=project, sub_obj=notification_template,
                            relationship='notification_templates_success', data={})


@pytest.mark.django_db
@pytest.mark.parametrize("res_role,expect", [
    ('read_role', True),
    (None, False)
])
def test_object_role_JT_attach(rando, job_template, workflow_job_template, inventory_source,
                               notification_template, res_role, expect):
    nt_organization = Organization.objects.create(name='organization just for the notification template')
    nt_organization.notification_admin_role.members.add(rando)
    notification_template.organization = nt_organization
    notification_template.save()
    kwargs = dict(
        sub_obj=notification_template,
        relationship='notification_templates_success',
        data={'id': notification_template.id}
    )
    permissions = {}
    expected_permissions = {}

    for resource in (job_template, workflow_job_template, inventory_source):
        permission_resource = resource
        if resource == inventory_source:
            permission_resource = inventory_source.inventory
        model_name = resource.__class__.__name__
        if res_role is None or hasattr(permission_resource, res_role):
            if res_role is not None:
                getattr(permission_resource, res_role).members.add(rando)
            permissions[model_name] = rando.can_access(
                resource.__class__, 'attach', resource, **kwargs
            )
            expected_permissions[model_name] = expect
        else:
            permissions[model_name] = None
            expected_permissions[model_name] = None

    assert permissions == expected_permissions


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
