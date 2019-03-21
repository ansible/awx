import pytest

# AWX
from awx.main.models.jobs import JobTemplate

from unittest import mock


def test_missing_project_error(job_template_factory):
    objects = job_template_factory(
        'missing-project-jt',
        organization='org1',
        inventory='inventory1',
        persisted=False)
    obj = objects.job_template
    assert 'project' in obj.resources_needed_to_start
    assert 'project' in obj.validation_errors


def test_inventory_need_to_start(job_template_factory):
    objects = job_template_factory(
        'job-template-few-resources',
        project='project1',
        persisted=False)
    obj = objects.job_template
    assert 'inventory' in obj.resources_needed_to_start


def test_inventory_contradictions(job_template_factory):
    objects = job_template_factory(
        'job-template-paradox',
        project='project1',
        persisted=False)
    obj = objects.job_template
    obj.ask_inventory_on_launch = False
    assert 'inventory' in obj.validation_errors


@pytest.mark.survey
def test_job_template_survey_password_redaction(job_template_with_survey_passwords_unit):
    """Tests the JobTemplate model's funciton to redact passwords from
    extra_vars - used when creating a new job"""
    assert job_template_with_survey_passwords_unit.survey_password_variables() == ['secret_key', 'SSN']


def test_job_template_survey_mixin(job_template_factory):
    objects = job_template_factory(
        'survey_mixin_test',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False,
    )
    obj = objects.job_template
    obj.survey_enabled = True
    obj.survey_spec = {'spec': [{'default':'my_default', 'type':'password', 'variable':'my_variable'}]}
    kwargs = obj._update_unified_job_kwargs({}, {'extra_vars': {'my_variable':'$encrypted$'}})
    assert kwargs['extra_vars'] == '{"my_variable": "my_default"}'


def test_job_template_survey_mixin_length(job_template_factory):
    objects = job_template_factory(
        'survey_mixin_test',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False,
    )
    obj = objects.job_template
    obj.survey_enabled = True
    obj.survey_spec = {'spec': [{'default':'my_default', 'type':'password', 'variable':'my_variable'},
                                {'type':'password', 'variable':'my_other_variable'}]}
    kwargs = obj._update_unified_job_kwargs({}, {'extra_vars': {'my_variable':'$encrypted$'}})
    assert kwargs['extra_vars'] == '{"my_variable": "my_default"}'


def test_job_template_survey_mixin_survey_runtime_has_highest_priority(job_template_factory):
    objects = job_template_factory(
        'survey_mixin_test',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False,
    )
    obj = objects.job_template
    obj.survey_enabled = True
    obj.survey_spec = {'spec': [{'default':'foo', 'type':'password', 'variable':'my_variable'}]}
    kwargs = obj._update_unified_job_kwargs({}, {'extra_vars': {'my_variable': 'bar'}})
    assert kwargs['extra_vars'] == '{"my_variable": "bar"}'


def test_job_template_can_start_with_callback_extra_vars_provided(job_template_factory):
    objects = job_template_factory(
        'callback_extra_vars_test',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False,
    )
    obj = objects.job_template
    obj.ask_variables_on_launch = True
    with mock.patch.object(obj.__class__, 'passwords_needed_to_start', []):
        assert obj.can_start_without_user_input(callback_extra_vars='{"foo": "bar"}') is True


def test_ask_mapping_integrity():
    assert 'credentials' in JobTemplate.get_ask_mapping()
    assert JobTemplate.get_ask_mapping()['job_tags'] == 'ask_tags_on_launch'
