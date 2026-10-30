import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from awx.api.versioning import reverse
from awx.main.models import WorkflowJobTemplate
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.schedules import Schedule
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
def test_activity_stream_prefetches_only_types_present_on_page(get, project, org_admin, mocker, settings):
    """A page should not prefetch unrelated Activity Stream associations."""
    settings.ACTIVITY_STREAM_ENABLED = True
    entry = ActivityStream.objects.create(
        operation='create',
        object1='project',
        object2='',
        actor=org_admin,
        changes='{}',
    )
    entry.project.add(project)

    prefetch = mocker.patch('awx.api.serializers.prefetch_related_objects')
    url = reverse('api:activity_stream_list')
    response = get(
        f'{url}?or__object1__in=project&or__object2__in=project&order_by=-id&page=1&page_size=1',
        org_admin,
    )

    assert response.status_code == 200
    assert response.data['results'][0]['id'] == entry.id
    prefetches = prefetch.call_args.args[1:]
    assert 'project' in prefetches
    assert not {'credential', 'inventory', 'job', 'user'}.intersection(prefetches)


@pytest.mark.django_db
@pytest.mark.parametrize('query', ['order_by=operation', 'page=not-an-integer', 'page_size=not-an-integer'])
def test_activity_stream_invalid_optimization_inputs_fall_back(get, org_admin, query, settings):
    """Unsupported pagination inputs use the normal Activity Stream queryset."""
    settings.ACTIVITY_STREAM_ENABLED = True
    response = get(f'{reverse("api:activity_stream_list")}?{query}', org_admin)

    assert response.status_code in (200, 400, 404)


@pytest.mark.django_db
def test_activity_stream_mixed_serialization_query_count(get, job_factory, project, inventory, org_credential, org_admin, settings):
    """Mixed activity-stream serialization should not issue one query per row."""
    settings.ACTIVITY_STREAM_ENABLED = True
    job = job_factory()
    entry_ids = []

    events = [('job', job), ('project', project), ('inventory', inventory), ('credential', org_credential)] * 25
    for object_type, related_object in events:
        entry = ActivityStream.objects.create(
            operation='create',
            object1=object_type,
            object2='',
            actor=org_admin,
            changes='{}',
        )
        getattr(entry, object_type).add(related_object)
        entry_ids.append(entry.id)

    url = reverse('api:activity_stream_list')
    query_counts = []
    unified_job_query_counts = []
    for page_size in (1, 20, 100):
        with CaptureQueriesContext(connection) as queries:
            response = get(
                f'{url}?or__object1__in=job%2Cproject%2Cinventory%2Ccredential&or__object2__in=job%2Cproject%2Cinventory%2Ccredential&order_by=-id&page=1&page_size={page_size}',
                org_admin,
            )
        assert response.status_code == 200
        assert all(result['id'] in entry_ids for result in response.data['results'])
        query_counts.append(len(queries))
        unified_job_table = connection.ops.quote_name('main_unifiedjob').lower()
        unified_job_query_counts.append(sum(unified_job_table in query['sql'].lower() and 'activitystream' not in query['sql'].lower() for query in queries))

    assert query_counts[1] - query_counts[0] <= 5, query_counts
    assert query_counts[2] - query_counts[1] <= 5, query_counts
    assert max(unified_job_query_counts) <= 2, unified_job_query_counts


@pytest.mark.django_db
def test_activity_stream_unfiltered_mixed_serialization_query_count(
    get,
    admin,
    job_factory,
    project,
    inventory,
    org_credential,
    organization,
    org_admin,
    team,
    deploy_jobtemplate,
    host,
    workflow_job_template,
    instance,
    execution_environment,
    group,
    instance_group,
    inventory_source,
    settings,
):
    """Unfiltered pages cover the mixed association types seen in production."""
    settings.ACTIVITY_STREAM_ENABLED = True
    jobs = [job_factory() for _ in range(25)]
    schedule = Schedule.objects.create(rrule='DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1', unified_job_template=deploy_jobtemplate)
    related_objects = [
        ('organization', organization),
        ('user', org_admin),
        ('team', team),
        ('job_template', deploy_jobtemplate),
        ('host', host),
        ('job', None),
        ('project', project),
        ('inventory', inventory),
        ('workflow_job_template', workflow_job_template),
        ('instance', instance),
        ('credential', org_credential),
        ('execution_environment', execution_environment),
        ('group', group),
        ('instance_group', instance_group),
        ('inventory_source', inventory_source),
        ('schedule', schedule),
    ]
    entry_ids = []
    for index in range(len(jobs)):
        for object_type, related_object in related_objects:
            related_object = jobs[index] if object_type == 'job' else related_object
            entry = ActivityStream.objects.create(
                operation='create',
                object1=object_type,
                object2='',
                actor=org_admin,
                changes='{}',
            )
            getattr(entry, object_type).add(related_object)
            entry_ids.append(entry.id)
    ActivityStream.objects.create(operation='create', object1='setting', object2='', setting={'category': 'foo'})

    url = reverse('api:activity_stream_list')
    query_counts = []
    unified_job_query_counts = []
    for page_size in (20, 100):
        with CaptureQueriesContext(connection) as queries:
            response = get(f'{url}?order_by=-id&page=1&page_size={page_size}', admin)
        assert response.status_code == 200
        query_counts.append(len(queries))
        unified_job_table = connection.ops.quote_name('main_unifiedjob').lower()
        unified_job_query_counts.append(sum(unified_job_table in query['sql'].lower() and 'activitystream' not in query['sql'].lower() for query in queries))

    returned_types = {result['object1'] for result in response.data['results'] if result['id'] in entry_ids}
    assert {object_type for object_type, _ in related_objects} <= returned_types
    assert 'setting' in {result['object1'] for result in response.data['results']}
    assert query_counts[1] - query_counts[0] <= 20, query_counts
    assert max(unified_job_query_counts) <= 2, unified_job_query_counts


