from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization, Inventory, Group


@pytest.mark.django_db
def test_create_group(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)

    result = run_module('tower_group', dict(
        name='Test Group',
        inventory='test-inv',
        variables='ansible_network_os: iosxr',
        state='present'
    ), admin_user)
    assert result.get('changed'), result

    group = Group.objects.get(name='Test Group')
    assert group.inventory == inv
    assert group.variables == 'ansible_network_os: iosxr'

    result.pop('invocation')
    assert result == {
        'credential_type': 'Nexus',
        'id': group.id,
        'name': 'Test Group',
        'changed': True,
        'state': 'present'
    }


@pytest.mark.django_db
def test_tower_group_idempotent(run_module, admin_user):
    # https://github.com/ansible/ansible/issues/46803
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)
    group = Group.objects.create(
        name='Test Group',
        inventory=inv,
        variables='ansible_network_os: iosxr'
    )

    result = run_module('tower_group', dict(
        name='Test Group',
        inventory='test-inv',
        variables='ansible_network_os: iosxr',
        state='present'
    ), admin_user)

    result.pop('invocation')
    assert result == {
        'id': group.id,
        'credential_type': 'Nexus',
        'name': 'Test Group',
        'changed': False,  # idempotency assertion
        'state': 'present'
    }
