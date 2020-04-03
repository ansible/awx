from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import (
    WorkflowJobTemplate, JobTemplate, Project, InventorySource,
    Inventory, WorkflowJobTemplateNode
)


@pytest.mark.django_db
def test_create_workflow_job_template(run_module, admin_user, organization, survey_spec, silence_deprecation):
    result = run_module('tower_workflow_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'extra_vars': {'foo': 'bar', 'another-foo': {'barz': 'bar2'}},
        'survey': survey_spec,
        'survey_enabled': True,
        'state': 'present'
    }, admin_user)

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    assert wfjt.extra_vars == '{"foo": "bar", "another-foo": {"barz": "bar2"}}'

    result.pop('invocation', None)
    assert result == {
        "workflow_template": "foo-workflow",  # TODO: remove after refactor
        "state": "present",
        "id": wfjt.id,
        "changed": True
    }

    assert wfjt.organization_id == organization.id
    assert wfjt.survey_spec == survey_spec


@pytest.mark.django_db
def test_with_nested_workflow(run_module, admin_user, organization, silence_deprecation):
    wfjt1 = WorkflowJobTemplate.objects.create(name='first', organization=organization)

    result = run_module('tower_workflow_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'schema': [
            {'workflow': wfjt1.name}
        ],
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    node = wfjt.workflow_nodes.first()
    assert node is not None
    assert node.unified_job_template == wfjt1


@pytest.mark.django_db
def test_schema_with_branches(run_module, admin_user, organization, silence_deprecation):

    proj = Project.objects.create(organization=organization, name='Ansible Examples')
    inv = Inventory.objects.create(organization=organization, name='test-inv')
    jt = JobTemplate.objects.create(
        project=proj,
        playbook='helloworld.yml',
        inventory=inv,
        name='Hello world'
    )
    inv_src = InventorySource.objects.create(
        inventory=inv,
        name='AWS servers',
        source='ec2'
    )

    result = run_module('tower_workflow_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'schema': [
            {
                'job_template': 'Hello world',
                'failure': [
                    {
                        'inventory_source': 'AWS servers',
                        'success': [
                            {
                                'project': 'Ansible Examples',
                                'always': [
                                    {
                                        'job_template': "Hello world"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    root_nodes = wfjt.workflow_nodes.filter(**{
        '%ss_success__isnull' % WorkflowJobTemplateNode.__name__.lower(): True,
        '%ss_failure__isnull' % WorkflowJobTemplateNode.__name__.lower(): True,
        '%ss_always__isnull' % WorkflowJobTemplateNode.__name__.lower(): True,
    })
    assert len(root_nodes) == 1
    node = root_nodes[0]
    assert node.unified_job_template == jt
    second = node.failure_nodes.first()
    assert second.unified_job_template == inv_src
    third = second.success_nodes.first()
    assert third.unified_job_template == proj
    fourth = third.always_nodes.first()
    assert fourth.unified_job_template == jt


@pytest.mark.django_db
def test_with_missing_ujt(run_module, admin_user, organization, silence_deprecation):
    result = run_module('tower_workflow_template', {
        'name': 'foo-workflow',
        'organization': organization.name,
        'schema': [
            {'foo': 'bar'}
        ],
        'state': 'present'
    }, admin_user)
    assert result.get('failed', False), result
    assert 'You should provide exactly one of the attributes job_template,' in result['msg']
