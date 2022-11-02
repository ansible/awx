from django.urls import re_path

from awx.api.views.debug import (
    DebugRootView,
    TaskManagerDebugView,
    DependencyManagerDebugView,
    WorkflowManagerDebugView,
)

urls = [
    re_path(r'^$', DebugRootView.as_view(), name='debug'),
    re_path(r'^task_manager/$', TaskManagerDebugView.as_view(), name='task_manager'),
    re_path(r'^dependency_manager/$', DependencyManagerDebugView.as_view(), name='dependency_manager'),
    re_path(r'^workflow_manager/$', WorkflowManagerDebugView.as_view(), name='workflow_manager'),
]

__all__ = ['urls']
