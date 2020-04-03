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
TEST_STDOUTS.append({
    'description': 'uri in a plain text document',
    'uri' : uri,
    'text' : 'hello world %s goodbye world' % uri,
    'occurrences' : 1
})

uri = URI(scheme="https", username="applepie@@@", password="thatyouknow@@@@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({
    'description': 'uri appears twice in a multiline plain text document',
    'uri' : uri,
    'text' : 'hello world %s \n\nyoyo\n\nhello\n%s' % (uri, uri),
    'occurrences' : 2
})



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
    i = InventoryUpdate.objects.create(
        inventory_source=inventory_source,
        status=status,
        source=inventory_source.source
    )
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
