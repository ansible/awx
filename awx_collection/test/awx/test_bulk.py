from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import WorkflowJob


@pytest.mark.django_db
def test_bulk_job_launch(run_module, admin_user, job_template):
    jobs = [dict(unified_job_template=job_template.id)]
    run_module(
        'bulk_job_launch',
        {
            'name': "foo-bulk-job",
            'jobs': jobs,
            'extra_vars': {'animal': 'owl'},
            'limit': 'foo',
            'wait': False,
        },
        admin_user,
    )

    bulk_job = WorkflowJob.objects.get(name="foo-bulk-job")
    assert bulk_job.extra_vars == '{"animal": "owl"}'
    assert bulk_job.limit == "foo"


@pytest.mark.django_db
def test_bulk_host_create(run_module, admin_user, inventory):
    hosts = [dict(name="127.0.0.1"), dict(name="foo.dns.org")]
    run_module(
        'bulk_host_create',
        {
            'inventory': inventory.name,
            'hosts': hosts,
        },
        admin_user,
    )
    resp_hosts = inventory.hosts.all().values_list('name', flat=True)
    for h in hosts:
        assert h['name'] in resp_hosts
