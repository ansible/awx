import pytest
import json

from awx.main.models.jobs import Job
from awx.main.tasks import RunJob

from awx.main.tests.factories import create_job_template


@pytest.fixture
def job_with_secret_vars():
    job_template = create_job_template(
        'jt', persisted=False,
        survey=['submitter_email',
                {'variable': 'secret_key', 'type': 'password'}]
    ).job_template
    job = Job(id=1, job_template=job_template, extra_vars=json.dumps({
        'submitter_email': 'foobar@redhat.com',
        'secret_key': '6kQngg3h8lgiSTvIEb21'
    }))
    return job

def test_job_args_redacted_passwords(job_with_secret_vars):
    """Verify that safe_args hides passwords in the job extra_vars"""
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    safe_args = run_job.build_safe_args(job_with_secret_vars, **kwargs)
    ev_index = safe_args.index('-e') + 1
    extra_vars = json.loads(safe_args[ev_index])
    assert extra_vars['secret_key'] == '$encrypted$'
    assert extra_vars['submitter_email'] == 'foobar@redhat.com'

def test_job_args_unredacted_passwords(job_with_secret_vars):
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    safe_args = run_job.build_args(job_with_secret_vars, **kwargs)
    ev_index = safe_args.index('-e') + 1
    extra_vars = json.loads(safe_args[ev_index])
    assert extra_vars['secret_key'] == '6kQngg3h8lgiSTvIEb21'
    assert extra_vars['submitter_email'] == 'foobar@redhat.com'
