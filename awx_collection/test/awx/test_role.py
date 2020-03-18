from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import WorkflowJobTemplate, User


@pytest.mark.django_db
def test_grant_organization_permission(run_module, admin_user, organization):
    rando = User.objects.create(username='rando')

    result = run_module('tower_role', {
        'user': rando.username,
        'organization': organization.name,
        'role': 'admin',
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    assert rando in organization.execute_role


@pytest.mark.django_db
def test_grant_workflow_permission(run_module, admin_user, organization):
    wfjt = WorkflowJobTemplate.objects.create(organization=organization, name='foo-workflow')
    rando = User.objects.create(username='rando')

    result = run_module('tower_role', {
        'user': rando.username,
        'workflow': wfjt.name,
        'role': 'execute',
        'state': 'present'
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    assert rando in wfjt.execute_role
