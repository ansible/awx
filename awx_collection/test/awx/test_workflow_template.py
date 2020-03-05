from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import WorkflowJobTemplate


@pytest.mark.django_db
def test_create_workflow_job_template(run_module, admin_user, organization):

    module_args = {
        'name': 'foo-workflow',
        'organization': organization.name,
        'extra_vars': {'foo': 'bar', 'another-foo': {'barz': 'bar2'}},
        'state': 'present'
    }

    result = run_module('tower_workflow_template', module_args, admin_user)

    wfjt = WorkflowJobTemplate.objects.get(name='foo-workflow')
    assert wfjt.extra_vars == '{"foo": "bar", "another-foo": {"barz": "bar2"}}'

    result.pop('module_args', None)
    assert result == {
        "workflow_template": "foo-workflow",  # TODO: remove after refactor
        "state": "present",
        "id": wfjt.id,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert wfjt.organization_id == organization.id
