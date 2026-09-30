from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Inventory


@pytest.mark.django_db
def test_inventory_create(run_module, admin_user, organization):
    # Create an insights credential

    result = run_module(
        'inventory',
        {
            'name': 'foo-inventory',
            'organization': organization.name,
            'variables': {'foo': 'bar', 'another-foo': {'barz': 'bar2'}},
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)

    inv = Inventory.objects.get(name='foo-inventory')
    assert inv.variables == '---\nanother-foo:\n  barz: bar2\nfoo: bar\n'

    result.pop('module_args', None)
    result.pop('invocation', None)
    assert result == {"name": "foo-inventory", "id": inv.id, "changed": True}

    assert inv.organization_id == organization.id


@pytest.mark.django_db
def test_inventory_empty_variables_clears(run_module, admin_user, organization):
    """An empty dict clears the field: it reaches the API as '', not as the JSON text '{}'."""
    inv_args = {'name': 'clear-vars-inventory', 'organization': organization.name, 'state': 'present'}
    result = run_module('inventory', dict(inv_args, variables={'foo': 'bar'}), admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    result = run_module('inventory', dict(inv_args, variables={}), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result
    assert Inventory.objects.get(name='clear-vars-inventory').variables == ''


@pytest.mark.django_db
def test_invalid_smart_inventory_create(run_module, admin_user, organization):
    result = run_module(
        'inventory',
        {'name': 'foo-inventory', 'organization': organization.name, 'kind': 'smart', 'host_filter': 'ansible', 'state': 'present'},
        admin_user,
    )
    assert result.get('failed', False), result

    assert 'Invalid query ansible' in result['msg']


@pytest.mark.django_db
def test_valid_smart_inventory_create(run_module, admin_user, organization):
    result = run_module(
        'inventory',
        {'name': 'foo-inventory', 'organization': organization.name, 'kind': 'smart', 'host_filter': 'name=my_host', 'state': 'present'},
        admin_user,
    )
    assert not result.get('failed', False), result

    inv = Inventory.objects.get(name='foo-inventory')
    assert inv.host_filter == 'name=my_host'
    assert inv.kind == 'smart'
    assert inv.organization_id == organization.id
