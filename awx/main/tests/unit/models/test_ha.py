import pytest
from unittest import mock
from unittest.mock import Mock
from decimal import Decimal

from awx.main.models import InstanceGroup, Instance
from awx.main.scheduler.task_manager_models import TaskManagerInstanceGroups


@pytest.mark.parametrize('capacity_adjustment', [0.0, 0.25, 0.5, 0.75, 1, 1.5, 3])
def test_capacity_adjustment_no_save(capacity_adjustment):
    inst = Instance(hostname='test-host', capacity_adjustment=Decimal(capacity_adjustment), capacity=0, cpu_capacity=10, mem_capacity=1000)
    assert inst.capacity == 0
    assert inst.capacity_adjustment == capacity_adjustment  # sanity
    inst.set_capacity_value()
    assert inst.capacity > 0
    assert inst.capacity == (float(inst.capacity_adjustment) * abs(inst.mem_capacity - inst.cpu_capacity) + min(inst.mem_capacity, inst.cpu_capacity))


def T(impact):
    j = mock.Mock(spec_set=['task_impact', 'capacity_type'])
    j.task_impact = impact
    j.capacity_type = 'execution'
    return j


def Is(param):
    """
    param:
        [remaining_capacity1, remaining_capacity2, remaining_capacity3, ...]
        [(jobs_running1, capacity1), (jobs_running2, capacity2), (jobs_running3, capacity3), ...]
    """

    instances = []
    if isinstance(param[0], tuple):
        for (jobs_running, capacity) in param:
            inst = Mock()
            inst.capacity = capacity
            inst.jobs_running = jobs_running
            inst.node_type = 'execution'
            instances.append(inst)
    else:
        for i in param:
            inst = Mock()
            inst.remaining_capacity = i
            inst.node_type = 'execution'
            instances.append(inst)
    return instances


class TestInstanceGroup(object):
    @pytest.mark.parametrize(
        'task,instances,instance_fit_index,reason',
        [
            (T(100), Is([100]), 0, "Only one, pick it"),
            (T(100), Is([100, 100]), 0, "Two equally good fits, pick the first"),
            (T(100), Is([50, 100]), 1, "First instance not as good as second instance"),
            (T(100), Is([50, 0, 20, 100, 100, 100, 30, 20]), 3, "Pick Instance [3] as it is the first that the task fits in."),
            (T(100), Is([50, 0, 20, 99, 11, 1, 5, 99]), None, "The task don't a fit, you must a quit!"),
        ],
    )
    def test_fit_task_to_most_remaining_capacity_instance(self, task, instances, instance_fit_index, reason):
        InstanceGroup(id=10)
        tm_igs = TaskManagerInstanceGroups(instance_groups={'controlplane': {'instances': instances}})

        instance_picked = tm_igs.fit_task_to_most_remaining_capacity_instance(task, 'controlplane')

        if instance_fit_index is None:
            assert instance_picked is None, reason
        else:
            assert instance_picked == instances[instance_fit_index], reason

    @pytest.mark.parametrize(
        'instances,instance_fit_index,reason',
        [
            (Is([(0, 100)]), 0, "One idle instance, pick it"),
            (Is([(1, 100)]), None, "One un-idle instance, pick nothing"),
            (Is([(0, 100), (0, 200), (1, 500), (0, 700)]), 3, "Pick the largest idle instance"),
            (Is([(0, 100), (0, 200), (1, 10000), (0, 700), (0, 699)]), 3, "Pick the largest idle instance"),
            (Is([(0, 0)]), None, "One idle but down instance, don't pick it"),
        ],
    )
    def test_find_largest_idle_instance(self, instances, instance_fit_index, reason):
        def filter_offline_instances(*args):
            return filter(lambda i: i.capacity > 0, instances)

        InstanceGroup(id=10)
        instances_online_only = filter_offline_instances(instances)
        tm_igs = TaskManagerInstanceGroups(instance_groups={'controlplane': {'instances': instances_online_only}})

        if instance_fit_index is None:
            assert tm_igs.find_largest_idle_instance('controlplane') is None, reason
        else:
            assert tm_igs.find_largest_idle_instance('controlplane') == instances[instance_fit_index], reason


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
