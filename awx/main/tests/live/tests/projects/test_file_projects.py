def test_git_file_project(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_git_file_project', 'debug.yml', scm_url=f'file://{live_tmp_folder}/debug')
