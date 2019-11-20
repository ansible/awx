import pytest

from awx.main.models import Organization, Inventory, InventorySource


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
        "inventory_source": "Test Inventory Source",
        "state": "present",
        "id": inv_src.id,
    }


@pytest.mark.django_db
def test_create_inventory_source_multiple_orgs(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)

    # make another inventory by same name in another org
    org2 = Organization.objects.create(name='test-org-number-two')
    Inventory.objects.create(name='test-inv', organization=org2)

    result = run_module('tower_inventory_source', dict(
        name='Test Inventory Source',
        inventory='test-inv',
        source='ec2',
        organization='test-org',
        state='present'
    ), admin_user)
    assert result.pop('changed', None), result

    inv_src = InventorySource.objects.get(name='Test Inventory Source')
    assert inv_src.inventory == inv

    result.pop('invocation')
    assert result == {
        "inventory_source": "Test Inventory Source",
        "state": "present",
        "id": inv_src.id,
    }
