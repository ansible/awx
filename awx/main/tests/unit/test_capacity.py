import pytest

from awx.main.scheduler.task_manager_models import TaskManagerInstanceGroups, TaskManagerInstances


class FakeMeta(object):
    model_name = 'job'


class FakeObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            self._meta = FakeMeta()
            self._meta.concrete_model = self


class Job(FakeObject):
    task_impact = 43
    is_container_group_task = False
    controller_node = ''
    execution_node = ''

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
        default = InstanceGroup(name='default')
        i1 = Instance(hostname='i1', capacity=200, node_type='hybrid')
        i2 = Instance(hostname='i2', capacity=200, node_type='hybrid')
        i3 = Instance(hostname='i3', capacity=200, node_type='hybrid')
        ig_small.instances.add(i1)
        ig_large.instances.add(i2, i3)
        default.instances.add(i2)
        return [default, ig_large, ig_small]

    return stand_up_cluster


@pytest.fixture
def create_ig_manager():
    def _rf(ig_list, tasks):
        instances = TaskManagerInstances(tasks, instances=set(inst for ig in ig_list for inst in ig.instance_list))

        seed_igs = {}
        for ig in ig_list:
            seed_igs[ig.name] = {'instances': [instances[inst.hostname] for inst in ig.instance_list]}

        instance_groups = TaskManagerInstanceGroups(instance_groups=seed_igs)
        return instance_groups

    return _rf


@pytest.mark.parametrize('ig_name,consumed_capacity', [('default', 43), ('ig_large', 43 * 2), ('ig_small', 43)])
def test_running_capacity(sample_cluster, ig_name, consumed_capacity, create_ig_manager):
    default, ig_large, ig_small = sample_cluster()
    ig_list = [default, ig_large, ig_small]
    tasks = [Job(status='running', execution_node='i1'), Job(status='running', execution_node='i2'), Job(status='running', execution_node='i3')]

    instance_groups_mgr = create_ig_manager(ig_list, tasks)

    assert instance_groups_mgr.get_consumed_capacity(ig_name) == consumed_capacity


def test_offline_node_running(sample_cluster, create_ig_manager):
    """
    Assure that algorithm doesn't explode if a job is marked running
    in an offline node
    """
    default, ig_large, ig_small = sample_cluster()
    ig_small.instance_list[0].capacity = 0
    tasks = [Job(status='running', execution_node='i1')]
    instance_groups_mgr = create_ig_manager([default, ig_large, ig_small], tasks)
    assert instance_groups_mgr.get_consumed_capacity('ig_small') == 43
    assert instance_groups_mgr.get_remaining_capacity('ig_small') == 0


def test_offline_node_waiting(sample_cluster, create_ig_manager):
    """
    Same but for a waiting job
    """
    default, ig_large, ig_small = sample_cluster()
    ig_small.instance_list[0].capacity = 0
    tasks = [Job(status='waiting', execution_node='i1')]
    instance_groups_mgr = create_ig_manager([default, ig_large, ig_small], tasks)
    assert instance_groups_mgr.get_consumed_capacity('ig_small') == 43
    assert instance_groups_mgr.get_remaining_capacity('ig_small') == 0


def test_RBAC_reduced_filter(sample_cluster, create_ig_manager):
    """
    User can see jobs that are running in `ig_small` and `ig_large` IGs,
    but user does not have permission to see those actual instance groups.
    Verify that this does not blow everything up.
    """
    default, ig_large, ig_small = sample_cluster()
    tasks = [Job(status='waiting', execution_node='i1'), Job(status='waiting', execution_node='i2'), Job(status='waiting', execution_node='i3')]
    instance_groups_mgr = create_ig_manager([default], tasks)
    # Cross-links between groups not visible to current user,
    # so a naieve accounting of capacities is returned instead
    assert instance_groups_mgr.get_consumed_capacity('default') == 43
