# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django REST Framework
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework import permissions

# AWX
from awx.main.access import check_user_access
from awx.main.models import Inventory, UnifiedJob
from awx.main.utils import get_object_or_400

logger = logging.getLogger('awx.api.permissions')

__all__ = ['ModelAccessPermission', 'JobTemplateCallbackPermission', 'VariableDataPermission',
           'TaskPermission', 'ProjectUpdatePermission', 'InventoryInventorySourcesUpdatePermission',
           'UserPermission', 'IsSuperUser', 'InstanceGroupTowerPermission', 'WorkflowApprovalPermission']


class ModelAccessPermission(permissions.BasePermission):
    '''
    Default permissions class to check user access based on the model and
    request method, optionally verifying the request data.
    '''

    def check_options_permissions(self, request, view, obj=None):
        return self.check_get_permissions(request, view, obj)

    def check_head_permissions(self, request, view, obj=None):
        return self.check_get_permissions(request, view, obj)

    def check_get_permissions(self, request, view, obj=None):
        if hasattr(view, 'parent_model'):
            parent_obj = view.get_parent_object()
            if not check_user_access(request.user, view.parent_model, 'read',
                                     parent_obj):
                return False
        if not obj:
            return True
        return check_user_access(request.user, view.model, 'read', obj)

    def check_post_permissions(self, request, view, obj=None):
        if hasattr(view, 'parent_model'):
            parent_obj = view.get_parent_object()
            if not check_user_access(request.user, view.parent_model, 'read',
                                     parent_obj):
                return False
            if hasattr(view, 'parent_key'):
                if not check_user_access(request.user, view.model, 'add', {view.parent_key: parent_obj}):
                    return False
            return True
        elif hasattr(view, 'obj_permission_type'):
            # Generic object-centric view permission check without object not needed
            if not obj:
                return True
            # Permission check that happens when get_object() is called
            extra_kwargs = {}
            if view.obj_permission_type == 'admin':
                extra_kwargs['data'] = {}
            return check_user_access(
                request.user, view.model, view.obj_permission_type, obj,
                **extra_kwargs
            )
        else:
            if obj:
                return True
            return check_user_access(request.user, view.model, 'add', request.data)

    def check_put_permissions(self, request, view, obj=None):
        if not obj:
            # FIXME: For some reason this needs to return True
            # because it is first called with obj=None?
            return True
        return check_user_access(request.user, view.model, 'change', obj,
                                 request.data)

    def check_patch_permissions(self, request, view, obj=None):
        return self.check_put_permissions(request, view, obj)

    def check_delete_permissions(self, request, view, obj=None):
        if not obj:
            # FIXME: For some reason this needs to return True
            # because it is first called with obj=None?
            return True

        return check_user_access(request.user, view.model, 'delete', obj)

    def check_permissions(self, request, view, obj=None):
        '''
        Perform basic permissions checking before delegating to the appropriate
        method based on the request method.
        '''

        # Don't allow anonymous users. 401, not 403, hence no raised exception.
        if not request.user or request.user.is_anonymous:
            return False

        # Always allow superusers
        if getattr(view, 'always_allow_superuser', True) and request.user.is_superuser:
            return True

        # Check if view supports the request method before checking permission
        # based on request method.
        if request.method.upper() not in view.allowed_methods:
            raise MethodNotAllowed(request.method)

        # Check permissions for the given view and object, based on the request
        # method used.
        check_method = getattr(self, 'check_%s_permissions' % request.method.lower(), None)
        result = check_method and check_method(request, view, obj)
        if not result:
            raise PermissionDenied()

        return result

    def has_permission(self, request, view, obj=None):
        logger.debug('has_permission(user=%s method=%s data=%r, %s, %r)',
                     request.user, request.method, request.data,
                     view.__class__.__name__, obj)
        try:
            response = self.check_permissions(request, view, obj)
        except Exception as e:
            logger.debug('has_permission raised %r', e, exc_info=True)
            raise
        else:
            logger.debug('has_permission returned %r', response)
            return response

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view, obj)