@pytest.mark.django_db
def test_activity_stream_access_includes_workflow_template_branches(org_admin, workflow_job_template, mocker, settings):
    """Workflow template visibility contributes its Activity Stream branches."""
    settings.ACTIVITY_STREAM_ENABLED = True
    mocker.patch.object(WorkflowJobTemplate, 'access_ids_qs', return_value=WorkflowJobTemplate.objects.filter(pk=workflow_job_template.pk))

    assert ActivityStreamAccess(org_admin).get_queryset().exists()


@pytest.mark.django_db
def test_activity_stream_limited_visibility_preserves_pages(get, org_admin, settings):
    """Per-branch top-N visibility limits must preserve paginated results."""
    settings.ACTIVITY_STREAM_ENABLED = True
    url = reverse('api:activity_stream_list')
    visible_ids = list(ActivityStreamAccess(org_admin).get_queryset().order_by('-id').values_list('id', flat=True))

    page_size = 3
    for page in range(1, (len(visible_ids) + page_size - 1) // page_size + 1):
        response = get(f'{url}?order_by=-id&page={page}&page_size={page_size}', org_admin)
        assert response.status_code == 200
        start = (page - 1) * page_size
        expected_ids = visible_ids[start : start + page_size]
        assert [result['id'] for result in response.data['results']] == expected_ids

    for page_size in (1, 20, 100):
        response = get(f'{url}?order_by=-id&page=1&page_size={page_size}', org_admin)
        assert response.status_code == 200
        assert [result['id'] for result in response.data['results']] == visible_ids[:page_size]


@pytest.mark.django_db
def test_activity_stream_filtered_windowed_pagination_preserves_count_and_pages(get, project, user, org_admin, settings):
    """Filtered pages rank matching visible rows and count all matching rows."""
    settings.ACTIVITY_STREAM_ENABLED = True
    marker = 'activity-stream-pagination-marker'
    entry_ids = []
    for _ in range(7):
        entry = ActivityStream.objects.create(
            operation='create',
            object1='project',
            object2='',
            actor=org_admin,
            changes='{"marker": "activity-stream-pagination-marker"}',
        )
        entry.project.add(project)
        entry_ids.append(entry.id)

    url = reverse('api:activity_stream_list')
    query = 'search={}&order_by=-id&page_size=3'.format(marker)
    original_ids = list(
        ActivityStreamAccess(org_admin)
        .get_queryset()
        .filter(changes__icontains=marker)
        .order_by('-id')
        .values_list('id', flat=True)
    )
    assert original_ids == entry_ids[::-1]

    pages = []
    for page in range(1, (len(original_ids) + 2) // 3 + 1):
        response = get(f'{url}?{query}&page={page}', org_admin)
        assert response.status_code == 200
        assert response.data['count'] == len(original_ids)
        start = (page - 1) * 3
        pages.extend(result['id'] for result in response.data['results'])
        assert [result['id'] for result in response.data['results']] == original_ids[start : start + 3]

    assert pages == original_ids
    assert response.data['next'] is None
    assert response.data['previous'] is not None

    no_access_user = user('activity-stream-no-access', False)
    no_access_page = get(f'{url}?{query}&page=1', no_access_user)
    assert no_access_page.status_code == 200
    assert no_access_page.data['count'] == 0
    assert no_access_page.data['results'] == []
    assert no_access_page.data['next'] is None
    assert no_access_page.data['previous'] is None


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
