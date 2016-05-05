import mock
import pytest

from django.core.urlresolvers import reverse
from awx.main.models.jobs import JobTemplate

def mock_feature_enabled(feature, bypass_database=None):
    return True

def mock_feature_disabled(feature, bypass_database=None):
    return False

@pytest.fixture
def survey_jobtemplate(project, inventory, credential):
    return JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=inventory,
        credential=credential,
        name='deploy-job-template'
    )

@mock.patch('awx.api.views.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_view_denied(deploy_jobtemplate, get, user):
    spec_url = reverse('api:job_template_survey_spec', args=(deploy_jobtemplate.id,))
    response = get(spec_url, user('admin', True))

    assert response.status_code == 402
    assert response.data['detail'] == 'Your license does not allow adding surveys.'

@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_view_allowed(deploy_jobtemplate, get, user):
    spec_url = reverse('api:job_template_survey_spec', args=(deploy_jobtemplate.id,))
    response = get(spec_url, user('admin', True))

    assert response.status_code == 200

@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_sucessful_creation(deploy_jobtemplate, post, user):
    spec_url = reverse('api:job_template_survey_spec', args=(deploy_jobtemplate.id,))
    response = post(
        url=spec_url,
        data={
            "description": "Email of the submitter",
            "spec": [{
                "variable": "submitter_email",
                "question_name": "Enter your email",
                "type": "text",
                "required": False
            }],
            "name": "Email survey"
        },
        user=user('admin', True))

    assert response.status_code == 200

@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_non_dict_error(deploy_jobtemplate, post, user):
    spec_url = reverse('api:job_template_survey_spec', args=(deploy_jobtemplate.id,))
    response = post(
        url=spec_url,
        data={"description": "Email of the submitter",
              "spec": ["What is your email?"], "name": "Email survey"},
        user=user('admin', True))

    assert response.status_code == 400
    assert response.data['error'] == "survey element 0 is not a json object"

@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_dual_names_error(deploy_jobtemplate, post, user):
    spec_url = reverse('api:job_template_survey_spec', args=(deploy_jobtemplate.id,))
    response = post(
        url=spec_url,
        data={
            "description": "Email of the submitter",
            "spec": [{
                "variable": "submitter_email",
                "question_name": "Enter your email",
                "type": "text",
                "required": False
            }, {
                "variable": "submitter_email",
                "question_name": "Same variable as last question",
                "type": "integer",
                "required": False
            }],
            "name": "Email survey"
        },
        user=user('admin', True))

    assert response.status_code == 400
    assert response.data['error'] == "'variable' name 'submitter_email' duplicated in survey element 1"
