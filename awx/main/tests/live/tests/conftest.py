import subprocess
import time
import os
import shutil
import tempfile

import pytest

from django.conf import settings

from awx.api.versioning import reverse

# These tests are invoked from the awx/main/tests/live/ subfolder
# so any fixtures from higher-up conftest files must be explicitly included
from awx.main.tests.functional.conftest import *  # noqa
from awx.main.tests.conftest import load_all_credentials  # noqa: F401; pylint: disable=unused-import
from awx.main.tests import data

from awx.main.models import Project, JobTemplate, Organization, Inventory


PROJ_DATA = os.path.join(os.path.dirname(data.__file__), 'projects')


def _copy_folders(source_path, dest_path, clear=False):
    "folder-by-folder, copy dirs in the source root dir to the destination root dir"
    for dirname in os.listdir(source_path):
        source_dir = os.path.join(source_path, dirname)
        expected_dir = os.path.join(dest_path, dirname)
        if clear and os.path.exists(expected_dir):
            shutil.rmtree(expected_dir)
        if (not os.path.isdir(source_dir)) or os.path.exists(expected_dir):
            continue
        shutil.copytree(source_dir, expected_dir)


GIT_COMMANDS = (
    'git config --global init.defaultBranch devel; '
    'git init; '
    'git config user.email jenkins@ansible.com; '
    'git config user.name DoneByTest; '
    'git add .; '
    'git commit -m "initial commit"'
)


@pytest.fixture(scope='session')
def live_tmp_folder():
    path = os.path.join(tempfile.gettempdir(), 'live_tests')
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    _copy_folders(PROJ_DATA, path)
    for dirname in os.listdir(path):
        source_dir = os.path.join(path, dirname)
        subprocess.run(GIT_COMMANDS, cwd=source_dir, shell=True)
    if path not in settings.AWX_ISOLATION_SHOW_PATHS:
        settings.AWX_ISOLATION_SHOW_PATHS = settings.AWX_ISOLATION_SHOW_PATHS + [path]
    return path


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


@pytest.fixture
def run_job_from_playbook(default_org, demo_inv, post, admin):
    def _rf(test_name, playbook, local_path=None, scm_url=None):
        project_name = f'{test_name} project'
        jt_name = f'{test_name} JT: {playbook}'

        old_proj = Project.objects.filter(name=project_name).first()
        if old_proj:
            old_proj.delete()

        old_jt = JobTemplate.objects.filter(name=jt_name).first()
        if old_jt:
            old_jt.delete()

        proj_kwargs = {'name': project_name, 'organization': default_org.id}
        if local_path:
            # manual path
            proj_kwargs['scm_type'] = ''
            proj_kwargs['local_path'] = local_path
        elif scm_url:
            proj_kwargs['scm_type'] = 'git'
            proj_kwargs['scm_url'] = scm_url
        else:
            raise RuntimeError('Need to provide scm_url or local_path')

        result = post(
            reverse('api:project_list'),
            proj_kwargs,
            admin,
            expect=201,
        )
        proj = Project.objects.get(id=result.data['id'])

        if proj.current_job:
            wait_for_job(proj.current_job)

        assert proj.get_project_path()
        assert playbook in proj.playbooks

        result = post(
            reverse('api:job_template_list'),
            {'name': jt_name, 'project': proj.id, 'playbook': playbook, 'inventory': demo_inv.id},
            admin,
            expect=201,
        )
        jt = JobTemplate.objects.get(id=result.data['id'])
        job = jt.create_unified_job()
        job.signal_start()

        wait_for_job(job)
        assert job.status == 'successful'

    return _rf
