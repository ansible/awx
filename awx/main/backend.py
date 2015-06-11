# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.dispatch import receiver

# django-auth-ldap
from django_auth_ldap.backend import LDAPSettings as BaseLDAPSettings
from django_auth_ldap.backend import LDAPBackend as BaseLDAPBackend
from django_auth_ldap.backend import populate_user

# Ansible Tower
from awx.api.license import feature_enabled

class LDAPSettings(BaseLDAPSettings):

    defaults = dict(BaseLDAPSettings.defaults.items() + {
        'ORGANIZATION_MAP': {},
        'TEAM_MAP': {},
    }.items())

class LDAPBackend(BaseLDAPBackend):
    '''
    Custom LDAP backend for AWX.
    '''

    settings_prefix = 'AUTH_LDAP_'

    def _get_settings(self):
        if self._settings is None:
            self._settings = LDAPSettings(self.settings_prefix)
        return self._settings

    def _set_settings(self, settings):
        self._settings = settings

    settings = property(_get_settings, _set_settings)

    def authenticate(self, username, password):
        if not self.settings.SERVER_URI or not feature_enabled('ldap'):
            return None
        return super(LDAPBackend, self).authenticate(username, password)

    def get_user(self, user_id):
        if not self.settings.SERVER_URI or not feature_enabled('ldap'):
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

def _update_m2m_from_groups(user, ldap_user, rel, opts, remove=False):
    '''
    Hepler function to update m2m relationship based on LDAP group membership.
    '''
    should_add = False
    if opts is None:
        return
    elif not opts:
        pass
    elif opts is True:
        should_add = True
    else:
        if isinstance(opts, basestring):
            opts = [opts]
        for group_dn in opts:
            if not isinstance(group_dn, basestring):
                continue
            if ldap_user._get_groups().is_member_of(group_dn):
                should_add = True
    if should_add:
        rel.add(user)
    elif remove:
        rel.remove(user)

@receiver(populate_user)
def on_populate_user(sender, **kwargs):
    '''
    Handle signal from LDAP backend to populate the user object.  Update user
    organization/team memberships according to their LDAP groups.
    '''
    from awx.main.models import Organization, Team
    user = kwargs['user']
    ldap_user = kwargs['ldap_user']
    backend = ldap_user.backend

    # Update organization membership based on group memberships.
    org_map = getattr(backend.settings, 'ORGANIZATION_MAP', {})
    for org_name, org_opts in org_map.items():
        org, created = Organization.objects.get_or_create(name=org_name)
        remove = bool(org_opts.get('remove', False))
        admins_opts = org_opts.get('admins', None)
        remove_admins = bool(org_opts.get('remove_admins', remove))
        _update_m2m_from_groups(user, ldap_user, org.admins, admins_opts,
                                remove_admins)
        users_opts = org_opts.get('users', None)
        remove_users = bool(org_opts.get('remove_users', remove))
        _update_m2m_from_groups(user, ldap_user, org.users, users_opts,
                                remove_users)

    # Update team membership based on group memberships.
    team_map = getattr(backend.settings, 'TEAM_MAP', {})
    for team_name, team_opts in team_map.items():
        if 'organization' not in team_opts:
            continue
        org, created = Organization.objects.get_or_create(name=team_opts['organization'])
        team, created = Team.objects.get_or_create(name=team_name, organization=org)
        users_opts = team_opts.get('users', None)
        remove = bool(team_opts.get('remove', False))
        _update_m2m_from_groups(user, ldap_user, team.users, users_opts,
                                remove)

    # Update user profile to store LDAP DN.
    profile = user.profile
    if profile.ldap_dn != ldap_user.dn:
        profile.ldap_dn = ldap_user.dn
        profile.save()
