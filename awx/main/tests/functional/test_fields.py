import pytest

from awx.main.models.ha import InstanceGroup
from awx.main.models.inventory import Inventory


@pytest.fixture
def instance_group():
    return InstanceGroup.objects.create(name='custom_ig')


@pytest.mark.django_db
def test_inventory_instance_groups(inventory, instance_group):
    inventory.instance_groups.add(instance_group)
    through_obj = inventory.instance_groups.through.objects.first()
    assert through_obj.position == 0


@pytest.mark.django_db
def test_inventory_input_inventories(inventory):
    input = Inventory.objects.create(name='source1')
    inventory.input_inventories.add(input)
    through_obj = inventory.input_inventories.through.objects.first()
    assert through_obj.position == 0
