from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_create_new(run_module, admin_user):
    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)
    assert result['changed']

    role_definition = RoleDefinition.objects.get(name='test_view_jt')
    assert role_definition
    permission_codenames = [p.codename for p in role_definition.permissions.all()]
    assert set(permission_codenames) == set(['view_jobtemplate', 'execute_jobtemplate'])
    assert role_definition.content_type.model == 'jobtemplate'


@pytest.mark.django_db
def test_update_existing(run_module, admin_user):
    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)

    assert result['changed']

    role_definition = RoleDefinition.objects.get(name='test_view_jt')
    permission_codenames = [p.codename for p in role_definition.permissions.all()]
    assert set(permission_codenames) == set(['view_jobtemplate'])
    assert role_definition.content_type.model == 'jobtemplate'

    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)

    assert result['changed']

    role_definition.refresh_from_db()
    permission_codenames = [p.codename for p in role_definition.permissions.all()]
    assert set(permission_codenames) == set(['view_jobtemplate', 'execute_jobtemplate'])
    assert role_definition.content_type.model == 'jobtemplate'


@pytest.mark.django_db
def test_delete_existing(run_module, admin_user):
    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)

    assert result['changed']

    role_definition = RoleDefinition.objects.get(name='test_view_jt')
    assert role_definition

    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
            'state': 'absent',
        },
        admin_user)

    assert result['changed']

    with pytest.raises(RoleDefinition.DoesNotExist):
        role_definition.refresh_from_db()


@pytest.mark.django_db
def test_idempotence(run_module, admin_user):
    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)

    assert result['changed']

    result = run_module(
        'role_definition',
        {
            'name': 'test_view_jt',
            'permissions': ['awx.view_jobtemplate', 'awx.execute_jobtemplate'],
            'content_type': 'awx.jobtemplate',
        },
        admin_user)

    assert not result['changed']

    role_definition = RoleDefinition.objects.get(name='test_view_jt')
    permission_codenames = [p.codename for p in role_definition.permissions.all()]
    assert set(permission_codenames) == set(['view_jobtemplate', 'execute_jobtemplate'])
