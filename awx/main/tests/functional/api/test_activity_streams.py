from types import SimpleNamespace

import pytest
from django.http import QueryDict

from awx.api.versioning import reverse
from awx.api.views import ActivityStreamList
from awx.main.models.activity_stream import ActivityStream
from awx.main.models import Credential, Inventory, JobTemplate, Organization, Project, Team, WorkflowJobTemplate
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
    assert activity_stream_entry.object1 == 'organization'
    assert activity_stream_entry.object2 == 'user'


@pytest.mark.django_db
def test_rbac_stream_user_roles(activity_stream_entry, organization, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    assert activity_stream_entry.user.first() == org_admin
    assert activity_stream_entry.organization.first() == organization
    assert activity_stream_entry.object1 == 'organization'
    assert activity_stream_entry.object2 == 'user'


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_stream_access_cant_change(activity_stream_entry, organization, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    access = ActivityStreamAccess(org_admin)
    # These should always return false because the activity stream cannot be edited
    assert not access.can_add(activity_stream_entry)
    assert not access.can_change(activity_stream_entry, {'organization': None})
    assert not access.can_delete(activity_stream_entry)


def test_filtered_activity_stream_object_type_fallbacks():
    view = ActivityStreamList()

    view.request = SimpleNamespace(query_params=QueryDict())
    assert view._activity_stream_object_types() is None

    view.request = SimpleNamespace(query_params=QueryDict('object1=job&or__unsupported__in=user'))
    assert view._activity_stream_object_types() is None

    view.request = SimpleNamespace(query_params=QueryDict('object1=job'))
    assert {'job', 'user', 'team'} <= view._activity_stream_object_types()

    view.request = SimpleNamespace(query_params=QueryDict('object1=job_template'))
    assert {'job_template', 'credential', 'user', 'team'} <= view._activity_stream_object_types()

    view.request = SimpleNamespace(query_params=QueryDict('object1=user'))
    assert view._activity_stream_object_types() == {
        'ad_hoc_command',
        'credential',
        'group',
        'host',
        'inventory',
        'inventory_source',
        'inventory_update',
        'job',
        'job_template',
        'label',
        'notification',
        'notification_template',
        'organization',
        'project',
        'project_update',
        'role',
        'team',
        'user',
        'workflow_job',
        'workflow_job_template',
        'workflow_job_template_node',
    }


@pytest.mark.django_db
def test_filtered_credential_activity_includes_template_visibility(user, job_template, org_credential, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    template_user = user('template-only-user', False)
    job_template.read_role.members.add(template_user)
    activity = ActivityStream.objects.create(
        actor=template_user,
        operation='associate',
        object1='job_template',
        object2='credential',
    )
    activity.job_template.add(job_template)
    activity.credential.add(org_credential)

    unfiltered = ActivityStreamAccess(template_user).get_queryset()
    view = ActivityStreamList()
    view.request = SimpleNamespace(query_params=QueryDict('object2=credential'))
    object_types = view._activity_stream_object_types()
    assert {'credential', 'job_template', 'workflow_job_template'} <= object_types

    filtered = ActivityStreamAccess(
        template_user,
        activity_stream_queryset=ActivityStream.objects.filter(object2='credential'),
        activity_stream_object_types=object_types,
    ).get_queryset()

    assert unfiltered.filter(pk=activity.pk).exists()
    assert filtered.filter(pk=activity.pk).exists()


@pytest.mark.django_db
def test_filtered_activity_stream_superuser_uses_filtered_queryset(org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    org_admin.is_superuser = True
    org_admin.save(update_fields=['is_superuser'])
    queryset = ActivityStream.objects.filter(object1='job')

    result = ActivityStreamAccess(
        org_admin,
        activity_stream_queryset=queryset,
        activity_stream_object_type='job',
    ).get_queryset()
    assert list(result) == list(queryset)

    access = ActivityStreamAccess(
        org_admin,
        activity_stream_queryset=queryset,
        activity_stream_object_type='job',
    )
    access.prefetch_related = ('actor',)
    assert list(access.get_queryset()) == list(queryset)


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_filtered_activity_stream_visibility_builds_all_access_branches(org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    access = ActivityStreamAccess(org_admin)
    assert ActivityStream.objects.filter(access._activity_stream_visibility_q()).exists() is True


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_filtered_activity_stream_evaluates_each_visibility_branch(org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    for object_type in (
        'ad_hoc_command',
        'credential',
        'inventory',
        'organization',
        'project',
        'job_template',
        'workflow_job_template',
        'team',
    ):
        ActivityStreamAccess(
            org_admin,
            activity_stream_queryset=ActivityStream.objects.filter(object1=object_type),
            activity_stream_object_type=object_type,
        ).get_queryset().exists()


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_filtered_activity_stream_prunes_unrelated_visibility_branches(mocker, org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True

    for object_type, unrelated_access_methods in (
        (
            'job',
            (
                (Inventory, 'access_ids_qs'),
                (Credential, 'access_ids_qs'),
                (Organization, 'access_qs'),
                (Project, 'access_ids_qs'),
                (WorkflowJobTemplate, 'access_ids_qs'),
                (Team, 'access_ids_qs'),
            ),
        ),
        (
            'project',
            (
                (Inventory, 'access_ids_qs'),
                (Credential, 'access_ids_qs'),
                (Organization, 'access_qs'),
                (JobTemplate, 'access_ids_qs'),
                (WorkflowJobTemplate, 'access_ids_qs'),
                (Team, 'access_ids_qs'),
            ),
        ),
    ):
        patches = [
            mocker.patch.object(model, method, side_effect=AssertionError(f'{model.__name__} branch evaluated')) for model, method in unrelated_access_methods
        ]
        try:
            queryset = ActivityStreamAccess(
                org_admin,
                activity_stream_queryset=ActivityStream.objects.filter(object1=object_type),
                activity_stream_object_type=object_type,
            ).get_queryset()
            queryset.exists()
            for patch in patches:
                patch.assert_not_called()
        finally:
            mocker.stopall()


@pytest.mark.django_db
@pytest.mark.activity_stream_access
def test_stream_queryset_hides_shows_items(
    activity_stream_entry,
    organization,
    user,
    org_admin,
    project,
    org_credential,
    inventory,
    label,
    deploy_jobtemplate,
    notification_template,
    group,
    host,
    team,
    settings,
):
    settings.ACTIVITY_STREAM_ENABLED = True
    # this user is not in any organizations and should not see any resource activity
    no_access_user = user('no-access-user', False)
    access = ActivityStreamAccess(no_access_user)
    queryset = access.get_queryset()

    assert not queryset.filter(project__pk=project.pk)
    assert not queryset.filter(credential__pk=org_credential.pk)
    assert not queryset.filter(inventory__pk=inventory.pk)
    assert not queryset.filter(label__pk=label.pk)
    assert not queryset.filter(job_template__pk=deploy_jobtemplate.pk)
    assert not queryset.filter(group__pk=group.pk)
    assert not queryset.filter(host__pk=host.pk)
    assert not queryset.filter(team__pk=team.pk)
    assert not queryset.filter(notification_template__pk=notification_template.pk)
    assert not access.can_read(activity_stream_entry)

    # Organization admin should be able to see most things in the ActivityStream
    access = ActivityStreamAccess(org_admin)
    queryset = access.get_queryset()

    assert queryset.filter(project__pk=project.pk, operation='create').count() == 1
    assert queryset.filter(credential__pk=org_credential.pk, operation='create').count() == 1
    assert queryset.filter(inventory__pk=inventory.pk, operation='create').count() == 1
    assert queryset.filter(label__pk=label.pk, operation='create').count() == 1
    assert queryset.filter(job_template__pk=deploy_jobtemplate.pk, operation='create').count() == 1
    assert queryset.filter(group__pk=group.pk, operation='create').count() == 1
    assert queryset.filter(host__pk=host.pk, operation='create').count() == 1
    assert queryset.filter(team__pk=team.pk, operation='create').count() == 1
    assert queryset.filter(notification_template__pk=notification_template.pk, operation='create').count() == 1
    assert access.can_read(activity_stream_entry)


@pytest.mark.django_db
def test_filtered_activity_stream_list_works_on_test_database(get, user, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    response = get(f'{reverse("api:activity_stream_list")}?object1=job', user('admin', True))

    assert response.status_code == 200


@pytest.mark.django_db
def test_filtered_activity_stream_list_uses_transaction_local_jit_on_postgresql(mocker):
    from django.db import connection
    from awx.api.generics import SimpleListAPIView

    view = ActivityStreamList()
    request = SimpleNamespace(query_params=QueryDict('object1=job'))
    cursor = mocker.MagicMock()
    mocker.patch.object(connection, 'vendor', 'postgresql')
    mocker.patch.object(connection, 'cursor', return_value=cursor)
    mocker.patch.object(view.pagination_class, 'has_filter_params', return_value=True)
    mocker.patch.object(SimpleListAPIView, 'list', return_value='response')

    assert view.list(request) == 'response'
    cursor.__enter__.return_value.execute.assert_any_call('SET LOCAL jit = off')


@pytest.mark.django_db
def test_filtered_activity_stream_view_queryset_and_fallback(org_admin, settings):
    settings.ACTIVITY_STREAM_ENABLED = True
    view = ActivityStreamList()
    view.request = SimpleNamespace(query_params=QueryDict('object1=job'), user=org_admin)
    assert view.get_queryset().query.select_related == {'actor': {}}

    view.request = SimpleNamespace(query_params=QueryDict('search=job'), user=org_admin)
    assert view.filter_queryset(ActivityStream.objects.all()) is not None


@pytest.mark.django_db
def test_activity_stream_pagination_uses_unfiltered_count(get, organization, project, user, settings):
    """The pagination count should reflect total activity stream rows, not
    the RBAC-filtered subset.  The RBAC-filtered COUNT is catastrophically
    slow on large tables (AAP-83773); an approximate over-count from an
    unfiltered SELECT COUNT(*) is acceptable for pagination UI."""
    settings.ACTIVITY_STREAM_ENABLED = True

    no_access_user = user('no-access-user', False)

    total_entries = ActivityStream.objects.count()
    assert total_entries > 0

    url = reverse('api:activity_stream_list')
    response = get(url, no_access_user)

    assert response.status_code == 200
    visible_results = len(response.data['results'])
    pagination_count = response.data['count']
    assert pagination_count == total_entries
    assert visible_results < pagination_count


@pytest.mark.django_db
def test_stream_user_direct_role_updates(get, post, organization_factory):
    objects = organization_factory('test_org', superusers=['admin'], users=['test'], inventories=['inv1'])

    url = reverse('api:user_roles_list', kwargs={'pk': objects.users.test.pk})
    post(url, dict(id=objects.inventories.inv1.read_role.pk), objects.superusers.admin)

    activity_stream = ActivityStream.objects.filter(inventory__pk=objects.inventories.inv1.pk, user__pk=objects.users.test.pk, operation='associate').first()
    url = reverse('api:activity_stream_detail', kwargs={'pk': activity_stream.pk})
    response = get(url, objects.users.test)

    assert response.data['object1'] == 'inventory'
    assert response.data['object2'] == 'user'
