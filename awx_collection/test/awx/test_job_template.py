from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import ActivityStream, JobTemplate, Job, NotificationTemplate


@pytest.mark.django_db
def test_create_job_template(run_module, admin_user, project, inventory):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'extra_vars': {'foo': 'bar'},
        'job_type': 'run',
        'state': 'present'
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')
    assert jt.extra_vars == '{"foo": "bar"}'

    assert result == {
        "name": "foo",
        "id": jt.id,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert jt.project_id == project.id
    assert jt.inventory_id == inventory.id


@pytest.mark.django_db
def test_resets_job_template_values(run_module, admin_user, project, inventory):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'extra_vars': {'foo': 'bar'},
        'job_type': 'run',
        'state': 'present',
        'forks': 20,
        'timeout': 50,
        'allow_simultaneous': True,
        'ask_limit_on_launch': True,
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')
    assert jt.forks == 20
    assert jt.timeout == 50
    assert jt.allow_simultaneous
    assert jt.ask_limit_on_launch

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'extra_vars': {'foo': 'bar'},
        'job_type': 'run',
        'state': 'present',
        'forks': 0,
        'timeout': 0,
        'allow_simultaneous': False,
        'ask_limit_on_launch': False,
    }

    result = run_module('tower_job_template', module_args, admin_user)
    assert result['changed']

    jt = JobTemplate.objects.get(name='foo')
    assert jt.forks == 0
    assert jt.timeout == 0
    assert not jt.allow_simultaneous
    assert not jt.ask_limit_on_launch


@pytest.mark.django_db
def test_job_launch_with_prompting(run_module, admin_user, project, inventory, machine_credential):
    JobTemplate.objects.create(
        name='foo',
        project=project,
        playbook='helloworld.yml',
        ask_variables_on_launch=True,
        ask_inventory_on_launch=True,
        ask_credential_on_launch=True
    )
    result = run_module('tower_job_launch', dict(
        job_template='foo',
        inventory=inventory.name,
        credential=machine_credential.name,
        extra_vars={"var1": "My First Variable",
                    "var2": "My Second Variable",
                    "var3": "My Third Variable"
                    }
    ), admin_user)
    assert result.pop('changed', None), result

    job = Job.objects.get(id=result['id'])
    assert job.extra_vars == '{"var1": "My First Variable", "var2": "My Second Variable", "var3": "My Third Variable"}'
    assert job.inventory == inventory
    assert [cred.id for cred in job.credentials.all()] == [machine_credential.id]


@pytest.mark.django_db
def test_job_template_with_new_credentials(
        run_module, admin_user, project, inventory,
        machine_credential, vault_credential):
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        credentials=[machine_credential.name, vault_credential.name]
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result
    jt = JobTemplate.objects.get(pk=result['id'])

    assert set([machine_credential.id, vault_credential.id]) == set([
        cred.pk for cred in jt.credentials.all()])

    prior_ct = ActivityStream.objects.count()
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        credentials=[machine_credential.name, vault_credential.name]
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result
    jt.refresh_from_db()
    assert result['id'] == jt.id

    assert set([machine_credential.id, vault_credential.id]) == set([
        cred.pk for cred in jt.credentials.all()])
    assert ActivityStream.objects.count() == prior_ct


@pytest.mark.django_db
def test_job_template_with_survey_spec(run_module, admin_user, project, inventory, survey_spec):
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        survey_spec=survey_spec,
        survey_enabled=True
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result
    jt = JobTemplate.objects.get(pk=result['id'])

    assert jt.survey_spec == survey_spec

    prior_ct = ActivityStream.objects.count()
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        survey_spec=survey_spec,
        survey_enabled=True
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result
    jt.refresh_from_db()
    assert result['id'] == jt.id

    assert jt.survey_spec == survey_spec
    assert ActivityStream.objects.count() == prior_ct


@pytest.mark.django_db
def test_job_template_with_wrong_survey_spec(run_module, admin_user, project, inventory, survey_spec):
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        survey_spec=survey_spec,
        survey_enabled=True
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result
    jt = JobTemplate.objects.get(pk=result['id'])

    assert jt.survey_spec == survey_spec

    prior_ct = ActivityStream.objects.count()

    del survey_spec['description']

    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        inventory=inventory.name,
        survey_spec=survey_spec,
        survey_enabled=True
    ), admin_user)
    assert result.get('failed', True)
    assert result.get('msg') == "Failed to update survey: Field 'description' is missing from survey spec."


@pytest.mark.django_db
def test_job_template_with_survey_encrypted_default(run_module, admin_user, project, inventory, silence_warning):
    spec = {
        "spec": [
            {
                "index": 0,
                "question_name": "my question?",
                "default": "very_secret_value",
                "variable": "myvar",
                "type": "password",
                "required": False
            }
        ],
        "description": "test",
        "name": "test"
    }
    for i in range(2):
        result = run_module('tower_job_template', dict(
            name='foo',
            playbook='helloworld.yml',
            project=project.name,
            inventory=inventory.name,
            survey_spec=spec,
            survey_enabled=True
        ), admin_user)
        assert not result.get('failed', False), result.get('msg', result)

    assert result.get('changed', False), result  # not actually desired, but assert for sanity

    silence_warning.assert_called_once_with(
        "The field survey_spec of job_template {0} has encrypted data and "
        "may inaccurately report task is changed.".format(result['id']))


@pytest.mark.django_db
def test_associate_only_on_success(run_module, admin_user, organization, project):
    jt = JobTemplate.objects.create(
        name='foo',
        project=project,
        playbook='helloworld.yml',
        ask_inventory_on_launch=True,
    )
    create_kwargs = dict(
        notification_configuration={
            'url': 'http://www.example.com/hook',
            'headers': {
                'X-Custom-Header': 'value123'
            },
            'password': 'bar'
        },
        notification_type='webhook',
        organization=organization
    )
    nt1 = NotificationTemplate.objects.create(name='nt1', **create_kwargs)
    nt2 = NotificationTemplate.objects.create(name='nt2', **create_kwargs)

    jt.notification_templates_error.add(nt1)

    # test preservation of error NTs when success NTs are added
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        notification_templates_success=['nt2']
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result

    assert list(jt.notification_templates_success.values_list('id', flat=True)) == [nt2.id]
    assert list(jt.notification_templates_error.values_list('id', flat=True)) == [nt1.id]

    # test removal to empty list
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        notification_templates_success=[]
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result

    assert list(jt.notification_templates_success.values_list('id', flat=True)) == []
    assert list(jt.notification_templates_error.values_list('id', flat=True)) == [nt1.id]
