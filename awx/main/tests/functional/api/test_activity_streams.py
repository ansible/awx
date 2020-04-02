import pytest

from awx.api.versioning import reverse
from awx.main.models.activity_stream import ActivityStream
from awx.main.access import ActivityStreamAccess
from awx.conf.models import Setting



@pytest.fixture
def activity_stream_entry(organization, org_admin):
    return ActivityStream.objects.filter(organization__pk=organization.pk, user=org_admin, operation='associate').first()


@pytest.mark.django_db
def test_get_activity_stream_list(monkeypatch, organization, get, user, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    url = reverse('api:activity_stream_list')
    response = get(url, user('admin', True))

    assert response.status_code == 200


@pytest.mark.django_db
def test_basic_fields(monkeypatch, organization, get, user, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    u = user('admin', True)
    activity_stream = ActivityStream.objects.filter(organization=organization).latest('pk')
    activity_stream.actor = u
    activity_stream.save()

    aspk = activity_stream.pk
    url = reverse('api:activity_stream_detail', kwargs={'pk': aspk})
    response = get(url, user('admin', True))

    assert response.status_code == 200
    assert 'related' in response.data
    assert 'organization' in response.data['related']
    assert 'summary_fields' in response.data
    assert 'organization' in response.data['summary_fields']
    assert response.data['summary_fields']['organization'][0]['name'] == 'test-org'


@pytest.mark.django_db
def test_ctint_activity_stream(monkeypatch, get, user, settings):
    Setting.objects.create(key="FOO", value="bar")
    settings.ACTIVITY_STREAM_ENABLED = True
    u = user('admin', True)
    activity_stream = ActivityStream.objects.filter(setting__icontains="FOO").latest('pk')
    activity_stream.actor = u
    activity_stream.save()

    aspk = activity_stream.pk
    url = reverse('api:activity_stream_detail', kwargs={'pk': aspk})
    response = get(url, user('admin', True))

    assert response.status_code == 200
    assert 'summary_fields' in response.data
    assert 'setting' in response.data['summary_fields']
    assert response.data['summary_fields']['setting'][0]['name'] == 'FOO'


@pytest.mark.django_db
def test_rbac_stream_resource_roles(activity_stream_entry, organization, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    assert activity_stream_entry.user.first() == org_admin
    assert activity_stream_entry.organization.first() == organization
    assert activity_stream_entry.role.first() == organization.admin_role
    assert activity_stream_entry.object_relationship_type == 'awx.main.models.organization.Organization.admin_role'


@pytest.mark.django_db
def test_rbac_stream_user_roles(activity_stream_entry, organization, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    assert activity_stream_entry.user.first() == org_admin
    assert activity_stream_entry.organization.first() == organization
    assert activity_stream_entry.role.first() == organization.admin_role
    assert activity_stream_entry.object_relationship_type == 'awx.main.models.organization.Organization.admin_role'


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_stream_access_cant_change(activity_stream_entry, organization, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    access = ActivityStreamAccess(org_admin)
    # These should always return false because the activity stream cannot be edited
    assert not access.can_add(activity_stream_entry)
    assert not access.can_change(activity_stream_entry, {'organization': None})
    assert not access.can_delete(activity_stream_entry)


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_stream_queryset_hides_shows_items(
        activity_stream_entry, organization, user, org_admin,
        project, org_credential, inventory, label, deploy_jobtemplate,
        notification_template, group, host, team, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    # this user is not in any organizations and should not see any resource activity
    no_access_user = user('no-access-user', False)
    queryset = ActivityStreamAccess(no_access_user).get_queryset()

    assert not queryset.filter(project__pk=project.pk)
    assert not queryset.filter(credential__pk=org_credential.pk)
    assert not queryset.filter(inventory__pk=inventory.pk)
    assert not queryset.filter(label__pk=label.pk)
    assert not queryset.filter(job_template__pk=deploy_jobtemplate.pk)
    assert not queryset.filter(group__pk=group.pk)
    assert not queryset.filter(host__pk=host.pk)
    assert not queryset.filter(team__pk=team.pk)
    assert not queryset.filter(notification_template__pk=notification_template.pk)

    # Organization admin should be able to see most things in the ActivityStream
    queryset = ActivityStreamAccess(org_admin).get_queryset()

    assert queryset.filter(project__pk=project.pk, operation='create').count() == 1
    assert queryset.filter(credential__pk=org_credential.pk, operation='create').count() == 1
    assert queryset.filter(inventory__pk=inventory.pk, operation='create').count() == 1
    assert queryset.filter(label__pk=label.pk, operation='create').count() == 1
    assert queryset.filter(job_template__pk=deploy_jobtemplate.pk, operation='create').count() == 1
    assert queryset.filter(group__pk=group.pk, operation='create').count() == 1
    assert queryset.filter(host__pk=host.pk, operation='create').count() == 1
    assert queryset.filter(team__pk=team.pk, operation='create').count() == 1
    assert queryset.filter(notification_template__pk=notification_template.pk, operation='create').count() == 1


@pytest.mark.django_db
def test_stream_user_direct_role_updates(get, post, organization_factory):
    objects = organization_factory('test_org',
                                   superusers=['admin'],
                                   users=['test'],
                                   inventories=['inv1'])

    url = reverse('api:user_roles_list', kwargs={'pk': objects.users.test.pk})
    post(url, dict(id=objects.inventories.inv1.read_role.pk), objects.superusers.admin)

    activity_stream = ActivityStream.objects.filter(
        inventory__pk=objects.inventories.inv1.pk,
        user__pk=objects.users.test.pk,
        role__pk=objects.inventories.inv1.read_role.pk).first()
    url = reverse('api:activity_stream_detail', kwargs={'pk': activity_stream.pk})
    response = get(url, objects.users.test)

    assert response.data['object1'] == 'user'
    assert response.data['object2'] == 'inventory'
