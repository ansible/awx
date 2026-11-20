from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Inventory, Label


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
def test_inventory_labels_association(run_module, admin_user, organization):
    """AAP-38666: inventory module should accept labels like job_template does."""
    labels = [Label.objects.create(name=f'inv-label-{i}', organization=organization) for i in range(3)]

    result = run_module(
        'inventory',
        {
            'name': 'labeled-inventory',
            'organization': organization.name,
            'labels': [label.name for label in labels],
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert result['changed']

    inv = Inventory.objects.get(name='labeled-inventory')
    assert set(inv.labels.values_list('id', flat=True)) == set(label.id for label in labels)

    # Re-running with the same labels should be idempotent
    result = run_module(
        'inventory',
        {
            'name': 'labeled-inventory',
            'organization': organization.name,
            'labels': [label.name for label in labels],
            'state': 'present',
        },
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert result['changed'] is False
