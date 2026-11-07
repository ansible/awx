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


def sanitize_pod_spec(pod_spec):
    spec = pod_spec.get('spec', {})
    spec['automountServiceAccountToken'] = False

    removed_volume_names = set()
    kept_volumes = []
    for volume in spec.get('volumes', []):
        if 'secret' in volume:
            removed_volume_names.add(volume.get('name'))
            continue
        if 'projected' in volume:
            sources = volume.get('projected', {}).get('sources', [])
            if any('serviceAccountToken' in source for source in sources):
                removed_volume_names.add(volume.get('name'))
                continue
        kept_volumes.append(volume)
    if 'volumes' in spec:
        spec['volumes'] = kept_volumes

    if removed_volume_names:
        for container_key in ('containers', 'initContainers', 'ephemeralContainers'):
            for container in spec.get(container_key, []):
                if 'volumeMounts' in container:
                    container['volumeMounts'] = [vm for vm in container['volumeMounts'] if vm.get('name') not in removed_volume_names]

    return pod_spec


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
