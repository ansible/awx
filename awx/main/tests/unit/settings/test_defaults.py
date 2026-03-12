import pytest

from django.conf import settings


@pytest.mark.parametrize(
    "task_name",
    [
        'awx.main.tasks.system.awx_periodic_scheduler',
    ],
)
def test_DISPATCHER_SCHEDULE(mocker, task_name):
    assert task_name in settings.DISPATCHER_SCHEDULE
    assert 'schedule' in settings.DISPATCHER_SCHEDULE[task_name]
    assert type(settings.DISPATCHER_SCHEDULE[task_name]['schedule']) in (int, float)
    assert settings.DISPATCHER_SCHEDULE[task_name]['task'] == task_name

    # Ensures that the function exists
    mocker.patch(task_name)
