# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import re
import logging


# Python Social Auth
from social_core.exceptions import AuthException

# Django
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

# Tower
from awx.conf.license import feature_enabled


logger = logging.getLogger('awx.sso.pipeline')


class AuthNotFound(AuthException):

    def __init__(self, backend, email_or_uid, *args, **kwargs):
        self.email_or_uid = email_or_uid
        super(AuthNotFound, self).__init__(backend, *args, **kwargs)

    def __str__(self):
        return _('An account cannot be found for {0}').format(self.email_or_uid)


class AuthInactive(AuthException):

    def __str__(self):
        return _('Your account is inactive')


def check_user_found_or_created(backend, details, user=None, *args, **kwargs):
    if not user:
        email_or_uid = details.get('email') or kwargs.get('email') or kwargs.get('uid') or '???'
        raise AuthNotFound(backend, email_or_uid)


def set_is_active_for_new_user(strategy, details, user=None, *args, **kwargs):
    if kwargs.get('is_new', False):
        details['is_active'] = True
        return {'details': details}


def prevent_inactive_login(backend, details, user=None, *args, **kwargs):
    if user and not user.is_active:
        raise AuthInactive(backend)


def _update_m2m_from_expression(user, rel, expr, remove=True):
    '''
    Helper function to update m2m relationship based on user matching one or
    more expressions.
    '''
    should_add = False
    if expr is None:
        return
    elif not expr:
        pass
    elif expr is True:
        should_add = True
    else:
        if isinstance(expr, (str, type(re.compile('')))):
            expr = [expr]
        for ex in expr:
            if isinstance(ex, str):
                if user.username == ex or user.email == ex:
                    should_add = True
            elif isinstance(ex, type(re.compile(''))):
                if ex.match(user.username) or ex.match(user.email):
                    should_add = True
    if should_add:
        rel.add(user)
    elif remove:
        rel.remove(user)


def _update_org_from_attr(user, rel, attr, remove, remove_admins):
    from awx.main.models import Organization
    multiple_orgs = feature_enabled('multiple_organizations')

    org_ids = []

    for org_name in attr:
        if multiple_orgs:
            org = Organization.objects.get_or_create(name=org_name)[0]
        else:
            try:
                org = Organization.objects.order_by('pk')[0]
            except IndexError:
                continue

        org_ids.append(org.id)
        getattr(org, rel).members.add(user)

    if remove:
        [o.member_role.members.remove(user) for o in
            Organization.objects.filter(Q(member_role__members=user) & ~Q(id__in=org_ids))]

    if remove_admins:
        [o.admin_role.members.remove(user) for o in
            Organization.objects.filter(Q(admin_role__members=user) & ~Q(id__in=org_ids))]


def update_user_orgs(backend, details, user=None, *args, **kwargs):
    '''
    Update organization memberships for the given user based on mapping rules
    defined in settings.
    '''
    if not user:
        return
    from awx.main.models import Organization
    multiple_orgs = feature_enabled('multiple_organizations')
    org_map = backend.setting('ORGANIZATION_MAP') or {}
    for org_name, org_opts in org_map.items():

        # Get or create the org to update.  If the license only allows for one
        # org, always use the first active org, unless no org exists.
        if multiple_orgs:
            org = Organization.objects.get_or_create(name=org_name)[0]
        else:
            try:
                org = Organization.objects.order_by('pk')[0]
            except IndexError:
                continue

        # Update org admins from expression(s).
        remove = bool(org_opts.get('remove', True))
        admins_expr = org_opts.get('admins', None)
        remove_admins = bool(org_opts.get('remove_admins', remove))
        _update_m2m_from_expression(user, org.admin_role.members, admins_expr, remove_admins)

        # Update org users from expression(s).
        users_expr = org_opts.get('users', None)
        remove_users = bool(org_opts.get('remove_users', remove))
        _update_m2m_from_expression(user, org.member_role.members, users_expr, remove_users)


def update_user_teams(backend, details, user=None, *args, **kwargs):
    '''
    Update team memberships for the given user based on mapping rules defined
    in settings.
    '''
    if not user:
        return
    from awx.main.models import Organization, Team
    multiple_orgs = feature_enabled('multiple_organizations')
    team_map = backend.setting('TEAM_MAP') or {}
    for team_name, team_opts in team_map.items():

        # Get or create the org to update.  If the license only allows for one
        # org, always use the first active org, unless no org exists.
        if multiple_orgs:
            if 'organization' not in team_opts:
                continue
            org = Organization.objects.get_or_create(name=team_opts['organization'])[0]
        else:
            try:
                org = Organization.objects.order_by('pk')[0]
            except IndexError:
                continue

        # Update team members from expression(s).
        team = Team.objects.get_or_create(name=team_name, organization=org)[0]
        users_expr = team_opts.get('users', None)
        remove = bool(team_opts.get('remove', True))
        _update_m2m_from_expression(user, team.member_role.members, users_expr, remove)


def update_user_orgs_by_saml_attr(backend, details, user=None, *args, **kwargs):
    if not user:
        return
    from django.conf import settings
    org_map = settings.SOCIAL_AUTH_SAML_ORGANIZATION_ATTR
    if org_map.get('saml_attr') is None and org_map.get('saml_admin_attr') is None:
        return

    remove = bool(org_map.get('remove', True))
    remove_admins = bool(org_map.get('remove_admins', True))

    attr_values = kwargs.get('response', {}).get('attributes', {}).get(org_map['saml_attr'], [])
    attr_admin_values = kwargs.get('response', {}).get('attributes', {}).get(org_map['saml_admin_attr'], [])

    _update_org_from_attr(user, "member_role", attr_values, remove, False)
    _update_org_from_attr(user, "admin_role", attr_admin_values, False, remove_admins)


def update_user_teams_by_saml_attr(backend, details, user=None, *args, **kwargs):
    if not user:
        return
    from awx.main.models import Organization, Team
    from django.conf import settings
    multiple_orgs = feature_enabled('multiple_organizations')
    team_map = settings.SOCIAL_AUTH_SAML_TEAM_ATTR
    if team_map.get('saml_attr') is None:
        return

    saml_team_names = set(kwargs
                          .get('response', {})
                          .get('attributes', {})
                          .get(team_map['saml_attr'], []))

    team_ids = []
    for team_name_map in team_map.get('team_org_map', []):
        team_name = team_name_map.get('team', '')
        if team_name in saml_team_names:
            if multiple_orgs:
                if not team_name_map.get('organization', ''):
                    # Settings field validation should prevent this.
                    logger.error("organization name invalid for team {}".format(team_name))
                    continue
                org = Organization.objects.get_or_create(name=team_name_map['organization'])[0]
            else:
                try:
                    org = Organization.objects.order_by('pk')[0]
                except IndexError:
                    continue
            team = Team.objects.get_or_create(name=team_name, organization=org)[0]

            team_ids.append(team.id)
            team.member_role.members.add(user)

    if team_map.get('remove', True):
        [t.member_role.members.remove(user) for t in
            Team.objects.filter(Q(member_role__members=user) & ~Q(id__in=team_ids))]
