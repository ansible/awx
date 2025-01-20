def test_indirect_host_counting(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_indirect_host_counting', 'run_task.yml', scm_url=f'file://{live_tmp_folder}/test_host_query')
    # TODO: add assertions that the host query data is populated
