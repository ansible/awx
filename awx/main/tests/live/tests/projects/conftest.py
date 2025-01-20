import pytest
import os
import shutil
import tempfile
import subprocess

from django.conf import settings

from awx.api.versioning import reverse
from awx.main.tests import data
from awx.main.models import Project, JobTemplate

from awx.main.tests.live.tests.conftest import wait_for_job

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


@pytest.fixture(scope='session')
def copy_project_folders():
    proj_root = settings.PROJECTS_ROOT
    if not os.path.exists(proj_root):
        os.mkdir(proj_root)
    _copy_folders(PROJ_DATA, proj_root, clear=True)


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
