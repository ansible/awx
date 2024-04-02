from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_base.rbac.models import RoleUserAssignment


@pytest.mark.django_db
def test_create_new(run_module, admin_user, job_template, job_template_role_definition):
    result = run_module(
        'role_user_assignment',
        {
            'user': admin_user.username,
            'object_id': job_template.id,
            'role_definition': job_template_role_definition.name,
        },
        admin_user)
    assert result['changed']
    assert RoleUserAssignment.objects.filter(user=admin_user, object_id=job_template.id, role_definition=job_template_role_definition).exists()


@pytest.mark.django_db
def test_idempotence(run_module, admin_user, job_template, job_template_role_definition):
    result = run_module(
        'role_user_assignment',
        {
            'user': admin_user.username,
            'object_id': job_template.id,
            'role_definition': job_template_role_definition.name,
        },
        admin_user)
    assert result['changed']

    result = run_module(
        'role_user_assignment',
        {
            'user': admin_user.username,
            'object_id': job_template.id,
            'role_definition': job_template_role_definition.name,
        },
        admin_user)
    assert not result['changed']


@pytest.mark.django_db
def test_delete_existing(run_module, admin_user, job_template, job_template_role_definition):
    result = run_module(
        'role_user_assignment',
        {
            'user': admin_user.username,
            'object_id': job_template.id,
            'role_definition': job_template_role_definition.name,
        },
        admin_user)
    assert result['changed']
    assert RoleUserAssignment.objects.filter(user=admin_user, object_id=job_template.id, role_definition=job_template_role_definition).exists()

    result = run_module(
        'role_user_assignment',
        {
            'user': admin_user.username,
            'object_id': job_template.id,
            'role_definition': job_template_role_definition.name,
            'state': 'absent'
        },
        admin_user)
    assert result['changed']
    assert not RoleUserAssignment.objects.filter(user=admin_user, object_id=job_template.id, role_definition=job_template_role_definition).exists()
