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
    if not os.path.isabs(private_data_dir):
        raise Exception
    if Path(private_data_dir) not in Path(path).parents:
        raise Exception
    return path.replace(private_data_dir, CONTAINER_ROOT)
