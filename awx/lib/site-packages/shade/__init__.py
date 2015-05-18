# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import logging
import operator
import os
import time

from cinderclient.v1 import client as cinder_client
from dogpile import cache
import glanceclient
import glanceclient.exc
from ironicclient import client as ironic_client
from ironicclient import exceptions as ironic_exceptions
from keystoneclient import auth as ksc_auth
from keystoneclient import session as ksc_session
from keystoneclient import client as keystone_client
from novaclient import client as nova_client
from novaclient import exceptions as nova_exceptions
from neutronclient.v2_0 import client as neutron_client
import os_client_config
import pbr.version
import swiftclient.client as swift_client
import swiftclient.exceptions as swift_exceptions
import troveclient.client as trove_client

# Disable the Rackspace warnings about deprecated certificates. We are aware
import warnings
warnings.filterwarnings('ignore', 'Certificate has no `subjectAltName`')

from shade import meta
from shade import task_manager
from shade import _tasks

__version__ = pbr.version.VersionInfo('shade').version_string()
OBJECT_MD5_KEY = 'x-object-meta-x-shade-md5'
OBJECT_SHA256_KEY = 'x-object-meta-x-shade-sha256'
IMAGE_MD5_KEY = 'owner_specified.shade.md5'
IMAGE_SHA256_KEY = 'owner_specified.shade.sha256'


OBJECT_CONTAINER_ACLS = {
    'public': ".r:*,.rlistings",
    'private': '',
}


class OpenStackCloudException(Exception):
    def __init__(self, message, extra_data=None):
        self.message = message
        self.extra_data = extra_data

    def __str__(self):
        return "%s (Extra: %s)" % (self.message, self.extra_data)


class OpenStackCloudTimeout(OpenStackCloudException):
    pass


def openstack_clouds(config=None, debug=False):
    if not config:
        config = os_client_config.OpenStackConfig()
    return [
        OpenStackCloud(
            cloud=f.name, debug=debug,
            cache_interval=config.get_cache_max_age(),
            cache_class=config.get_cache_class(),
            cache_arguments=config.get_cache_arguments(),
            **f.config)
        for f in config.get_all_clouds()
    ]


def openstack_cloud(debug=False, **kwargs):
    config = os_client_config.OpenStackConfig()
    cloud_config = config.get_one_cloud(**kwargs)
    return OpenStackCloud(
        cloud=cloud_config.name,
        cache_interval=config.get_cache_max_age(),
        cache_class=config.get_cache_class(),
        cache_arguments=config.get_cache_arguments(),
        debug=debug, **cloud_config.config)


def operator_cloud(debug=False, **kwargs):
    config = os_client_config.OpenStackConfig()
    cloud_config = config.get_one_cloud(**kwargs)
    return OperatorCloud(
        cloud_config.name, debug=debug,
        cache_interval=config.get_cache_max_age(),
        cache_class=config.get_cache_class(),
        cache_arguments=config.get_cache_arguments(),
        **cloud_config.config)


def _ssl_args(verify, cacert, cert, key):
    if cacert:
        if not os.path.exists(cacert):
            raise OpenStackCloudException(
                "CA Cert {0} does not exist".format(cacert))
        verify = cacert

    if cert:
        if not os.path.exists(cert):
            raise OpenStackCloudException(
                "Client Cert {0} does not exist".format(cert))
        if key:
            if not os.path.exists(key):
                raise OpenStackCloudException(
                    "Client key {0} does not exist".format(key))
            cert = (cert, key)
    return (verify, cert)


def _get_service_values(kwargs, service_key):
    return {k[:-(len(service_key) + 1)]: kwargs[k]
            for k in kwargs.keys() if k.endswith(service_key)}


def _iterate_timeout(timeout, message):
    """Iterate and raise an exception on timeout.

    This is a generator that will continually yield and sleep for 2
    seconds, and if the timeout is reached, will raise an exception
    with <message>.

    """

    start = time.time()
    count = 0
    while (timeout is None) or (time.time() < start + timeout):
        count += 1
        yield count
        time.sleep(2)
    raise OpenStackCloudTimeout(message)


