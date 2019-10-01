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
from django.utils.encoding import force_text

# django-auth-ldap
from django_auth_ldap.backend import LDAPSettings as BaseLDAPSettings
from django_auth_ldap.backend import LDAPBackend as BaseLDAPBackend
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

logger = logging.getLogger('awx.sso.backends')


class LDAPSettings(BaseLDAPSettings):

    defaults = dict(list(BaseLDAPSettings.defaults.items()) + list({
        'ORGANIZATION_MAP': {},
        'TEAM_MAP': {},
        'GROUP_TYPE_PARAMS': {},
    }.items()))

    def __init__(self, prefix='AUTH_LDAP_', defaults={}):
        super(LDAPSettings, self).__init__(prefix, defaults)

        # If a DB-backed setting is specified that wipes out the
        # OPT_NETWORK_TIMEOUT, fall back to a sane default
        if ldap.OPT_NETWORK_TIMEOUT not in getattr(self, 'CONNECTION_OPTIONS', {}):
            options = getattr(self, 'CONNECTION_OPTIONS', {})
            options[ldap.OPT_NETWORK_TIMEOUT] = 30
            self.CONNECTION_OPTIONS = options

        # when specifying `.set_option()` calls for TLS in python-ldap, the
        # *order* in which you invoke them *matters*, particularly in Python3,
        # where dictionary insertion order is persisted
        #
        # specifically, it is *critical* that `ldap.OPT_X_TLS_NEWCTX` be set *last*
        # this manual sorting puts `OPT_X_TLS_NEWCTX` *after* other TLS-related
        # options
        #
        # see: https://github.com/python-ldap/python-ldap/issues/55
        newctx_option = self.CONNECTION_OPTIONS.pop(ldap.OPT_X_TLS_NEWCTX, None)
        self.CONNECTION_OPTIONS = OrderedDict(self.CONNECTION_OPTIONS)
        if newctx_option is not None:
            self.CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = newctx_option


class LDAPBackend(BaseLDAPBackend):
    '''
    Custom LDAP backend for AWX.
    '''

    settings_prefix = 'AUTH_LDAP_'

    def __init__(self, *args, **kwargs):
        self._dispatch_uid = uuid.uuid4()
        super(LDAPBackend, self).__init__(*args, **kwargs)
        setting_changed.connect(self._on_setting_changed, dispatch_uid=self._dispatch_uid)

    def _on_setting_changed(self, sender, **kwargs):
        # If any AUTH_LDAP_* setting changes, force settings to be reloaded for
        # this backend instance.
        if kwargs.get('setting', '').startswith(self.settings_prefix):
            self._settings = None

    def _get_settings(self):
        if self._settings is None:
            self._settings = LDAPSettings(self.settings_prefix)
        return self._settings

    def _set_settings(self, settings):
        self._settings = settings

    settings = property(_get_settings, _set_settings)

    def authenticate(self, request, username, password):
        if self.settings.START_TLS and ldap.OPT_X_TLS_REQUIRE_CERT in self.settings.CONNECTION_OPTIONS:
            # with python-ldap, if you want to set connection-specific TLS
            # parameters, you must also specify OPT_X_TLS_NEWCTX = 0
            # see: https://stackoverflow.com/a/29722445
            # see: https://stackoverflow.com/a/38136255
            self.settings.CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0

        if not self.settings.SERVER_URI:
            return None
        try:
            user = User.objects.get(username=username)
            if user and (not user.profile or not user.profile.ldap_dn):
                return None
        except User.DoesNotExist:
            pass

        try:
            for setting_name, type_ in [
                ('GROUP_SEARCH', 'LDAPSearch'),
                ('GROUP_TYPE', 'LDAPGroupType'),
            ]:
                if getattr(self.settings, setting_name) is None:
                    raise ImproperlyConfigured(
                        "{} must be an {} instance.".format(setting_name, type_)
                    )
            return super(LDAPBackend, self).authenticate(request, username, password)
        except Exception:
            logger.exception("Encountered an error authenticating to LDAP")
            return None

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


class LDAPBackend1(LDAPBackend):
    settings_prefix = 'AUTH_LDAP_1_'


class LDAPBackend2(LDAPBackend):
    settings_prefix = 'AUTH_LDAP_2_'


class LDAPBackend3(LDAPBackend):
    settings_prefix = 'AUTH_LDAP_3_'


class LDAPBackend4(LDAPBackend):
    settings_prefix = 'AUTH_LDAP_4_'


class LDAPBackend5(LDAPBackend):
    settings_prefix = 'AUTH_LDAP_5_'


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
        logger.debug("Created enterprise user %s via %s backend." %
                     (username, enterprise_auth.get_provider_display()))
        created = True
    if created or user.is_in_enterprise_category(provider):
        return user
    logger.warn("Enterprise user %s already defined in Tower." % username)


class RADIUSBackend(BaseRADIUSBackend):
    '''
    Custom Radius backend to verify license status
    '''

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

    def get_django_user(self, username, password=None):
        return _get_or_set_enterprise_user(force_text(username), force_text(password), 'radius')


