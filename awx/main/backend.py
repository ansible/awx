# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# django-auth-ldap
from django_auth_ldap.backend import LDAPBackend as BaseLDAPBackend

class LDAPBackend(BaseLDAPBackend):
    '''
    Custom LDAP backend for AWX.
    '''

    settings_prefix = 'AUTH_LDAP_'

    def authenticate(self, username, password):
        if not self.settings.SERVER_URI:
            return None
        return super(LDAPBackend, self).authenticate(username, password)

    def get_user(self, user_id):
        if not self.settings.SERVER_URI:
            return None
        return super(LDAPBackend, self).get_user(user_id)

    # Disable any LDAP based authorization / permissions checking.

    def has_perm(self, user, perm, obj=None):
        return False

    def has_module_perms(self, user, app_label):
        return False

    def get_all_permissions(self, user, obj=None):
        return set()

    def get_group_permissions(self, user, obj=None):
        return set()
