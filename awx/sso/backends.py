# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict
import logging
import uuid

import ldap

# Django
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.utils.encoding import force_str

# django-auth-ldap
from django_auth_ldap.backend import populate_user
from django.core.exceptions import ImproperlyConfigured

# radiusauth
from radiusauth.backends import RADIUSBackend as BaseRADIUSBackend

# tacacs+ auth
import tacacs_plus

# social
from social_core.backends.saml import OID_USERID
from social_core.backends.saml import SAMLAuth as BaseSAMLAuth
from social_core.backends.saml import SAMLIdentityProvider as BaseSAMLIdentityProvider

# Ansible Tower
from awx.sso.models import UserEnterpriseAuth
from awx.sso.common import create_org_and_teams, reconcile_users_org_team_mappings

logger = logging.getLogger('awx.sso.backends')


def _decorate_enterprise_user(user, provider):
    user.set_unusable_password()
    user.save()
    enterprise_auth, _ = UserEnterpriseAuth.objects.get_or_create(user=user, provider=provider)
    return enterprise_auth


def _get_or_set_enterprise_user(username, password, provider):
    created = False
    try:
        user = User.objects.prefetch_related('enterprise_auth').get(username=username)
    except User.DoesNotExist:
        user = User(username=username)
        enterprise_auth = _decorate_enterprise_user(user, provider)
        logger.debug("Created enterprise user %s via %s backend." % (username, enterprise_auth.get_provider_display()))
        created = True
    if created or user.is_in_enterprise_category(provider):
        return user
    logger.warning("Enterprise user %s already defined in Tower." % username)


class RADIUSBackend(BaseRADIUSBackend):
    """
    Custom Radius backend to verify license status
    """

    def authenticate(self, request, username, password):
        if not django_settings.RADIUS_SERVER:
            return None
        return super(RADIUSBackend, self).authenticate(request, username, password)

    def get_user(self, user_id):
        if not django_settings.RADIUS_SERVER:
            return None
        user = super(RADIUSBackend, self).get_user(user_id)
        if not user.has_usable_password():
            return user

    def get_django_user(self, username, password=None, groups=[], is_staff=False, is_superuser=False):
        return _get_or_set_enterprise_user(force_str(username), force_str(password), 'radius')


class TACACSPlusBackend(object):
    """
    Custom TACACS+ auth backend for AWX
    """

    def authenticate(self, request, username, password):
        if not django_settings.TACACSPLUS_HOST:
            return None
        try:
            # Upstream TACACS+ client does not accept non-string, so convert if needed.
            tacacs_client = tacacs_plus.TACACSClient(
                django_settings.TACACSPLUS_HOST,
                django_settings.TACACSPLUS_PORT,
                django_settings.TACACSPLUS_SECRET,
                timeout=django_settings.TACACSPLUS_SESSION_TIMEOUT,
            )
            auth_kwargs = {'authen_type': tacacs_plus.TAC_PLUS_AUTHEN_TYPES[django_settings.TACACSPLUS_AUTH_PROTOCOL]}
            if django_settings.TACACSPLUS_AUTH_PROTOCOL:
                client_ip = self._get_client_ip(request)
                if client_ip:
                    auth_kwargs['rem_addr'] = client_ip
            auth = tacacs_client.authenticate(username, password, **auth_kwargs)
        except Exception as e:
            logger.exception("TACACS+ Authentication Error: %s" % str(e))
            return None
        if auth.valid:
            return _get_or_set_enterprise_user(username, password, 'tacacs+')

    def get_user(self, user_id):
        if not django_settings.TACACSPLUS_HOST:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _get_client_ip(self, request):
        if not request or not hasattr(request, 'META'):
            return None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TowerSAMLIdentityProvider(BaseSAMLIdentityProvider):
    """
    Custom Identity Provider to make attributes to what we expect.
    """

    def get_user_permanent_id(self, attributes):
        uid = attributes[self.conf.get('attr_user_permanent_id', OID_USERID)]
        if isinstance(uid, str):
            return uid
        return uid[0]

    def get_attr(self, attributes, conf_key, default_attribute):
        """
        Get the attribute 'default_attribute' out of the attributes,
        unless self.conf[conf_key] overrides the default by specifying
        another attribute to use.
        """
        key = self.conf.get(conf_key, default_attribute)
        value = attributes[key] if key in attributes else None
        # In certain implementations (like https://pagure.io/ipsilon) this value is a string, not a list
        if isinstance(value, (list, tuple)):
            value = value[0]
        if conf_key in ('attr_first_name', 'attr_last_name', 'attr_username', 'attr_email') and value is None:
            logger.warning(
                "Could not map user detail '%s' from SAML attribute '%s'; update SOCIAL_AUTH_SAML_ENABLED_IDPS['%s']['%s'] with the correct SAML attribute.",
                conf_key[5:],
                key,
                self.name,
                conf_key,
            )
        return str(value) if value is not None else value


