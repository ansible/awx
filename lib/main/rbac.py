# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.


import logging
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions
from lib.main.access import *

logger = logging.getLogger('lib.main.rbac')

# FIXME: this will probably need to be subclassed by object type

class CustomRbac(permissions.BasePermission):

    def _check_options_permissions(self, request, view, obj=None):
        return self._check_get_permissions(request, view, obj)

    def _check_head_permissions(self, request, view, obj=None):
        return self._check_get_permissions(request, view, obj)

    def _check_get_permissions(self, request, view, obj=None):
        if hasattr(view, 'parent_model'):
            parent_obj = view.parent_model.objects.get(pk=view.kwargs['pk'])
            if not check_user_access(request.user, view.parent_model, 'read',
                                     parent_obj):
                return False
        if not obj:
            return True
        return check_user_access(request.user, view.model, 'read', obj)

    def _check_post_permissions(self, request, view, obj=None):
        if hasattr(view, 'parent_model'):
            parent_obj = view.parent_model.objects.get(pk=view.kwargs['pk'])
            #if not check_user_access(request.user, view.parent_model, 'change',
            #                         parent_obj, None):
            #    return False
            # FIXME: attach/unattach
            return True
        else:
            if obj:
                return True
            return check_user_access(request.user, view.model, 'add', request.DATA)

    def _check_put_permissions(self, request, view, obj=None):
        if not obj:
            return True # FIXME: For some reason this needs to return True
                        # because it is first called with obj=None?
        return check_user_access(request.user, view.model, 'change', obj,
                                 request.DATA)

    def _check_delete_permissions(self, request, view, obj=None):
        if not obj:
            return True # FIXME: For some reason this needs to return True
                        # because it is first called with obj=None?
        return check_user_access(request.user, view.model, 'delete', obj)

    def _check_permissions(self, request, view, obj=None):
        #if not obj and hasattr(view, 'get_object'):
        #    obj = view.get_object()
        # Check that obj (if given) is active, otherwise raise a 404.
        active = getattr(obj, 'active', getattr(obj, 'is_active', True))
        if callable(active):
            active = active()
        if not active:
            raise Http404()
        # Don't allow anonymous users. 401, not 403, hence no raised exception.
        if not request.user or request.user.is_anonymous():
            return False
        # Don't allow inactive users (and respond with a 403).
        if not request.user.is_active:
            raise PermissionDenied('your account is inactive')
        # Always allow superusers (as long as they are active).
        if request.user.is_superuser:
            return True
        # Check permissions for the given view and object, based on the request
        # method used.
        check_method = getattr(self, '_check_%s_permissions' % \
                               request.method.lower(), None)
        result = check_method and check_method(request, view, obj)
        if not result:
            raise PermissionDenied()
        return result
            
        # If no obj is given, check list permissions.
        if obj is None:
            if getattr(view, 'list_permissions_check', None):
                if not view.list_permissions_check(request):
                    raise PermissionDenied()
            elif not getattr(view, 'item_permissions_check', None):
                raise Exception('internal error, list_permissions_check or '
                                'item_permissions_check must be defined')
            return True
        # Otherwise, check the item permissions for the given obj.
        else:
            if not view.item_permissions_check(request, obj):
                raise PermissionDenied()
            return True

    def has_permission(self, request, view, obj=None):
        logger.debug('has_permission(user=%s method=%s data=%r, %s, %r)',
                     request.user, request.method, request.DATA,
                     view.__class__.__name__, obj)
        try:
            response = self._check_permissions(request, view, obj)
        except Exception, e:
            logger.debug('has_permission raised %r', e, exc_info=True)
            raise
        else:
            logger.debug('has_permission returned %r', response)
            return response

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view, obj)
