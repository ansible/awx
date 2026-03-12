from collections import OrderedDict

from django.conf import settings

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from awx.api.generics import APIView
from ansible_base.lib.utils.schema import extend_schema_if_available

from awx.main.scheduler import TaskManager, DependencyManager, WorkflowManager


class TaskManagerDebugView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    prefix = 'Task'
    resource_purpose = 'debug task manager'

    @extend_schema_if_available(extensions={"x-ai-description": "Trigger task manager scheduling"})
    def get(self, request):
        TaskManager().schedule()
        if not settings.AWX_DISABLE_TASK_MANAGERS:
            msg = f"Running {self.prefix} manager. To disable other triggers to the {self.prefix} manager, set AWX_DISABLE_TASK_MANAGERS to True"
        else:
            msg = f"AWX_DISABLE_TASK_MANAGERS is True, this view is the only way to trigger the {self.prefix} manager"
        return Response(msg)


class DependencyManagerDebugView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    prefix = 'Dependency'
    resource_purpose = 'debug dependency manager'

    @extend_schema_if_available(extensions={"x-ai-description": "Trigger dependency manager scheduling"})
    def get(self, request):
        DependencyManager().schedule()
        if not settings.AWX_DISABLE_TASK_MANAGERS:
            msg = f"Running {self.prefix} manager. To disable other triggers to the {self.prefix} manager, set AWX_DISABLE_TASK_MANAGERS to True"
        else:
            msg = f"AWX_DISABLE_TASK_MANAGERS is True, this view is the only way to trigger the {self.prefix} manager"
        return Response(msg)


class WorkflowManagerDebugView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    prefix = 'Workflow'
    resource_purpose = 'debug workflow manager'

    @extend_schema_if_available(extensions={"x-ai-description": "Trigger workflow manager scheduling"})
    def get(self, request):
        WorkflowManager().schedule()
        if not settings.AWX_DISABLE_TASK_MANAGERS:
            msg = f"Running {self.prefix} manager. To disable other triggers to the {self.prefix} manager, set AWX_DISABLE_TASK_MANAGERS to True"
        else:
            msg = f"AWX_DISABLE_TASK_MANAGERS is True, this view is the only way to trigger the {self.prefix} manager"
        return Response(msg)


class DebugRootView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    resource_purpose = 'debug endpoints root'

    @extend_schema_if_available(extensions={"x-ai-description": "List available debug endpoints"})
    def get(self, request, format=None):
        '''List of available debug urls'''
        data = OrderedDict()
        data['task_manager'] = '/api/debug/task_manager/'
        data['dependency_manager'] = '/api/debug/dependency_manager/'
        data['workflow_manager'] = '/api/debug/workflow_manager/'
        return Response(data)
