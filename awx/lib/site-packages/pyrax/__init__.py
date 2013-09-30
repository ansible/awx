#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


# For doxygen class doc generation:
"""
\mainpage Class Documentation for pyrax

This module provides the Python Language Bindings for creating applications
built on the Rackspace / OpenStack Cloud.<br />

The source code for <b>pyrax</b> can be found at:

http://github.com/rackspace/pyrax

\package cf_wrapper

This module wraps <b>swiftclient</b>, the Python client for OpenStack / Swift,
providing an object-oriented interface to the Swift object store.

It also adds in CDN functionality that is Rackspace-specific.
"""
import ConfigParser
from functools import wraps
import inspect
import logging
import os

# keyring is an optional import
try:
    import keyring
except ImportError:
    keyring = None

# The following try block is only needed when first installing pyrax,
# since importing the version info in setup.py tries to import this
# entire module.
try:
    from identity import *

    import exceptions as exc
    import version

    import cf_wrapper.client as _cf
    from cf_wrapper.storage_object import StorageObject
    from cf_wrapper.container import Container
    from novaclient import exceptions as _cs_exceptions
    from novaclient import auth_plugin as _cs_auth_plugin
    from novaclient.v1_1 import client as _cs_client
    from novaclient.v1_1.servers import Server as CloudServer

    from autoscale import AutoScaleClient
    from clouddatabases import CloudDatabaseClient
    from clouddatabases import CloudDatabaseDatabase
    from clouddatabases import CloudDatabaseFlavor
    from clouddatabases import CloudDatabaseInstance
    from clouddatabases import CloudDatabaseUser
    from cloudloadbalancers import CloudLoadBalancer
    from cloudloadbalancers import CloudLoadBalancerClient
    from cloudblockstorage import CloudBlockStorageClient
    from clouddns import CloudDNSClient
    from cloudnetworks import CloudNetworkClient
    from cloudmonitoring import CloudMonitorClient
except ImportError:
    # See if this is the result of the importing of version.py in setup.py
    callstack = inspect.stack()
    in_setup = False
    for stack in callstack:
        if stack[1].endswith("/setup.py"):
            in_setup = True
    if not in_setup:
        # This isn't a normal import problem during setup; re-raise
        raise

# Initiate the services to None until we are authenticated.
cloudservers = None
cloudfiles = None
cloud_loadbalancers = None
cloud_databases = None
cloud_blockstorage = None
cloud_dns = None
cloud_networks = None
cloud_monitoring = None
autoscale = None
# Default region for all services. Can be individually overridden if needed
default_region = None
# Encoding to use when working with non-ASCII names
default_encoding = "utf-8"

# Config settings
settings = {}
_environment = "default"
identity = None

# Value to plug into the user-agent headers
USER_AGENT = "pyrax/%s" % version.version

# Do we output HTTP traffic for debugging?
_http_debug = False

# Regions and services available from the service catalog
regions = tuple()
services = tuple()

_client_classes = {
        "database": CloudDatabaseClient,
        "load_balancer": CloudLoadBalancerClient,
        "volume": CloudBlockStorageClient,
        "dns": CloudDNSClient,
        "compute:network": CloudNetworkClient,
        "monitor": CloudMonitorClient,
        "autoscale": AutoScaleClient,
        }


def _id_type(ityp):
    """Allow for shorthand names for the most common types."""
    if ityp.lower() == "rackspace":
        ityp = "rax_identity.RaxIdentity"
    elif ityp.lower() == "keystone":
        ityp = "keystone_identity.KeystoneIdentity"
    return ityp


def _import_identity(import_str):
    import_str = _id_type(import_str)
    full_str = "pyrax.identity.%s" % import_str
    return utils.import_class(full_str)



