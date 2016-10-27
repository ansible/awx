import pytest
import json

from awx.main.tasks import RunJob
from awx.main.models import Job


@pytest.fixture
def job(mocker):
    ret = mocker.MagicMock(**{
        'display_extra_vars.return_value': '{\"secret_key\": \"$encrypted$\"}',
        'extra_vars_dict': {"secret_key": "my_password"},
        'pk': 1, 'job_template.pk': 1, 'job_template.name': '',
        'created_by.pk': 1, 'created_by.username': 'admin',
        'launch_type': 'manual'})
    ret.project = mocker.MagicMock(scm_revision='asdf1234')
    return ret

@pytest.mark.survey
def test_job_survey_password_redaction():
    """Tests the Job model's funciton to redact passwords from
    extra_vars - used when displaying job information"""
    job = Job(
        name="test-job-with-passwords",
        extra_vars=json.dumps({
            'submitter_email': 'foobar@redhat.com',
            'secret_key': '6kQngg3h8lgiSTvIEb21',
            'SSN': '123-45-6789'}),
        survey_passwords={
            'secret_key': '$encrypted$',
            'SSN': '$encrypted$'})
    assert json.loads(job.display_extra_vars()) == {
        'submitter_email': 'foobar@redhat.com',
        'secret_key': '$encrypted$',
        'SSN': '$encrypted$'}

@pytest.mark.survey
def test_survey_passwords_not_in_extra_vars():
    """Tests that survey passwords not included in extra_vars are
    not included when displaying job information"""
    job = Job(
        name="test-survey-not-in",
        extra_vars=json.dumps({
            'submitter_email': 'foobar@redhat.com'}),
        survey_passwords={
            'secret_key': '$encrypted$',
            'SSN': '$encrypted$'})
    assert json.loads(job.display_extra_vars()) == {
        'submitter_email': 'foobar@redhat.com',
    }

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
