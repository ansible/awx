import pytest

from awx.main.models import InstanceGroup


@pytest.fixture(scope='function')
def source_model(request):
    return request.getfixturevalue(request.param)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'source_model', ['job_template', 'inventory', 'organization'], indirect=True
)
def test_instance_group_ordering(source_model):
    groups = [
        InstanceGroup.objects.create(name='host-%d' % i)
        for i in range(5)
    ]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    assert [g.name for g in source_model.instance_groups.all()] == [
        'host-4', 'host-3', 'host-2', 'host-1', 'host-0'
    ]
    assert [
        (row.position, row.instancegroup.name)
        for row in source_model.instance_groups.through.objects.all()
    ] == [
        (0, 'host-4'),
        (1, 'host-3'),
        (2, 'host-2'),
        (3, 'host-1'),
        (4, 'host-0'),
    ]

    source_model.instance_groups.remove(groups[0])
    assert [g.name for g in source_model.instance_groups.all()] == [
        'host-3', 'host-2', 'host-1', 'host-0'
    ]
    assert [
        (row.position, row.instancegroup.name)
        for row in source_model.instance_groups.through.objects.all()
    ] == [
        (0, 'host-3'),
        (1, 'host-2'),
        (2, 'host-1'),
        (3, 'host-0'),
    ]

    source_model.instance_groups.clear()
    assert source_model.instance_groups.through.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    'source_model', ['job_template', 'inventory', 'organization'], indirect=True
)
def test_instance_group_middle_deletion(source_model):
    groups = [
        InstanceGroup.objects.create(name='host-%d' % i)
        for i in range(5)
    ]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    source_model.instance_groups.remove(groups[2])
    assert [g.name for g in source_model.instance_groups.all()] == [
        'host-4', 'host-3', 'host-1', 'host-0'
    ]
    assert [
        (row.position, row.instancegroup.name)
        for row in source_model.instance_groups.through.objects.all()
    ] == [
        (0, 'host-4'),
        (1, 'host-3'),
        (2, 'host-1'),
        (3, 'host-0'),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'source_model', ['job_template', 'inventory', 'organization'], indirect=True
)
def test_explicit_ordering(source_model):
    groups = [
        InstanceGroup.objects.create(name='host-%d' % i)
        for i in range(5)
    ]
    groups.reverse()
    for group in groups:
        source_model.instance_groups.add(group)

    assert [g.name for g in source_model.instance_groups.all()] == [
        'host-4', 'host-3', 'host-2', 'host-1', 'host-0'
    ]
    assert [g.name for g in source_model.instance_groups.order_by('name').all()] == [
        'host-0', 'host-1', 'host-2', 'host-3', 'host-4'
    ]
