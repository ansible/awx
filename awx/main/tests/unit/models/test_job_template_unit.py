import pytest
import json

from awx.main.tests.factories import create_job_template
from awx.main.models.jobs import Job


@pytest.fixture
def job_template_sensitive_data():
    return create_job_template(
        'jt', project='prj', persisted=False,
        survey=['submitter_email',
                {'variable': 'secret_key', 'type': 'password'},
                {'variable': 'SSN', 'type': 'password'}]
    ).job_template

def test_missing_project_error():
    objects = create_job_template(
        'missing-project-jt',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False)
    obj = objects.job_template
    assert 'project' in obj.resources_needed_to_start
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'project' in validation_errors

def test_inventory_credential_need_to_start():
    objects = create_job_template(
        'job-template-few-resources',
        project='project1',
        persisted=False)
    obj = objects.job_template
    assert 'inventory' in obj.resources_needed_to_start
    assert 'credential' in obj.resources_needed_to_start

def test_inventory_credential_contradictions():
    objects = create_job_template(
        'job-template-paradox',
        project='project1',
        persisted=False)
    obj = objects.job_template
    obj.ask_inventory_on_launch = False
    obj.ask_credential_on_launch = False
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'inventory' in validation_errors
    assert 'credential' in validation_errors

@pytest.mark.survey
def test_survey_password_list(job_template_sensitive_data):
    """Verify the output of the survey_passwords function
    gives a list of survey variable names which are passwords"""
    assert job_template_sensitive_data.survey_password_variables() == ['secret_key', 'SSN']

@pytest.mark.survey
def test_job_redacted_extra_vars(job_template_sensitive_data):
    """Verify that this method redacts vars marked as passwords in a survey"""
    job_obj = Job(
        job_type="run", job_template=job_template_sensitive_data,
        extra_vars=json.dumps({'submitter_email': 'foobar@redhat.com',
                               'secret_key': 'b86hpFChM2XSb40Zld9x',
                               'SSN': '123-45-6789'}))
    assert json.loads(job_obj.display_extra_vars()) == {
        'submitter_email': 'foobar@redhat.com',
        'secret_key': '$encrypted$',
        'SSN': '$encrypted$'
    }
