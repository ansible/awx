from unittest import mock
import pytest
import json


from awx.api.versioning import reverse
from awx.main.models.jobs import JobTemplate, Job
from awx.main.models.activity_stream import ActivityStream
from awx.conf.license import LicenseForbids
from awx.main.access import JobTemplateAccess
from awx.main.utils.common import get_type_for_model


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
@pytest.mark.parametrize("role_field,expected_status_code", [
    ('admin_role', 200),
    ('execute_role', 403),
    ('read_role', 403)
])
def test_survey_edit_access(job_template, workflow_job_template, survey_spec_factory, rando, post,
                            role_field, expected_status_code):
    survey_input_data = survey_spec_factory('new_question')
    for template in (job_template, workflow_job_template):
        role = getattr(template, role_field)
        role.members.add(rando)
        post(reverse('api:{}_survey_spec'.format(get_type_for_model(template.__class__)),
             kwargs={'pk': template.id}),
             user=rando, data=survey_input_data, expect=expected_status_code)


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


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.parametrize('with_default', [True, False])
@pytest.mark.parametrize('value, status', [
    ('SUPERSECRET', 201),
    (['some', 'invalid', 'list'], 400),
    ({'some-invalid': 'dict'}, 400),
    (False, 400)
])
def test_survey_spec_passwords_are_encrypted_on_launch(job_template_factory, post, admin_user, with_default, value, status):
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred')
    job_template = objects.job_template
    job_template.survey_enabled = True
    job_template.save()
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': True,
            'variable': 'secret_value',
            'type': 'password'
        }],
        'name': 'my survey'
    }
    if with_default:
        input_data['spec'][0]['default'] = 'some-default'
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)
    resp = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                dict(extra_vars=dict(secret_value=value)), admin_user, expect=status)

    if status == 201:
        job = Job.objects.get(pk=resp.data['id'])
        assert json.loads(job.extra_vars)['secret_value'].startswith('$encrypted$')
        assert json.loads(job.decrypted_extra_vars()) == {
            'secret_value': value
        }
    else:
        assert "for 'secret_value' expected to be a string." in json.dumps(resp.data)


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
def test_survey_spec_passwords_with_empty_default(job_template_factory, post, admin_user):
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred')
    job_template = objects.job_template
    job_template.survey_enabled = True
    job_template.save()
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': False,
            'variable': 'secret_value',
            'type': 'password',
            'default': ''
        }],
        'name': 'my survey'
    }
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)

    resp = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                {}, admin_user, expect=201)
    job = Job.objects.get(pk=resp.data['id'])
    assert json.loads(job.extra_vars)['secret_value'] == ''
    assert json.loads(job.decrypted_extra_vars()) == {
        'secret_value': ''
    }


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.parametrize('default, launch_value, expected_extra_vars, status', [
    ['', '$encrypted$', {'secret_value': ''}, 201],
    ['', 'y', {'secret_value': 'y'}, 201],
    ['', 'y' * 100, None, 400],
    [None, '$encrypted$', {}, 201],
    [None, 'y', {'secret_value': 'y'}, 201],
    [None, 'y' * 100, {}, 400],
    ['x', '$encrypted$', {'secret_value': 'x'}, 201],
    ['x', 'y', {'secret_value': 'y'}, 201],
    ['x', 'y' * 100, {}, 400],
    ['x' * 100, '$encrypted$', {}, 201],
    ['x' * 100, 'y', {'secret_value': 'y'}, 201],
    ['x' * 100, 'y' * 100, {}, 400],
])
def test_survey_spec_passwords_with_default_optional(job_template_factory, post, admin_user,
                                                     default, launch_value,
                                                     expected_extra_vars, status):
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred')
    job_template = objects.job_template
    job_template.survey_enabled = True
    job_template.save()
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': False,
            'variable': 'secret_value',
            'type': 'password',
            'max': 3
        }],
        'name': 'my survey'
    }
    if default is not None:
        input_data['spec'][0]['default'] = default
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)

    resp = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                data={'extra_vars': {'secret_value': launch_value}}, user=admin_user, expect=status)

    if status == 201:
        job = Job.objects.get(pk=resp.data['job'])
        assert json.loads(job.decrypted_extra_vars()) == expected_extra_vars
        if default:
            assert default not in json.loads(job.extra_vars).values()
        assert launch_value not in json.loads(job.extra_vars).values()


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.parametrize('default, launch_value, expected_extra_vars, status', [
    ['', '$encrypted$', {'secret_value': ''}, 201],
    [None, '$encrypted$', {}, 400],
    [None, 'y', {'secret_value': 'y'}, 201],
])
def test_survey_spec_passwords_with_default_required(job_template_factory, post, admin_user,
                                                     default, launch_value,
                                                     expected_extra_vars, status):
    objects = job_template_factory('jt', organization='org1', project='prj',
                                   inventory='inv', credential='cred')
    job_template = objects.job_template
    job_template.survey_enabled = True
    job_template.save()
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': True,
            'variable': 'secret_value',
            'type': 'password',
            'max': 3
        }],
        'name': 'my survey'
    }
    if default is not None:
        input_data['spec'][0]['default'] = default
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)

    resp = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                data={'extra_vars': {'secret_value': launch_value}}, user=admin_user, expect=status)

    if status == 201:
        job = Job.objects.get(pk=resp.data['job'])
        assert json.loads(job.decrypted_extra_vars()) == expected_extra_vars
        if default:
            assert default not in json.loads(job.extra_vars).values()
        assert launch_value not in json.loads(job.extra_vars).values()


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
@pytest.mark.parametrize('default, status', [
    ('SUPERSECRET', 200),
    ({'some-invalid': 'dict'}, 400),
])
def test_survey_spec_default_passwords_are_encrypted(job_template, post, admin_user, default, status):
    job_template.survey_enabled = True
    job_template.save()
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': True,
            'variable': 'secret_value',
            'default': default,
            'type': 'password'
        }],
        'name': 'my survey'
    }
    resp = post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
                data=input_data, user=admin_user, expect=status)

    if status == 200:
        updated_jt = JobTemplate.objects.get(pk=job_template.pk)
        assert updated_jt.survey_spec['spec'][0]['default'].startswith('$encrypted$')

        job = updated_jt.create_unified_job()
        assert json.loads(job.extra_vars)['secret_value'].startswith('$encrypted$')
        assert json.loads(job.decrypted_extra_vars()) == {
            'secret_value': default
        }
    else:
        assert "expected to be string." in str(resp.data)


@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
@pytest.mark.django_db
def test_survey_spec_default_passwords_encrypted_on_update(job_template, post, put, admin_user):
    input_data = {
        'description': 'A survey',
        'spec': [{
            'index': 0,
            'question_name': 'What is your password?',
            'required': True,
            'variable': 'secret_value',
            'default': 'SUPERSECRET',
            'type': 'password'
        }],
        'name': 'my survey'
    }
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)
    updated_jt = JobTemplate.objects.get(pk=job_template.pk)

    # simulate a survey field edit where we're not changing the default value
    input_data['spec'][0]['default'] = '$encrypted$'
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=input_data, user=admin_user, expect=200)
    assert updated_jt.survey_spec == JobTemplate.objects.get(pk=job_template.pk).survey_spec


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
            lambda self, **kwargs: mock.MagicMock(spec=Job, id=968))
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
