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
            print "PD4"
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
                    print "DEBUG: PD1"
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
            print "DEBUG: PD2"
            return False
        if not obj.active:
            raise Http404()
        if not view.item_permissions_check(request, obj):
            print "DEBUG: PD3"
            raise PermissionDenied()
        return True
