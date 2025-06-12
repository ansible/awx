import logging

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
    job_label: str = settings.AWX_CONTAINER_GROUP_DEFAULT_JOB_LABEL
    ee = get_default_execution_environment()
    if ee is None:
        raise RuntimeError("Unable to find an execution environment.")

    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"namespace": settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE, "labels": {job_label: ""}},
        "spec": {
            "serviceAccountName": "default",
            "automountServiceAccountToken": False,
            "affinity": {
                "podAntiAffinity": {
                    "preferredDuringSchedulingIgnoredDuringExecution": [
                        {
                            "weight": 100,
                            "podAffinityTerm": {
                                "labelSelector": {
                                    "matchExpressions": [
                                        {
                                            "key": job_label,
                                            "operator": "Exists",
                                        }
                                    ]
                                },
                                "topologyKey": "kubernetes.io/hostname",
                            },
                        }
                    ]
                }
            },
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
