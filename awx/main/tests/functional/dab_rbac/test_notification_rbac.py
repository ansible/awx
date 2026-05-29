import pytest

from awx.api.versioning import reverse
from awx.main.models import NotificationTemplate, Organization

from ansible_base.rbac.models import RoleDefinition
from ansible_base.rbac import permission_registry

NT_DATA = {
    'notification_type': 'webhook',
    'notification_configuration': {
        'url': 'http://localhost',
        'username': '',
        'password': '',
        'headers': {},
    },
}


def nt_url(pk):
    return reverse('api:notification_template_detail', kwargs={'pk': pk})


@pytest.fixture
def nt_add_role(setup_managed_roles):
    """A custom role with only add_notificationtemplate and view_organization.
    This is intentionally narrower than Organization NotificationTemplate Admin
    so that give_creator_permissions actually creates creator permissions."""
    rd, _ = RoleDefinition.objects.get_or_create(
        name='nt-add-only',
        permissions=['add_notificationtemplate', 'view_organization'],
        content_type=permission_registry.content_type_model.objects.get_for_model(Organization),
    )
    return rd


@pytest.mark.django_db
def test_create_with_add_only_role_gets_creator_permissions(rando, organization, post, get, patch, nt_add_role):
    """User with only add permission creates a notification template and gets
    creator permissions (change, delete, view) via give_creator_permissions.
    This exercises the fix for models without old-style roles (AAP-57274)."""
    nt_add_role.give_permission(rando, organization)

    r = post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )
    nt = NotificationTemplate.objects.get(pk=r.data['id'])
    assert rando.has_obj_perm(nt, 'change')
    assert rando.has_obj_perm(nt, 'view')

    # Creator permissions survive revocation of the org-level add role
    nt_add_role.remove_permission(rando, organization)
    get(nt_url(nt.pk), user=rando, expect=200)
    patch(nt_url(nt.pk), data={'description': 'updated'}, user=rando, expect=200)


@pytest.mark.django_db
def test_org_admin_can_crud(rando, organization, post, get, patch, delete, setup_managed_roles):
    """User with org-level notification admin can create, view, edit, and delete"""
    rd = RoleDefinition.objects.get(name='Organization NotificationTemplate Admin')
    rd.give_permission(rando, organization)

    r = post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )
    pk = r.data['id']
    url = nt_url(pk)

    get(url, user=rando, expect=200)
    patch(url, data={'description': 'updated'}, user=rando, expect=200)
    delete(url, user=rando, expect=204)
    assert not NotificationTemplate.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_unpermissioned_user_cannot_access(rando, notification_template, get, patch, delete, setup_managed_roles):
    """User without any permissions cannot view, edit, or delete a notification template"""
    url = nt_url(notification_template.pk)

    get(url, user=rando, expect=403)
    patch(url, data={'description': 'nope'}, user=rando, expect=403)
    delete(url, user=rando, expect=403)


@pytest.mark.django_db
def test_grant_and_revoke_object_role(rando, notification_template, get, patch, setup_managed_roles):
    """Granting and revoking NotificationTemplate Admin role controls access"""
    rd = RoleDefinition.objects.get(name='NotificationTemplate Admin')
    url = nt_url(notification_template.pk)

    get(url, user=rando, expect=403)

    rd.give_permission(rando, notification_template)
    get(url, user=rando, expect=200)
    patch(url, data={'description': 'changed'}, user=rando, expect=200)

    rd.remove_permission(rando, notification_template)
    get(url, user=rando, expect=403)
    patch(url, data={'description': 'nope'}, user=rando, expect=403)


@pytest.mark.django_db
def test_creator_can_access_sub_endpoints(rando, organization, post, get, nt_add_role):
    """Creator can access notification list sub-endpoint"""
    nt_add_role.give_permission(rando, organization)

    r = post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )
    pk = r.data['id']

    # Revoke org-level role so only creator permissions remain
    nt_add_role.remove_permission(rando, organization)

    get(
        reverse('api:notification_template_notification_list', kwargs={'pk': pk}),
        user=rando,
        expect=200,
    )


