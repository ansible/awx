import mock
import pytest
import json


from awx.api.versioning import reverse
from awx.main.models.jobs import JobTemplate, Job
from awx.main.models.activity_stream import ActivityStream
from awx.conf.license import LicenseForbids
from awx.main.access import JobTemplateAccess


def mock_no_surveys(self, add_host=False, feature=None, check_expiration=True):
    if feature == 'surveys':
        raise LicenseForbids("Feature %s is not enabled in the active license." % feature)
    else:
        pass


@pytest.fixture
def job_template_with_survey(job_template_factory):
    objects = job_template_factory('jt', project='prj', survey='submitted_email')
    return objects.job_template


# Survey license-based denial tests
@mock.patch('awx.api.views.feature_enabled', lambda feature: False)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_view_denied(job_template_with_survey, get, admin_user):
    # TODO: Test non-enterprise license
    response = get(reverse('api:job_template_survey_spec',
                   kwargs={'pk': job_template_with_survey.id}), admin_user, expect=402)
    assert response.data['detail'] == 'Your license does not allow adding surveys.'


@mock.patch('awx.main.access.BaseAccess.check_license', mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_deny_enabling_survey(deploy_jobtemplate, patch, admin_user):
    response = patch(url=deploy_jobtemplate.get_absolute_url(),
                     data=dict(survey_enabled=True), user=admin_user, expect=402)
    assert response.data['detail'] == 'Feature surveys is not enabled in the active license.'


@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_job_start_blocked_without_survey_license(job_template_with_survey, admin_user):
    """Check that user can't start a job with surveys without a survey license."""
    access = JobTemplateAccess(admin_user)
    with pytest.raises(LicenseForbids):
        access.can_start(job_template_with_survey)


@mock.patch('awx.main.access.BaseAccess.check_license', mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_deny_creating_with_survey(project, post, admin_user):
    response = post(
        url=reverse('api:job_template_list'),
        data=dict(
            name = 'JT with survey',
            job_type = 'run',
            project = project.pk,
            playbook = 'helloworld.yml',
            ask_credential_on_launch = True,
            ask_inventory_on_launch = True,
            survey_enabled = True),
        user=admin_user, expect=402)
    assert response.data['detail'] == 'Feature surveys is not enabled in the active license.'


# Test normal operations with survey license work
@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_view_allowed(deploy_jobtemplate, get, admin_user):
    get(reverse('api:job_template_survey_spec', kwargs={'pk': deploy_jobtemplate.id}),
        admin_user, expect=200)


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_sucessful_creation(survey_spec_factory, job_template, post, admin_user):
    survey_input_data = survey_spec_factory('new_question')
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=survey_input_data, user=admin_user, expect=200)
    updated_jt = JobTemplate.objects.get(pk=job_template.pk)
    assert updated_jt.survey_spec == survey_input_data


# Tests related to survey content validation
@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_non_dict_error(deploy_jobtemplate, post, admin_user):
    """When a question doesn't follow the standard format, verify error thrown."""
    response = post(
        url=reverse('api:job_template_survey_spec', kwargs={'pk': deploy_jobtemplate.id}),
        data={
            "description": "Email of the submitter",
            "spec": ["What is your email?"], "name": "Email survey"
        },
        user=admin_user,
        expect=400
    )
    assert response.data['error'] == "Survey question 0 is not a json object."


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_dual_names_error(survey_spec_factory, deploy_jobtemplate, post, user):
    response = post(
        url=reverse('api:job_template_survey_spec', kwargs={'pk': deploy_jobtemplate.id}),
        data=survey_spec_factory(['submitter_email', 'submitter_email']),
        user=user('admin', True),
        expect=400
    )
    assert response.data['error'] == "'variable' 'submitter_email' duplicated in survey question 1."


# Test actions that should be allowed with non-survey license
@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_disable_survey_access_without_license(job_template_with_survey, admin_user):
    """Assure that user can disable a JT survey after downgrading license."""
    access = JobTemplateAccess(admin_user)
    assert access.can_change(job_template_with_survey, dict(survey_enabled=False))


@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_delete_survey_access_without_license(job_template_with_survey, admin_user):
    """Assure that access.py allows deleting surveys after downgrading license."""
    access = JobTemplateAccess(admin_user)
    assert access.can_change(job_template_with_survey, dict(survey_spec=None))
    assert access.can_change(job_template_with_survey, dict(survey_spec={}))


@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_job_start_allowed_with_survey_spec(job_template_factory, admin_user):
    """After user downgrades survey license and disables survey on the JT,
    check that jobs still launch even if the survey_spec data persists."""
    objects = job_template_factory('jt', project='prj', survey='submitter_email')
    obj = objects.job_template
    obj.survey_enabled = False
    obj.save()
    access = JobTemplateAccess(admin_user)
    assert access.can_start(job_template_with_survey, {})


@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_job_template_delete_access_with_survey(job_template_with_survey, admin_user):
    """The survey_spec view relies on JT `can_delete` to determine permission
    to delete the survey. This checks that system admins can delete the survey on a JT."""
    access = JobTemplateAccess(admin_user)
    assert access.can_delete(job_template_with_survey)


@mock.patch('awx.api.views.feature_enabled', lambda feature: False)
@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@pytest.mark.django_db
@pytest.mark.survey
def test_delete_survey_spec_without_license(job_template_with_survey, delete, admin_user):
    """Functional delete test through the survey_spec view."""
    delete(reverse('api:job_template_survey_spec', kwargs={'pk': job_template_with_survey.pk}),
           admin_user, expect=200)
    new_jt = JobTemplate.objects.get(pk=job_template_with_survey.pk)
    assert new_jt.survey_spec == {}


@mock.patch('awx.main.access.BaseAccess.check_license', lambda self, **kwargs: True)
@mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job',
            lambda self, extra_vars: mock.MagicMock(spec=Job, id=968))
