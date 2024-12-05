import time

# These tests are invoked from the awx/main/tests/live/ subfolder
# so any fixtures from higher-up conftest files must be explicitly included
from awx.main.tests.functional.conftest import *  # noqa


def wait_to_leave_status(job, status, timeout=25, sleep_time=0.1):
    """Wait until the job does NOT have the specified status with some timeout

    the default timeout of 25 if chosen because the task manager runs on a 20 second
    schedule, and the API does not guarentee working jobs faster than this
    """
    start = time.time()
    while time.time() - start < timeout:
        job.refresh_from_db()
        if job.status != status:
            return
        time.sleep(sleep_time)
    raise RuntimeError(f'Job failed to exit {status} in {timeout} seconds. job_explanation={job.job_explanation} tb={job.result_traceback}')


def wait_for_job(job, final_status='successful', running_timeout=800):
    wait_to_leave_status(job, 'pending')
    wait_to_leave_status(job, 'waiting')
    wait_to_leave_status(job, 'running', timeout=running_timeout)

    assert job.status == final_status, f'Job was not successful id={job.id} status={job.status}'
