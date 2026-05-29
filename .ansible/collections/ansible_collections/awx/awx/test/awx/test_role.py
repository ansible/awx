from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import WorkflowJobTemplate, User


@pytest.mark.django_db
@pytest.mark.parametrize('state', ('present', 'absent'))
def test_grant_organization_permission(run_module, admin_user, organization, state):
    rando = User.objects.create(username='rando')
    if state == 'absent':
        organization.admin_role.members.add(rando)

    result = run_module('role', {'user': rando.username, 'organization': organization.name, 'role': 'admin', 'state': state}, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    if state == 'present':
        assert rando in organization.admin_role
    else:
        assert rando not in organization.admin_role


@pytest.mark.django_db
@pytest.mark.parametrize('state', ('present', 'absent'))
def test_grant_workflow_permission(run_module, admin_user, organization, state):
    wfjt = WorkflowJobTemplate.objects.create(organization=organization, name='foo-workflow')
    rando = User.objects.create(username='rando')
    if state == 'absent':
        wfjt.execute_role.members.add(rando)

    result = run_module('role', {'user': rando.username, 'workflow': wfjt.name, 'role': 'execute', 'state': state}, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    if state == 'present':
        assert rando in wfjt.execute_role
    else:
        assert rando not in wfjt.execute_role


@pytest.mark.django_db
@pytest.mark.parametrize('state', ('present', 'absent'))
def test_grant_workflow_list_permission(run_module, admin_user, organization, state):
    wfjt = WorkflowJobTemplate.objects.create(organization=organization, name='foo-workflow')
    rando = User.objects.create(username='rando')
    if state == 'absent':
        wfjt.execute_role.members.add(rando)

    result = run_module(
        'role',
        {'user': rando.username, 'lookup_organization': wfjt.organization.name, 'workflows': [wfjt.name], 'role': 'execute', 'state': state},
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)

    if state == 'present':
        assert rando in wfjt.execute_role
    else:
        assert rando not in wfjt.execute_role


@pytest.mark.django_db
@pytest.mark.parametrize('state', ('present', 'absent'))
def test_grant_workflow_approval_permission(run_module, admin_user, organization, state):
    wfjt = WorkflowJobTemplate.objects.create(organization=organization, name='foo-workflow')
    rando = User.objects.create(username='rando')
    if state == 'absent':
        wfjt.execute_role.members.add(rando)

    result = run_module('role', {'user': rando.username, 'workflow': wfjt.name, 'role': 'approval', 'state': state}, admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    if state == 'present':
        assert rando in wfjt.approval_role
    else:
        assert rando not in wfjt.approval_role


@pytest.mark.django_db
def test_invalid_role(run_module, admin_user, project):
    rando = User.objects.create(username='rando')
    result = run_module('role', {'user': rando.username, 'project': project.name, 'role': 'adhoc', 'state': 'present'}, admin_user)
    assert result.get('failed', False)
    msg = result.get('msg')
    assert 'has no role adhoc_role' in msg
    assert 'available roles: admin_role, use_role, update_role, read_role' in msg
