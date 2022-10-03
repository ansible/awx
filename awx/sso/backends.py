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
from django.contrib.contenttypes.models import ContentType
from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.utils.encoding import force_str
from django.db.utils import IntegrityError

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

    defaults = dict(list(BaseLDAPSettings.defaults.items()) + list({'ORGANIZATION_MAP': {}, 'TEAM_MAP': {}, 'GROUP_TYPE_PARAMS': {}}.items()))

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

    """
    Custom LDAP backend for AWX.
    """

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
            for setting_name, type_ in [('GROUP_SEARCH', 'LDAPSearch'), ('GROUP_TYPE', 'LDAPGroupType')]:
                if getattr(self.settings, setting_name) is None:
                    raise ImproperlyConfigured("{} must be an {} instance.".format(setting_name, type_))
            ldap_user = super(LDAPBackend, self).authenticate(request, username, password)
            # If we have an LDAP user and that user we found has an ldap_user internal object and that object has a bound connection
            # Then we can try and force an unbind to close the sticky connection
            if ldap_user and ldap_user.ldap_user and ldap_user.ldap_user._connection_bound:
                logger.debug("Forcing LDAP connection to close")
                try:
                    ldap_user.ldap_user._connection.unbind_s()
                    ldap_user.ldap_user._connection_bound = False
                except Exception:
                    logger.exception(f"Got unexpected LDAP exception when forcing LDAP disconnect for user {ldap_user}, login will still proceed")
            return ldap_user
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
            auth = tacacs_plus.TACACSClient(
                django_settings.TACACSPLUS_HOST,
                django_settings.TACACSPLUS_PORT,
                django_settings.TACACSPLUS_SECRET,
                timeout=django_settings.TACACSPLUS_SESSION_TIMEOUT,
            ).authenticate(username, password, authen_type=tacacs_plus.TAC_PLUS_AUTHEN_TYPES[django_settings.TACACSPLUS_AUTH_PROTOCOL])
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
                "Could not map user detail '%s' from SAML attribute '%s'; " "update SOCIAL_AUTH_SAML_ENABLED_IDPS['%s']['%s'] with the correct SAML attribute.",
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
    return False


@receiver(populate_user, dispatch_uid='populate-ldap-user')
def on_populate_user(sender, **kwargs):
    """
    Handle signal from LDAP backend to populate the user object.  Update user
    organization/team memberships according to their LDAP groups.
    """
    from awx.main.models import Organization, Team

    user = kwargs['user']
    ldap_user = kwargs['ldap_user']
    backend = ldap_user.backend

    # Boolean to determine if we should force an user update
    # to avoid duplicate SQL update statements
    force_user_update = False

    # Prefetch user's groups to prevent LDAP queries for each org/team when
    # checking membership.
    ldap_user._get_groups().get_group_dns()

    # If the LDAP user has a first or last name > $maxlen chars, truncate it
    for field in ('first_name', 'last_name'):
        max_len = User._meta.get_field(field).max_length
        field_len = len(getattr(user, field))
        if field_len > max_len:
            setattr(user, field, getattr(user, field)[:max_len])
            force_user_update = True
            logger.warning('LDAP user {} has {} > max {} characters'.format(user.username, field, max_len))

    org_map = getattr(backend.settings, 'ORGANIZATION_MAP', {})
    team_map = getattr(backend.settings, 'TEAM_MAP', {})

    # Move this junk into save of the settings for performance later, there is no need to do that here
    #    with maybe the exception of someone defining this in settings before the server is started?
    # ==============================================================================================================

    # Get all of the IDs and names of orgs in the DB and create any new org defined in LDAP that does not exist in the DB
    existing_orgs = {}
    for (org_id, org_name) in Organization.objects.all().values_list('id', 'name'):
        existing_orgs[org_name] = org_id

    # Create any orgs (if needed) for all entries in the org and team maps
    for org_name in set(list(org_map.keys()) + [item.get('organization', None) for item in team_map.values()]):
        if org_name and org_name not in existing_orgs:
            logger.info("LDAP adapter is creating org {}".format(org_name))
            try:
                new_org = Organization.objects.create(name=org_name)
            except IntegrityError:
                # Another thread must have created this org before we did so now we need to get it
                new_org = Organization.objects.get(name=org_name)
            # Add the org name to the existing orgs since we created it and we may need it to build the teams below
            existing_orgs[org_name] = new_org.id

    # Do the same for teams
    existing_team_names = list(Team.objects.all().values_list('name', flat=True))
    for team_name, team_opts in team_map.items():
        if 'organization' not in team_opts:
            # You can't save the LDAP config in the UI w/o an org so if we somehow got this condition its an error
            logger.error("Team named {} in LDAP team map settings is invalid due to missing organization".format(team_name))
            continue
        if team_name not in existing_team_names:
            try:
                Team.objects.create(name=team_name, organization_id=existing_orgs[team_opts['organization']])
            except IntegrityError:
                # If another process got here before us that is ok because we don't need the ID from this team or anything
                pass
    # End move some day
    # ==============================================================================================================

    # Compute in memory what the state is of the different LDAP orgs
    org_roles_and_ldap_attributes = {'admin_role': 'admins', 'auditor_role': 'auditors', 'member_role': 'users'}
    desired_org_states = {}
    for org_name, org_opts in org_map.items():
        remove = bool(org_opts.get('remove', True))
        desired_org_states[org_name] = {}
        for org_role_name in org_roles_and_ldap_attributes.keys():
            ldap_name = org_roles_and_ldap_attributes[org_role_name]
            opts = org_opts.get(ldap_name, None)
            remove = bool(org_opts.get('remove_{}'.format(ldap_name), remove))
            desired_org_states[org_name][org_role_name] = _update_m2m_from_groups(ldap_user, opts, remove)

        # If everything returned None (because there was no configuration) we can remove this org from our map
        # This will prevent us from loading the org in the next query
        if all(desired_org_states[org_name][org_role_name] is None for org_role_name in org_roles_and_ldap_attributes.keys()):
            del desired_org_states[org_name]

    # Compute in memory what the state is of the different LDAP teams
    desired_team_states = {}
    for team_name, team_opts in team_map.items():
        if 'organization' not in team_opts:
            continue
        users_opts = team_opts.get('users', None)
        remove = bool(team_opts.get('remove', True))
        state = _update_m2m_from_groups(ldap_user, users_opts, remove)
        if state is not None:
            desired_team_states[team_name] = {'member_role': state}

    # Check if user.profile is available, otherwise force user.save()
    try:
        _ = user.profile
    except ValueError:
        force_user_update = True
    finally:
        if force_user_update:
            user.save()

    # Update user profile to store LDAP DN.
    profile = user.profile
    if profile.ldap_dn != ldap_user.dn:
        profile.ldap_dn = ldap_user.dn
        profile.save()

    reconcile_users_org_team_mappings(user, desired_org_states, desired_team_states, 'LDAP')


