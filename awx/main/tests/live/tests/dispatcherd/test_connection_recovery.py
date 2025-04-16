import time

from dispatcherd.config import settings
from dispatcherd.factories import get_control_from_settings
from dispatcherd.utils import serialize_task

from awx.main.models import JobTemplate

from awx.main.tests.data.sleep_task import sleep_break_connection
from awx.main.tests.live.tests.conftest import wait_for_job


def test_can_recover_connection():
    min_workers = settings.service['pool_kwargs']['min_workers']
    ctl = get_control_from_settings()

    for i in range(min_workers):
        sleep_break_connection.delay()

    task_name = serialize_task(sleep_break_connection)

    running_tasks = [1]
    start = time.monotonic()

    while running_tasks:
        responses = ctl.control_with_reply('running')
        assert len(responses) == 1
        response = responses[0]
        response.pop('node_id')
        running_tasks = [task_data for task_data in response.values() if task_data['task'] == task_name]
        if time.monotonic() - start > 5.0:
            assert False, f'Never finished working through tasks: {running_tasks}'

    # Jobs should still work even after the breaking task has ran
    jt = JobTemplate.objects.get(name='Demo Job Template')
    job = jt.create_unified_job()
    job.signal_start()
    wait_for_job(job)
