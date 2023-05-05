import pytest

from awx.main.models import InstanceGroup, Inventory


@pytest.fixture(scope='function')
def source_model(request):
    return request.getfixturevalue(request.param)


@pytest.mark.django_db
@pytest.mark.parametrize('source_model', ['job_template', 'inventory', 'organization'], indirect=True)
def test_instance_group_ordering(source_model):
    groups = [InstanceGroup.objects.create(name='host-%d' % i) for i in range(5)]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    assert [g.name for g in source_model.instance_groups.all()] == ['host-4', 'host-3', 'host-2', 'host-1', 'host-0']
    assert [(row.position, row.instancegroup.name) for row in source_model.instance_groups.through.objects.all()] == [
        (1, 'host-4'),
        (2, 'host-3'),
        (3, 'host-2'),
        (4, 'host-1'),
        (5, 'host-0'),
    ]

    source_model.instance_groups.remove(groups[0])
    assert [g.name for g in source_model.instance_groups.all()] == ['host-3', 'host-2', 'host-1', 'host-0']
    assert [(row.position, row.instancegroup.name) for row in source_model.instance_groups.through.objects.all()] == [
        (2, 'host-3'),
        (3, 'host-2'),
        (4, 'host-1'),
        (5, 'host-0'),
    ]

    source_model.instance_groups.clear()
    assert source_model.instance_groups.through.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('source_model', ['job_template', 'inventory', 'organization'], indirect=True)
def test_instance_group_bulk_add(source_model):
    groups = [InstanceGroup.objects.create(name='host-%d' % i) for i in range(5)]
    groups.reverse()
    source_model.instance_groups.add(*groups)
    assert list(source_model.instance_groups.all()) == groups


@pytest.mark.django_db
@pytest.mark.parametrize('source_model', ['job_template', 'inventory', 'organization'], indirect=True)
def test_instance_group_middle_deletion(source_model):
    groups = [InstanceGroup.objects.create(name='host-%d' % i) for i in range(5)]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    source_model.instance_groups.remove(groups[2])
    assert [g.name for g in source_model.instance_groups.all()] == ['host-4', 'host-3', 'host-1', 'host-0']
    assert [(row.position, row.instancegroup.name) for row in source_model.instance_groups.through.objects.all()] == [
        (1, 'host-4'),
        (2, 'host-3'),
        (4, 'host-1'),
        (5, 'host-0'),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize('source_model', ['job_template', 'inventory', 'organization'], indirect=True)
def test_explicit_ordering(source_model):
    groups = [InstanceGroup.objects.create(name='host-%d' % i) for i in range(5)]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    assert [g.name for g in source_model.instance_groups.all()] == ['host-4', 'host-3', 'host-2', 'host-1', 'host-0']
    assert [g.name for g in source_model.instance_groups.order_by('name').all()] == ['host-0', 'host-1', 'host-2', 'host-3', 'host-4']


@pytest.mark.django_db
def test_input_inventories_ordering():
    constructed_inventory = Inventory.objects.create(name='my_constructed', kind='constructed')
    input_inventories = [Inventory.objects.create(name='inv-%d' % i) for i in range(5)]
    input_inventories.reverse()
    for inv in input_inventories:
        constructed_inventory.input_inventories.add(inv)

    assert [g.name for g in constructed_inventory.input_inventories.all()] == ['inv-4', 'inv-3', 'inv-2', 'inv-1', 'inv-0']
    assert [(row.position, row.to_inventory.name) for row in constructed_inventory.input_inventories.through.objects.all()] == [
        (1, 'inv-4'),
        (2, 'inv-3'),
        (3, 'inv-2'),
        (4, 'inv-1'),
        (5, 'inv-0'),
    ]

    constructed_inventory.input_inventories.remove(input_inventories[0])
    assert [g.name for g in constructed_inventory.input_inventories.all()] == ['inv-3', 'inv-2', 'inv-1', 'inv-0']
    assert [(row.position, row.to_inventory.name) for row in constructed_inventory.input_inventories.through.objects.all()] == [
        (2, 'inv-3'),
        (3, 'inv-2'),
        (4, 'inv-1'),
        (5, 'inv-0'),
    ]

    constructed_inventory.input_inventories.clear()
    assert constructed_inventory.input_inventories.through.objects.count() == 0
