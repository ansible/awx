import os
from pathlib import Path

from django.conf import settings

from awx.main.models.execution_environments import ExecutionEnvironment


def get_default_execution_environment():
    if settings.DEFAULT_EXECUTION_ENVIRONMENT is not None:
        return settings.DEFAULT_EXECUTION_ENVIRONMENT
    return ExecutionEnvironment.objects.filter(organization=None, managed_by_tower=True).first()


def get_default_pod_spec():

    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"namespace": settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE},
        "spec": {
            "containers": [
                {
                    "image": get_default_execution_environment().image,
                    "name": 'worker',
                    "args": ['ansible-runner', 'worker', '--private-data-dir=/runner'],
                }
            ],
        },
    }


# this is the root of the private data dir as seen from inside
# of the container running a job
CONTAINER_ROOT = '/runner'


def to_container_path(path, private_data_dir):
    """Given a path inside of the host machine filesystem,
    this returns the expected path which would be observed by the job running
    inside of the EE container.
    This only handles the volume mount from private_data_dir to /runner
    """
    if not os.path.isabs(private_data_dir):
        raise RuntimeError('The private_data_dir path must be absolute')
    if private_data_dir != path and Path(private_data_dir) not in Path(path).resolve().parents:
        raise RuntimeError(f'Cannot convert path {path} unless it is a subdir of {private_data_dir}')
    return path.replace(private_data_dir, CONTAINER_ROOT, 1)


def to_host_path(path, private_data_dir):
    """Given a path inside of the EE container, this gives the absolute path
    on the host machine within the private_data_dir
    """
    if not os.path.isabs(private_data_dir):
        raise RuntimeError('The private_data_dir path must be absolute')
    if CONTAINER_ROOT != path and Path(CONTAINER_ROOT) not in Path(path).resolve().parents:
        raise RuntimeError(f'Cannot convert path {path} unless it is a subdir of {CONTAINER_ROOT}')
    return path.replace(CONTAINER_ROOT, private_data_dir, 1)
