from django.test import TransactionTestCase

from awx.main.models import (
    Instance,
    InstanceGroup,
)
from awx.main.scheduler.task_manager_models import TaskManagerInstanceGroups, TaskManagerInstances


class TestInstanceGroupInstanceMapping(TransactionTestCase):
    def sample_cluster(self):
        ig_small = InstanceGroup.objects.create(name='ig_small')
        ig_large = InstanceGroup.objects.create(name='ig_large')
        default = InstanceGroup.objects.create(name='default')
        i1 = Instance.objects.create(hostname='i1', capacity=200)
        i2 = Instance.objects.create(hostname='i2', capacity=200)
        i3 = Instance.objects.create(hostname='i3', capacity=200)
        ig_small.instances.add(i1)
        ig_large.instances.add(i2, i3)
        default.instances.add(i2)
        return [default, ig_large, ig_small]

    def test_mapping(self):
        self.sample_cluster()
        with self.assertNumQueries(3):
            instances = TaskManagerInstances([])  # empty task list
            instance_groups = TaskManagerInstanceGroups(instances_by_hostname=instances)

        ig_instance_map = instance_groups.instance_groups

        assert set(i.hostname for i in ig_instance_map['ig_small']['instances']) == set(['i1'])
        assert set(i.hostname for i in ig_instance_map['ig_large']['instances']) == set(['i2', 'i3'])
        assert set(i.hostname for i in ig_instance_map['default']['instances']) == set(['i2'])
