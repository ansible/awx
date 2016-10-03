# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db.models import Q

# Tower
from awx.main.access import BaseAccess, register_access
from awx.conf.models import Setting


class SettingAccess(BaseAccess):
    '''
    - I can see settings when I am a super user or system auditor.
    - I can edit settings when I am a super user.
    - I can clear settings when I am a super user.
    - I can always see/edit/clear my own user settings.
    '''

    model = Setting

    # For the checks below, obj will be an instance of a "Settings" class with
    # an attribute for each setting and a "user" attribute (set to None unless
    # it is a user setting).

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            return self.model.objects.filter(Q(user__isnull=True) | Q(user=self.user))
        else:
            return self.model.objects.filter(user=self.user)

    def can_read(self, obj):
        return bool(self.user.is_superuser or self.user.is_system_auditor or (obj and obj.user == self.user))

    def can_add(self, data):
        return False  # There is no API endpoint to POST new settings.

    def can_change(self, obj, data):
        return bool(self.user.is_superuser or (obj and obj.user == self.user))

    def can_delete(self, obj):
        return bool(self.user.is_superuser or (obj and obj.user == self.user))


register_access(Setting, SettingAccess)
