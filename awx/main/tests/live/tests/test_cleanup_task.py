import os
import tempfile
import subprocess

from awx.main.tasks.receptor import _convert_args_to_cli
from awx.main.models import Instance, JobTemplate


def test_folder_cleanup_multiple_running_jobs_execution_node(request):
    demo_jt = JobTemplate.objects.get(name='Demo Job Template')

    jobs = [demo_jt.create_unified_job(_eager_fields={'status': 'running'}) for i in range(3)]

    def delete_jobs():
        for job in jobs:
            job.delete()

    request.addfinalizer(delete_jobs)

    job_dirs = []
    job_patterns = []
    for job in jobs:
        job_pattern = f'awx_{job.id}_1234'
        job_dir = os.path.join(tempfile.gettempdir(), job_pattern)
        job_patterns.append(job_pattern)
        job_dirs.append(job_dir)
        os.mkdir(job_dir)

    inst = Instance.objects.me()
    runner_cleanup_kwargs = inst.get_cleanup_task_kwargs(exclude_strings=job_patterns, grace_period=0)

    # We can not call worker_cleanup directly because execution and control nodes are not fungible
    args = _convert_args_to_cli(runner_cleanup_kwargs)
    remote_command = ' '.join(args)

    subprocess.call('ansible-runner worker ' + remote_command, shell=True)
    print('ansible-runner worker ' + remote_command)

    assert [os.path.exists(job_dir) for job_dir in job_dirs] == [True for i in range(3)]
