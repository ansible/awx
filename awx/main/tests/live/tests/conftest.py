import subprocess
import time

import pytest

# These tests are invoked from the awx/main/tests/live/ subfolder
# so any fixtures from higher-up conftest files must be explicitly included
from awx.main.tests.functional.conftest import *  # noqa
from awx.main.tests.conftest import load_all_credentials  # noqa: F401; pylint: disable=unused-import

from awx.main.models import Organization, Inventory


def wait_to_leave_status(job, status, timeout=30, sleep_time=0.1):
    """Wait until the job does NOT have the specified status with some timeout

    the default timeout is based on the task manager running a 20 second
    schedule, and the API does not guarentee working jobs faster than this
    """
    start = time.time()
    while time.time() - start < timeout:
        job.refresh_from_db()
        if job.status != status:
            return
        time.sleep(sleep_time)
    raise RuntimeError(f'Job failed to exit {status} in {timeout} seconds. job_explanation={job.job_explanation} tb={job.result_traceback}')


def wait_for_events(uj, timeout=2):
    start = time.time()
    while uj.event_processing_finished is False:
        time.sleep(0.2)
        uj.refresh_from_db()
        if time.time() - start > timeout:
            break


def unified_job_stdout(uj):
    wait_for_events(uj)
    return '\n'.join([event.stdout for event in uj.get_event_queryset().order_by('created')])


def wait_for_job(job, final_status='successful', running_timeout=800):
    wait_to_leave_status(job, 'pending')
    wait_to_leave_status(job, 'waiting')
    wait_to_leave_status(job, 'running', timeout=running_timeout)

    assert job.status == final_status, f'Job was not successful id={job.id} status={job.status} tb={job.result_traceback} output=\n{unified_job_stdout(job)}'


@pytest.fixture(scope='session')
def default_org():
    org = Organization.objects.filter(name='Default').first()
    if org is None:
        raise Exception('Tests expect Default org to already be created and it is not')
    return org


@pytest.fixture(scope='session')
def demo_inv(default_org):
    inventory, _ = Inventory.objects.get_or_create(name='Demo Inventory', defaults={'organization': default_org})
    return inventory


@pytest.fixture
def podman_image_generator():
    """
    Generate a tagless podman image from awx base EE
    """

    def fn():
        dockerfile = """
        FROM quay.io/ansible/awx-ee:latest
        RUN echo "Hello, Podman!" > /tmp/hello.txt
        """
        cmd = ['podman', 'build', '-f', '-']  # Create an image without a tag
        subprocess.run(cmd, capture_output=True, input=dockerfile, text=True, check=True)

    return fn
