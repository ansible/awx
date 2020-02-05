from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization, Inventory, InventorySource, Project


@pytest.fixture
def base_inventory():
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)
    Project.objects.create(
        name='test-proj',
        organization=org,
        scm_type='git',
        scm_url='https://github.com/ansible/test-playbooks.git',
    )
    return inv


@pytest.mark.django_db
def test_inventory_source_create(run_module, admin_user, base_inventory):
    source_path = '/var/lib/awx/example_source_path/'
    result = run_module('tower_inventory_source', dict(
        name='foo',
        inventory='test-inv',
        state='present',
        source='scm',
        source_path=source_path,
        source_project='test-proj'
    ), admin_user)
    assert result.pop('changed', None), result

    inv_src = InventorySource.objects.get(name='foo')
    assert inv_src.inventory == base_inventory
    result.pop('invocation')
    assert result == {
        'id': inv_src.id,
        'name': 'foo',
        'state': 'present',
        'credential_type': 'Nexus'
    }


@pytest.mark.django_db
def test_create_inventory_source_implied_org(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)

    result = run_module('tower_inventory_source', dict(
        name='Test Inventory Source',
        inventory='test-inv',
        source='ec2',
        state='present'
    ), admin_user)
    assert result.pop('changed', None), result

    inv_src = InventorySource.objects.get(name='Test Inventory Source')
    assert inv_src.inventory == inv

    result.pop('invocation')
    assert result == {
        "credential_type": "Nexus",
        "name": "Test Inventory Source",
        "state": "present",
        "id": inv_src.id,
    }


@pytest.mark.django_db
def test_create_inventory_source_multiple_orgs(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    Inventory.objects.create(name='test-inv', organization=org)

    # make another inventory by same name in another org
    org2 = Organization.objects.create(name='test-org-number-two')
    inv2 = Inventory.objects.create(name='test-inv', organization=org2)

    result = run_module('tower_inventory_source', dict(
        name='Test Inventory Source',
        inventory=inv2.id,
        source='ec2',
        state='present'
    ), admin_user)
    assert result.pop('changed', None), result

    inv_src = InventorySource.objects.get(name='Test Inventory Source')
    assert inv_src.inventory == inv2

    result.pop('invocation')
    assert result == {
        "credential_type": "Nexus",
        "name": "Test Inventory Source",
        "state": "present",
        "id": inv_src.id,
    }


@pytest.mark.django_db
def test_create_inventory_source_with_venv(run_module, admin_user, base_inventory, mocker):
    path = '/var/lib/awx/venv/custom-venv/foobar13489435/'
    source_path = '/var/lib/awx/example_source_path/'
    with mocker.patch('awx.main.models.mixins.get_custom_venv_choices', return_value=[path]):
        result = run_module('tower_inventory_source', dict(
            name='foo',
            inventory='test-inv',
            state='present',
            source='scm',
            source_project='test-proj',
            custom_virtualenv=path,
            source_path=source_path
        ), admin_user)
    assert result.pop('changed'), result

    inv_src = InventorySource.objects.get(name='foo')
    assert inv_src.inventory == base_inventory
    result.pop('invocation')

    assert inv_src.custom_virtualenv == path


@pytest.mark.django_db
def test_custom_venv_no_op(run_module, admin_user, base_inventory, mocker):
    """If the inventory source is modified, then it should not blank fields
    unrelated to the params that the user passed.
    This enforces assumptions about the behavior of the AnsibleModule
    default argument_spec behavior.
    """
    source_path = '/var/lib/awx/example_source_path/'
    inv_src = InventorySource.objects.create(
        name='foo',
        inventory=base_inventory,
        source_project=Project.objects.get(name='test-proj'),
        source='scm',
        custom_virtualenv='/venv/foobar/'
    )
    # mock needed due to API behavior, not incorrect client behavior
    with mocker.patch('awx.main.models.mixins.get_custom_venv_choices', return_value=['/venv/foobar/']):
        result = run_module('tower_inventory_source', dict(
            name='foo',
            description='this is the changed description',
            inventory='test-inv',
            source='scm',  # is required, but behavior is arguable
            state='present',
            source_project='test-proj',
            source_path=source_path
        ), admin_user)
    assert result.pop('changed', None), result
    inv_src.refresh_from_db()
    assert inv_src.custom_virtualenv == '/venv/foobar/'
    assert inv_src.description == 'this is the changed description'