class Settings(object):
    """
    Holds and manages the settings for pyrax.
    """
    _environment = None
    env_dct = {
            "identity_type": "CLOUD_ID_TYPE",
            "auth_endpoint": "CLOUD_AUTH_ENDPOINT",
            "keyring_username": "CLOUD_KEYRING_USER",
            "region": "CLOUD_REGION",
            "tenant_id": "CLOUD_TENANT_ID",
            "tenant_name": "CLOUD_TENANT_NAME",
            "encoding": "CLOUD_ENCODING",
            "custom_user_agent": "CLOUD_USER_AGENT",
            "debug": "CLOUD_DEBUG",
            "verify_ssl": "CLOUD_VERIFY_SSL",
            }
    _settings = {"default": dict.fromkeys(env_dct.keys())}
    _default_set = False


    def get(self, key, env=None):
        """
        Returns the config setting for the specified environment. If no
        environment is specified, the value for the current environment is
        returned. If an unknown key or environment is passed, None is returned.
        """
        if env is None:
            env = self.environment
        try:
            return self._settings[env][key]
        except KeyError:
            # See if it's set in the environment
            if key == "identity_class":
                # This is defined via the identity_type
                env_var = self.env_dct.get("identity_type")
                ityp = os.environ.get(env_var)
                if ityp:
                    return _import_identity(ityp)
            else:
                env_var = self.env_dct.get(key)
            try:
                return os.environ[env_var]
            except KeyError:
                return None


    def set(self, key, val, env=None):
        """
        Changes the value for the setting specified by 'key' to the new value.
        By default this will change the current environment, but you can change
        values in other environments by passing the name of that environment as
        the 'env' parameter.
        """
        if env is None:
            env = self.environment
        else:
            if env not in self._settings:
                raise exc.EnvironmentNotFound("There is no environment named "
                "'%s'." % env)
        dct = self._settings[env]
        if key not in dct:
            raise exc.InvalidSetting("The setting '%s' is not defined." % key)
        dct[key] = val
        if key == "identity_type":
            # If setting the identity_type, also change the identity_class.
            dct["identity_class"] = _import_identity(val)
        elif key == "region":
            if not identity:
                return
            current = identity.region
            if current == val:
                return
            if "LON" in (current, val):
                # This is an outlier, as it has a separate auth
                identity.region = val
        elif key == "verify_ssl":
            if not identity:
                return
            identity.verify_ssl = val


    def _getEnvironment(self):
        return self._environment or "default"

    def _setEnvironment(self, val):
        if val not in self._settings:
            raise exc.EnvironmentNotFound("The environment '%s' has not been "
                    "defined." % val)
        if val != self.environment:
            self._environment = val
            clear_credentials()
            _create_identity()

    environment = property(_getEnvironment, _setEnvironment, None,
            """Users can define several environments for use with pyrax. This
            holds the name of the current environment they are working in.
            Changing this value will discard any existing authentication
            credentials, and will set all the individual clients for cloud
            services, such as `pyrax.cloudservers`, to None. You must
            authenticate against the new environment with the credentials
            appropriate for that cloud provider.""")


    @property
    def environments(self):
        return self._settings.keys()


    def read_config(self, config_file):
        """
        Parses the specified configuration file and stores the values. Raises
        an InvalidConfigurationFile exception if the file is not well-formed.
        """
        cfg = ConfigParser.SafeConfigParser()
        try:
            cfg.read(config_file)
        except ConfigParser.MissingSectionHeaderError as e:
            # The file exists, but doesn't have the correct format.
            raise exc.InvalidConfigurationFile(e)

        def safe_get(section, option, default=None):
            try:
                return cfg.get(section, option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                return default

        for section in cfg.sections():
            if section == "settings":
                section_name = "default"
                self._default_set = True
            else:
                section_name = section
            dct = self._settings[section_name] = {}
            dct["region"] = safe_get(section, "region", default_region)
            ityp = safe_get(section, "identity_type")
            dct["identity_type"] = _id_type(ityp)
            dct["identity_class"] = _import_identity(ityp)
            # Handle both the old and new names for this setting.
            debug = safe_get(section, "debug")
            if debug is None:
                debug = safe_get(section, "http_debug", "False")
            dct["http_debug"] = debug == "True"
            verify_ssl = safe_get(section, "verify_ssl", "True")
            dct["verify_ssl"] = verify_ssl == "True"
            dct["keyring_username"] = safe_get(section, "keyring_username")
            dct["encoding"] = safe_get(section, "encoding", default_encoding)
            dct["auth_endpoint"] = safe_get(section, "auth_endpoint")
            dct["tenant_name"] = safe_get(section, "tenant_name")
            dct["tenant_id"] = safe_get(section, "tenant_id")
            app_agent = safe_get(section, "custom_user_agent")
            if app_agent:
                # Customize the user-agent string with the app name.
                dct["user_agent"] = "%s %s" % (app_agent, USER_AGENT)
            else:
                dct["user_agent"] = USER_AGENT

            # If this is the first section, make it the default
            if not self._default_set:
                self._settings["default"] = self._settings[section]
                self._default_set = True


def get_environment():
    """
    Returns the name of the current environment.
    """
    return settings.environment


def set_environment(env):
    """
    Change your configuration environment. An EnvironmentNotFound exception
    is raised if you pass in an undefined environment name.
    """
    settings.environment = env


def list_environments():
    """
    Returns a list of all defined environments.
    """
    return settings.environments


def get_setting(key, env=None):
    """
    Returns the config setting for the specified key. If no environment is
    specified, returns the setting for the current environment.
    """
    return settings.get(key, env=env)


def set_setting(key, val, env=None):
    """
    Changes the value of the specified key in the current environment, or in
    another environment if specified.
    """
    return settings.set(key, val, env=env)


def set_default_region(region):
    """Changes the default_region setting."""
    global default_region
    default_region = region


def _create_identity():
    """
    Creates an instance of the current identity_class and assigns it to the
    module-level name 'identity'.
    """
    global identity
    cls = settings.get("identity_class")
    if not cls:
        raise exc.IdentityClassNotDefined("No identity class has "
                "been defined for the current environment.")
    verify_ssl = get_setting("verify_ssl")
    identity = cls(verify_ssl=verify_ssl)


def _assure_identity(fnc):
    """Ensures that the 'identity' attribute is not None."""
    def _wrapped(*args, **kwargs):
        if identity is None:
            _create_identity()
        return fnc(*args, **kwargs)
    return _wrapped


def _require_auth(fnc):
    """Authentication decorator."""
    @wraps(fnc)
    @_assure_identity
    def _wrapped(*args, **kwargs):
        if not identity.authenticated:
            msg = "Authentication required before calling '%s'." % fnc.__name__
            raise exc.NotAuthenticated(msg)
        return fnc(*args, **kwargs)
    return _wrapped


@_assure_identity
def _safe_region(region=None):
    """Value to use when no region is specified."""
    ret = region or settings.get("region")
    if not ret:
        # Nothing specified; get the default from the identity object.
        ret = identity.get_default_region()
    return ret


@_assure_identity
def auth_with_token(token, tenant_id=None, tenant_name=None, region=None):
    """
    If you already have a valid token and either a tenant ID or name, you can
    call this to configure the identity and available services.
    """
    identity.auth_with_token(token, tenant_id=tenant_id,
            tenant_name=tenant_name)
    connect_to_services(region=region)


@_assure_identity
def set_credentials(username, api_key=None, password=None, region=None,
        tenant_id=None, authenticate=True):
    """
    Set the credentials directly, and then try to authenticate.

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    pw_key = password or api_key
    region = _safe_region(region)
    tenant_id = tenant_id or settings.get("tenant_id")
    identity.set_credentials(username=username, password=pw_key,
            tenant_id=tenant_id, region=region)
    if authenticate:
        _auth_and_connect(region=region)


@_assure_identity
def set_credential_file(cred_file, region=None, authenticate=True):
    """
    Read in the credentials from the supplied file path, and then try to
    authenticate. The file should be a standard config file in one of the
    following formats:

    For Keystone authentication:
        [keystone]
        username = myusername
        password = 1234567890abcdef
        tenant_id = abcdef1234567890

    For Rackspace authentication:
        [rackspace_cloud]
        username = myusername
        api_key = 1234567890abcdef

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    region = _safe_region(region)
    identity.set_credential_file(cred_file, region=region)
    if authenticate:
        _auth_and_connect(region=region)


def keyring_auth(username=None, region=None, authenticate=True):
    """
    Use the password stored within the keyring to authenticate. If a username
    is supplied, that name is used; otherwise, the keyring_username value
    from the config file is used.

    If there is no username defined, or if the keyring module is not installed,
    or there is no password set for the given username, the appropriate errors
    will be raised.

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    if not keyring:
        # Module not installed
        raise exc.KeyringModuleNotInstalled("The 'keyring' Python module is "
                "not installed on this system.")
    if username is None:
        username = settings.get("keyring_username")
    if not username:
        raise exc.KeyringUsernameMissing("No username specified for keyring "
                "authentication.")
    password = keyring.get_password("pyrax", username)
    if password is None:
        raise exc.KeyringPasswordNotFound("No password was found for the "
                "username '%s'." % username)
    set_credentials(username, password, region=region,
            authenticate=authenticate)


def _auth_and_connect(region=None, connect=True):
    """
    Handles the call to authenticate, and if successful, connects to the
    various services.
    """
    global default_region
    identity.authenticated = False
    default_region = region or default_region
    try:
        identity.authenticate()
    except exc.AuthenticationFailed:
        clear_credentials()
        raise
    if connect:
        connect_to_services(region=region)


@_assure_identity
def authenticate(connect=True):
    """
    Generally you will not need to call this directly; passing in your
    credentials via set_credentials() and set_credential_file() will call
    authenticate() on the identity object by default. But for situations where
    you set your credentials manually or otherwise need finer control over
    the authentication sequence, this method will call the identity object's
    authenticate() method, and an AuthenticationFailed exception will be raised
    if your credentials have not been properly set first.

    Normally after successful authentication, connections to the various
    services will be made. However, passing False to the `connect` parameter
    will skip the service connection step.
    """
    _auth_and_connect(connect=connect)


def plug_hole_in_swiftclient_auth(clt, url):
    """
    This is necessary because swiftclient has an issue when a token expires and
    it needs to re-authenticate against Rackspace auth. It is a temporary
    workaround until we can fix swiftclient.
    """
    conn = clt.connection
    conn.token = identity.token
    conn.url = url


def clear_credentials():
    """De-authenticate by clearing all the names back to None."""
    global identity, regions, services, cloudservers, cloudfiles
    global cloud_loadbalancers, cloud_databases, cloud_blockstorage, cloud_dns
    global cloud_networks, cloud_monitoring, autoscale
    identity = None
    regions = tuple()
    services = tuple()
    cloudservers = None
    cloudfiles = None
    cloud_loadbalancers = None
    cloud_databases = None
    cloud_blockstorage = None
    cloud_dns = None
    cloud_networks = None
    cloud_monitoring = None
    autoscale = None


def _make_agent_name(base):
    """Appends pyrax information to the underlying library's user agent."""
    if base:
        if "pyrax" in base:
            return base
        else:
            return "%s %s" % (USER_AGENT, base)
    else:
        return USER_AGENT


def connect_to_services(region=None):
    """Establishes authenticated connections to the various cloud APIs."""
    global cloudservers, cloudfiles, cloud_loadbalancers, cloud_databases
    global cloud_blockstorage, cloud_dns, cloud_networks, cloud_monitoring
    global autoscale
    cloudservers = connect_to_cloudservers(region=region)
    cloudfiles = connect_to_cloudfiles(region=region)
    cloud_loadbalancers = connect_to_cloud_loadbalancers(region=region)
    cloud_databases = connect_to_cloud_databases(region=region)
    cloud_blockstorage = connect_to_cloud_blockstorage(region=region)
    cloud_dns = connect_to_cloud_dns(region=region)
    cloud_networks = connect_to_cloud_networks(region=region)
    cloud_monitoring = connect_to_cloud_monitoring(region=region)
    autoscale = connect_to_autoscale(region=region)


def _get_service_endpoint(svc, region=None, public=True):
    """
    Parses the services dict to get the proper endpoint for the given service.
    """
    region = _safe_region(region)
    url_type = {True: "public_url", False: "internal_url"}[public]
    ep = identity.services.get(svc, {}).get("endpoints", {}).get(
            region, {}).get(url_type)
    if not ep:
        # Try the "ALL" region, and substitute the actual region
        ep = identity.services.get(svc, {}).get("endpoints", {}).get(
                "ALL", {}).get(url_type)
    return ep


@_require_auth
def connect_to_cloudservers(region=None, **kwargs):
    """Creates a client for working with cloud servers."""
    _cs_auth_plugin.discover_auth_systems()
    id_type = get_setting("identity_type")
    if id_type != "keystone":
        auth_plugin = _cs_auth_plugin.load_plugin(id_type)
    else:
        auth_plugin = None
    region = _safe_region(region)
    mgt_url = _get_service_endpoint("compute", region)
    cloudservers = None
    if not mgt_url:
        # Service is not available
        return
    insecure = not get_setting("verify_ssl")
    cloudservers = _cs_client.Client(identity.username, identity.password,
            project_id=identity.tenant_id, auth_url=identity.auth_endpoint,
            auth_system=id_type, region_name=region, service_type="compute",
            auth_plugin=auth_plugin, insecure=insecure,
            http_log_debug=_http_debug, **kwargs)
    agt = cloudservers.client.USER_AGENT
    cloudservers.client.USER_AGENT = _make_agent_name(agt)
    cloudservers.client.management_url = mgt_url
    cloudservers.client.auth_token = identity.token
    cloudservers.exceptions = _cs_exceptions
    # Add some convenience methods
    cloudservers.list_images = cloudservers.images.list
    cloudservers.list_flavors = cloudservers.flavors.list
    cloudservers.list = cloudservers.servers.list

    def list_base_images():
        """
        Returns a list of all base images; excludes any images created
        by this account.
        """
        return [image for image in cloudservers.images.list()
                if not hasattr(image, "server")]

    def list_snapshots():
        """
        Returns a list of all images created by this account; in other words, it
        excludes all the base images.
        """
        return [image for image in cloudservers.images.list()
                if hasattr(image, "server")]

    cloudservers.list_base_images = list_base_images
    cloudservers.list_snapshots = list_snapshots
    return cloudservers


@_require_auth
def connect_to_cloudfiles(region=None, public=True):
    """
    Creates a client for working with cloud files. The default is to connect
    to the public URL; if you need to work with the ServiceNet connection, pass
    False to the 'public' parameter.
    """
    region = _safe_region(region)
    cf_url = _get_service_endpoint("object_store", region, public=public)
    cloudfiles = None
    if not cf_url:
        # Service is not available
        return
    cdn_url = _get_service_endpoint("object_cdn", region)
    ep_type = {True: "publicURL", False: "internalURL"}[public]
    opts = {"tenant_id": identity.tenant_name, "auth_token": identity.token,
            "endpoint_type": ep_type, "tenant_name": identity.tenant_name,
            "object_storage_url": cf_url, "object_cdn_url": cdn_url,
            "region_name": region}
    verify_ssl = get_setting("verify_ssl")
    cloudfiles = _cf.CFClient(identity.auth_endpoint, identity.username,
            identity.password, tenant_name=identity.tenant_name,
            preauthurl=cf_url, preauthtoken=identity.token, auth_version="2",
            os_options=opts, verify_ssl=verify_ssl, http_log_debug=_http_debug)
    cloudfiles.user_agent = _make_agent_name(cloudfiles.user_agent)
    return cloudfiles


@_require_auth
def _create_client(ep_name, service_type, region):
    region = _safe_region(region)
    ep = _get_service_endpoint(ep_name.split(":")[0], region)
    if not ep:
        return
    verify_ssl = get_setting("verify_ssl")
    cls = _client_classes[ep_name]
    client = cls(region_name=region, management_url=ep, verify_ssl=verify_ssl,
            http_log_debug=_http_debug, service_type=service_type)
    client.user_agent = _make_agent_name(client.user_agent)
    return client


def connect_to_cloud_databases(region=None):
    """Creates a client for working with cloud databases."""
    return _create_client(ep_name="database", service_type="rax:database",
            region=region)


def connect_to_cloud_loadbalancers(region=None):
    """Creates a client for working with cloud loadbalancers."""
    return _create_client(ep_name="load_balancer",
            service_type="rax:load-balancer", region=region)


def connect_to_cloud_blockstorage(region=None):
    """Creates a client for working with cloud blockstorage."""
    return _create_client(ep_name="volume", service_type="volume",
            region=region)


def connect_to_cloud_dns(region=None):
    """Creates a client for working with cloud dns."""
    return _create_client(ep_name="dns", service_type="rax:dns", region=region)


def connect_to_cloud_networks(region=None):
    """Creates a client for working with cloud networks."""
    return _create_client(ep_name="compute:network", service_type="compute",
            region=region)


def connect_to_cloud_monitoring(region=None):
    """Creates a client for working with cloud monitoring."""
    return _create_client(ep_name="monitor", service_type="monitor",
            region=region)


def connect_to_autoscale(region=None):
    """Creates a client for working with AutoScale."""
    return _create_client(ep_name="autoscale",
            service_type="autoscale", region=region)


def get_http_debug():
    return _http_debug


@_assure_identity
def set_http_debug(val):
    global _http_debug
    _http_debug = val
    # Set debug on the various services
    identity.http_log_debug = val
    for svc in (cloudservers, cloudfiles, cloud_loadbalancers,
            cloud_blockstorage, cloud_databases, cloud_dns, cloud_networks,
            autoscale):
        if svc is not None:
            svc.http_log_debug = val
    if not val:
        # Need to manually remove the debug handler for swiftclient
        swift_logger = _cf._swift_client.logger
        for handler in swift_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                swift_logger.removeHandler(handler)


def get_encoding():
    """Returns the unicode encoding type."""
    return settings.get("encoding") or default_encoding


# Read in the configuration file, if any
settings = Settings()
config_file = os.path.expanduser("~/.pyrax.cfg")
if os.path.exists(config_file):
    settings.read_config(config_file)
    debug = get_setting("http_debug") or False
    set_http_debug(debug)
