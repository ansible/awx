# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import re
import logging


# Python Social Auth
from social_core.exceptions import AuthException

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


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


def _update_m2m_from_expression(user, related, expr, remove=True):
    """
    Helper function to update m2m relationship based on user matching one or
    more expressions.
    """
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
        related.add(user)
    elif remove:
        related.remove(user)


def get_or_create_with_default_galaxy_cred(**kwargs):
    from awx.main.models import Organization, Credential

    (org, org_created) = Organization.objects.get_or_create(**kwargs)
    if org_created:
        logger.debug("Created org {} (id {}) from {}".format(org.name, org.id, kwargs))
        public_galaxy_credential = Credential.objects.filter(managed=True, name='Ansible Galaxy').first()
        if public_galaxy_credential is not None:
            org.galaxy_credentials.add(public_galaxy_credential)
            logger.debug("Added default Ansible Galaxy credential to org")
        else:
            logger.debug("Could not find default Ansible Galaxy credential to add to org")
    return org


def _update_org_from_attr(user, related, attr, remove, remove_admins, remove_auditors, backend):
    from awx.main.models import Organization
    from django.conf import settings

    org_ids = []

    for org_name in attr:
        try:
            if settings.SAML_AUTO_CREATE_OBJECTS:
                try:
                    organization_alias = backend.setting('ORGANIZATION_MAP').get(org_name).get('organization_alias')
                    if organization_alias is not None:
                        organization_name = organization_alias
                    else:
                        organization_name = org_name
                except Exception:
                    organization_name = org_name
                org = get_or_create_with_default_galaxy_cred(name=organization_name)
            else:
                org = Organization.objects.get(name=org_name)
        except ObjectDoesNotExist:
            continue

        org_ids.append(org.id)
        getattr(org, related).members.add(user)

    if remove:
        [o.member_role.members.remove(user) for o in Organization.objects.filter(Q(member_role__members=user) & ~Q(id__in=org_ids))]

    if remove_admins:
        [o.admin_role.members.remove(user) for o in Organization.objects.filter(Q(admin_role__members=user) & ~Q(id__in=org_ids))]

    if remove_auditors:
        [o.auditor_role.members.remove(user) for o in Organization.objects.filter(Q(auditor_role__members=user) & ~Q(id__in=org_ids))]


def update_user_orgs(backend, details, user=None, *args, **kwargs):
    """
    Update organization memberships for the given user based on mapping rules
    defined in settings.
    """
    if not user:
        return

    org_map = backend.setting('ORGANIZATION_MAP') or {}
    for org_name, org_opts in org_map.items():
        organization_alias = org_opts.get('organization_alias')
        if organization_alias:
            organization_name = organization_alias
        else:
            organization_name = org_name
        org = get_or_create_with_default_galaxy_cred(name=organization_name)

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
    """
    Update team memberships for the given user based on mapping rules defined
    in settings.
    """
    if not user:
        return
    from awx.main.models import Team

    team_map = backend.setting('TEAM_MAP') or {}
    for team_name, team_opts in team_map.items():
        # Get or create the org to update.
        if 'organization' not in team_opts:
            continue
        org = get_or_create_with_default_galaxy_cred(name=team_opts['organization'])

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
    if org_map.get('saml_attr') is None and org_map.get('saml_admin_attr') is None and org_map.get('saml_auditor_attr') is None:
        return

    remove = bool(org_map.get('remove', True))
    remove_admins = bool(org_map.get('remove_admins', True))
    remove_auditors = bool(org_map.get('remove_auditors', True))

    attr_values = kwargs.get('response', {}).get('attributes', {}).get(org_map.get('saml_attr'), [])
    attr_admin_values = kwargs.get('response', {}).get('attributes', {}).get(org_map.get('saml_admin_attr'), [])
    attr_auditor_values = kwargs.get('response', {}).get('attributes', {}).get(org_map.get('saml_auditor_attr'), [])

    _update_org_from_attr(user, "member_role", attr_values, remove, False, False, backend)
    _update_org_from_attr(user, "admin_role", attr_admin_values, False, remove_admins, False, backend)
    _update_org_from_attr(user, "auditor_role", attr_auditor_values, False, False, remove_auditors, backend)


