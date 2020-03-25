from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization, Inventory, Host


@pytest.mark.django_db
def test_duplicate_inventories(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    decoy_org = Organization.objects.create(name='decoy')
    for this_org in (decoy_org, org):
        inv = Inventory.objects.create(name='test-inv', organization=this_org)

    result = run_module('tower_host', dict(
        name='Test Host',
        inventory=inv.name,
        state='present'
    ), admin_user)
    assert result.get('failed', True)
    msg = result.get('msg', '')
    assert 'Obtained 2 objects at endpoint inventories with data' in msg
    assert 'try ID or context param organization' in msg


@pytest.mark.django_db
def test_create_host(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    decoy_org = Organization.objects.create(name='decoy')
    for this_org in (decoy_org, org):
        inv = Inventory.objects.create(name='test-inv', organization=this_org)
    variables = {"ansible_network_os": "iosxr"}

    result = run_module('tower_host', dict(
        name='Test Host',
        inventory=inv.name,
        organization=org.name,
        variables=variables,
        state='present'
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    host = Host.objects.get(name='Test Host')
    assert host.inventory == inv
    assert host.inventory.organization == org

    assert result['id'] == host.id
    assert result['name'] == 'Test Host'
