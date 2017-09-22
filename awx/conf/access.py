# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Tower
from awx.main.access import BaseAccess, register_access
from awx.conf.models import Setting


class SettingAccess(BaseAccess):
    '''
    - I can see settings when I am a super user or system auditor.
    - I can edit settings when I am a super user.
    - I can clear settings when I am a super user.
    '''

    model = Setting

    # For the checks below, obj will be an instance of a "Settings" class with
    # an attribute for each setting and a "user" attribute (set to None unless
    # it is a user setting).

    def can_read(self, obj):
        return bool(self.user.is_superuser or self.user.is_system_auditor)

    def can_add(self, data):
        return False  # There is no API endpoint to POST new settings.


register_access(Setting, SettingAccess)