class JobTemplateCallbackPermission(ModelAccessPermission):
    '''
    Permission check used by job template callback view for requests from
    empheral hosts.
    '''

    def has_permission(self, request, view, obj=None):
        # If another authentication method was used and it's not a POST, return
        # True to fall through to the next permission class.
        if (request.user or request.auth) and request.method.lower() != 'post':
            return super(JobTemplateCallbackPermission, self).has_permission(request, view, obj)

        # Require method to be POST, host_config_key to be specified and match
        # the requested job template, and require the job template to be
        # active in order to proceed.
        host_config_key = request.data.get('host_config_key', '')
        if request.method.lower() != 'post':
            raise PermissionDenied()
        elif not host_config_key:
            raise PermissionDenied()
        elif obj and obj.host_config_key != host_config_key:
            raise PermissionDenied()
        else:
            return True


class VariableDataPermission(ModelAccessPermission):

    def check_put_permissions(self, request, view, obj=None):
        if not obj:
            return True
        return check_user_access(request.user, view.model, 'change', obj,
                                 dict(variables=request.data))


class TaskPermission(ModelAccessPermission):
    '''
    Permission checks used for API callbacks from running a task.
    '''

    def has_permission(self, request, view, obj=None):
        # If another authentication method was used other than the one for
        # callbacks, default to the superclass permissions checking.
        if request.user or not request.auth:
            return super(TaskPermission, self).has_permission(request, view, obj)

        # Verify that the ID present in the auth token is for a valid, active
        # unified job.
        try:
            unified_job = UnifiedJob.objects.get(status='running',
                                                 pk=int(request.auth.split('-')[0]))
        except (UnifiedJob.DoesNotExist, TypeError):
            return False

        # Verify that the request method is one of those allowed for the given
        # view, also that the job or inventory being accessed matches the auth
        # token.
        if view.model == Inventory and request.method.lower() in ('head', 'get'):
            return bool(not obj or obj.pk == unified_job.inventory_id)
        else:
            return False


class WorkflowApprovalPermission(ModelAccessPermission):
    '''
    Permission check used by workflow `approval` and `deny` views to determine
    who has access to approve and deny paused workflow nodes
    '''

    def check_post_permissions(self, request, view, obj=None):
        approval = get_object_or_400(view.model, pk=view.kwargs['pk'])
        return check_user_access(request.user, view.model, 'approve_or_deny', approval)


class ProjectUpdatePermission(ModelAccessPermission):
    '''
    Permission check used by ProjectUpdateView to determine who can update projects
    '''
    def check_get_permissions(self, request, view, obj=None):
        project = get_object_or_400(view.model, pk=view.kwargs['pk'])
        return check_user_access(request.user, view.model, 'read', project)

    def check_post_permissions(self, request, view, obj=None):
        project = get_object_or_400(view.model, pk=view.kwargs['pk'])
        return check_user_access(request.user, view.model, 'start', project)


class InventoryInventorySourcesUpdatePermission(ModelAccessPermission):
    def check_post_permissions(self, request, view, obj=None):
        inventory = get_object_or_400(view.model, pk=view.kwargs['pk'])
        return check_user_access(request.user, view.model, 'update', inventory)


class UserPermission(ModelAccessPermission):
    def check_post_permissions(self, request, view, obj=None):
        if not request.data:
            return request.user.admin_of_organizations.exists()
        elif request.user.is_superuser:
            return True
        raise PermissionDenied()


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class InstanceGroupTowerPermission(ModelAccessPermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE' and obj.name == "tower":
            return False
        return super(InstanceGroupTowerPermission, self).has_object_permission(request, view, obj)


class WebhookKeyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.can_access(view.model, 'admin', obj, request.data)
