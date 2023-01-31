import pytest
from decimal import Decimal

from awx.main.models import Instance


@pytest.mark.parametrize('capacity_adjustment', [0.0, 0.25, 0.5, 0.75, 1, 1.5, 3])
def test_capacity_adjustment_no_save(capacity_adjustment):
    inst = Instance(hostname='test-host', capacity_adjustment=Decimal(capacity_adjustment), capacity=0, cpu_capacity=10, mem_capacity=1000)
    assert inst.capacity == 0
    assert inst.capacity_adjustment == capacity_adjustment  # sanity
    inst.set_capacity_value()
    assert inst.capacity > 0
    assert inst.capacity == (float(inst.capacity_adjustment) * abs(inst.mem_capacity - inst.cpu_capacity) + min(inst.mem_capacity, inst.cpu_capacity))


def test_cleanup_params_defaults():
    inst = Instance(hostname='foobar')
    assert inst.get_cleanup_task_kwargs(exclude_strings=['awx_423_']) == {'exclude_strings': ['awx_423_'], 'file_pattern': '/tmp/awx_*_*', 'grace_period': 60}


def test_cleanup_params_for_image_cleanup():
    inst = Instance(hostname='foobar')
    # see CLI conversion in awx.main.tests.unit.utils.test_receptor
    assert inst.get_cleanup_task_kwargs(file_pattern='', remove_images=['quay.invalid/foo/bar'], image_prune=True) == {
        'file_pattern': '',
        'process_isolation_executable': 'podman',
        'remove_images': ['quay.invalid/foo/bar'],
        'image_prune': True,
        'grace_period': 60,
    }
