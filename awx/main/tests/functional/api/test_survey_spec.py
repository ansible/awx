from unittest import mock
import pytest
import json


from awx.api.versioning import reverse
from awx.main.models.jobs import JobTemplate, Job
from awx.main.models.activity_stream import ActivityStream
from awx.main.access import JobTemplateAccess
from awx.main.utils.common import get_type_for_model



@pytest.fixture
def job_template_with_survey(job_template_factory):
    objects = job_template_factory('jt', project='prj', survey='submitted_email')
    return objects.job_template


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


# Test normal operations with survey license work
@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_view_allowed(deploy_jobtemplate, get, admin_user):
    get(reverse('api:job_template_survey_spec', kwargs={'pk': deploy_jobtemplate.id}),
        admin_user, expect=200)


@pytest.mark.django_db
@pytest.mark.survey
def test_survey_spec_sucessful_creation(survey_spec_factory, job_template, post, admin_user):
    survey_input_data = survey_spec_factory('new_question')
    post(url=reverse('api:job_template_survey_spec', kwargs={'pk': job_template.id}),
         data=survey_input_data, user=admin_user, expect=200)
    updated_jt = JobTemplate.objects.get(pk=job_template.pk)
    assert updated_jt.survey_spec == survey_input_data


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


@pytest.mark.django_db
def test_survey_spec_default_not_allowed(job_template, post, admin_user):
    survey_input_data = {
        'description': 'A survey',
        'spec': [{
            'question_name': 'You must choose wisely',
            'variable': 'your_choice',
            'default': 'blue',
            'required': False,
            'type': 'multiplechoice',
            "choices": ["red", "green", "purple"]
        }],
        'name': 'my survey'
    }
    r = post(
        url=reverse(
            'api:job_template_survey_spec',
            kwargs={'pk': job_template.id}
        ),
        data=survey_input_data, user=admin_user, expect=400
    )
    assert r.data['error'] == 'Default choice must be answered from the choices listed.'


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


@pytest.mark.django_db
@pytest.mark.survey
def test_job_template_delete_access_with_survey(job_template_with_survey, admin_user):
    """The survey_spec view relies on JT `can_delete` to determine permission
    to delete the survey. This checks that system admins can delete the survey on a JT."""
    access = JobTemplateAccess(admin_user)
    assert access.can_delete(job_template_with_survey)


@pytest.mark.django_db
@pytest.mark.survey
def test_delete_survey_spec(job_template_with_survey, delete, admin_user):
    """Functional delete test through the survey_spec view."""
    delete(reverse('api:job_template_survey_spec', kwargs={'pk': job_template_with_survey.pk}),
           admin_user, expect=200)
    new_jt = JobTemplate.objects.get(pk=job_template_with_survey.pk)
    assert new_jt.survey_spec == {}


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


@pytest.mark.django_db
@pytest.mark.survey
def test_redact_survey_passwords_in_activity_stream(job_template_with_survey_passwords):
    job_template_with_survey_passwords.create_unified_job()
    AS_record = ActivityStream.objects.filter(object1='job').all()[0]
    changes_dict = json.loads(AS_record.changes)
    extra_vars = json.loads(changes_dict['extra_vars'])
    assert extra_vars['secret_key'] == '$encrypted$'