class SAMLAuth(BaseSAMLAuth):
    """
    Custom SAMLAuth backend to verify license status
    """

    def get_idp(self, idp_name):
        idp_config = self.setting('ENABLED_IDPS')[idp_name]
        return TowerSAMLIdentityProvider(idp_name, **idp_config)

    def authenticate(self, request, *args, **kwargs):
        if not all(
            [
                django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID,
                django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY,
                django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS,
            ]
        ):
            return None
        user = super(SAMLAuth, self).authenticate(request, *args, **kwargs)
        # Comes from https://github.com/omab/python-social-auth/blob/v0.2.21/social/backends/base.py#L91
        if getattr(user, 'is_new', False):
            enterprise_auth = _decorate_enterprise_user(user, 'saml')
            logger.debug("Created enterprise user %s from %s backend." % (user.username, enterprise_auth.get_provider_display()))
        elif user and not user.is_in_enterprise_category('saml'):
            return None
        if user:
            logger.debug("Enterprise user %s already created in Tower." % user.username)
        return user

    def get_user(self, user_id):
        if not all(
            [
                django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID,
                django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY,
                django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS,
            ]
        ):
            return None
        return super(SAMLAuth, self).get_user(user_id)


def _update_m2m_from_groups(ldap_user, opts, remove=True):
    """
    Hepler function to evaluate the LDAP team/org options to determine if LDAP user should
      be a member of the team/org based on their ldap group dns.

    Returns:
        True - User should be added
        False - User should be removed
        None - Users membership should not be changed
    """
    if opts is None:
        return None
    elif not opts:
        pass
    elif isinstance(opts, bool) and opts is True:
        return True
    else:
        if isinstance(opts, str):
            opts = [opts]
        # If any of the users groups matches any of the list options
        for group_dn in opts:
            if not isinstance(group_dn, str):
                continue
            if ldap_user._get_groups().is_member_of(group_dn):
                return True
    if remove:
        return False
    return None


# Do we still need to populate ldap field on profile
# @receiver(populate_user, dispatch_uid='populate-ldap-user')
# def on_populate_user(sender, **kwargs):
#     """
#     Handle signal from LDAP backend to populate the user object.  Update user
#     organization/team memberships according to their LDAP groups.
#     """
#     user = kwargs['user']
#     ldap_user = kwargs['ldap_user']
#     backend = ldap_user.backend

#     # Boolean to determine if we should force an user update
#     # to avoid duplicate SQL update statements
#     force_user_update = False

#     # Prefetch user's groups to prevent LDAP queries for each org/team when
#     # checking membership.
#     ldap_user._get_groups().get_group_dns()

#     # If the LDAP user has a first or last name > $maxlen chars, truncate it
#     for field in ('first_name', 'last_name'):
#         max_len = User._meta.get_field(field).max_length
#         field_len = len(getattr(user, field))
#         if field_len > max_len:
#             setattr(user, field, getattr(user, field)[:max_len])
#             force_user_update = True
#             logger.warning('LDAP user {} has {} > max {} characters'.format(user.username, field, max_len))

#     org_map = getattr(backend.settings, 'ORGANIZATION_MAP', {})
#     team_map_settings = getattr(backend.settings, 'TEAM_MAP', {})
#     orgs_list = list(org_map.keys())
#     team_map = {}
#     for team_name, team_opts in team_map_settings.items():
#         if not team_opts.get('organization', None):
#             # You can't save the LDAP config in the UI w/o an org (or '' or null as the org) so if we somehow got this condition its an error
#             logger.error("Team named {} in LDAP team map settings is invalid due to missing organization".format(team_name))
#             continue
#         team_map[team_name] = team_opts['organization']

#     create_org_and_teams(orgs_list, team_map, 'LDAP')

#     # Compute in memory what the state is of the different LDAP orgs
#     org_roles_and_ldap_attributes = {'admin_role': 'admins', 'auditor_role': 'auditors', 'member_role': 'users'}
#     desired_org_states = {}
#     for org_name, org_opts in org_map.items():
#         remove = bool(org_opts.get('remove', True))
#         desired_org_states[org_name] = {}
#         for org_role_name in org_roles_and_ldap_attributes.keys():
#             ldap_name = org_roles_and_ldap_attributes[org_role_name]
#             opts = org_opts.get(ldap_name, None)
#             remove = bool(org_opts.get('remove_{}'.format(ldap_name), remove))
#             desired_org_states[org_name][org_role_name] = _update_m2m_from_groups(ldap_user, opts, remove)

#         # If everything returned None (because there was no configuration) we can remove this org from our map
#         # This will prevent us from loading the org in the next query
#         if all(desired_org_states[org_name][org_role_name] is None for org_role_name in org_roles_and_ldap_attributes.keys()):
#             del desired_org_states[org_name]

#     # Compute in memory what the state is of the different LDAP teams
#     desired_team_states = {}
#     for team_name, team_opts in team_map_settings.items():
#         if 'organization' not in team_opts:
#             continue
#         users_opts = team_opts.get('users', None)
#         remove = bool(team_opts.get('remove', True))
#         state = _update_m2m_from_groups(ldap_user, users_opts, remove)
#         if state is not None:
#             organization = team_opts['organization']
#             if organization not in desired_team_states:
#                 desired_team_states[organization] = {}
#             desired_team_states[organization][team_name] = {'member_role': state}

#     # Check if user.profile is available, otherwise force user.save()
#     try:
#         _ = user.profile
#     except ValueError:
#         force_user_update = True
#     finally:
#         if force_user_update:
#             user.save()

#     # Update user profile to store LDAP DN.
#     profile = user.profile
#     if profile.ldap_dn != ldap_user.dn:
#         profile.ldap_dn = ldap_user.dn
#         profile.save()

#     reconcile_users_org_team_mappings(user, desired_org_states, desired_team_states, 'LDAP')
