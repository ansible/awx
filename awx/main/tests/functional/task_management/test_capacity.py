import pytest
import mock

from django.test import TransactionTestCase

from awx.main.models import (
    Job,
    Instance,
    InstanceGroup,
)


@pytest.mark.django_db
class TestCapacityMapping(TransactionTestCase):

    def sample_cluster(self):
        ig_small = InstanceGroup.objects.create(name='ig_small')
        ig_large = InstanceGroup.objects.create(name='ig_large')
        tower = InstanceGroup.objects.create(name='tower')
        i1 = Instance.objects.create(hostname='i1', capacity=200)
        i2 = Instance.objects.create(hostname='i2', capacity=200)
        i3 = Instance.objects.create(hostname='i3', capacity=200)
        ig_small.instances.add(i1)
        ig_large.instances.add(i2, i3)
        tower.instances.add(i2)
        return [tower, ig_large, ig_small]

    def test_mapping(self):
        self.sample_cluster()
        with self.assertNumQueries(2):
            inst_map, ig_map = Instance.objects.capacity_mapping()
        assert inst_map['i1'] == set(['ig_small'])
        assert inst_map['i2'] == set(['ig_large', 'tower'])
        assert ig_map['ig_small'] == set(['ig_small'])
        assert ig_map['ig_large'] == set(['ig_large', 'tower'])
        assert ig_map['tower'] == set(['ig_large', 'tower'])

    def test_committed_capacity(self):
        tower, ig_large, ig_small = self.sample_cluster()
        tasks = [
            Job(status='waiting', instance_group=tower),
            Job(status='waiting', instance_group=ig_large),
            Job(status='waiting', instance_group=ig_small)
        ]
        with mock.patch.object(Job, 'task_impact', new=mock.PropertyMock(return_value=43)):
            capacities = InstanceGroup.objects.capacity_values(
                tasks=tasks, breakdown=True
            )
        # Jobs submitted to either tower or ig_larg must count toward both
        assert capacities['tower']['committed_capacity'] == 43 * 2
        assert capacities['ig_large']['committed_capacity'] == 43 * 2
        assert capacities['ig_small']['committed_capacity'] == 43

    def test_running_capacity(self):
        tower, ig_large, ig_small = self.sample_cluster()
        tasks = [
            Job(status='running', execution_node='i1'),
            Job(status='running', execution_node='i2'),
            Job(status='running', execution_node='i3')
        ]
        with mock.patch.object(Job, 'task_impact', new=mock.PropertyMock(return_value=43)):
            capacities = InstanceGroup.objects.capacity_values(
                tasks=tasks, breakdown=True
            )
        # Tower is only given 1 instance
        assert capacities['tower']['running_capacity'] == 43
        # Large IG has 2 instances
        assert capacities['ig_large']['running_capacity'] == 43 * 2
        assert capacities['ig_small']['running_capacity'] == 43
