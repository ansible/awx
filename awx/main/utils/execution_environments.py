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
                }
            ],
        },
    }
