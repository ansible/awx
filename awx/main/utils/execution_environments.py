import os
import logging
from pathlib import Path

from django.conf import settings

from awx.main.models.execution_environments import ExecutionEnvironment


logger = logging.getLogger(__name__)


def get_control_plane_execution_environment():
    ee = ExecutionEnvironment.objects.filter(organization=None, managed=True).first()
    if ee == None:
        logger.error('Failed to find control plane ee, there are no managed EEs without organizations')
        raise RuntimeError("Failed to find default control plane EE")
    return ee


def get_default_execution_environment():
    if settings.DEFAULT_EXECUTION_ENVIRONMENT is not None:
        return settings.DEFAULT_EXECUTION_ENVIRONMENT
    installed_default = ExecutionEnvironment.objects.filter(
        image__in=[ee['image'] for ee in settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS], organization=None, managed=False
    ).first()
    if installed_default:
        return installed_default
    return ExecutionEnvironment.objects.filter(organization=None, managed=False).first()


def get_default_pod_spec():
    ee = get_default_execution_environment()
    if ee is None:
        raise RuntimeError("Unable to find an execution environment.")

    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"namespace": settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE},
        "spec": {
            "serviceAccountName": "default",
            "automountServiceAccountToken": False,
            "containers": [
                {
                    "image": ee.image,
                    "name": 'worker',
                    "args": ['ansible-runner', 'worker', '--private-data-dir=/runner'],
                    "resources": {"requests": {"cpu": "250m", "memory": "100Mi"}},
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
    # due to how tempfile.mkstemp works, we are probably passed a resolved path, but unresolved private_data_dir
    resolved_path = Path(path).resolve()
    resolved_pdd = Path(private_data_dir).resolve()
    if resolved_pdd != resolved_path and resolved_pdd not in resolved_path.parents:
        raise RuntimeError(f'Cannot convert path {resolved_path} unless it is a subdir of {resolved_pdd}')
    return str(resolved_path).replace(str(resolved_pdd), CONTAINER_ROOT, 1)
