
# Python
import pytest

from awx.main.tests.factories import (
    create_organization,
    create_job_template,
    create_notification_template,
    create_survey_spec,
    create_workflow_job_template,
)

@pytest.fixture
def job_template_factory():
    return create_job_template

@pytest.fixture
def organization_factory():
    return create_organization

@pytest.fixture
def notification_template_factory():
    return create_notification_template

@pytest.fixture
def survey_spec_factory():
    return create_survey_spec

@pytest.fixture
def job_template_with_survey_passwords_factory(job_template_factory):
    def rf(persisted):
        "Returns job with linked JT survey with password survey questions"
        objects = job_template_factory('jt', organization='org1', survey=[
            {'variable': 'submitter_email', 'type': 'text', 'default': 'foobar@redhat.com'},
            {'variable': 'secret_key', 'default': '6kQngg3h8lgiSTvIEb21', 'type': 'password'},
            {'variable': 'SSN', 'type': 'password'}], persisted=persisted)
        return objects.job_template
    return rf

@pytest.fixture
def job_with_secret_key_unit(job_with_secret_key_factory):
    return job_with_secret_key_factory(persisted=False)

@pytest.fixture
def workflow_job_template_factory():
    return create_workflow_job_template

@pytest.fixture
def get_ssh_version(mocker):
    return mocker.patch('awx.main.tasks.get_ssh_version', return_value='OpenSSH_6.9p1, LibreSSL 2.1.8')

@pytest.fixture
def job_template_with_survey_passwords_unit(job_template_with_survey_passwords_factory):
    return job_template_with_survey_passwords_factory(persisted=False)
