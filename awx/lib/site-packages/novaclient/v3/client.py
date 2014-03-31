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
from novaclient.v3 import quota_classes
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

    Then call methods on its managers::

        >>> client.servers.list()
        ...
        >>> client.flavors.list()
        ...

    """

    # FIXME(jesse): project_id isn't required to authenticate
    def __init__(self, username, password, project_id, auth_url=None,
                  insecure=False, timeout=None, proxy_tenant_id=None,
                  proxy_token=None, region_name=None,
                  endpoint_type='publicURL', extensions=None,
                  service_type='computev3', service_name=None,
                  volume_service_name=None, timings=False,
                  bypass_url=None, os_cache=False, no_cache=True,
                  http_log_debug=False, auth_system='keystone',
                  auth_plugin=None, auth_token=None,
                  cacert=None, tenant_id=None):
        self.projectid = project_id
        self.tenant_id = tenant_id
        self.os_cache = os_cache or not no_cache
        #TODO(bnemec): Add back in v3 extensions
        self.agents = agents.AgentsManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.availability_zones = \
            availability_zones.AvailabilityZoneManager(self)
        self.certs = certs.CertificateManager(self)
        self.hosts = hosts.HostManager(self)
        self.flavors = flavors.FlavorManager(self)
        self.flavor_access = flavor_access.FlavorAccessManager(self)
        self.hypervisors = hypervisors.HypervisorManager(self)
        self.images = images.ImageManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.quota_classes = quota_classes.QuotaClassSetManager(self)
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

        self.client = client.HTTPClient(username,
                                    password,
                                    projectid=project_id,
                                    tenant_id=tenant_id,
                                    auth_url=auth_url,
                                    insecure=insecure,
                                    timeout=timeout,
                                    auth_system=auth_system,
                                    auth_plugin=auth_plugin,
                                    auth_token=auth_token,
                                    proxy_token=proxy_token,
                                    proxy_tenant_id=proxy_tenant_id,
                                    region_name=region_name,
                                    endpoint_type=endpoint_type,
                                    service_type=service_type,
                                    service_name=service_name,
                                    volume_service_name=volume_service_name,
                                    timings=timings,
                                    bypass_url=bypass_url,
                                    os_cache=os_cache,
                                    http_log_debug=http_log_debug,
                                    cacert=cacert)

    def set_management_url(self, url):
        self.client.set_management_url(url)

    def get_timings(self):
        return self.client.get_timings()

    def reset_timings(self):
        self.client.reset_timings()

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
