# Copyright (c) 2009, Peter Sagerson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
LDAP authentication backend

Complete documentation can be found in docs/howto/auth-ldap.txt (or the thing it
compiles to).

Use of this backend requires the python-ldap module. To support unit tests, we
import ldap in a single centralized place (config._LDAPConfig) so that the test
harness can insert a mock object.

A few notes on naming conventions. If an identifier ends in _dn, it is a string
representation of a distinguished name. If it ends in _info, it is a 2-tuple
containing a DN and a dictionary of lists of attributes. ldap.search_s returns a
list of such structures. An identifier that ends in _attrs is the dictionary of
attributes from the _info structure.

A connection is an LDAPObject that has been successfully bound with a DN and
password. The identifier 'user' always refers to a User model object; LDAP user
information will be user_dn or user_info.

Additional classes can be found in the config module next to this one.
"""

import ldap
import sys
import traceback
import pprint
import copy

from django.contrib.auth.models import User, Group, Permission, SiteProfileNotAvailable
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
import django.dispatch

# Support Django 1.5's custom user models
try:
    from django.contrib.auth import get_user_model
    get_user_username = lambda u: u.get_username()
except ImportError:
    get_user_model = lambda: User                                        # noqa
    get_user_username = lambda u: u.username


from django_auth_ldap.config import _LDAPConfig, LDAPSearch


logger = _LDAPConfig.get_logger()


# Signals for populating user objects.
populate_user = django.dispatch.Signal(providing_args=["user", "ldap_user"])
populate_user_profile = django.dispatch.Signal(providing_args=["profile", "ldap_user"])


class LDAPBackend(object):
    """
    The main backend class. This implements the auth backend API, although it
    actually delegates most of its work to _LDAPUser, which is defined next.
    """
    supports_anonymous_user = False
    supports_object_permissions = True
    supports_inactive_user = False

    _settings = None
    _ldap = None  # The cached ldap module (or mock object)

    # This is prepended to our internal setting names to produce the names we
    # expect in Django's settings file. Subclasses can change this in order to
    # support multiple collections of settings.
    settings_prefix = 'AUTH_LDAP_'

    def __getstate__(self):
        """
        Exclude certain cached properties from pickling.
        """
        state = filter(
            lambda (k, v): k not in ['_settings', '_ldap'],
            self.__dict__.iteritems()
        )

        return dict(state)

    def _get_settings(self):
        if self._settings is None:
            self._settings = LDAPSettings(self.settings_prefix)

        return self._settings

    def _set_settings(self, settings):
        self._settings = settings

    settings = property(_get_settings, _set_settings)

    def _get_ldap(self):
        if self._ldap is None:
            from django.conf import settings

            options = getattr(settings, 'AUTH_LDAP_GLOBAL_OPTIONS', None)

            self._ldap = _LDAPConfig.get_ldap(options)

        return self._ldap
    ldap = property(_get_ldap)

    def get_user_model(self):
        """
        By default, this will return the model class configured by
        AUTH_USER_MODEL. Subclasses may wish to override it and return a proxy
        model.
        """
        return get_user_model()

    #
    # The Django auth backend API
    #

    def authenticate(self, username, password):
        if len(password) == 0 and not self.settings.PERMIT_EMPTY_PASSWORD:
            logger.debug('Rejecting empty password for %s' % username)
            return None

        ldap_user = _LDAPUser(self, username=username.strip())
        user = ldap_user.authenticate(password)

        return user

    def get_user(self, user_id):
        user = None

        try:
            user = self.get_user_model().objects.get(pk=user_id)
            _LDAPUser(self, user=user)  # This sets user.ldap_user
        except ObjectDoesNotExist:
            pass

        return user

    def has_perm(self, user, perm, obj=None):
        return perm in self.get_all_permissions(user, obj)

    def has_module_perms(self, user, app_label):
        for perm in self.get_all_permissions(user):
            if perm[:perm.index('.')] == app_label:
                return True

        return False

    def get_all_permissions(self, user, obj=None):
        return self.get_group_permissions(user, obj)

    def get_group_permissions(self, user, obj=None):
        if not hasattr(user, 'ldap_user') and self.settings.AUTHORIZE_ALL_USERS:
            _LDAPUser(self, user=user)  # This sets user.ldap_user

        if hasattr(user, 'ldap_user'):
            return user.ldap_user.get_group_permissions()
        else:
            return set()

    #
    # Bonus API: populate the Django user from LDAP without authenticating.
    #

    def populate_user(self, username):
        ldap_user = _LDAPUser(self, username=username)
        user = ldap_user.populate_user()

        return user

    #
    # Hooks for subclasses
    #

    def get_or_create_user(self, username, ldap_user):
        """
        This must return a (User, created) 2-tuple for the given LDAP user.
        username is the Django-friendly username of the user. ldap_user.dn is
        the user's DN and ldap_user.attrs contains all of their LDAP attributes.
        """
        model = self.get_user_model()
        username_field = getattr(model, 'USERNAME_FIELD', 'username')

        kwargs = {
            username_field + '__iexact': username,
            'defaults': {username_field: username.lower()}
        }

        return model.objects.get_or_create(**kwargs)

    def ldap_to_django_username(self, username):
        return username

    def django_to_ldap_username(self, username):
        return username


class _LDAPUser(object):
    """
    Represents an LDAP user and ultimately fields all requests that the
    backend receives. This class exists for two reasons. First, it's
    convenient to have a separate object for each request so that we can use
    object attributes without running into threading problems. Second, these
    objects get attached to the User objects, which allows us to cache
    expensive LDAP information, especially around groups and permissions.

    self.backend is a reference back to the LDAPBackend instance, which we need
    to access the ldap module and any hooks that a subclass has overridden.
    """
    class AuthenticationFailed(Exception):
        pass

    # Defaults
    _user = None
    _user_dn = None
    _user_attrs = None
    _groups = None
    _group_permissions = None
    _connection = None
    _connection_bound = False

    #
    # Initialization
    #

    def __init__(self, backend, username=None, user=None):
        """
        A new LDAPUser must be initialized with either a username or an
        authenticated User object. If a user is given, the username will be
        ignored.
        """
        self.backend = backend
        self._username = username

        if user is not None:
            self._set_authenticated_user(user)

        if username is None and user is None:
            raise Exception("Internal error: _LDAPUser improperly initialized.")

    def __deepcopy__(self, memo):
        obj = object.__new__(self.__class__)
        obj.backend = self.backend
        obj._user = copy.deepcopy(self._user, memo)

        # This is all just cached immutable data. There's no point copying it.
        obj._username = self._username
        obj._user_dn = self._user_dn
        obj._user_attrs = self._user_attrs
        obj._groups = self._groups
        obj._group_permissions = self._group_permissions

        # The connection couldn't be copied even if we wanted to
        obj._connection = self._connection
        obj._connection_bound = self._connection_bound

        return obj

    def __getstate__(self):
        """
        Most of our properties are cached from the LDAP server. We only want to
        pickle a few crucial things.
        """
        state = filter(
            lambda (k, v): k in ['backend', '_username', '_user'],
            self.__dict__.iteritems()
        )

        return dict(state)

    def _set_authenticated_user(self, user):
        self._user = user
        self._username = self.backend.django_to_ldap_username(get_user_username(user))

        user.ldap_user = self
        user.ldap_username = self._username

    def _get_ldap(self):
        return self.backend.ldap
    ldap = property(_get_ldap)

    def _get_settings(self):
        return self.backend.settings
    settings = property(_get_settings)

    #
    # Entry points
    #

    def authenticate(self, password):
        """
        Authenticates against the LDAP directory and returns the corresponding
        User object if successful. Returns None on failure.
        """
        user = None

        try:
            self._authenticate_user_dn(password)
            self._check_requirements()
            self._get_or_create_user()

            user = self._user
        except self.AuthenticationFailed, e:
            logger.debug(u"Authentication failed for %s" % self._username)
        except ldap.LDAPError, e:
            logger.warning(u"Caught LDAPError while authenticating %s: %s",
                           self._username, pprint.pformat(e))
        except Exception:
            logger.exception(u"Caught Exception while authenticating %s",
                             self._username)
            raise

        return user

    def get_group_permissions(self):
        """
        If allowed by the configuration, this returns the set of permissions
        defined by the user's LDAP group memberships.
        """
        if self._group_permissions is None:
            self._group_permissions = set()

            if self.settings.FIND_GROUP_PERMS:
                try:
                    self._load_group_permissions()
                except ldap.LDAPError, e:
                    logger.warning("Caught LDAPError loading group permissions: %s",
                                   pprint.pformat(e))

        return self._group_permissions

    def populate_user(self):
        """
        Populates the Django user object using the default bind credentials.
        """
        user = None

        try:
            # self.attrs will only be non-None if we were able to load this user
            # from the LDAP directory, so this filters out nonexistent users.
            if self.attrs is not None:
                self._get_or_create_user(force_populate=True)

            user = self._user
        except ldap.LDAPError, e:
            logger.warning(u"Caught LDAPError while authenticating %s: %s",
                           self._username, pprint.pformat(e))
        except Exception, e:
            logger.error(u"Caught Exception while authenticating %s: %s",
                         self._username, pprint.pformat(e))
            logger.error(''.join(traceback.format_tb(sys.exc_info()[2])))
            raise

        return user

    #
    # Public properties (callbacks). These are all lazy for performance reasons.
    #

    def _get_user_dn(self):
        if self._user_dn is None:
            self._load_user_dn()

        return self._user_dn
    dn = property(_get_user_dn)

    def _get_user_attrs(self):
        if self._user_attrs is None:
            self._load_user_attrs()

        return self._user_attrs
    attrs = property(_get_user_attrs)

    def _get_group_dns(self):
        return self._get_groups().get_group_dns()
    group_dns = property(_get_group_dns)

    def _get_group_names(self):
        return self._get_groups().get_group_names()
    group_names = property(_get_group_names)

    def _get_bound_connection(self):
        if not self._connection_bound:
            self._bind()

        return self._get_connection()
    connection = property(_get_bound_connection)

    #
    # Authentication
    #

    def _authenticate_user_dn(self, password):
        """
        Binds to the LDAP server with the user's DN and password. Raises
        AuthenticationFailed on failure.
        """
        if self.dn is None:
            raise self.AuthenticationFailed("Failed to map the username to a DN.")

        try:
            sticky = self.settings.BIND_AS_AUTHENTICATING_USER

            self._bind_as(self.dn, password, sticky=sticky)
        except ldap.INVALID_CREDENTIALS:
            raise self.AuthenticationFailed("User DN/password rejected by LDAP server.")

    def _load_user_attrs(self):
        if self.dn is not None:
            search = LDAPSearch(self.dn, ldap.SCOPE_BASE)
            results = search.execute(self.connection)

            if results is not None and len(results) > 0:
                self._user_attrs = results[0][1]

    def _load_user_dn(self):
        """
        Populates self._user_dn with the distinguished name of our user. This
        will either construct the DN from a template in
        AUTH_LDAP_USER_DN_TEMPLATE or connect to the server and search for it.
        """
        if self._using_simple_bind_mode():
            self._construct_simple_user_dn()
        else:
            self._search_for_user_dn()

    def _using_simple_bind_mode(self):
        return (self.settings.USER_DN_TEMPLATE is not None)

    def _construct_simple_user_dn(self):
        template = self.settings.USER_DN_TEMPLATE
        username = ldap.dn.escape_dn_chars(self._username)

        self._user_dn = template % {'user': username}

    def _search_for_user_dn(self):
        """
        Searches the directory for a user matching AUTH_LDAP_USER_SEARCH.
        Populates self._user_dn and self._user_attrs.
        """
        search = self.settings.USER_SEARCH
        if search is None:
            raise ImproperlyConfigured('AUTH_LDAP_USER_SEARCH must be an LDAPSearch instance.')

        results = search.execute(self.connection, {'user': self._username})
        if results is not None and len(results) == 1:
            (self._user_dn, self._user_attrs) = results[0]

    def _check_requirements(self):
        """
        Checks all authentication requirements beyond credentials. Raises
        AuthenticationFailed on failure.
        """
        self._check_required_group()
        self._check_denied_group()

    def _check_required_group(self):
        """
        Returns True if the group requirement (AUTH_LDAP_REQUIRE_GROUP) is
        met. Always returns True if AUTH_LDAP_REQUIRE_GROUP is None.
        """
        required_group_dn = self.settings.REQUIRE_GROUP

        if required_group_dn is not None:
            is_member = self._get_groups().is_member_of(required_group_dn)
            if not is_member:
                raise self.AuthenticationFailed("User is not a member of AUTH_LDAP_REQUIRE_GROUP")

        return True

    def _check_denied_group(self):
        """
        Returns True if the negative group requirement (AUTH_LDAP_DENY_GROUP)
        is met. Always returns True if AUTH_LDAP_DENY_GROUP is None.
        """
        denied_group_dn = self.settings.DENY_GROUP

        if denied_group_dn is not None:
            is_member = self._get_groups().is_member_of(denied_group_dn)
            if is_member:
                raise self.AuthenticationFailed("User is a member of AUTH_LDAP_DENY_GROUP")

        return True

    #
    # User management
    #

    def _get_or_create_user(self, force_populate=False):
        """
        Loads the User model object from the database or creates it if it
        doesn't exist. Also populates the fields, subject to
        AUTH_LDAP_ALWAYS_UPDATE_USER.
        """
        save_user = False

        username = self.backend.ldap_to_django_username(self._username)

        self._user, created = self.backend.get_or_create_user(username, self)
        self._user.ldap_user = self
        self._user.ldap_username = self._username

        should_populate = force_populate or self.settings.ALWAYS_UPDATE_USER or created

        if created:
            logger.debug("Created Django user %s", username)
            self._user.set_unusable_password()
            save_user = True

        if should_populate:
            logger.debug("Populating Django user %s", username)
            self._populate_user()
            save_user = True

        if self.settings.MIRROR_GROUPS:
            self._mirror_groups()

        # Give the client a chance to finish populating the user just before
        # saving.
        if should_populate:
            signal_responses = populate_user.send(self.backend.__class__, user=self._user, ldap_user=self)
            if len(signal_responses) > 0:
                save_user = True

        if save_user:
            self._user.save()

        # We populate the profile after the user model is saved to give the
        # client a chance to create the profile. Custom user models in Django
        # 1.5 probably won't have a get_profile method.
        if should_populate and hasattr(self._user, 'get_profile'):
            self._populate_and_save_user_profile()

    def _populate_user(self):
        """
        Populates our User object with information from the LDAP directory.
        """
        self._populate_user_from_attributes()
        self._populate_user_from_group_memberships()

    def _populate_user_from_attributes(self):
        for field, attr in self.settings.USER_ATTR_MAP.iteritems():
            try:
                setattr(self._user, field, self.attrs[attr][0])
            except StandardError:
                logger.warning("%s does not have a value for the attribute %s", self.dn, attr)

    def _populate_user_from_group_memberships(self):
        for field, group_dns in self.settings.USER_FLAGS_BY_GROUP.iteritems():
            if isinstance(group_dns, basestring):
                group_dns = [group_dns]
            value = any(self._get_groups().is_member_of(dn) for dn in group_dns)
            setattr(self._user, field, value)

    def _populate_and_save_user_profile(self):
        """
        Populates a User profile object with fields from the LDAP directory.
        """
        try:
            profile = self._user.get_profile()
            save_profile = False

            logger.debug("Populating Django user profile for %s", get_user_username(self._user))

            save_profile = self._populate_profile_from_attributes(profile) or save_profile
            save_profile = self._populate_profile_from_group_memberships(profile) or save_profile

            signal_responses = populate_user_profile.send(self.backend.__class__, profile=profile, ldap_user=self)
            if len(signal_responses) > 0:
                save_profile = True

            if save_profile:
                profile.save()
        except (SiteProfileNotAvailable, ObjectDoesNotExist):
            logger.debug("Django user %s does not have a profile to populate", get_user_username(self._user))

    def _populate_profile_from_attributes(self, profile):
        """
        Populate the given profile object from AUTH_LDAP_PROFILE_ATTR_MAP.
        Returns True if the profile was modified.
        """
        save_profile = False

        for field, attr in self.settings.PROFILE_ATTR_MAP.iteritems():
            try:
                # user_attrs is a hash of lists of attribute values
                setattr(profile, field, self.attrs[attr][0])
                save_profile = True
            except StandardError:
                logger.warning("%s does not have a value for the attribute %s", self.dn, attr)

        return save_profile

    def _populate_profile_from_group_memberships(self, profile):
        """
        Populate the given profile object from AUTH_LDAP_PROFILE_FLAGS_BY_GROUP.
        Returns True if the profile was modified.
        """
        save_profile = False

        for field, group_dns in self.settings.PROFILE_FLAGS_BY_GROUP.iteritems():
            if isinstance(group_dns, basestring):
                group_dns = [group_dns]
            value = any(self._get_groups().is_member_of(dn) for dn in group_dns)
            setattr(profile, field, value)
            save_profile = True

        return save_profile

    def _mirror_groups(self):
        """
        Mirrors the user's LDAP groups in the Django database and updates the
        user's membership.
        """
        group_names = self._get_groups().get_group_names()
        groups = [Group.objects.get_or_create(name=group_name)[0] for group_name
                  in group_names]

        self._user.groups = groups

    #
    # Group information
    #

    def _load_group_permissions(self):
        """
        Populates self._group_permissions based on LDAP group membership and
        Django group permissions.
        """
        group_names = self._get_groups().get_group_names()

        perms = Permission.objects.filter(group__name__in=group_names)
        perms = perms.values_list('content_type__app_label', 'codename')
        perms = perms.order_by()

        self._group_permissions = set(["%s.%s" % (ct, name) for ct, name in perms])

    def _get_groups(self):
        """
        Returns an _LDAPUserGroups object, which can determine group
        membership.
        """
        if self._groups is None:
            self._groups = _LDAPUserGroups(self)

        return self._groups

    #
    # LDAP connection
    #

    def _bind(self):
        """
        Binds to the LDAP server with AUTH_LDAP_BIND_DN and
        AUTH_LDAP_BIND_PASSWORD.
        """
        self._bind_as(self.settings.BIND_DN, self.settings.BIND_PASSWORD,
                      sticky=True)

    def _bind_as(self, bind_dn, bind_password, sticky=False):
        """
        Binds to the LDAP server with the given credentials. This does not trap
        exceptions.

        If sticky is True, then we will consider the connection to be bound for
        the life of this object. If False, then the caller only wishes to test
        the credentials, after which the connection will be considered unbound.
        """
        self._get_connection().simple_bind_s(bind_dn.encode('utf-8'),
                                             bind_password.encode('utf-8'))

        self._connection_bound = sticky

    def _get_connection(self):
        """
        Returns our cached LDAPObject, which may or may not be bound.
        """
        if self._connection is None:
            uri = self.settings.SERVER_URI
            if callable(uri):
                uri = uri()

            self._connection = self.backend.ldap.initialize(uri)

            for opt, value in self.settings.CONNECTION_OPTIONS.iteritems():
                self._connection.set_option(opt, value)

            if self.settings.START_TLS:
                logger.debug("Initiating TLS")
                self._connection.start_tls_s()

        return self._connection


class _LDAPUserGroups(object):
    """
    Represents the set of groups that a user belongs to.
    """
    def __init__(self, ldap_user):
        self.settings = ldap_user.settings
        self._ldap_user = ldap_user
        self._group_type = None
        self._group_search = None
        self._group_infos = None
        self._group_dns = None
        self._group_names = None

        self._init_group_settings()

    def _init_group_settings(self):
        """
        Loads the settings we need to deal with groups. Raises
        ImproperlyConfigured if anything's not right.
        """
        self._group_type = self.settings.GROUP_TYPE
        if self._group_type is None:
            raise ImproperlyConfigured("AUTH_LDAP_GROUP_TYPE must be an LDAPGroupType instance.")

        self._group_search = self.settings.GROUP_SEARCH
        if self._group_search is None:
            raise ImproperlyConfigured("AUTH_LDAP_GROUP_SEARCH must be an LDAPSearch instance.")

    def get_group_names(self):
        """
        Returns the set of Django group names that this user belongs to by
        virtue of LDAP group memberships.
        """
        if self._group_names is None:
            self._load_cached_attr("_group_names")

        if self._group_names is None:
            group_infos = self._get_group_infos()
            self._group_names = set(
                self._group_type.group_name_from_info(group_info)
                for group_info in group_infos
            )
            self._cache_attr("_group_names")

        return self._group_names

    def is_member_of(self, group_dn):
        """
        Returns true if our user is a member of the given group.
        """
        is_member = None

        # Normalize the DN
        group_dn = group_dn.lower()

        # If we have self._group_dns, we'll use it. Otherwise, we'll try to
        # avoid the cost of loading it.
        if self._group_dns is None:
            is_member = self._group_type.is_member(self._ldap_user, group_dn)

        if is_member is None:
            is_member = (group_dn in self.get_group_dns())

        logger.debug("%s is%sa member of %s", self._ldap_user.dn,
                     is_member and " " or " not ", group_dn)

        return is_member

    def get_group_dns(self):
        """
        Returns a (cached) set of the distinguished names in self._group_infos.
        """
        if self._group_dns is None:
            group_infos = self._get_group_infos()
            self._group_dns = set(group_info[0] for group_info in group_infos)

        return self._group_dns

    def _get_group_infos(self):
        """
        Returns a (cached) list of group_info structures for the groups that our
        user is a member of.
        """
        if self._group_infos is None:
            self._group_infos = self._group_type.user_groups(self._ldap_user,
                                                             self._group_search)

        return self._group_infos

    def _load_cached_attr(self, attr_name):
        if self.settings.CACHE_GROUPS:
            key = self._cache_key(attr_name)
            value = cache.get(key)
            setattr(self, attr_name, value)

    def _cache_attr(self, attr_name):
        if self.settings.CACHE_GROUPS:
            key = self._cache_key(attr_name)
            value = getattr(self, attr_name, None)
            cache.set(key, value, self.settings.GROUP_CACHE_TIMEOUT)

    def _cache_key(self, attr_name):
        """
        Memcache keys can't have spaces in them, so we'll remove them from the
        DN for maximum compatibility.
        """
        dn = self._ldap_user.dn.replace(' ', '%20')
        key = u'auth_ldap.%s.%s.%s' % (self.__class__.__name__, attr_name, dn)

        return key


class LDAPSettings(object):
    """
    This is a simple class to take the place of the global settings object. An
    instance will contain all of our settings as attributes, with default values
    if they are not specified by the configuration.
    """
    defaults = {
        'ALWAYS_UPDATE_USER': True,
        'AUTHORIZE_ALL_USERS': False,
        'BIND_AS_AUTHENTICATING_USER': False,
        'BIND_DN': '',
        'BIND_PASSWORD': '',
        'CACHE_GROUPS': False,
        'CONNECTION_OPTIONS': {},
        'DENY_GROUP': None,
        'FIND_GROUP_PERMS': False,
        'GROUP_CACHE_TIMEOUT': None,
        'GROUP_SEARCH': None,
        'GROUP_TYPE': None,
        'MIRROR_GROUPS': False,
        'PERMIT_EMPTY_PASSWORD': False,
        'PROFILE_ATTR_MAP': {},
        'PROFILE_FLAGS_BY_GROUP': {},
        'REQUIRE_GROUP': None,
        'SERVER_URI': 'ldap://localhost',
        'START_TLS': False,
        'USER_ATTR_MAP': {},
        'USER_DN_TEMPLATE': None,
        'USER_FLAGS_BY_GROUP': {},
        'USER_SEARCH': None,
    }

    def __init__(self, prefix='AUTH_LDAP_'):
        """
        Loads our settings from django.conf.settings, applying defaults for any
        that are omitted.
        """
        from django.conf import settings

        for name, default in self.defaults.iteritems():
            value = getattr(settings, prefix + name, default)
            setattr(self, name, value)
