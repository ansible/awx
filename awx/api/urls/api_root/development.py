from django.urls import re_path

from awx import MODE
from awx.api.views.debug import (
    DebugRootView,
    TaskManagerDebugView,
    DependencyManagerDebugView,
    WorkflowManagerDebugView,
)
from awx.api.swagger import schema_view

urls = []

if MODE == 'development':
    # Only include these if we are in the development environment
    entry_point = r'^debug'
    urls = [
        re_path(r'^$', DebugRootView.as_view(), name='debug'),
        re_path(r'^task_manager/$', TaskManagerDebugView.as_view(), name='task_manager'),
        re_path(r'^dependency_manager/$', DependencyManagerDebugView.as_view(), name='dependency_manager'),
        re_path(r'^workflow_manager/$', WorkflowManagerDebugView.as_view(), name='workflow_manager'),
    ]

    extend_urls = [
        re_path(r'^swagger(?P<format>\.json|\.yaml)/$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
