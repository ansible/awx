import pytest
from unittest import mock

from rest_framework.test import APIRequestFactory, force_authenticate

from awx.api.views.debug import (
    DebugRootView,
    TaskManagerDebugView,
    DependencyManagerDebugView,
    WorkflowManagerDebugView,
)
from awx.api.permissions import IsSystemAdmin

ALL_DEBUG_VIEWS = [
    DebugRootView,
    TaskManagerDebugView,
    DependencyManagerDebugView,
    WorkflowManagerDebugView,
]

MANAGER_VIEWS = [
    pytest.param(
        TaskManagerDebugView,
        'awx.api.views.debug.TaskManager',
        id='TaskManagerDebugView',
    ),
    pytest.param(
        DependencyManagerDebugView,
        'awx.api.views.debug.DependencyManager',
        id='DependencyManagerDebugView',
    ),
    pytest.param(
        WorkflowManagerDebugView,
        'awx.api.views.debug.WorkflowManager',
        id='WorkflowManagerDebugView',
    ),
]


def _superuser():
    user = mock.MagicMock()
    user.is_authenticated = True
    user.is_superuser = True
    user.is_anonymous = False
    return user


def _normal_user():
    user = mock.MagicMock()
    user.is_authenticated = True
    user.is_superuser = False
    user.is_anonymous = False
    return user


class TestDebugViewPermissionClasses:
    """All debug views must declare IsSystemAdmin, not AllowAny."""

    @pytest.mark.parametrize(
        'view_class',
        ALL_DEBUG_VIEWS,
        ids=[v.__name__ for v in ALL_DEBUG_VIEWS],
    )
    def test_permission_class_is_system_admin(self, view_class):
        assert IsSystemAdmin in view_class.permission_classes


class TestDebugViewRejectsUnauthenticated:
    """Anonymous requests must be denied (401/403)."""

    @pytest.mark.parametrize(
        'view_class',
        ALL_DEBUG_VIEWS,
        ids=[v.__name__ for v in ALL_DEBUG_VIEWS],
    )
    def test_anonymous_request_blocked(self, view_class):
        request = APIRequestFactory().get('/test/')
        force_authenticate(request, user=None)
        response = view_class.as_view()(request)
        assert response.status_code in (401, 403)


class TestDebugViewRejectsNonSuperuser:
    """Authenticated non-superuser requests must be denied (403)."""

    @pytest.mark.parametrize(
        'view_class',
        ALL_DEBUG_VIEWS,
        ids=[v.__name__ for v in ALL_DEBUG_VIEWS],
    )
    def test_normal_user_request_blocked(self, view_class):
        request = APIRequestFactory().get('/test/')
        force_authenticate(request, user=_normal_user())
        response = view_class.as_view()(request)
        assert response.status_code == 403


class TestDebugViewPermitsSuperuser:
    """Superuser requests must be allowed (200)."""

    def test_root_view_returns_200(self):
        request = APIRequestFactory().get('/test/')
        force_authenticate(request, user=_superuser())
        response = DebugRootView.as_view()(request)
        assert response.status_code == 200

    @pytest.mark.parametrize('view_class,manager_path', MANAGER_VIEWS)
    def test_manager_view_returns_200(self, view_class, manager_path):
        request = APIRequestFactory().get('/test/')
        force_authenticate(request, user=_superuser())
        with mock.patch(manager_path) as mock_mgr, mock.patch('awx.api.views.debug.settings') as mock_settings:
            mock_mgr.return_value.schedule.return_value = None
            mock_settings.AWX_DISABLE_TASK_MANAGERS = False
            response = view_class.as_view()(request)
        assert response.status_code == 200
