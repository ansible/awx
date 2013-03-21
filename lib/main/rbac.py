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
        if type(request.user) == AnonymousUser:
            # 401, not 403, hence no raised exception
            return False
        # superusers are always good
        if request.user.is_superuser:
            return True
        # other users must have associated acom user records & be active
        acom_user = User.objects.filter(auth_user = request.user)
        if len(acom_user) != 1:
            raise PermissionDenied()
        if not acom_user[0].active:
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
        if not obj.active:
            raise Http404()
        if not view.item_permissions_check(request, obj):
            raise PermissionDenied()
        return True