def update_user_teams_by_saml_attr(backend, details, user=None, *args, **kwargs):
    if not user:
        return
    from awx.main.models import Organization, Team
    from django.conf import settings

    team_map = settings.SOCIAL_AUTH_SAML_TEAM_ATTR
    if team_map.get('saml_attr') is None:
        return

    saml_team_names = set(kwargs.get('response', {}).get('attributes', {}).get(team_map['saml_attr'], []))

    team_ids = []
    for team_name_map in team_map.get('team_org_map', []):
        team_name = team_name_map.get('team', None)
        team_alias = team_name_map.get('team_alias', None)
        organization_name = team_name_map.get('organization', None)
        if team_name in saml_team_names:
            if not organization_name:
                # Settings field validation should prevent this.
                logger.error("organization name invalid for team {}".format(team_name))
                continue

            try:
                if settings.SAML_AUTO_CREATE_OBJECTS:
                    org = get_or_create_with_default_galaxy_cred(name=organization_name)
                else:
                    org = Organization.objects.get(name=organization_name)
            except ObjectDoesNotExist:
                continue

            if team_alias:
                team_name = team_alias
            try:
                if settings.SAML_AUTO_CREATE_OBJECTS:
                    team = Team.objects.get_or_create(name=team_name, organization=org)[0]
                else:
                    team = Team.objects.get(name=team_name, organization=org)
            except ObjectDoesNotExist:
                continue

            team_ids.append(team.id)
            team.member_role.members.add(user)

    if team_map.get('remove', True):
        [t.member_role.members.remove(user) for t in Team.objects.filter(Q(member_role__members=user) & ~Q(id__in=team_ids))]


def _get_matches(list1, list2):
    # Because we are just doing an intersection here we don't really care which list is in which parameter

    # A SAML provider could return either a string or a list of items so we need to coerce the SAML value into a list (if needed)
    if not isinstance(list1, (list, tuple)):
        list1 = [list1]

    # In addition, we used to allow strings in the SAML config instead of Lists. The migration should take case of that but just in case, we will convert our list too
    if not isinstance(list2, (list, tuple)):
        list2 = [list2]

    return set(list1).intersection(set(list2))


def _check_flag(user, flag, attributes, user_flags_settings):
    '''
    Helper function to set the is_superuser is_system_auditor flags for the SAML adapter
    Returns the new flag and whether or not it changed the flag
    '''
    new_flag = False
    is_role_key = "is_%s_role" % (flag)
    is_attr_key = "is_%s_attr" % (flag)
    is_value_key = "is_%s_value" % (flag)
    remove_setting = "remove_%ss" % (flag)

    # Check to see if we are respecting a role and, if so, does our user have that role?
    required_roles = user_flags_settings.get(is_role_key, None)
    if required_roles:
        matching_roles = _get_matches(required_roles, attributes.get('Role', []))

        # We do a 2 layer check here so that we don't spit out the else message if there is no role defined
        if matching_roles:
            logger.debug("User %s has %s role(s) %s" % (user.username, flag, ', '.join(matching_roles)))
            new_flag = True
        else:
            logger.debug("User %s is missing the %s role(s) %s" % (user.username, flag, ', '.join(required_roles)))

    # Next, check to see if we are respecting an attribute; this will take priority over the role if its defined
    attr_setting = user_flags_settings.get(is_attr_key, None)
    if attr_setting and attributes.get(attr_setting, None):
        # Do we have a required value for the attribute
        required_value = user_flags_settings.get(is_value_key, None)
        if required_value:
            # If so, check and see if the value of the attr matches the required value
            saml_user_attribute_value = attributes.get(attr_setting, None)
            matching_values = _get_matches(required_value, saml_user_attribute_value)

            if matching_values:
                logger.debug("Giving %s %s from attribute %s with matching values %s" % (user.username, flag, attr_setting, ', '.join(matching_values)))
                new_flag = True
            # if they don't match make sure that new_flag is false
            else:
                logger.debug(
                    "Refusing %s for %s because attr %s (%s) did not match value(s) %s"
                    % (flag, user.username, attr_setting, ", ".join(saml_user_attribute_value), ', '.join(required_value))
                )
                new_flag = False
        # If there was no required value then we can just allow them in because of the attribute
        else:
            logger.debug("Giving %s %s from attribute %s" % (user.username, flag, attr_setting))
            new_flag = True

    # Get the users old flag
    old_value = getattr(user, "is_%s" % (flag))

    # If we are not removing the flag and they were a system admin and now we don't want them to be just return
    remove_flag = user_flags_settings.get(remove_setting, True)
    if not remove_flag and (old_value and not new_flag):
        logger.debug("Remove flag %s preventing removal of %s for %s" % (remove_flag, flag, user.username))
        return old_value, False

    # If the user was flagged and we are going to make them not flagged make sure there is a message
    if old_value and not new_flag:
        logger.debug("Revoking %s from %s" % (flag, user.username))

    return new_flag, old_value != new_flag


def update_user_flags(backend, details, user=None, *args, **kwargs):
    if not user:
        return

    from django.conf import settings

    user_flags_settings = settings.SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR

    attributes = kwargs.get('response', {}).get('attributes', {})
    logger.debug("User attributes for %s: %s" % (user.username, attributes))

    user.is_superuser, superuser_changed = _check_flag(user, 'superuser', attributes, user_flags_settings)
    user.is_system_auditor, auditor_changed = _check_flag(user, 'system_auditor', attributes, user_flags_settings)

    if superuser_changed or auditor_changed:
        user.save()
