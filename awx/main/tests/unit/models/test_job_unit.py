import pytest
import json

from awx.main.tasks import RunJob


@pytest.fixture
def job(mocker):
    return mocker.MagicMock(**{
        'display_extra_vars.return_value': '{\"secret_key\": \"$encrypted$\"}',
        'extra_vars_dict': {"secret_key": "my_password"},
        'pk': 1, 'job_template.pk': 1, 'job_template.name': '',
        'created_by.pk': 1, 'created_by.username': 'admin',
        'launch_type': 'manual'})

@pytest.mark.survey
def test_job_redacted_extra_vars(job_with_secret_key_unit):
    """Verify that this method redacts vars marked as passwords in a survey"""
    assert json.loads(job_with_secret_key_unit.display_extra_vars()) == {
        'submitter_email': 'foobar@redhat.com',
        'secret_key': '$encrypted$',
        'SSN': '$encrypted$'}

def test_job_safe_args_redacted_passwords(job):
    """Verify that safe_args hides passwords in the job extra_vars"""
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    safe_args = run_job.build_safe_args(job, **kwargs)
    ev_index = safe_args.index('-e') + 1
    extra_vars = json.loads(safe_args[ev_index])
    assert extra_vars['secret_key'] == '$encrypted$'

def test_job_args_unredacted_passwords(job):
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    args = run_job.build_args(job, **kwargs)
    ev_index = args.index('-e') + 1
    extra_vars = json.loads(args[ev_index])
    assert extra_vars['secret_key'] == 'my_password'
