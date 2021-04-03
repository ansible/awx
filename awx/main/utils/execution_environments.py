from django.conf import settings

from awx.main.models.execution_environments import ExecutionEnvironment


def get_execution_environment_default():
    if settings.DEFAULT_EXECUTION_ENVIRONMENT is not None:
        return settings.DEFAULT_EXECUTION_ENVIRONMENT
    return ExecutionEnvironment.objects.filter(organization=None, managed_by_tower=True).first()