@pytest.mark.django_db
def test_list_filtered_by_permissions(rando, admin_user, organization, post, get, nt_add_role):
    """Notification template list only shows templates the user has access to"""
    nt_add_role.give_permission(rando, organization)

    post(
        reverse('api:notification_template_list'),
        dict(name='admin-nt', organization=organization.id, **NT_DATA),
        user=admin_user,
        expect=201,
    )
    post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )

    # rando has org-level add, but admin-nt was created by admin → rando shouldn't see it
    # unless org admin role also gives view. With add-only role, rando has view_organization
    # but not view_notificationtemplate at the org level, so they only see their own (via creator perms)
    nt_add_role.remove_permission(rando, organization)
    r = get(reverse('api:notification_template_list'), user=rando, expect=200)
    visible_names = {item['name'] for item in r.data['results']}
    assert 'rando-nt' in visible_names
    assert 'admin-nt' not in visible_names


@pytest.mark.django_db
def test_creator_access_list_with_add_only_role(rando, organization, post, get, nt_add_role):
    """User with add_only role creates a notification template and can access its access_list endpoint"""
    from ansible_base.rbac.models import DABContentType

    nt_add_role.give_permission(rando, organization)

    r = post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )
    nt = NotificationTemplate.objects.get(pk=r.data['id'])

    # Revoke org-level role so only creator permissions remain
    nt_add_role.remove_permission(rando, organization)

    # Creator should be able to access the access_list endpoint for their own notification template
    # Use the DAB access_list endpoint pattern: /api/v2/role_user_access/{model_name}/{pk}/
    ct = DABContentType.objects.get_for_model(NotificationTemplate)
    access_list_url = f'/api/v2/role_user_access/{ct.api_slug}/{nt.pk}/?order_by=id'
    r = get(access_list_url, user=rando, expect=200)

    # The creator should be listed in the access list
    usernames = {user['username'] for user in r.data['results']}
    assert rando.username in usernames


@pytest.mark.django_db
def test_unpermissioned_user_cannot_access_access_list(rando, organization, post, admin_user, get, setup_managed_roles):
    """User without view permission cannot access the access_list endpoint"""
    from ansible_base.rbac.models import DABContentType

    # Create a notification template as admin
    r = post(
        reverse('api:notification_template_list'),
        dict(name='admin-nt', organization=organization.id, **NT_DATA),
        user=admin_user,
        expect=201,
    )
    nt = NotificationTemplate.objects.get(pk=r.data['id'])

    ct = DABContentType.objects.get_for_model(NotificationTemplate)
    access_list_url = f'/api/v2/role_user_access/{ct.api_slug}/{nt.pk}/?order_by=id'
    # rando has no permissions on this notification template, so they can't see it or its access list
    # The endpoint returns 404 (not found) instead of 403 when user can't view the resource
    get(access_list_url, user=rando, expect=404)


@pytest.mark.django_db
def test_access_list_shows_creator(rando, organization, post, get, nt_add_role, setup_managed_roles):
    """Access list shows the creator with direct permissions"""
    from ansible_base.rbac.models import DABContentType
    from ansible_base.rbac.models import RoleDefinition

    nt_add_role.give_permission(rando, organization)

    # rando creates a notification template
    r = post(
        reverse('api:notification_template_list'),
        dict(name='rando-nt', organization=organization.id, **NT_DATA),
        user=rando,
        expect=201,
    )
    nt = NotificationTemplate.objects.get(pk=r.data['id'])

    # Now assign them the object admin role directly too
    rd = RoleDefinition.objects.get(name='NotificationTemplate Admin')
    rd.give_permission(rando, nt)

    ct = DABContentType.objects.get_for_model(NotificationTemplate)
    access_list_url = f'/api/v2/role_user_access/{ct.api_slug}/{nt.pk}/?order_by=id'
    r = get(access_list_url, user=rando, expect=200)

    # rando should be listed with direct permissions from both creator and object role assignment
    user_data = {item['username']: item for item in r.data['results']}
    assert rando.username in user_data

    # Verify they have direct role assignments
    assert len(user_data[rando.username]['object_role_assignments']) > 0
    assert any(assign.get('type') == 'direct' for assign in user_data[rando.username]['object_role_assignments'])
