from lib.main.models import *
from lib.main.serializers import *
from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser

# FIXME: this will probably need to be subclassed by object type

class CustomRbac(permissions.BasePermission):

    def _common_user_check(self, request):
        # no anonymous users
        if type(request.user) == AnonymousUser:
            return False
        # superusers are always good
        if request.user.is_superuser:
            return True
        # other users must have associated acom user records & be active
        acom_user = User.objects.filter(auth_user = request.user)
        if len(acom_user) != 1:
            return False
        if not acom_user[0].active:
            return False
        return True

    def has_permission(self, request, view, obj=None):
        if not self._common_user_check(request):
            return False
        if obj is None:
            return True
        else:
            # haven't tested around these confines yet
            raise Exception("FIXME")

    def has_object_permission(self, request, view, obj):
        if not self._common_user_check(request):
            return False
        # FIXME: TODO: verify the user is actually allowed to see this resource
        return True

