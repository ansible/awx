from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Inventory, Organization


@pytest.mark.django_db
def test_inventory_create(run_module, admin_user, organization):
    """Creating a basic inventory sets its variables and organization correctly."""
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
    """An invalid host_filter query on a smart inventory fails the module."""
    result = run_module(
        'inventory',
        {'name': 'foo-inventory', 'organization': organization.name, 'kind': 'smart', 'host_filter': 'ansible', 'state': 'present'},
        admin_user,
    )
    assert result.get('failed', False), result

    assert 'Invalid query ansible' in result['msg']


@pytest.mark.django_db
def test_valid_smart_inventory_create(run_module, admin_user, organization):
    """A valid host_filter query creates a smart inventory with that filter."""
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
def test_constructed_inventory_input_inventories_scoped_to_organization(run_module, admin_user, organization):
    """Regression test for https://github.com/ansible/awx/issues/16393.

    Two organizations each have an inventory with the *same* name. A
    constructed inventory in org-a should be able to reference org-a's
    "shared-name" inventory as an input inventory without the lookup
    becoming ambiguous because org-b also has an inventory called
    "shared-name".
    """
    other_organization = Organization.objects.create(name='other-organization')

    Inventory.objects.create(name='shared-name', organization=organization)
    Inventory.objects.create(name='shared-name', organization=other_organization)

    result = run_module(
        'inventory',
        {
            'name': 'my-constructed-inventory',
            'organization': organization.name,
            'kind': 'constructed',
            'input_inventories': ['shared-name'],
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)

    constructed_inv = Inventory.objects.get(name='my-constructed-inventory')
    assert constructed_inv.organization_id == organization.id

    expected_input_inventory = Inventory.objects.get(name='shared-name', organization=organization)
    input_inventory_ids = list(constructed_inv.input_inventories.values_list('id', flat=True))
    assert input_inventory_ids == [expected_input_inventory.id]
