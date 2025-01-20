def test_manual_project(copy_project_folders, run_job_from_playbook):
    run_job_from_playbook('test_manual_project', 'debug.yml', local_path='debug')


def test_git_file_collection_requirement(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_git_file_collection_requirement', 'run_task.yml', scm_url=f'file://{live_tmp_folder}/test_host_query')
