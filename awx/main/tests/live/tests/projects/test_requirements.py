import os
import time

import pytest

from django.conf import settings

from awx.main.tests.live.tests.conftest import wait_for_job, wait_for_events

from awx.main.models import Project, SystemJobTemplate, Job


@pytest.fixture(scope='session')
def project_with_requirements(default_org):
    project, _ = Project.objects.get_or_create(
        name='project-with-requirements',
        scm_url='https://github.com/ansible/test-playbooks.git',
        scm_branch="with_requirements",
        scm_type='git',
        organization=default_org,
    )
    start = time.time()
    while time.time() - start < 3.0:
        if project.current_job or project.last_job or project.last_job_run:
            break
    assert project.current_job or project.last_job or project.last_job_run, f'Project never updated id={project.id}'
    update = project.current_job or project.last_job
    if update:
        wait_for_job(update)
    return project


def project_cache_is_populated(project):
    proj_cache = os.path.join(project.get_cache_path(), project.cache_id)
    return os.path.exists(proj_cache)


def test_cache_is_populated_after_cleanup_job(project_with_requirements):
    assert project_with_requirements.cache_id is not None  # already updated, should be something
    cache_path = os.path.join(settings.PROJECTS_ROOT, '.__awx_cache')
    assert os.path.exists(cache_path)

    assert project_cache_is_populated(project_with_requirements)

    cleanup_sjt = SystemJobTemplate.objects.get(name='Cleanup Job Details')
    cleanup_job = cleanup_sjt.create_unified_job(extra_vars={'days': 0})
    cleanup_job.signal_start()
    wait_for_job(cleanup_job)

    project_with_requirements.refresh_from_db()
    assert project_with_requirements.cache_id is not None
    update = project_with_requirements.update()
    wait_for_job(update)

    # Now, we still have a populated cache
    assert project_cache_is_populated(project_with_requirements)


def test_git_file_collection_requirement(live_tmp_folder, copy_project_folders, run_job_from_playbook):
    # this behaves differently, as use_requirements.yml references only the folder, does not include the github name
    run_job_from_playbook('test_git_file_collection_requirement', 'use_requirement.yml', scm_url=f'file://{live_tmp_folder}/with_requirements')
    job = Job.objects.filter(name__icontains='test_git_file_collection_requirement').order_by('-created').first()
    wait_for_events(job)
    assert '1234567890' in job.job_events.filter(task='debug variable', event='runner_on_ok').first().stdout