@mock.patch('awx.api.serializers.JobSerializer.to_representation', lambda self, obj: {})
@pytest.mark.django_db
@pytest.mark.survey
def test_launch_survey_enabled_but_no_survey_spec(job_template_factory, post, admin_user):
    """False-ish values for survey_spec are interpreted as a survey with 0 questions."""
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred')
    obj = objects.job_template
    obj.survey_enabled = True
    obj.save()
    response = post(reverse('api:job_template_launch', kwargs={'pk':obj.pk}),
                    dict(extra_vars=dict(survey_var=7)), admin_user, expect=201)
    assert 'survey_var' in response.data['ignored_fields']['extra_vars']


@mock.patch('awx.main.access.BaseAccess.check_license', new=mock_no_surveys)
@mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job',
            lambda self: mock.MagicMock(spec=Job, id=968))
@mock.patch('awx.api.serializers.JobSerializer.to_representation', lambda self, obj: {})
@pytest.mark.django_db
@pytest.mark.survey
def test_launch_with_non_empty_survey_spec_no_license(job_template_factory, post, admin_user):
    """Assure jobs can still be launched from JTs with a survey_spec
    when the survey is diabled."""
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred',
                                   survey='survey_var')
    obj = objects.job_template
    obj.survey_enabled = False
    obj.save()
    post(reverse('api:job_template_launch', kwargs={'pk': obj.pk}), {}, admin_user, expect=201)


@pytest.mark.django_db
@pytest.mark.survey
def test_redact_survey_passwords_in_activity_stream(job_template_with_survey_passwords):
    job_template_with_survey_passwords.create_unified_job()
    AS_record = ActivityStream.objects.filter(object1='job').all()[0]
    changes_dict = json.loads(AS_record.changes)
    extra_vars = json.loads(changes_dict['extra_vars'])
    assert extra_vars['secret_key'] == '$encrypted$'