def reconcile_users_org_team_mappings(user, desired_org_states, desired_team_states, source):
    from awx.main.models import Organization, Team

    org_content_type = ContentType.objects.get_for_model(Organization)
    team_content_type = ContentType.objects.get_for_model(Team)

    # users_roles is a flat list of IDs
    users_roles = list(user.roles.filter(content_type__in=[org_content_type, team_content_type]).values_list('pk', flat=True))

    for object_type, desired_states, model in [('organization', desired_org_states, Organization), ('team', desired_team_states, Team)]:
        # Get all of the roles in the desired states for efficient DB extraction
        roles = []
        for sub_dict in desired_states.values():
            for role_name in sub_dict:
                if sub_dict[role_name] == None:
                    continue
                if role_name not in roles:
                    roles.append(role_name)

        # Get a set of named tuples for the org name plus all of the roles we got above
        model_roles = getattr(model, 'objects').filter(name__in=desired_states.keys()).values_list(*(['name'] + roles), named=True)
        for row in model_roles:
            for role_name in roles:
                desired_state = desired_states.get(row.name, {})
                if desired_state[role_name] == None:
                    # The mapping was not defined for this [org/team]/role so we can just pass
                    pass

                # If somehow the auth adapter knows about an items role but that role is not defined in the DB we are going to print a pretty error
                # This is your classic safety net that we should never hit; but here you are reading this comment... good luck and Godspeed.
                role_id = getattr(row, role_name, None)
                if role_id == None:
                    logger.error("{} adapter wanted to manage role {} of {} {} but that role is not defined".format(source, role_name, object_type, row.name))
                    continue

                if desired_state[role_name]:
                    # The desired state was the user mapped into the object_type, if the user was not mapped in map them in
                    if role_id not in users_roles:
                        logger.debug("{} adapter adding user {} to {} {} as {}".format(source, user.username, object_type, row.name, role_name))
                        user.roles.add(role_id)
                else:
                    # The desired state was the user was not mapped into the org, if the user has the permission remove it
                    if role_id in users_roles:
                        logger.debug("{} adapter removing user {} permission of {} from {} {}".format(source, user.username, role_name, object_type, row.name))
                        user.roles.remove(role_id)
