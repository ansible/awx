import os
import json
import pytest
import tempfile
import subprocess

from unittest import mock

from awx.main.tasks.receptor import _convert_args_to_cli, run_until_complete
from awx.main.tasks.system import CleanupImagesAndFiles
from awx.main.models import Instance, JobTemplate


def get_podman_images():
    cmd = ['podman', 'images', '--format', 'json']
    return json.loads((subprocess.run(cmd, capture_output=True, text=True, check=True)).stdout)


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


@pytest.mark.parametrize(
    'worktype',
    ('remote', 'local'),
)
def test_tagless_image(podman_image_generator, worktype: str):
    """
    Ensure podman images on Control and Hybrid nodes are deleted during cleanup.
    """
    podman_image_generator()

    dangling_image = next((image for image in get_podman_images() if image.get('Dangling', False)), None)
    assert dangling_image

    instance_me = Instance.objects.me()

    match worktype:
        case 'local':
            CleanupImagesAndFiles.run_local(instance_me, image_prune=True)
        case 'remote':
            with (
                mock.patch(
                    'awx.main.tasks.receptor.run_until_complete', lambda *args, **kwargs: run_until_complete(*args, worktype='local', ttl=None, **kwargs)
                ),
                mock.patch('awx.main.tasks.system.CleanupImagesAndFiles.get_execution_instances', lambda: [Instance.objects.me()]),
            ):
                CleanupImagesAndFiles.run_remote(instance_me, image_prune=True)
        case _:
            raise ValueError(f'worktype "{worktype}" not supported.')

    for image in get_podman_images():
        assert image['Id'] != dangling_image['Id']
