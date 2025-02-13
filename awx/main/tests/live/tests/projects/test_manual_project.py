def test_manual_project(copy_project_folders, run_job_from_playbook):
    run_job_from_playbook('test_manual_project', 'debug.yml', local_path='debug')
