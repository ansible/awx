import pytest

from awx.main.models import InstanceGroup


class FakeObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Job(FakeObject):
    task_impact = 43
    is_containerized = False

    def log_format(self):
        return 'job 382 (fake)'


@pytest.fixture
def sample_cluster():
    def stand_up_cluster():

        class Instances(FakeObject):
            def add(self, *args):
                for instance in args:
                    self.obj.instance_list.append(instance)

            def all(self):
                return self.obj.instance_list

        class InstanceGroup(FakeObject):

            def __init__(self, **kwargs):
                super(InstanceGroup, self).__init__(**kwargs)
                self.instance_list = []

            @property
            def instances(self):
                mgr = Instances(obj=self)
                return mgr


        class Instance(FakeObject):
            pass


        ig_small = InstanceGroup(name='ig_small')
        ig_large = InstanceGroup(name='ig_large')
        tower = InstanceGroup(name='tower')
        i1 = Instance(hostname='i1', capacity=200)
        i2 = Instance(hostname='i2', capacity=200)
        i3 = Instance(hostname='i3', capacity=200)
        ig_small.instances.add(i1)
        ig_large.instances.add(i2, i3)
        tower.instances.add(i2)
        return [tower, ig_large, ig_small]
    return stand_up_cluster


def test_committed_capacity(sample_cluster):
    tower, ig_large, ig_small = sample_cluster()
    tasks = [
        Job(status='waiting', instance_group=tower),
        Job(status='waiting', instance_group=ig_large),
        Job(status='waiting', instance_group=ig_small)
    ]
    capacities = InstanceGroup.objects.capacity_values(
        qs=[tower, ig_large, ig_small], tasks=tasks, breakdown=True
    )
    # Jobs submitted to either tower or ig_larg must count toward both
    assert capacities['tower']['committed_capacity'] == 43 * 2
    assert capacities['ig_large']['committed_capacity'] == 43 * 2
    assert capacities['ig_small']['committed_capacity'] == 43


def test_running_capacity(sample_cluster):
    tower, ig_large, ig_small = sample_cluster()
    tasks = [
        Job(status='running', execution_node='i1'),
        Job(status='running', execution_node='i2'),
        Job(status='running', execution_node='i3')
    ]
    capacities = InstanceGroup.objects.capacity_values(
        qs=[tower, ig_large, ig_small], tasks=tasks, breakdown=True
    )
    # Tower is only given 1 instance
    assert capacities['tower']['running_capacity'] == 43
    # Large IG has 2 instances
    assert capacities['ig_large']['running_capacity'] == 43 * 2
    assert capacities['ig_small']['running_capacity'] == 43


def test_offline_node_running(sample_cluster):
    """
    Assure that algorithm doesn't explode if a job is marked running
    in an offline node
    """
    tower, ig_large, ig_small = sample_cluster()
    ig_small.instance_list[0].capacity = 0
    tasks = [Job(status='running', execution_node='i1', instance_group=ig_small)]
    capacities = InstanceGroup.objects.capacity_values(
        qs=[tower, ig_large, ig_small], tasks=tasks)
    assert capacities['ig_small']['consumed_capacity'] == 43


def test_offline_node_waiting(sample_cluster):
    """
    Same but for a waiting job
    """
    tower, ig_large, ig_small = sample_cluster()
    ig_small.instance_list[0].capacity = 0
    tasks = [Job(status='waiting', instance_group=ig_small)]
    capacities = InstanceGroup.objects.capacity_values(
        qs=[tower, ig_large, ig_small], tasks=tasks)
    assert capacities['ig_small']['consumed_capacity'] == 43


def test_RBAC_reduced_filter(sample_cluster):
    """
    User can see jobs that are running in `ig_small` and `ig_large` IGs,
    but user does not have permission to see those actual instance groups.
    Verify that this does not blow everything up.
    """
    tower, ig_large, ig_small = sample_cluster()
    tasks = [
        Job(status='waiting', instance_group=tower),
        Job(status='waiting', instance_group=ig_large),
        Job(status='waiting', instance_group=ig_small)
    ]
    capacities = InstanceGroup.objects.capacity_values(
        qs=[tower], tasks=tasks, breakdown=True
    )
    # Cross-links between groups not visible to current user,
    # so a naieve accounting of capacities is returned instead
    assert capacities['tower']['committed_capacity'] == 43
