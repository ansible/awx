import os
import subprocess

import pytest

from awx.main.tests.live.tests.conftest import wait_for_job


def test_git_file_project(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_git_file_project', 'debug.yml', scm_url=f'file://{live_tmp_folder}/debug')


@pytest.mark.parametrize('allow_override', [True, False])
def test_amend_commit(live_tmp_folder, project_factory, allow_override):
    proj = project_factory(scm_url=f'file://{live_tmp_folder}/debug', allow_override=allow_override)
    assert proj.current_job
    wait_for_job(proj.current_job)
    assert proj.allow_override is allow_override

    source_dir = os.path.join(live_tmp_folder, 'debug')
    subprocess.run('git commit --amend --no-edit', cwd=source_dir, shell=True)

    update = proj.update()
    update.signal_start()
    wait_for_job(update)
