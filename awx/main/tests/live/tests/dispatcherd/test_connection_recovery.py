import time

from dispatcherd.config import settings
from dispatcherd.factories import get_control_from_settings
from dispatcherd.utils import serialize_task

from awx.main.models import JobTemplate

from awx.main.tests.data.sleep_task import sleep_break_connection, advisory_lock_exception
from awx.main.tests.live.tests.conftest import wait_for_job


def poll_for_task_finish(task_name):
    running_tasks = [1]
    start = time.monotonic()
    ctl = get_control_from_settings()
    while running_tasks:
        responses = ctl.control_with_reply('running')
        assert len(responses) == 1
        response = responses[0]
        response.pop('node_id')
        running_tasks = [task_data for task_data in response.values() if task_data['task'] == task_name]
        if time.monotonic() - start > 5.0:
            assert False, f'Never finished working through tasks: {running_tasks}'


def check_jobs_work():
    jt = JobTemplate.objects.get(name='Demo Job Template')
    job = jt.create_unified_job()
    job.signal_start()
    wait_for_job(job)


def test_advisory_lock_error_clears():
    """Run a task that has an exception while holding advisory_lock

    This is regression testing for a bug in its exception handling
    expected to be fixed by
    https://github.com/ansible/django-ansible-base/pull/713

    This is an "easier" test case than the next,
    because it passes just by fixing the DAB case,
    and passing this does not generally guarentee that
    workers will not be left with a connection in a bad state.
    """
    min_workers = settings.service['pool_kwargs']['min_workers']

    for i in range(min_workers):
        advisory_lock_exception.delay()

    task_name = serialize_task(advisory_lock_exception)
    poll_for_task_finish(task_name)

    # Jobs should still work even after the breaking task has ran
    check_jobs_work()


def test_can_recover_connection():
    """Run a task that intentionally times out the worker connection

    If no connection fixing is implemented outside of that task scope,
    then subsequent tasks will all error, thus checking that jobs run,
    after running the sleep_break_connection task.
    """
    min_workers = settings.service['pool_kwargs']['min_workers']

    for i in range(min_workers):
        sleep_break_connection.delay()

    task_name = serialize_task(sleep_break_connection)
    poll_for_task_finish(task_name)

    # Jobs should still work even after the breaking task has ran
    check_jobs_work()
