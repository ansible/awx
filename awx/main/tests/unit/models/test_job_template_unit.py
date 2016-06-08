import pytest
import json


def test_missing_project_error(job_template_factory):
    objects = job_template_factory(
        'missing-project-jt',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False)
    obj = objects.job_template
    assert 'project' in obj.resources_needed_to_start
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'project' in validation_errors

def test_inventory_credential_need_to_start(job_template_factory):
    objects = job_template_factory(
        'job-template-few-resources',
        project='project1',
        persisted=False)
    obj = objects.job_template
    assert 'inventory' in obj.resources_needed_to_start
    assert 'credential' in obj.resources_needed_to_start

def test_inventory_credential_contradictions(job_template_factory):
    objects = job_template_factory(
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
def test_survey_password_list(job_with_secret_key_unit):
    """Verify that survey_password_variables method gives a list of survey passwords"""
    assert job_with_secret_key_unit.job_template.survey_password_variables() == ['secret_key', 'SSN']

@pytest.mark.survey
def test_job_redacted_extra_vars(job_with_secret_key_unit):
    """Verify that this method redacts vars marked as passwords in a survey"""
    assert json.loads(job_with_secret_key_unit.display_extra_vars()) == {
        'submitter_email': 'foobar@redhat.com',
        'secret_key': '$encrypted$',
        'SSN': '$encrypted$'}