class OpenStackCloud(object):
    """Represent a connection to an OpenStack Cloud.

    OpenStackCloud is the entry point for all cloud operations, regardless
    of which OpenStack service those operations may ultimately come from.
    The operations on an OpenStackCloud are resource oriented rather than
    REST API operation oriented. For instance, one will request a Floating IP
    and that Floating IP will be actualized either via neutron or via nova
    depending on how this particular cloud has decided to arrange itself.

    :param string name: The name of the cloud
    :param dict auth: Dictionary containing authentication information.
                      Depending on the value of auth_plugin, the contents
                      of this dict can vary wildly.
    :param string region_name: The region of the cloud that all operations
                               should be performed against.
                               (optional, default '')
    :param string auth_plugin: The name of the keystone auth_plugin to be used
    :param string endpoint_type: The type of endpoint to get for services
                                 from the service catalog. Valid types are
                                 `public` ,`internal` or `admin`. (optional,
                                 defaults to `public`)
    :param bool private: Whether to return or use private IPs by default for
                         servers. (optional, defaults to False)
    :param float api_timeout: A timeout to pass to REST client constructors
                              indicating network-level timeouts. (optional)
    :param bool verify: The verification arguments to pass to requests. True
                        tells requests to verify SSL requests, False to not
                        verify. (optional, defaults to True)
    :param string cacert: A path to a CA Cert bundle that can be used as part
                          of verifying SSL requests. If this is set, verify
                          is set to True. (optional)
    :param string cert: A path to a client certificate to pass to requests.
                        (optional)
    :param string key: A path to a client key to pass to requests. (optional)
    :param bool debug: Enable or disable debug logging (optional, defaults to
                       False)
    :param int cache_interval: How long to cache items fetched from the cloud.
                               Value will be passed to dogpile.cache. None
                               means do not cache at all.
                               (optional, defaults to None)
    :param string cache_class: What dogpile.cache cache class to use.
                               (optional, defaults to "dogpile.cache.null")
    :param dict cache_arguments: Additional arguments to pass to the cache
                                 constructor (optional, defaults to None)
    :param TaskManager manager: Optional task manager to use for running
                                OpenStack API tasks. Unless you're doing
                                rate limiting client side, you almost
                                certainly don't need this. (optional)
    """

    def __init__(self, cloud, auth,
                 region_name='',
                 auth_plugin='password',
                 endpoint_type='public',
                 private=False,
                 verify=True, cacert=None, cert=None, key=None,
                 api_timeout=None,
                 debug=False, cache_interval=None,
                 cache_class='dogpile.cache.null',
                 cache_arguments=None,
                 manager=None,
                 **kwargs):

        self.name = cloud
        self.auth = auth
        self.region_name = region_name
        self.auth_plugin = auth_plugin
        self.endpoint_type = endpoint_type
        self.private = private
        self.api_timeout = api_timeout
        if manager is not None:
            self.manager = manager
        else:
            self.manager = task_manager.TaskManager(
                name=self.name, client=self)

        self.service_types = _get_service_values(kwargs, 'service_type')
        self.service_names = _get_service_values(kwargs, 'service_name')
        self.endpoints = _get_service_values(kwargs, 'endpoint')
        self.api_versions = _get_service_values(kwargs, 'api_version')

        (self.verify, self.cert) = _ssl_args(verify, cacert, cert, key)

        self._cache = cache.make_region(
            function_key_generator=self._make_cache_key
        ).configure(
            cache_class, expiration_time=cache_interval,
            arguments=cache_arguments)
        self._container_cache = dict()
        self._file_hash_cache = dict()

        self._keystone_session = None
        self._auth_token = None

        self._cinder_client = None
        self._glance_client = None
        self._glance_endpoint = None
        self._ironic_client = None
        self._keystone_client = None
        self._neutron_client = None
        self._nova_client = None
        self._swift_client = None
        self._trove_client = None

        self.log = logging.getLogger('shade')
        log_level = logging.INFO
        if debug:
            log_level = logging.DEBUG
        self.log.setLevel(log_level)
        self.log.addHandler(logging.StreamHandler())

    def _make_cache_key(self, namespace, fn):
        fname = fn.__name__
        if namespace is None:
            name_key = self.name
        else:
            name_key = '%s:%s' % (self.name, namespace)

        def generate_key(*args, **kwargs):
            arg_key = ','.join(args)
            kwargs_keys = kwargs.keys()
            kwargs_keys.sort()
            kwargs_key = ','.join(
                ['%s:%s' % (k, kwargs[k]) for k in kwargs_keys])
            return "_".join(
                [name_key, fname, arg_key, kwargs_key])
        return generate_key

    def get_service_type(self, service):
        return self.service_types.get(service, service)

    def get_service_name(self, service):
        return self.service_names.get(service, None)

    def _get_nova_api_version(self):
        return self.api_versions['compute']

    @property
    def nova_client(self):
        if self._nova_client is None:

            # Make the connection
            try:
                self._nova_client = nova_client.Client(
                    self._get_nova_api_version(),
                    session=self.keystone_session,
                    service_name=self.get_service_name('compute'),
                    region_name=self.region_name,
                    timeout=self.api_timeout)
            except Exception:
                self.log.debug("Couldn't construct nova object", exc_info=True)
                raise

            if self._nova_client is None:
                raise OpenStackCloudException(
                    "Failed to instantiate nova client."
                    " This could mean that your credentials are wrong.")

        return self._nova_client

    @property
    def keystone_session(self):
        if self._keystone_session is None:
            # keystoneclient does crazy things with logging that are
            # none of them interesting
            keystone_logging = logging.getLogger('keystoneclient')
            keystone_logging.addHandler(logging.NullHandler())

            try:
                auth_plugin = ksc_auth.get_plugin_class(self.auth_plugin)
            except Exception as e:
                self.log.debug("keystone auth plugin failure", exc_info=True)
                raise OpenStackCloudException(
                    "Could not find auth plugin: {plugin}".format(
                    plugin=self.auth_plugin))
            try:
                keystone_auth = auth_plugin(**self.auth)
            except Exception as e:
                self.log.debug(
                    "keystone couldn't construct plugin", exc_info=True)
                raise OpenStackCloudException(
                    "Error constructing auth plugin: {plugin}".format(
                        plugin=self.auth_plugin))

            try:
                self._keystone_session = ksc_session.Session(
                    auth=keystone_auth,
                    verify=self.verify,
                    cert=self.cert)
            except Exception as e:
                self.log.debug("keystone unknown issue", exc_info=True)
                raise OpenStackCloudException(
                    "Error authenticating to the keystone: %s " % e.message)
        return self._keystone_session

    @property
    def keystone_client(self):
        if self._keystone_client is None:
            try:
                self._keystone_client = keystone_client.Client(
                    session=self.keystone_session,
                    auth_url=self.keystone_session.get_endpoint(
                        interface=ksc_auth.AUTH_INTERFACE),
                    timeout=self.api_timeout)
            except Exception as e:
                self.log.debug(
                    "Couldn't construct keystone object", exc_info=True)
                raise OpenStackCloudException(
                    "Error constructing keystone client: %s" % e.message)
        return self._keystone_client

    @property
    def service_catalog(self):
        return self.keystone_session.auth.get_access(
            self.keystone_session).service_catalog.get_data()

    @property
    def auth_token(self):
        if not self._auth_token:
            self._auth_token = self.keystone_session.get_token()
        return self._auth_token

    @property
    def project_cache(self):
        @self._cache.cache_on_arguments()
        def _project_cache():
            return {project.id: project for project in
                    self._project_manager.list()}
        return _project_cache()

    @property
    def _project_manager(self):
        # Keystone v2 calls this attribute tenants
        # Keystone v3 calls it projects
        # Yay for usable APIs!
        return getattr(
            self.keystone_client, 'projects', self.keystone_client.tenants)

    def _get_project(self, name_or_id):
        """Retrieve a project by name or id."""

        # TODO(mordred): This, and other keystone operations, need to have
        #                domain information passed in. When there is no
        #                available domain information, we should default to
        #                the currently scoped domain which we can requset from
        #                the session.
        for id, project in self.project_cache.items():
            if name_or_id in (id, project.name):
                return project
        return None

    def get_project(self, name_or_id):
        """Retrieve a project by name or id."""
        project = self._get_project(name_or_id)
        if project:
            return meta.obj_to_dict(project)
        return None

    def update_project(self, name_or_id, description=None, enabled=True):
        try:
            project = self._get_project(name_or_id)
            return meta.obj_to_dict(
                project.update(description=description, enabled=enabled))
        except Exception as e:
            self.log.debug("keystone update project issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in updating project {project}: {message}".format(
                    project=name_or_id, message=e.message))

    def create_project(self, name, description=None, enabled=True):
        """Create a project."""
        try:
            self._project_manager.create(
                project_name=name, description=description, enabled=enabled)
        except Exception as e:
            self.log.debug("keystone create project issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in creating project {project}: {message}".format(
                    project=name, message=e.message))

    def delete_project(self, name_or_id):
        try:
            project = self._get_project(name_or_id)
            self._project_manager.delete(project.id)
        except Exception as e:
            self.log.debug("keystone delete project issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in deleting project {project}: {message}".format(
                    project=name_or_id, message=e.message))

    @property
    def user_cache(self):
        @self._cache.cache_on_arguments()
        def _user_cache():
            user_list = self.manager.submitTask(_tasks.UserListTask())
            return {user.id: user for user in user_list}
        return _user_cache()

    def _get_user(self, name_or_id):
        """Retrieve a user by name or id."""

        for id, user in self.user_cache.items():
            if name_or_id in (id, user.name):
                return user
        return None

    def get_user(self, name_or_id):
        """Retrieve a user by name or id."""
        user = self._get_user(name_or_id)
        if user:
            return meta.obj_to_dict(user)
        return None

    def update_user(self, name_or_id, email=None, enabled=True):
        try:
            user = self._get_user(name_or_id)
            return meta.obj_to_dict(
                user.update(email=email, enabled=enabled))
        except Exception as e:
            self.log.debug("keystone update user issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in updating user {user}: {message}".format(
                    user=name_or_id, message=e.message))

    def create_user(
            self, name, password=None, email=None, project=None,
            enabled=True):
        """Create a user."""
        try:
            if project:
                project_id = self._get_project(project).id
            else:
                project_id = None
            self.manager.submitTask(_tasks.UserCreate(
                user_name=name, password=password, email=email,
                project=project_id, enabled=enabled))
        except Exception as e:
            self.log.debug("keystone create user issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in creating user {user}: {message}".format(
                    user=name, message=e.message))

    def delete_user(self, name_or_id):
        try:
            user = self._get_user(name_or_id)
            self._user_manager.delete(user.id)
        except Exception as e:
            self.log.debug("keystone delete user issue", exc_info=True)
            raise OpenStackCloudException(
                "Error in deleting user {user}: {message}".format(
                    user=name_or_id, message=e.message))

    def _get_glance_api_version(self):
        if 'image' in self.api_versions:
            return self.api_versions['image']
        # Yay. We get to guess ...
        # Get rid of trailing '/' if present
        endpoint = self._get_glance_endpoint()
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        url_bits = endpoint.split('/')
        if url_bits[-1].startswith('v'):
            return url_bits[-1][1]
        return '1'  # Who knows? Let's just try 1 ...

    def _get_glance_endpoint(self):
        if self._glance_endpoint is None:
            self._glance_endpoint = self.get_endpoint(
                service_type=self.get_service_type('image'))
        return self._glance_endpoint

    @property
    def glance_client(self):
        if self._glance_client is None:
            token = self.auth_token
            endpoint = self._get_glance_endpoint()
            glance_api_version = self._get_glance_api_version()
            kwargs = dict()
            if self.api_timeout is not None:
                kwargs['timeout'] = self.api_timeout
            try:
                self._glance_client = glanceclient.Client(
                    glance_api_version, endpoint, token=token,
                    session=self.keystone_session,
                    **kwargs)
            except Exception as e:
                self.log.debug("glance unknown issue", exc_info=True)
                raise OpenStackCloudException(
                    "Error in connecting to glance: %s" % e.message)

            if not self._glance_client:
                raise OpenStackCloudException("Error connecting to glance")
        return self._glance_client

    @property
    def swift_client(self):
        if self._swift_client is None:
            token = self.auth_token
            endpoint = self.get_endpoint(
                service_type=self.get_service_type('object-store'))
            self._swift_client = swift_client.Connection(
                preauthurl=endpoint,
                preauthtoken=token,
                os_options=dict(region_name=self.region_name),
            )
        return self._swift_client

    @property
    def cinder_client(self):

        if self._cinder_client is None:
            # Make the connection
            self._cinder_client = cinder_client.Client(
                session=self.keystone_session,
                region_name=self.region_name,
                timeout=self.api_timeout)

            if self._cinder_client is None:
                raise OpenStackCloudException(
                    "Failed to instantiate cinder client."
                    " This could mean that your credentials are wrong.")

        return self._cinder_client

    def _get_trove_api_version(self, endpoint):
        if 'database' in self.api_versions:
            return self.api_versions['database']
        # Yay. We get to guess ...
        # Get rid of trailing '/' if present
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        url_bits = endpoint.split('/')
        for bit in url_bits:
            if bit.startswith('v'):
                return bit[1:]
        return '1.0'  # Who knows? Let's just try 1.0 ...

    @property
    def trove_client(self):
        if self._trove_client is None:
            endpoint = self.get_endpoint(
                service_type=self.get_service_type('database'))
            trove_api_version = self._get_trove_api_version(endpoint)
            # Make the connection - can't use keystone session until there
            # is one
            self._trove_client = trove_client.Client(
                trove_api_version,
                session=self.keystone_session,
                region_name=self.region_name,
                service_type=self.get_service_type('database'),
                timeout=self.api_timeout,
            )

            if self._trove_client is None:
                raise OpenStackCloudException(
                    "Failed to instantiate Trove client."
                    " This could mean that your credentials are wrong.")

        return self._trove_client

    @property
    def neutron_client(self):
        if self._neutron_client is None:
            self._neutron_client = neutron_client.Client(
                token=self.auth_token,
                session=self.keystone_session,
                region_name=self.region_name,
                timeout=self.api_timeout)
        return self._neutron_client

    def get_name(self):
        return self.name

    def get_region(self):
        return self.region_name

    @property
    def flavor_cache(self):
        @self._cache.cache_on_arguments()
        def _flavor_cache(cloud):
            return {flavor.id: flavor for flavor in
                    self.manager.submitTask(_tasks.FlavorList())}
        return _flavor_cache(self.name)

    def get_flavor_name(self, flavor_id):
        flavor = self.flavor_cache.get(flavor_id, None)
        if flavor:
            return flavor.name
        return None

    def get_flavor(self, name_or_id):
        for id, flavor in self.flavor_cache.items():
            if name_or_id in (id, flavor.name):
                return flavor
        return None

    def get_flavor_by_ram(self, ram, include=None):
        for flavor in sorted(
                self.flavor_cache.values(),
                key=operator.attrgetter('ram')):
            if (flavor.ram >= ram and
                    (not include or include in flavor.name)):
                return flavor
        raise OpenStackCloudException(
            "Cloud not find a flavor with {ram} and '{include}'".format(
                ram=ram, include=include))

    def get_endpoint(self, service_type):
        if service_type in self.endpoints:
            return self.endpoints[service_type]
        try:
            endpoint = self.keystone_session.get_endpoint(
                service_type=service_type,
                interface=self.endpoint_type,
                region_name=self.region_name)
        except Exception as e:
            self.log.debug("keystone cannot get endpoint", exc_info=True)
            raise OpenStackCloudException(
                "Error getting %s endpoint: %s" % (service_type, e.message))
        return endpoint

    def list_servers(self):
        return self.manager.submitTask(_tasks.ServerList())

    def list_server_dicts(self):
        return [self.get_openstack_vars(server)
                for server in self.list_servers()]

    def list_keypairs(self):
        return self.manager.submitTask(_tasks.KeypairList())

    def list_keypair_dicts(self):
        return [meta.obj_to_dict(keypair)
                for keypair in self.list_keypairs()]

    def create_keypair(self, name, public_key):
        return self.manager.submitTask(_tasks.KeypairCreate(
            name=name, public_key=public_key))

    def delete_keypair(self, name):
        return self.manager.submitTask(_tasks.KeypairDelete(key=name))

    @property
    def extension_cache(self):
        if not self._extension_cache:
            self._extension_cache = set()

            try:
                resp, body = self.manager.submitTask(
                    _tasks.NovaUrlGet(url='/extensions'))
                if resp.status_code == 200:
                    for x in body['extensions']:
                        self._extension_cache.add(x['alias'])
            except nova_exceptions.NotFound:
                pass
        return self._extension_cache

    def has_extension(self, extension_name):
        return extension_name in self.extension_cache

    def list_networks(self):
        return self.manager.submitTask(_tasks.NetworkList())['networks']

    def get_network(self, name_or_id):
        for network in self.list_networks():
            if name_or_id in (network['id'], network['name']):
                return network
        return None

    def list_routers(self):
        return self.manager.submitTask(_tasks.RouterList())['routers']

    def get_router(self, name_or_id):
        for router in self.list_routers():
            if name_or_id in (router['id'], router['name']):
                return router
        return None

    # TODO(Shrews): This will eventually need to support tenant ID and
    # provider networks, which are admin-level params.
    def create_network(self, name, shared=False, admin_state_up=True):
        """Create a network.

        :param name: Name of the network being created.
        :param shared: Set the network as shared.
        :param admin_state_up: Set the network administrative state to up.

        :returns: The network object.
        :raises: OpenStackCloudException on operation error.
        """

        network = {
            'name': name,
            'shared': shared,
            'admin_state_up': admin_state_up
        }

        try:
            net = self.manager.submitTask(
                _tasks.NetworkCreate(body=dict({'network': network})))
        except Exception as e:
            self.log.debug("Network creation failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in creating network %s: %s" % (name, e.message))
        # Turns out neutron returns an actual dict, so no need for the
        # use of meta.obj_to_dict() here (which would not work against
        # a dict).
        return net['network']

    def delete_network(self, name_or_id):
        """Delete a network.

        :param name_or_id: Name or ID of the network being deleted.
        :raises: OpenStackCloudException on operation error.
        """
        network = self.get_network(name_or_id)
        try:
            self.manager.submitTask(
                _tasks.NetworkDelete(network=network['id']))
        except Exception as e:
            self.log.debug("Network deletion failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in deleting network %s: %s" % (name_or_id, e.message))

    def create_router(self, name=None, admin_state_up=True):
        """Create a logical router.

        :param name: The router name.
        :param admin_state_up: The administrative state of the router.

        :returns: The router object.
        :raises: OpenStackCloudException on operation error.
        """
        router = {
            'admin_state_up': admin_state_up
        }
        if name:
            router['name'] = name

        try:
            new_router = self.manager.submitTask(
                _tasks.RouterCreate(body=dict(router=router)))
        except Exception as e:
            self.log.debug("Router create failed", exc_info=True)
            raise OpenStackCloudException(
                "Error creating router %s: %s" % (name, e))
        # Turns out neutron returns an actual dict, so no need for the
        # use of meta.obj_to_dict() here (which would not work against
        # a dict).
        return new_router['router']

    def update_router(self, router_id, name=None, admin_state_up=None,
                      ext_gateway_net_id=None):
        """Update an existing logical router.

        :param router_id: The router UUID.
        :param name: The router name.
        :param admin_state_up: The administrative state of the router.
        :param ext_gateway_net_id: The network ID for the external gateway.

        :returns: The router object.
        :raises: OpenStackCloudException on operation error.
        """
        router = {}
        if name:
            router['name'] = name
        if admin_state_up:
            router['admin_state_up'] = admin_state_up
        if ext_gateway_net_id:
            router['external_gateway_info'] = {
                'network_id': ext_gateway_net_id
            }

        if not router:
            self.log.debug("No router data to update")
            return

        try:
            new_router = self.manager.submitTask(
                _tasks.RouterUpdate(
                    router=router_id, body=dict(router=router)))
        except Exception as e:
            self.log.debug("Router update failed", exc_info=True)
            raise OpenStackCloudException(
                "Error updating router %s: %s" % (name, e))
        # Turns out neutron returns an actual dict, so no need for the
        # use of meta.obj_to_dict() here (which would not work against
        # a dict).
        return new_router['router']

    def delete_router(self, name_or_id):
        """Delete a logical router.

        If a name, instead of a unique UUID, is supplied, it is possible
        that we could find more than one matching router since names are
        not required to be unique. An error will be raised in this case.

        :param name_or_id: Name or ID of the router being deleted.
        :raises: OpenStackCloudException on operation error.
        """
        routers = []
        for router in self.list_routers():
            if name_or_id in (router['id'], router['name']):
                routers.append(router)

        if not routers:
            raise OpenStackCloudException(
                "Router %s not found." % name_or_id)

        if len(routers) > 1:
            raise OpenStackCloudException(
                "More than one router named %s. Use ID." % name_or_id)

        try:
            self.manager.submitTask(
                _tasks.RouterDelete(router=routers[0]['id']))
        except Exception as e:
            self.log.debug("Router delete failed", exc_info=True)
            raise OpenStackCloudException(
                "Error deleting router %s: %s" % (name_or_id, e))

    def _get_images_from_cloud(self, filter_deleted):
        # First, try to actually get images from glance, it's more efficient
        images = dict()
        try:
            # If the cloud does not expose the glance API publically
            image_list = self.manager.submitTask(_tasks.GlanceImageList())
        except (OpenStackCloudException,
                glanceclient.exc.HTTPInternalServerError):
            # We didn't have glance, let's try nova
            # If this doesn't work - we just let the exception propagate
            image_list = self.manager.submitTask(_tasks.NovaImageList())
        for image in image_list:
            # The cloud might return DELETED for invalid images.
            # While that's cute and all, that's an implementation detail.
            if not filter_deleted:
                images[image.id] = image
            elif image.status != 'DELETED':
                images[image.id] = image
        return images

    def _reset_image_cache(self):
        self._image_cache = None

    def list_images(self, filter_deleted=True):
        """Get available glance images.

        :param filter_deleted: Control whether deleted images are returned.
        :returns: A dictionary of glance images indexed by image UUID.
        """
        @self._cache.cache_on_arguments()
        def _list_images():
            return self._get_images_from_cloud(filter_deleted)
        return _list_images()

    def get_image_name(self, image_id, exclude=None):
        image = self.get_image(image_id, exclude)
        if image:
            return image.id
        return None

    def get_image_id(self, image_name, exclude=None):
        image = self.get_image(image_name, exclude)
        if image:
            return image.id
        return None

    def get_image(self, name_or_id, exclude=None):
        for (image_id, image) in self.list_images().items():
            if image_id == name_or_id:
                return image
            if (image is not None and
                    name_or_id == image.name and (
                    not exclude or exclude not in image.name)):
                return image
        return None

    def get_image_dict(self, name_or_id, exclude=None):
        image = self.get_image(name_or_id, exclude)
        if not image:
            return image
        if getattr(image, 'validate', None):
            # glanceclient returns a "warlock" object if you use v2
            return meta.warlock_to_dict(image)
        else:
            # glanceclient returns a normal object if you use v1
            return meta.obj_to_dict(image)

    def create_image_snapshot(self, name, **metadata):
        image = self.manager.submitTask(_tasks.ImageSnapshotCreate(
            name=name, **metadata))
        if image:
            return meta.obj_to_dict(image)
        return None

    def delete_image(self, name_or_id, wait=False, timeout=3600):
        image = self.get_image(name_or_id)
        try:
            # Note that in v1, the param name is image, but in v2,
            # it's image_id
            glance_api_version = self._get_glance_api_version()
            if glance_api_version == '2':
                self.manager.submitTask(
                    _tasks.ImageDelete(image_id=image.id))
            elif glance_api_version == '1':
                self.manager.submitTask(
                    _tasks.ImageDelete(image=image.id))
        except Exception as e:
            self.log.debug("Image deletion failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in deleting image: %s" % e.message)

        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for the image to be deleted."):
                self._cache.invalidate()
                if self.get_image(image.id) is None:
                    return

    def create_image(
            self, name, filename, container='images',
            md5=None, sha256=None,
            disk_format=None, container_format=None,
            wait=False, timeout=3600, **kwargs):
        if not md5 or not sha256:
            (md5, sha256) = self._get_file_hashes(filename)
        current_image = self.get_image_dict(name)
        if (current_image and current_image.get(IMAGE_MD5_KEY, '') == md5
                and current_image.get(IMAGE_SHA256_KEY, '') == sha256):
            self.log.debug(
                "image {name} exists and is up to date".format(name=name))
            return current_image
        kwargs[IMAGE_MD5_KEY] = md5
        kwargs[IMAGE_SHA256_KEY] = sha256
        # This makes me want to die inside
        glance_api_version = self._get_glance_api_version()
        if glance_api_version == '2':
            return self._upload_image_v2(
                name, filename, container,
                current_image=current_image,
                wait=wait, timeout=timeout, **kwargs)
        elif glance_api_version == '1':
            image_kwargs = dict(properties=kwargs)
            if disk_format:
                image_kwargs['disk_format'] = disk_format
            if container_format:
                image_kwargs['container_format'] = container_format

            return self._upload_image_v1(name, filename, **image_kwargs)

    def _upload_image_v1(self, name, filename, **image_kwargs):
        image = self.manager.submitTask(_tasks.ImageCreate(
            name=name, **image_kwargs))
        self.manager.submitTask(_tasks.ImageUpdate(
            image=image, data=open(filename, 'rb')))
        self._cache.invalidate()
        return self.get_image_dict(image.id)

    def _upload_image_v2(
            self, name, filename, container, current_image=None,
            wait=True, timeout=None, **image_properties):
        self.create_object(
            container, name, filename,
            md5=image_properties.get('md5', None),
            sha256=image_properties.get('sha256', None))
        if not current_image:
            current_image = self.get_image(name)
        # TODO(mordred): Can we do something similar to what nodepool does
        # using glance properties to not delete then upload but instead make a
        # new "good" image and then mark the old one as "bad"
        # self.glance_client.images.delete(current_image)
        glance_task = self.manager.submitTask(_tasks.ImageTaskCreate(
            type='import', input=dict(
                import_from='{container}/{name}'.format(
                    container=container, name=name),
                image_properties=dict(name=name))))
        if wait:
            image_id = None
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for the image to import."):
                try:
                    if image_id is None:
                        status = self.manager.submitTask(
                            _tasks.ImageTaskGet(task_id=glance_task.id))
                except glanceclient.exc.HTTPServiceUnavailable:
                    # Intermittent failure - catch and try again
                    continue

                if status.status == 'success':
                    image_id = status.result['image_id']
                    self._reset_image_cache()
                    try:
                        image = self.get_image(image_id)
                    except glanceclient.exc.HTTPServiceUnavailable:
                        # Intermittent failure - catch and try again
                        continue
                    if image is None:
                        continue
                    self.update_image_properties(
                        image=image,
                        **image_properties)
                    return self.get_image_dict(status.result['image_id'])
                if status.status == 'failure':
                    raise OpenStackCloudException(
                        "Image creation failed: {message}".format(
                            message=status.message),
                        extra_data=status)
        else:
            return meta.warlock_to_dict(glance_task)

    def update_image_properties(
            self, image=None, name_or_id=None, **properties):
        if image is None:
            image = self.get_image(name_or_id)

        img_props = {}
        for k, v in properties.iteritems():
            if v and k in ['ramdisk', 'kernel']:
                v = self.get_image_id(v)
                k = '{0}_id'.format(k)
            img_props[k] = v

        # This makes me want to die inside
        if self._get_glance_api_version() == '2':
            return self._update_image_properties_v2(image, img_props)
        else:
            return self._update_image_properties_v1(image, img_props)

    def _update_image_properties_v2(self, image, properties):
        img_props = {}
        for k, v in properties.iteritems():
            if image.get(k, None) != v:
                img_props[k] = str(v)
        if not img_props:
            return False
        self.manager.submitTask(_tasks.ImageUpdate(
            image_id=image.id, **img_props))
        return True

    def _update_image_properties_v1(self, image, properties):
        img_props = {}
        for k, v in properties.iteritems():
            if image.properties.get(k, None) != v:
                img_props[k] = v
        if not img_props:
            return False
        self.manager.submitTask(_tasks.ImageUpdate(
            image=image, properties=img_props))
        return True

    def create_volume(self, wait=True, timeout=None, **kwargs):
        """Create a volume.

        :param wait: If true, waits for volume to be created.
        :param timeout: Seconds to wait for volume creation. None is forever.
        :param volkwargs: Keyword arguments as expected for cinder client.

        :returns: The created volume object.

        :raises: OpenStackCloudTimeout if wait time exceeded.
        :raises: OpenStackCloudException on operation error.
        """

        try:
            volume = self.manager.submitTask(_tasks.VolumeCreate(**kwargs))
        except Exception as e:
            self.log.debug("Volume creation failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in creating volume: %s" % e.message)

        if volume.status == 'error':
            raise OpenStackCloudException("Error in creating volume")

        if wait:
            vol_id = volume.id
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for the volume to be available."):
                volume = self.get_volume(vol_id, cache=False, error=False)

                if not volume:
                    continue

                if volume.status == 'available':
                    return volume

                if volume.status == 'error':
                    raise OpenStackCloudException(
                        "Error in creating volume, please check logs")

    def delete_volume(self, name_or_id=None, wait=True, timeout=None):
        """Delete a volume.

        :param name_or_id: Name or unique ID of the volume.
        :param wait: If true, waits for volume to be deleted.
        :param timeout: Seconds to wait for volume deletion. None is forever.

        :raises: OpenStackCloudTimeout if wait time exceeded.
        :raises: OpenStackCloudException on operation error.
        """

        volume = self.get_volume(name_or_id, cache=False)

        try:
            volume = self.manager.submitTask(
                _tasks.VolumeDelete(volume=volume.id))
        except Exception as e:
            self.log.debug("Volume deletion failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in deleting volume: %s" % e.message)

        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for the volume to be deleted."):
                if not self.volume_exists(volume.id):
                    return

    def _get_volumes_from_cloud(self):
        try:
            return self.manager.submitTask(_tasks.VolumeList())
        except Exception:
            return []

    def list_volumes(self, cache=True):
        @self._cache.cache_on_arguments()
        def _list_volumes():
            return self._get_volumes_from_cloud()
        return _list_volumes()

    def get_volumes(self, server, cache=True):
        volumes = []
        for volume in self.list_volumes(cache=cache):
            for attach in volume.attachments:
                if attach['server_id'] == server.id:
                    volumes.append(volume)
        return volumes

    def get_volume_id(self, name_or_id):
        image = self.get_volume(name_or_id)
        if image:
            return image.id
        return None

    def get_volume(self, name_or_id, cache=True, error=True):
        for v in self.list_volumes(cache=cache):
            if name_or_id in (v.display_name, v.id):
                return v
        if error:
            raise OpenStackCloudException(
                "Error finding volume from %s" % name_or_id)
        return None

    def volume_exists(self, name_or_id):
        return self.get_volume(
            name_or_id, cache=False, error=False) is not None

    def get_volume_attach_device(self, volume, server_id):
        """Return the device name a volume is attached to for a server.

        This can also be used to verify if a volume is attached to
        a particular server.

        :param volume: Volume object
        :param server_id: ID of server to check

        :returns: Device name if attached, None if volume is not attached.
        """
        for attach in volume.attachments:
            if server_id == attach['server_id']:
                return attach['device']
        return None

    def detach_volume(self, server, volume, wait=True, timeout=None):
        """Detach a volume from a server.

        :param server: The server object to detach from.
        :param volume: The volume object to detach.
        :param wait: If true, waits for volume to be detached.
        :param timeout: Seconds to wait for volume detachment. None is forever.

        :raises: OpenStackCloudTimeout if wait time exceeded.
        :raises: OpenStackCloudException on operation error.
        """
        dev = self.get_volume_attach_device(volume, server.id)
        if not dev:
            raise OpenStackCloudException(
                "Volume %s is not attached to server %s"
                % (volume.id, server.id)
            )

        try:
            self.manager.submitTask(
                _tasks.VolumeDetach(volume_id=volume, server_id=server.id))
        except Exception as e:
            self.log.debug("nova volume detach failed", exc_info=True)
            raise OpenStackCloudException(
                "Error detaching volume %s from server %s: %s" %
                (volume.id, server.id, e)
            )

        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for volume %s to detach." % volume.id):
                try:
                    vol = self.get_volume(volume.id, cache=False)
                except Exception:
                    self.log.debug(
                        "Error getting volume info %s" % volume.id,
                        exc_info=True)
                    continue

                if vol.status == 'available':
                    return

                if vol.status == 'error':
                    raise OpenStackCloudException(
                        "Error in detaching volume %s" % volume.id
                    )

    def attach_volume(self, server, volume, device=None,
                      wait=True, timeout=None):
        """Attach a volume to a server.

        This will attach a volume, described by the passed in volume
        object (as returned by get_volume()), to the server described by
        the passed in server object (as returned by get_server()) on the
        named device on the server.

        If the volume is already attached to the server, or generally not
        available, then an exception is raised. To re-attach to a server,
        but under a different device, the user must detach it first.

        :param server: The server object to attach to.
        :param volume: The volume object to attach.
        :param device: The device name where the volume will attach.
        :param wait: If true, waits for volume to be attached.
        :param timeout: Seconds to wait for volume attachment. None is forever.

        :raises: OpenStackCloudTimeout if wait time exceeded.
        :raises: OpenStackCloudException on operation error.
        """
        dev = self.get_volume_attach_device(volume, server.id)
        if dev:
            raise OpenStackCloudException(
                "Volume %s already attached to server %s on device %s"
                % (volume.id, server.id, dev)
            )

        if volume.status != 'available':
            raise OpenStackCloudException(
                "Volume %s is not available. Status is '%s'"
                % (volume.id, volume.status)
            )

        try:
            self.manager.submitTask(
                _tasks.VolumeAttach(
                    volume_id=volume.id, server_id=server.id, device=device))
        except Exception as e:
            self.log.debug(
                "nova volume attach of %s failed" % volume.id, exc_info=True)
            raise OpenStackCloudException(
                "Error attaching volume %s to server %s: %s" %
                (volume.id, server.id, e)
            )

        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for volume %s to attach." % volume.id):
                try:
                    vol = self.get_volume(volume.id, cache=False)
                except Exception:
                    self.log.debug(
                        "Error getting volume info %s" % volume.id,
                        exc_info=True)
                    continue

                if self.get_volume_attach_device(vol, server.id):
                    return

                # TODO(Shrews) check to see if a volume can be in error status
                #              and also attached. If so, we should move this
                #              above the get_volume_attach_device call
                if vol.status == 'error':
                    raise OpenStackCloudException(
                        "Error in attaching volume %s" % volume.id
                    )

    def get_server_id(self, name_or_id):
        server = self.get_server(name_or_id)
        if server:
            return server.id
        return None

    def get_server_private_ip(self, server):
        return meta.get_server_private_ip(server)

    def get_server_public_ip(self, server):
        return meta.get_server_public_ip(server)

    def get_server(self, name_or_id):
        for server in self.list_servers():
            if name_or_id in (server.name, server.id):
                return server
        return None

    def get_server_dict(self, name_or_id):
        server = self.get_server(name_or_id)
        if not server:
            return server
        return self.get_openstack_vars(server)

    def get_server_meta(self, server):
        server_vars = meta.get_hostvars_from_server(self, server)
        groups = meta.get_groups_from_server(self, server, server_vars)
        return dict(server_vars=server_vars, groups=groups)

    def get_security_group(self, name_or_id):
        for secgroup in self.manager.submitTask(_tasks.SecurityGroupList()):
            if name_or_id in (secgroup.name, secgroup.id):
                return secgroup
        return None

    def get_openstack_vars(self, server):
        return meta.get_hostvars_from_server(self, server)

    def add_ip_from_pool(self, server, pools):

        # empty dict and list
        usable_floating_ips = {}

        # get the list of all floating IPs. Mileage may
        # vary according to Nova Compute configuration
        # per cloud provider
        all_floating_ips = self.manager.submitTask(_tasks.FloatingIPList())

        # iterate through all pools of IP address. Empty
        # string means all and is the default value
        for pool in pools:
            # temporary list per pool
            pool_ips = []
            # loop through all floating IPs
            for f_ip in all_floating_ips:
                # if not reserved and the correct pool, add
                if f_ip.instance_id is None and (f_ip.pool == pool):
                    pool_ips.append(f_ip.ip)
                    # only need one
                    break

            # if the list is empty, add for this pool
            if not pool_ips:
                try:
                    new_ip = self.manager.submitTask(
                        _tasks.FloatingIPCreate(pool=pool))
                except Exception:
                    self.log.debug(
                        "nova floating ip create failed", exc_info=True)
                    raise OpenStackCloudException(
                        "Unable to create floating ip in pool %s" % pool)
                pool_ips.append(new_ip.ip)
            # Add to the main list
            usable_floating_ips[pool] = pool_ips

        # finally, add ip(s) to instance for each pool
        for pool in usable_floating_ips:
            for ip in usable_floating_ips[pool]:
                self.add_ip_list(server, [ip])
                # We only need to assign one ip - but there is an inherent
                # race condition and some other cloud operation may have
                # stolen an available floating ip
                break

    def add_ip_list(self, server, ips):
        # add ip(s) to instance
        for ip in ips:
            try:
                self.manager.submitTask(
                    _tasks.FloatingIPAttach(server=server, address=ip))
            except Exception as e:
                self.log.debug(
                    "nova floating ip add failed", exc_info=True)
                raise OpenStackCloudException(
                    "Error attaching IP {ip} to instance {id}: {msg} ".format(
                        ip=ip, id=server.id, msg=e.message))

    def add_auto_ip(self, server):
        try:
            new_ip = self.manager.submitTask(_tasks.FloatingIPCreate())
        except Exception as e:
            self.log.debug(
                "nova floating ip create failed", exc_info=True)
            raise OpenStackCloudException(
                "Unable to create floating ip: %s" % (e.message))
        try:
            self.add_ip_list(server, [new_ip])
        except OpenStackCloudException:
            # Clean up - we auto-created this ip, and it's not attached
            # to the server, so the cloud will not know what to do with it
            self.manager.submitTask(
                _tasks.FloatingIPDelete(floating_ip=new_ip))
            raise

    def add_ips_to_server(self, server, auto_ip=True, ips=None, ip_pool=None):
        if ip_pool:
            self.add_ip_from_pool(server, ip_pool)
        elif ips:
            self.add_ip_list(server, ips)
        elif auto_ip:
            if self.get_server_public_ip(server):
                return server
            self.add_auto_ip(server)
        else:
            return server

        # this may look redundant, but if there is now a
        # floating IP, then it needs to be obtained from
        # a recent server object if the above code path exec'd
        try:
            server = self.manager.submitTask(_tasks.ServerGet(server=server))
        except Exception as e:
            self.log.debug("nova info failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in getting info from instance: %s " % e.message)
        return server

    def create_server(self, auto_ip=True, ips=None, ip_pool=None,
                      root_volume=None, terminate_volume=False,
                      wait=False, timeout=180, **bootkwargs):

        if root_volume:
            if terminate_volume:
                suffix = ':::1'
            else:
                suffix = ':::0'
            volume_id = self.get_volume_id(root_volume) + suffix
            if 'block_device_mapping' not in bootkwargs:
                bootkwargs['block_device_mapping'] = dict()
            bootkwargs['block_device_mapping']['vda'] = volume_id

        try:
            server = self.manager.submitTask(_tasks.ServerCreate(**bootkwargs))
            server = self.manager.submitTask(_tasks.ServerGet(server=server))
        except Exception as e:
            self.log.debug("nova instance create failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in creating instance: %s" % e.message)
        if server.status == 'ERROR':
            raise OpenStackCloudException(
                "Error in creating the server.")
        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for the server to come up."):
                try:
                    server = self.manager.submitTask(
                        _tasks.ServerGet(server=server))
                except Exception:
                    continue

                if server.status == 'ACTIVE':
                    return self.add_ips_to_server(
                        server, auto_ip, ips, ip_pool)

                if server.status == 'ERROR':
                    raise OpenStackCloudException(
                        "Error in creating the server",
                        extra_data=dict(
                            server=meta.obj_to_dict(server)))
        return server

    def rebuild_server(self, server_id, image_id, wait=False, timeout=180):
        try:
            server = self.manager.submitTask(_tasks.ServerRebuild(
                server=server_id, image=image_id))
        except Exception as e:
            self.log.debug("nova instance rebuild failed", exc_info=True)
            raise OpenStackCloudException(
                "Error in rebuilding instance: {0}".format(e))
        if wait:
            for count in _iterate_timeout(
                    timeout,
                    "Timeout waiting for server {0} to "
                    "rebuild.".format(server_id)):
                try:
                    server = self.manager.submitTask(
                        _tasks.ServerGet(server=server))
                except Exception:
                    continue

                if server.status == 'ACTIVE':
                    break

                if server.status == 'ERROR':
                    raise OpenStackCloudException(
                        "Error in rebuilding the server",
                        extra_data=dict(
                            server=meta.obj_to_dict(server)))
        return server

    def delete_server(self, name, wait=False, timeout=180):
        # TODO(mordred): Why is this not using self.get_server()?
        server_list = self.manager.submitTask(_tasks.ServerList(
            detailed=True, search_opts={'name': name}))
        # TODO(mordred): Why, after searching for a name, are we filtering
        # again?
        if server_list:
            server = [x for x in server_list if x.name == name]
            self.manager.submitTask(_tasks.ServerDelete(server=server.pop()))
        if not wait:
            return
        for count in _iterate_timeout(
                timeout,
                "Timed out waiting for server to get deleted."):
            server = self.manager.submitTask(_tasks.ServerGet(server=server))
            if not server:
                return

    def get_container(self, name, skip_cache=False):
        if skip_cache or name not in self._container_cache:
            try:
                container = self.manager.submitTask(
                    _tasks.ContainerGet(container=name))
                self._container_cache[name] = container
            except swift_exceptions.ClientException as e:
                if e.http_status == 404:
                    return None
                self.log.debug("swift container fetch failed", exc_info=True)
                raise OpenStackCloudException(
                    "Container fetch failed: %s (%s/%s)" % (
                        e.http_reason, e.http_host, e.http_path))
        return self._container_cache[name]

    def create_container(self, name, public=False):
        container = self.get_container(name)
        if container:
            return container
        try:
            self.manager.submitTask(
                _tasks.ContainerCreate(container=name))
            if public:
                self.set_container_access(name, 'public')
            return self.get_container(name, skip_cache=True)
        except swift_exceptions.ClientException as e:
            self.log.debug("swift container create failed", exc_info=True)
            raise OpenStackCloudException(
                "Container creation failed: %s (%s/%s)" % (
                    e.http_reason, e.http_host, e.http_path))

    def delete_container(self, name):
        try:
            self.manager.submitTask(
                _tasks.ContainerDelete(container=name))
        except swift_exceptions.ClientException as e:
            if e.http_status == 404:
                return
            self.log.debug("swift container delete failed", exc_info=True)
            raise OpenStackCloudException(
                "Container deletion failed: %s (%s/%s)" % (
                    e.http_reason, e.http_host, e.http_path))

    def update_container(self, name, headers):
        try:
            self.manager.submitTask(
                _tasks.ContainerUpdate(container=name, headers=headers))
        except swift_exceptions.ClientException as e:
            self.log.debug("swift container update failed", exc_info=True)
            raise OpenStackCloudException(
                "Container update failed: %s (%s/%s)" % (
                    e.http_reason, e.http_host, e.http_path))

    def set_container_access(self, name, access):
        if access not in OBJECT_CONTAINER_ACLS:
            raise OpenStackCloudException(
                "Invalid container access specified: %s.  Must be one of %s"
                % (access, list(OBJECT_CONTAINER_ACLS.keys())))
        header = {'x-container-read': OBJECT_CONTAINER_ACLS[access]}
        self.update_container(name, header)

    def get_container_access(self, name):
        container = self.get_container(name, skip_cache=True)
        if not container:
            raise OpenStackCloudException("Container not found: %s" % name)
        acl = container.get('x-container-read', '')
        try:
            return [p for p, a in OBJECT_CONTAINER_ACLS.items()
                    if acl == a].pop()
        except IndexError:
            raise OpenStackCloudException(
                "Could not determine container access for ACL: %s." % acl)

    def _get_file_hashes(self, filename):
        if filename not in self._file_hash_cache:
            md5 = hashlib.md5()
            sha256 = hashlib.sha256()
            with open(filename, 'rb') as file_obj:
                for chunk in iter(lambda: file_obj.read(8192), b''):
                    md5.update(chunk)
                    sha256.update(chunk)
            self._file_hash_cache[filename] = dict(
                md5=md5.hexdigest(), sha256=sha256.hexdigest())
        return (self._file_hash_cache[filename]['md5'],
                self._file_hash_cache[filename]['sha256'])

    def is_object_stale(
        self, container, name, filename, file_md5=None, file_sha256=None):

        metadata = self.get_object_metadata(container, name)
        if not metadata:
            self.log.debug(
                "swift stale check, no object: {container}/{name}".format(
                    container=container, name=name))
            return True

        if file_md5 is None or file_sha256 is None:
            (file_md5, file_sha256) = self._get_file_hashes(filename)

        if metadata.get(OBJECT_MD5_KEY, '') != file_md5:
            self.log.debug(
                "swift md5 mismatch: {filename}!={container}/{name}".format(
                    filename=filename, container=container, name=name))
            return True
        if metadata.get(OBJECT_SHA256_KEY, '') != file_sha256:
            self.log.debug(
                "swift sha256 mismatch: {filename}!={container}/{name}".format(
                    filename=filename, container=container, name=name))
            return True

        self.log.debug(
            "swift object up to date: {container}/{name}".format(
            container=container, name=name))
        return False

    def create_object(
            self, container, name, filename=None,
            md5=None, sha256=None, **headers):
        if not filename:
            filename = name

        # On some clouds this is not necessary. On others it is. I'm confused.
        self.create_container(container)

        if self.is_object_stale(container, name, filename, md5, sha256):
            with open(filename, 'r') as fileobj:
                self.log.debug(
                    "swift uploading {filename} to {container}/{name}".format(
                        filename=filename, container=container, name=name))
                self.manager.submitTask(_tasks.ObjectCreate(
                    container=container, obj=name, contents=fileobj))

        (md5, sha256) = self._get_file_hashes(filename)
        headers[OBJECT_MD5_KEY] = md5
        headers[OBJECT_SHA256_KEY] = sha256
        self.manager.submitTask(_tasks.ObjectUpdate(
            container=container, obj=name, headers=headers))

    def delete_object(self, container, name):
        if not self.get_object_metadata(container, name):
            return
        try:
            self.manager.submitTask(_tasks.ObjectDelete(
                container=container, obj=name))
        except swift_exceptions.ClientException as e:
            raise OpenStackCloudException(
                "Object deletion failed: %s (%s/%s)" % (
                    e.http_reason, e.http_host, e.http_path))

    def get_object_metadata(self, container, name):
        try:
            return self.manager.submitTask(_tasks.ObjectMetadata(
                container=container, obj=name))
        except swift_exceptions.ClientException as e:
            if e.http_status == 404:
                return None
            self.log.debug("swift metadata fetch failed", exc_info=True)
            raise OpenStackCloudException(
                "Object metadata fetch failed: %s (%s/%s)" % (
                    e.http_reason, e.http_host, e.http_path))


