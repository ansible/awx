import pytest

from django.db import connection
from django.test.utils import CaptureQueriesContext

from awx.api.versioning import reverse

from awx.main.models import Organization, Inventory, Host, Job, JobHostSummary


def _build_inventory(name, host_count, job_count):
    org = Organization.objects.create(name='org-%s' % name)
    inventory = Inventory.objects.create(name='inv-%s' % name, organization=org)
    jobs = [Job.objects.create(name='job-%s-%d' % (name, i), inventory=inventory) for i in range(job_count)]
    for i in range(host_count):
        host = Host.objects.create(name='host-%s-%d' % (name, i), inventory=inventory)
        for job in jobs:
            JobHostSummary.objects.create(job=job, host=host, host_name=host.name)
    return inventory, jobs


def _summary_queries(captured):
    return [query for query in captured if 'main_jobhostsummary' in query['sql']]


@pytest.mark.django_db
def test_recent_jobs_query_count_is_independent_of_page_size(get, admin):
    """The host list must not read job host summaries once per row."""
    counts = {}
    for host_count in (2, 10):
        inventory, _ = _build_inventory('n%d' % host_count, host_count, job_count=8)
        url = '%s?inventory=%d&page_size=200' % (reverse('api:host_list'), inventory.pk)
        get(url, admin)  # warm anything cached outside the queries we care about
        with CaptureQueriesContext(connection) as ctx:
            response = get(url, admin)
        assert len(response.data['results']) == host_count
        counts[host_count] = len(_summary_queries(ctx.captured_queries))

    assert counts[2] == counts[10], 'job host summary queries scale with the number of hosts: %r' % counts


@pytest.mark.django_db
def test_recent_jobs_returns_the_five_newest_per_host(get, admin):
    inventory, jobs = _build_inventory('newest', host_count=3, job_count=8)
    url = '%s?inventory=%d&page_size=200' % (reverse('api:host_list'), inventory.pk)

    response = get(url, admin)

    newest = [job.id for job in sorted(jobs, key=lambda job: job.id, reverse=True)[:5]]
    for result in response.data['results']:
        recent = result['summary_fields']['recent_jobs']
        assert [entry['id'] for entry in recent] == newest


@pytest.mark.django_db
def test_recent_jobs_on_host_detail(get, admin):
    """The detail view serializes a single host, so it keeps the per-object path."""
    inventory, jobs = _build_inventory('detail', host_count=1, job_count=8)
    host = inventory.hosts.first()

    response = get(reverse('api:host_detail', kwargs={'pk': host.pk}), admin)

    newest = [job.id for job in sorted(jobs, key=lambda job: job.id, reverse=True)[:5]]
    assert [entry['id'] for entry in response.data['summary_fields']['recent_jobs']] == newest


@pytest.mark.django_db
def test_recent_jobs_empty_for_hosts_that_never_ran(get, admin):
    org = Organization.objects.create(name='org-never')
    inventory = Inventory.objects.create(name='inv-never', organization=org)
    Host.objects.create(name='host-never', inventory=inventory)

    response = get('%s?inventory=%d' % (reverse('api:host_list'), inventory.pk), admin)

    assert response.data['results'][0]['summary_fields']['recent_jobs'] == []
