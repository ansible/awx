import mock
import pytest
import json

from awx.main.utils import timestamp_apiformat
from django.core.urlresolvers import reverse
from django.utils import timezone

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
    print response.data


