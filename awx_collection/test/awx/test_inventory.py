from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Inventory, Organization


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
    assert inv.variables == '{"foo": "bar", "another-foo": {"barz": "bar2"}}'

    result.pop('module_args', None)
    result.pop('invocation', None)
    assert result == {"name": "foo-inventory", "id": inv.id, "changed": True}

    assert inv.organization_id == organization.id


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


@pytest.mark.django_db
def test_constructed_inventory_input_inventories_with_duplicate_names(run_module, admin_user, organization):
    org_b = Organization.objects.create(name='org-b')

    Inventory.objects.create(name='shared-inv-name', organization=organization)
    Inventory.objects.create(name='shared-inv-name', organization=org_b)

    result = run_module(
        'inventory',
        {
            'name': 'my-constructed-inventory',
            'organization': organization.name,
            'kind': 'constructed',
            'input_inventories': ['shared-inv-name'],
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)

    constructed = Inventory.objects.get(name='my-constructed-inventory')
    assert constructed.kind == 'constructed'
    assert constructed.organization_id == organization.id
    assert list(constructed.input_inventories.values_list('name', flat=True)) == ['shared-inv-name']
    assert constructed.input_inventories.first().organization_id == organization.id