class OperatorCloud(OpenStackCloud):

    @property
    def auth_token(self):
        if self.auth_plugin in (None, "None", ''):
            return self._auth_token
        if not self._auth_token:
            self._auth_token = self.keystone_session.get_token()
        return self._auth_token

    @property
    def ironic_client(self):
        if self._ironic_client is None:
            ironic_logging = logging.getLogger('ironicclient')
            ironic_logging.addHandler(logging.NullHandler())
            token = self.auth_token
            if self.auth_plugin in (None, "None", ''):
                # TODO: This needs to be improved logic wise, perhaps a list,
                # or enhancement of the data stuctures with-in the library
                # to allow for things aside password authentication, or no
                # authentication if so desired by the user.
                #
                # Attempt to utilize a pre-stored endpoint in the auth
                # dict as the endpoint.
                endpoint = self.auth['endpoint']
            else:
                endpoint = self.get_endpoint(service_type='baremetal')
            try:
                self._ironic_client = ironic_client.Client(
                    '1', endpoint, token=token,
                    timeout=self.api_timeout)
            except Exception as e:
                self.log.debug("ironic auth failed", exc_info=True)
                raise OpenStackCloudException(
                    "Error in connecting to ironic: %s" % e.message)
        return self._ironic_client

    def list_nics(self):
        return self.ironic_client.port.list()

    def list_nics_for_machine(self, uuid):
        return self.ironic_client.node.list_ports(uuid)

    def get_nic_by_mac(self, mac):
        try:
            return self.ironic_client.port.get(mac)
        except ironic_exceptions.ClientException:
            return None

    def list_machines(self):
        return self.ironic_client.node.list()

    def get_machine_by_uuid(self, uuid):
        try:
            return self.ironic_client.node.get(uuid)
        except ironic_exceptions.ClientException:
            return None

    def get_machine_by_mac(self, mac):
        try:
            port = self.ironic_client.port.get(mac)
            return self.ironic_client.node.get(port.node_uuid)
        except ironic_exceptions.ClientException:
            return None

    def register_machine(self, nics, **kwargs):
        try:
            machine = self.ironic_client.node.create(**kwargs)
        except Exception as e:
            self.log.debug("ironic machine registration failed", exc_info=True)
            raise OpenStackCloudException(
                "Error registering machine with Ironic: %s" % e.message)

        created_nics = []
        try:
            for row in nics:
                nic = self.ironic_client.port.create(address=row['mac'],
                                                     node_uuid=machine.uuid)
                created_nics.append(nic.uuid)
        except Exception as e:
            self.log.debug("ironic NIC registration failed", exc_info=True)
            # TODO(mordred) Handle failures here
            for uuid in created_nics:
                self.ironic_client.port.delete(uuid)
            self.ironic_client.node.delete(machine.uuid)
            raise OpenStackCloudException(
                "Error registering NICs with Ironic: %s" % e.message)
        return machine

    def unregister_machine(self, nics, uuid):
        for nic in nics:
            try:
                self.ironic_client.port.delete(
                    self.ironic_client.port.get_by_address(nic['mac']))
            except Exception as e:
                self.log.debug(
                    "ironic NIC unregistration failed", exc_info=True)
                raise OpenStackCloudException(e.message)
        try:
            self.ironic_client.node.delete(uuid)
        except Exception as e:
            self.log.debug(
                "ironic machine unregistration failed", exc_info=True)
            raise OpenStackCloudException(
                "Error unregistering machine from Ironic: %s" % e.message)

    def validate_node(self, uuid):
        try:
            ifaces = self.ironic_client.node.validate(uuid)
        except Exception as e:
            self.log.debug(
                "ironic node validation call failed", exc_info=True)
            raise OpenStackCloudException(e.message)

        if not ifaces.deploy or not ifaces.power:
            raise OpenStackCloudException(
                "ironic node %s failed to validate. "
                "(deploy: %s, power: %s)" % (ifaces.deploy, ifaces.power))

    def node_set_provision_state(self, uuid, state, configdrive=None):
        try:
            self.ironic_client.node.set_provision_state(
                uuid,
                state,
                configdrive
            )
        except Exception as e:
            self.log.debug(
                "ironic node failed change provision state to %s" % state,
                exc_info=True)
            raise OpenStackCloudException(e.message)

    def activate_node(self, uuid, configdrive=None):
        self.node_set_provision_state(uuid, 'active', configdrive)

    def deactivate_node(self, uuid):
        self.node_set_provision_state(uuid, 'deleted')

    def set_node_instance_info(self, uuid, patch):
        try:
            self.ironic_client.node.update(uuid, patch)
        except Exception as e:
            self.log.debug(
                "Failed to update instance_info", exc_info=True)
            raise OpenStackCloudException(e.message)

    def purge_node_instance_info(self, uuid):
        patch = []
        patch.append({'op': 'remove', 'path': '/instance_info'})
        try:
            return self.ironic_client.node.update(uuid, patch)
        except Exception as e:
            self.log.debug(
                "Failed to delete instance_info", exc_info=True)
            raise OpenStackCloudException(e.message)
