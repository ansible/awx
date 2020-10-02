import pytest
from unittest import mock
from unittest.mock import Mock

from awx.main.models import (
    Job,
    InstanceGroup,
)


def T(impact):
    j = mock.Mock(Job())
    j.task_impact = impact
    return j


def Is(param):
    '''
    param:
        [remaining_capacity1, remaining_capacity2, remaining_capacity3, ...]
        [(jobs_running1, capacity1), (jobs_running2, capacity2), (jobs_running3, capacity3), ...]
    '''

    instances = []
    if isinstance(param[0], tuple):
        for (jobs_running, capacity) in param:
            inst = Mock()
            inst.capacity = capacity
            inst.jobs_running = jobs_running
            instances.append(inst)
    else:
        for i in param:
            inst = Mock()
            inst.remaining_capacity = i
            instances.append(inst)
    return instances


class TestInstanceGroup(object):
    @pytest.mark.parametrize('task,instances,instance_fit_index,reason', [
        (T(100), Is([100]), 0, "Only one, pick it"),
        (T(100), Is([100, 100]), 0, "Two equally good fits, pick the first"),
        (T(100), Is([50, 100]), 1, "First instance not as good as second instance"),
        (T(100), Is([50, 0, 20, 100, 100, 100, 30, 20]), 3, "Pick Instance [3] as it is the first that the task fits in."),
        (T(100), Is([50, 0, 20, 99, 11, 1, 5, 99]), None, "The task don't a fit, you must a quit!"),
    ])
    def test_fit_task_to_most_remaining_capacity_instance(self, task, instances, instance_fit_index, reason):
        ig = InstanceGroup(id=10)

        instance_picked = ig.fit_task_to_most_remaining_capacity_instance(task, instances)

        if instance_fit_index is None:
            assert instance_picked is None, reason
        else:
            assert instance_picked == instances[instance_fit_index], reason

    @pytest.mark.parametrize('instances,instance_fit_index,reason', [
        (Is([(0, 100)]), 0, "One idle instance, pick it"),
        (Is([(1, 100)]), None, "One un-idle instance, pick nothing"),
        (Is([(0, 100), (0, 200), (1, 500), (0, 700)]), 3, "Pick the largest idle instance"),
        (Is([(0, 100), (0, 200), (1, 10000), (0, 700), (0, 699)]), 3, "Pick the largest idle instance"),
        (Is([(0, 0)]), None, "One idle but down instance, don't pick it"),
    ])
    def test_find_largest_idle_instance(self, instances, instance_fit_index, reason):
        def filter_offline_instances(*args):
            return filter(lambda i: i.capacity > 0, instances)

        ig = InstanceGroup(id=10)
        instances_online_only = filter_offline_instances(instances)

        if instance_fit_index is None:
            assert ig.find_largest_idle_instance(instances_online_only) is None, reason
        else:
            assert ig.find_largest_idle_instance(instances_online_only) == \
                instances[instance_fit_index], reason

