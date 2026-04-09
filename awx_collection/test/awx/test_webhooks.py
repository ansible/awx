from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import JobTemplate, WorkflowJobTemplate


# The backend supports these webhook services on job/workflow templates
# (see awx/main/models/mixins.py). The collection modules must accept all of
# them in their argument_spec ``choices`` list. This test guards against the
# module's choices drifting from the backend -- see AAP-45980, where
# ``bitbucket_dc`` had been supported by the API since migration 0188 but was
# still being rejected by the job_template/workflow_job_template modules.
WEBHOOK_SERVICES = ['github', 'gitlab', 'bitbucket_dc']


@pytest.mark.django_db
@pytest.mark.parametrize('webhook_service', WEBHOOK_SERVICES)
def test_job_template_accepts_webhook_service(run_module, admin_user, project, inventory, webhook_service):
    result = run_module(
        'job_template',
        {
            'name': 'foo',
            'playbook': 'helloworld.yml',
            'project': project.name,
            'inventory': inventory.name,
            'webhook_service': webhook_service,
            'state': 'present',
        },
        admin_user,
    )

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result

    jt = JobTemplate.objects.get(name='foo')
    assert jt.webhook_service == webhook_service

    # Re-running with the same args must be a no-op (idempotence).
    result = run_module(
        'job_template',
        {
            'name': 'foo',
            'playbook': 'helloworld.yml',
            'project': project.name,
            'inventory': inventory.name,
            'webhook_service': webhook_service,
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result


@pytest.mark.django_db
@pytest.mark.parametrize('webhook_service', WEBHOOK_SERVICES)
def test_workflow_job_template_accepts_webhook_service(run_module, admin_user, organization, webhook_service):
    result = run_module(
        'workflow_job_template',
        {
            'name': 'foo-workflow',
            'organization': organization.name,
            'webhook_service': webhook_service,
            'state': 'present',
        },
        admin_user,
    )

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    assert wfjt.webhook_service == webhook_service

    # Re-running with the same args must be a no-op (idempotence).
    result = run_module(
        'workflow_job_template',
        {
            'name': 'foo-workflow',
            'organization': organization.name,
            'webhook_service': webhook_service,
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.get('changed', True), result


@pytest.mark.django_db
def test_job_template_rejects_unknown_webhook_service(run_module, admin_user, project, inventory):
    result = run_module(
        'job_template',
        {
            'name': 'foo',
            'playbook': 'helloworld.yml',
            'project': project.name,
            'inventory': inventory.name,
            'webhook_service': 'not_a_real_service',
            'state': 'present',
        },
        admin_user,
    )
    assert result.get('failed', False), result
    assert 'webhook_service' in result.get('msg', '')


@pytest.mark.django_db
def test_workflow_job_template_rejects_unknown_webhook_service(run_module, admin_user, organization):
    result = run_module(
        'workflow_job_template',
        {
            'name': 'foo-workflow',
            'organization': organization.name,
            'webhook_service': 'not_a_real_service',
            'state': 'present',
        },
        admin_user,
    )
    assert result.get('failed', False), result
    assert 'webhook_service' in result.get('msg', '')
