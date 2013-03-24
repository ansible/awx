# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

from lib.main.models import *
from lib.main.serializers import *
from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404

# FIXME: this will probably need to be subclassed by object type

class CustomRbac(permissions.BasePermission):

    def _common_user_check(self, request):
        # no anonymous users
        if request.user.is_anonymous():
            # 401, not 403, hence no raised exception
            return False
        # superusers are always good
        if request.user.is_superuser:
            return True
        # other users must have associated acom user records & be active
        if not request.user.is_active:
            raise PermissionDenied()
        return True

    def has_permission(self, request, view, obj=None):
        if not self._common_user_check(request):
            return False
        if obj is None:
            if getattr(view, 'list_permissions_check', None):
                if request.user.is_superuser:
                    return True
                if not view.list_permissions_check(request):
                    raise PermissionDenied()
            elif not getattr(view, 'item_permissions_check', None):
                raise Exception("internal error, list_permissions_check or item_permissions_check must be defined")
            return True
        else:
            # haven't tested around these confines yet
            raise Exception("did not expect to get to this position")

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if not self._common_user_check(request):
            return False
        if type(obj) == User:
            if not obj.is_active:
                raise Http404()
        else:
            if not obj.active:
                raise Http404()
        if not view.item_permissions_check(request, obj):
            raise PermissionDenied()
        return True

