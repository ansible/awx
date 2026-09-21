import pytest

from django.utils.encoding import smart_str

from awx.api.versioning import reverse
from awx.main.models import UnifiedJob, ProjectUpdate, InventoryUpdate
from awx.main.tests.URI import URI
from awx.main.constants import ACTIVE_STATES

TEST_STATES = list(ACTIVE_STATES)
TEST_STATES.remove('new')


TEST_STDOUTS = []
uri = URI(scheme="https", username="Dhh3U47nmC26xk9PKscV", password="PXPfWW8YzYrgS@E5NbQ2H@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({'description': 'uri in a plain text document', 'uri': uri, 'text': 'hello world %s goodbye world' % uri, 'occurrences': 1})

uri = URI(scheme="https", username="applepie@@@", password="thatyouknow@@@@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append(
    {
        'description': 'uri appears twice in a multiline plain text document',
        'uri': uri,
        'text': 'hello world %s \n\nyoyo\n\nhello\n%s' % (uri, uri),
        'occurrences': 2,
    }
)


@pytest.fixture
def test_cases(project):
    ret = []
    for e in TEST_STDOUTS:
        pu = ProjectUpdate(project=project)
        pu.save()
        e['project'] = pu
        e['project'].result_stdout_text = e['text']
        e['project'].save()
        ret.append(e)
    return ret


@pytest.fixture
def negative_test_cases(job_factory):
    ret = []
    for e in TEST_STDOUTS:
        e['job'] = job_factory()
        e['job'].result_stdout_text = e['text']
        e['job'].save()
        ret.append(e)
    return ret


formats = [
    ('json', 'application/json'),
    ('ansi', 'text/plain'),
    ('txt', 'text/plain'),
    ('html', 'text/html'),
]


@pytest.mark.parametrize("format,content_type", formats)
@pytest.mark.django_db
def test_project_update_redaction_enabled(get, format, content_type, test_cases, admin):
    for test_data in test_cases:
        job = test_data['project']
        response = get(reverse("api:project_update_stdout", kwargs={'pk': job.pk}) + "?format=" + format, user=admin, expect=200, accept=content_type)
        assert content_type in response['CONTENT-TYPE']
        assert response.data is not None
        content = response.data['content'] if format == 'json' else response.data
        content = smart_str(content)
        assert test_data['uri'].username not in content
        assert test_data['uri'].password not in content
        assert content.count(test_data['uri'].host) == test_data['occurrences']


@pytest.mark.parametrize("format,content_type", formats)
@pytest.mark.django_db
def test_job_redaction_disabled(get, format, content_type, negative_test_cases, admin):
    for test_data in negative_test_cases:
        job = test_data['job']
        response = get(reverse("api:job_stdout", kwargs={'pk': job.pk}) + "?format=" + format, user=admin, expect=200, format=format)
        content = response.data['content'] if format == 'json' else response.data
        content = smart_str(content)
        assert response.data is not None
        assert test_data['uri'].username in content
        assert test_data['uri'].password in content


@pytest.mark.django_db
def test_options_fields_choices(instance, options, user):
    url = reverse('api:unified_job_list')
    response = options(url, None, user('admin', True))

    assert 'launch_type' in response.data['actions']['GET']
    assert 'choice' == response.data['actions']['GET']['launch_type']['type']
    assert UnifiedJob.LAUNCH_TYPE_CHOICES == response.data['actions']['GET']['launch_type']['choices']
    assert 'choice' == response.data['actions']['GET']['status']['type']
    assert UnifiedJob.STATUS_CHOICES == response.data['actions']['GET']['status']['choices']


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_job_in_active_state(job_factory, delete, admin, status):
    j = job_factory(initial_state=status)
    url = reverse('api:job_detail', kwargs={'pk': j.pk})
    delete(url, None, admin, expect=403)


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_project_update_in_active_state(project, delete, admin, status):
    p = ProjectUpdate(project=project, status=status)
    p.save()
    url = reverse('api:project_update_detail', kwargs={'pk': p.pk})
    delete(url, None, admin, expect=403)


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_inventory_update_in_active_state(inventory_source, delete, admin, status):
    i = InventoryUpdate.objects.create(inventory_source=inventory_source, status=status, source=inventory_source.source)
    url = reverse('api:inventory_update_detail', kwargs={'pk': i.pk})
    delete(url, None, admin, expect=403)


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_workflow_job_in_active_state(workflow_job_factory, delete, admin, status):
    wj = workflow_job_factory(initial_state=status)
    url = reverse('api:workflow_job_detail', kwargs={'pk': wj.pk})
    delete(url, None, admin, expect=403)


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_system_job_in_active_state(system_job_factory, delete, admin, status):
    sys_j = system_job_factory(initial_state=status)
    url = reverse('api:system_job_detail', kwargs={'pk': sys_j.pk})
    delete(url, None, admin, expect=403)


@pytest.mark.parametrize("status", list(TEST_STATES))
@pytest.mark.django_db
def test_delete_ad_hoc_command_in_active_state(ad_hoc_command_factory, delete, admin, status):
    adhoc = ad_hoc_command_factory(initial_state=status)
    url = reverse('api:ad_hoc_command_detail', kwargs={'pk': adhoc.pk})
    delete(url, None, admin, expect=403)


@pytest.fixture
def job_with_heavy_fields(job_factory):
    job = job_factory()
    job.extra_vars = '{"some_var": "some_value"}'
    job.artifacts = {"some_artifact": "some_value"}
    job.save()
    return job


def _job_result(response, job_id):
    for row in response.data['results']:
        if row['id'] == job_id:
            return row
    raise AssertionError('job {} not found in {}'.format(job_id, [r['id'] for r in response.data['results']]))


@pytest.mark.django_db
def test_unified_jobs_list_includes_heavy_fields_by_default(get, admin, job_with_heavy_fields):
    response = get(reverse('api:unified_job_list') + '?id={}'.format(job_with_heavy_fields.id), admin, expect=200)
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' in row
    assert 'extra_vars' in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_artifacts(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:unified_job_list') + '?id={}&exclude=artifacts'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' not in row
    assert 'extra_vars' in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_extra_vars(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:unified_job_list') + '?id={}&exclude=extra_vars'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'extra_vars' not in row
    assert 'artifacts' in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_both(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:unified_job_list') + '?id={}&exclude=artifacts,extra_vars'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' not in row
    assert 'extra_vars' not in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_tolerates_whitespace(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:unified_job_list') + '?id={}&exclude=%20artifacts%20,%20extra_vars%20'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' not in row
    assert 'extra_vars' not in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_ignores_unknown(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:unified_job_list') + '?id={}&exclude=does_not_exist'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' in row
    assert 'extra_vars' in row


@pytest.mark.django_db
def test_unified_jobs_list_exclude_does_not_honor_always_stripped(get, admin, job_with_heavy_fields):
    # Always-stripped fields like event_processing_finished, job_args, result_traceback
    # must remain stripped regardless of the ?exclude= param — they cannot be re-included.
    response = get(
        reverse('api:unified_job_list') + '?id={}'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'event_processing_finished' not in row
    assert 'job_args' not in row
    assert 'result_traceback' not in row


@pytest.mark.django_db
def test_jobs_list_includes_heavy_fields_by_default(get, admin, job_with_heavy_fields):
    response = get(reverse('api:job_list') + '?id={}'.format(job_with_heavy_fields.id), admin, expect=200)
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'artifacts' in row
    assert 'extra_vars' in row


@pytest.mark.django_db
def test_jobs_list_exclude_extra_vars(get, admin, job_with_heavy_fields):
    response = get(
        reverse('api:job_list') + '?id={}&exclude=extra_vars'.format(job_with_heavy_fields.id),
        admin,
        expect=200,
    )
    row = _job_result(response, job_with_heavy_fields.id)
    assert 'extra_vars' not in row
    assert 'artifacts' in row