class TACACSPlusBackend(object):
    '''
    Custom TACACS+ auth backend for AWX
    '''

    def authenticate(self, request, username, password):
        if not django_settings.TACACSPLUS_HOST:
            return None
        try:
            # Upstream TACACS+ client does not accept non-string, so convert if needed.
            auth = tacacs_plus.TACACSClient(
                django_settings.TACACSPLUS_HOST,
                django_settings.TACACSPLUS_PORT,
                django_settings.TACACSPLUS_SECRET,
                timeout=django_settings.TACACSPLUS_SESSION_TIMEOUT,
            ).authenticate(
                username, password,
                authen_type=tacacs_plus.TAC_PLUS_AUTHEN_TYPES[django_settings.TACACSPLUS_AUTH_PROTOCOL],
            )
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


class TowerSAMLIdentityProvider(BaseSAMLIdentityProvider):
    '''
    Custom Identity Provider to make attributes to what we expect.
    '''

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
            logger.warn("Could not map user detail '%s' from SAML attribute '%s'; "
                        "update SOCIAL_AUTH_SAML_ENABLED_IDPS['%s']['%s'] with the correct SAML attribute.",
                        conf_key[5:], key, self.name, conf_key)
        return str(value) if value is not None else value


class SAMLAuth(BaseSAMLAuth):
    '''
    Custom SAMLAuth backend to verify license status
    '''

    def get_idp(self, idp_name):
        idp_config = self.setting('ENABLED_IDPS')[idp_name]
        return TowerSAMLIdentityProvider(idp_name, **idp_config)

    def authenticate(self, request, *args, **kwargs):
        if not all([django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID, django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                    django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY, django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                    django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT, django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                    django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS]):
            return None
        user = super(SAMLAuth, self).authenticate(request, *args, **kwargs)
        # Comes from https://github.com/omab/python-social-auth/blob/v0.2.21/social/backends/base.py#L91
        if getattr(user, 'is_new', False):
            _decorate_enterprise_user(user, 'saml')
        elif user and not user.is_in_enterprise_category('saml'):
            return None
        return user

    def get_user(self, user_id):
        if not all([django_settings.SOCIAL_AUTH_SAML_SP_ENTITY_ID, django_settings.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
                    django_settings.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY, django_settings.SOCIAL_AUTH_SAML_ORG_INFO,
                    django_settings.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT, django_settings.SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
                    django_settings.SOCIAL_AUTH_SAML_ENABLED_IDPS]):
            return None
        return super(SAMLAuth, self).get_user(user_id)


def _update_m2m_from_groups(user, ldap_user, related, opts, remove=True):
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
        if isinstance(opts, str):
            opts = [opts]
        for group_dn in opts:
            if not isinstance(group_dn, str):
                continue
            if ldap_user._get_groups().is_member_of(group_dn):
                should_add = True
    if should_add:
        user.save()
        related.add(user)
    elif remove and user in related.all():
        user.save()
        related.remove(user)


@receiver(populate_user, dispatch_uid='populate-ldap-user')
def on_populate_user(sender, **kwargs):
    '''
    Handle signal from LDAP backend to populate the user object.  Update user
    organization/team memberships according to their LDAP groups.
    '''
    from awx.main.models import Organization, Team
    user = kwargs['user']
    ldap_user = kwargs['ldap_user']
    backend = ldap_user.backend

    # Prefetch user's groups to prevent LDAP queries for each org/team when
    # checking membership.
    ldap_user._get_groups().get_group_dns()

    # If the LDAP user has a first or last name > $maxlen chars, truncate it
    for field in ('first_name', 'last_name'):
        max_len = User._meta.get_field(field).max_length
        field_len = len(getattr(user, field))
        if field_len > max_len:
            setattr(user, field, getattr(user, field)[:max_len])
            logger.warn(
                'LDAP user {} has {} > max {} characters'.format(user.username, field, max_len)
            )

    # Update organization membership based on group memberships.
    org_map = getattr(backend.settings, 'ORGANIZATION_MAP', {})
    for org_name, org_opts in org_map.items():
        org, created = Organization.objects.get_or_create(name=org_name)
        remove = bool(org_opts.get('remove', True))
        admins_opts = org_opts.get('admins', None)
        remove_admins = bool(org_opts.get('remove_admins', remove))
        _update_m2m_from_groups(user, ldap_user, org.admin_role.members, admins_opts,
                                remove_admins)
        auditors_opts = org_opts.get('auditors', None)
        remove_auditors = bool(org_opts.get('remove_auditors', remove))
        _update_m2m_from_groups(user, ldap_user, org.auditor_role.members, auditors_opts,
                                remove_auditors)
        users_opts = org_opts.get('users', None)
        remove_users = bool(org_opts.get('remove_users', remove))
        _update_m2m_from_groups(user, ldap_user, org.member_role.members, users_opts,
                                remove_users)

    # Update team membership based on group memberships.
    team_map = getattr(backend.settings, 'TEAM_MAP', {})
    for team_name, team_opts in team_map.items():
        if 'organization' not in team_opts:
            continue
        org, created = Organization.objects.get_or_create(name=team_opts['organization'])
        team, created = Team.objects.get_or_create(name=team_name, organization=org)
        users_opts = team_opts.get('users', None)
        remove = bool(team_opts.get('remove', True))
        _update_m2m_from_groups(user, ldap_user, team.member_role.members, users_opts,
                                remove)

    # Update user profile to store LDAP DN.
    user.save()
    profile = user.profile
    if profile.ldap_dn != ldap_user.dn:
        profile.ldap_dn = ldap_user.dn
        profile.save()
