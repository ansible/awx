# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from novaclient import client
from novaclient.v3 import agents
from novaclient.v3 import aggregates
from novaclient.v3 import availability_zones
from novaclient.v3 import certs
from novaclient.v3 import flavor_access
from novaclient.v3 import flavors
from novaclient.v3 import hosts
from novaclient.v3 import hypervisors
from novaclient.v3 import images
from novaclient.v3 import keypairs
from novaclient.v3 import list_extensions
from novaclient.v3 import quotas
from novaclient.v3 import servers
from novaclient.v3 import services
from novaclient.v3 import usage
from novaclient.v3 import volumes


class Client(object):
    """
    Top-level object to access the OpenStack Compute API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Or, alternatively, you can create a client instance using the
    keystoneclient.session API::

        >>> from keystoneclient.auth.identity import v2
        >>> from keystoneclient import session
        >>> from novaclient.client import Client
        >>> auth = v2.Password(auth_url=AUTH_URL,
                               username=USERNAME,
                               password=PASSWORD,
                               tenant_name=PROJECT_ID)
        >>> sess = session.Session(auth=auth)
        >>> nova = client.Client(VERSION, session=sess)

    Then call methods on its managers::

        >>> client.servers.list()
        ...
        >>> client.flavors.list()
        ...

    It is also possible to use an instance as a context manager in which
    case there will be a session kept alive for the duration of the with
    statement::

        >>> with Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL) as client:
        ...     client.servers.list()
        ...     client.flavors.list()
        ...

    It is also possible to have a permanent (process-long) connection pool,
    by passing a connection_pool=True::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID,
        ...     AUTH_URL, connection_pool=True)
    """

    def __init__(self, username=None, password=None, project_id=None,
                 auth_url=None, insecure=False, timeout=None,
                 proxy_tenant_id=None, proxy_token=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='computev3', service_name=None,
                 volume_service_name=None, timings=False, bypass_url=None,
                 os_cache=False, no_cache=True, http_log_debug=False,
                 auth_system='keystone', auth_plugin=None, auth_token=None,
                 cacert=None, tenant_id=None, user_id=None,
                 connection_pool=False, session=None, auth=None,
                 completion_cache=None):
        # NOTE(cyeoh): In the novaclient context (unlike Nova) the
        # project_id is not the same as the tenant_id. Here project_id
        # is a name (what the Nova API often refers to as a project or
        # tenant name) and tenant_id is a UUID (what the Nova API
        # often refers to as a project_id or tenant_id).

        self.projectid = project_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.os_cache = os_cache or not no_cache
        # TODO(bnemec): Add back in v3 extensions
        self.agents = agents.AgentsManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.availability_zones = \
            availability_zones.AvailabilityZoneManager(self)
        self.certs = certs.CertificateManager(self)
        self.list_extensions = list_extensions.ListExtManager(self)
        self.hosts = hosts.HostManager(self)
        self.flavors = flavors.FlavorManager(self)
        self.flavor_access = flavor_access.FlavorAccessManager(self)
        self.hypervisors = hypervisors.HypervisorManager(self)
        self.images = images.ImageManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.servers = servers.ServerManager(self)
        self.services = services.ServiceManager(self)
        self.usage = usage.UsageManager(self)
        self.volumes = volumes.VolumeManager(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = client._construct_http_client(
            username=username,
            password=password,
            user_id=user_id,
            project_id=project_id,
            tenant_id=tenant_id,
            auth_url=auth_url,
            auth_token=auth_token,
            insecure=insecure,
            timeout=timeout,
            auth_system=auth_system,
            auth_plugin=auth_plugin,
            proxy_token=proxy_token,
            proxy_tenant_id=proxy_tenant_id,
            region_name=region_name,
            endpoint_type=endpoint_type,
            service_type=service_type,
            service_name=service_name,
            volume_service_name=volume_service_name,
            timings=timings,
            bypass_url=bypass_url,
            os_cache=self.os_cache,
            http_log_debug=http_log_debug,
            cacert=cacert,
            connection_pool=connection_pool,
            session=session,
            auth=auth)

        self.completion_cache = completion_cache

    def write_object_to_completion_cache(self, obj):
        if self.completion_cache:
            self.completion_cache.write_object(obj)

    def clear_completion_cache_for_class(self, obj_class):
        if self.completion_cache:
            self.completion_cache.clear_class(obj_class)

    @client._original_only
    def __enter__(self):
        self.client.open_session()
        return self

    @client._original_only
    def __exit__(self, t, v, tb):
        self.client.close_session()

    @client._original_only
    def set_management_url(self, url):
        self.client.set_management_url(url)

    @client._original_only
    def get_timings(self):
        return self.client.get_timings()

    @client._original_only
    def reset_timings(self):
        self.client.reset_timings()

    @client._original_only
    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
