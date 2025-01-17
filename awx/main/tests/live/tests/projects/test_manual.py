import pytest
import os
import shutil

from django.conf import settings

from awx.api.versioning import reverse
from awx.main.tests import data
from awx.main.models import Project, JobTemplate, Inventory

from awx.main.tests.live.tests.conftest import wait_for_job

DATA = os.path.join(os.path.dirname(data.__file__), 'projects')


@pytest.fixture
def copy_project_folders():
    proj_root = settings.PROJECTS_ROOT
    for dirname in os.listdir(DATA):
        source_dir = os.path.join(DATA, dirname)
        expected_dir = os.path.join(proj_root, dirname)
        if (not os.path.isdir(source_dir)) or os.path.exists(expected_dir):
            continue
        shutil.copytree(source_dir, expected_dir)


def test_manual_project(copy_project_folders, default_org, post, admin):
    old_proj = Project.objects.filter(name='Manual Project - debug').first()
    if old_proj:
        old_proj.delete()

    old_jt = JobTemplate.objects.filter(name='debug from Manual Project').first()
    if old_jt:
        old_jt.delete()

    result = post(
        reverse('api:project_list'),
        {'name': 'Manual Project - debug', 'organization': default_org.id, 'scm_type': '', 'local_path': 'debug'},  # manual
        admin,
        expect=201,
    )
    proj = Project.objects.get(id=result.data['id'])
    assert proj.get_project_path()
    assert 'debug.yml' in proj.playbooks
    inventory, _ = Inventory.objects.get_or_create(name='Demo Inventory', defaults={'organization': default_org})
    result = post(
        reverse('api:job_template_list'),
        {'name': 'debug from Manual Project', 'project': proj.id, 'playbook': 'debug.yml', 'inventory': inventory.id},
        admin,
        expect=201,
    )
    jt = JobTemplate.objects.get(id=result.data['id'])
    job = jt.create_unified_job()
    job.signal_start()

    wait_for_job(job)
    assert job.status == 'successful'
