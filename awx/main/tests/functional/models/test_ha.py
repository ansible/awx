import pytest

# AWX
from awx.main.ha import is_ha_environment
from awx.main.models.ha import Instance
from awx.main.dispatch.pool import get_auto_max_workers

# Django
from django.test.utils import override_settings


@pytest.mark.django_db
def test_multiple_instances():
    for i in range(2):
        Instance.objects.create(hostname=f'foo{i}', node_type='hybrid')
    assert is_ha_environment()


@pytest.mark.django_db
def test_db_localhost():
    Instance.objects.create(hostname='foo', node_type='hybrid')
    Instance.objects.create(hostname='bar', node_type='execution')
    assert is_ha_environment() is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    'settings',
    [
        dict(SYSTEM_TASK_ABS_MEM='16Gi', SYSTEM_TASK_ABS_CPU='24', SYSTEM_TASK_FORKS_MEM=400, SYSTEM_TASK_FORKS_CPU=4),
        dict(SYSTEM_TASK_ABS_MEM='124Gi', SYSTEM_TASK_ABS_CPU='2', SYSTEM_TASK_FORKS_MEM=None, SYSTEM_TASK_FORKS_CPU=None),
    ],
    ids=['cpu_dominated', 'memory_dominated'],
)
def test_dispatcher_max_workers_reserve(settings, fake_redis):
    """This tests that the dispatcher max_workers matches instance capacity

    Assumes capacity_adjustment is 1,
    plus reserve worker count
    """
    with override_settings(**settings):
        i = Instance.objects.create(hostname='test-1', node_type='hybrid')
        i.local_health_check()

        assert get_auto_max_workers() == i.capacity + 7, (i.cpu, i.memory, i.cpu_capacity, i.mem_capacity)
