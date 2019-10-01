from django.test import TransactionTestCase

from awx.main.models import (
    Instance,
    InstanceGroup,
)


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
            inst_map, ig_map = InstanceGroup.objects.capacity_mapping()
        assert inst_map['i1'] == set(['ig_small'])
        assert inst_map['i2'] == set(['ig_large', 'tower'])
        assert ig_map['ig_small'] == set(['ig_small'])
        assert ig_map['ig_large'] == set(['ig_large', 'tower'])
        assert ig_map['tower'] == set(['ig_large', 'tower'])
