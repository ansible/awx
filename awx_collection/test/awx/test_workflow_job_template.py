from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import WorkflowJobTemplate, NotificationTemplate


@pytest.mark.django_db
def test_create_workflow_job_template(run_module, admin_user, organization, survey_spec):
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'extra_vars': {'foo': 'bar', 'another-foo': {'barz': 'bar2'}},
        'survey_spec': survey_spec,
        'survey_enabled': True,
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    assert wfjt.extra_vars == '{"foo": "bar", "another-foo": {"barz": "bar2"}}'

    result.pop('invocation', None)
    assert result == {"name": "foo-workflow", "id": wfjt.id, "changed": True}

    assert wfjt.organization_id == organization.id
    assert wfjt.survey_spec == survey_spec


@pytest.mark.django_db
def test_create_modify_no_survey(run_module, admin_user, organization, survey_spec):
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    assert wfjt.organization_id == organization.id
    assert wfjt.survey_spec == {}
    result.pop('invocation', None)
    assert result == {"name": "foo-workflow", "id": wfjt.id, "changed": True}

    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result


@pytest.mark.django_db
def test_survey_spec_only_changed(run_module, admin_user, organization, survey_spec):
    wfjt = WorkflowJobTemplate.objects.create(
        organization=organization, name='foo-workflow',
        survey_enabled=True, survey_spec=survey_spec
    )
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result
    wfjt.refresh_from_db()
    assert wfjt.survey_spec == survey_spec

    survey_spec['description'] = 'changed description'

    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'survey_spec': survey_spec,
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result
    wfjt.refresh_from_db()
    assert wfjt.survey_spec == survey_spec


@pytest.mark.django_db
def test_associate_only_on_success(run_module, admin_user, organization, project):
    wfjt = WorkflowJobTemplate.objects.create(
        organization=organization, name='foo-workflow',
        # survey_enabled=True, survey_spec=survey_spec
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

    wfjt.notification_templates_error.add(nt1)

    # test preservation of error NTs when success NTs are added
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'notification_templates_success': ['nt2']
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result

    assert list(wfjt.notification_templates_success.values_list('id', flat=True)) == [nt2.id]
    assert list(wfjt.notification_templates_error.values_list('id', flat=True)) == [nt1.id]

    # test removal to empty list
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'notification_templates_success': []
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result

    assert list(wfjt.notification_templates_success.values_list('id', flat=True)) == []
    assert list(wfjt.notification_templates_error.values_list('id', flat=True)) == [nt1.id]


@pytest.mark.django_db
def test_delete_with_spec(run_module, admin_user, organization, survey_spec):
    WorkflowJobTemplate.objects.create(
        organization=organization, name='foo-workflow',
        survey_enabled=True, survey_spec=survey_spec
    )
    result = run_module('tower_workflow_job_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'state': 'absent'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', True), result

    assert WorkflowJobTemplate.objects.filter(
        name='foo-workflow', organization=organization).count() == 0
