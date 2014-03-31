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
from novaclient.v1_1 import agents
from novaclient.v1_1 import aggregates
from novaclient.v1_1 import availability_zones
from novaclient.v1_1 import certs
from novaclient.v1_1 import cloudpipe
from novaclient.v1_1 import fixed_ips
from novaclient.v1_1 import flavor_access
from novaclient.v1_1 import flavors
from novaclient.v1_1 import floating_ip_dns
from novaclient.v1_1 import floating_ip_pools
from novaclient.v1_1 import floating_ips
from novaclient.v1_1 import floating_ips_bulk
from novaclient.v1_1 import fping
from novaclient.v1_1 import hosts
from novaclient.v1_1 import hypervisors
from novaclient.v1_1 import images
from novaclient.v1_1 import keypairs
from novaclient.v1_1 import limits
from novaclient.v1_1 import networks
from novaclient.v1_1 import quota_classes
from novaclient.v1_1 import quotas
from novaclient.v1_1 import security_group_rules
from novaclient.v1_1 import security_groups
from novaclient.v1_1 import servers
from novaclient.v1_1 import services
from novaclient.v1_1 import usage
from novaclient.v1_1 import virtual_interfaces
from novaclient.v1_1 import volume_snapshots
from novaclient.v1_1 import volume_types
from novaclient.v1_1 import volumes


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
    def __init__(self, username, api_key, project_id, auth_url=None,
                  insecure=False, timeout=None, proxy_tenant_id=None,
                  proxy_token=None, region_name=None,
                  endpoint_type='publicURL', extensions=None,
                  service_type='compute', service_name=None,
                  volume_service_name=None, timings=False,
                  bypass_url=None, os_cache=False, no_cache=True,
                  http_log_debug=False, auth_system='keystone',
                  auth_plugin=None, auth_token=None,
                  cacert=None, tenant_id=None):
        # FIXME(comstud): Rename the api_key argument above when we
        # know it's not being used as keyword argument
        password = api_key
        self.projectid = project_id
        self.tenant_id = tenant_id
        self.flavors = flavors.FlavorManager(self)
        self.flavor_access = flavor_access.FlavorAccessManager(self)
        self.images = images.ImageManager(self)
        self.limits = limits.LimitsManager(self)
        self.servers = servers.ServerManager(self)

        # extensions
        self.agents = agents.AgentsManager(self)
        self.dns_domains = floating_ip_dns.FloatingIPDNSDomainManager(self)
        self.dns_entries = floating_ip_dns.FloatingIPDNSEntryManager(self)
        self.cloudpipe = cloudpipe.CloudpipeManager(self)
        self.certs = certs.CertificateManager(self)
        self.floating_ips = floating_ips.FloatingIPManager(self)
        self.floating_ip_pools = floating_ip_pools.FloatingIPPoolManager(self)
        self.fping = fping.FpingManager(self)
        self.volumes = volumes.VolumeManager(self)
        self.volume_snapshots = volume_snapshots.SnapshotManager(self)
        self.volume_types = volume_types.VolumeTypeManager(self)
        self.keypairs = keypairs.KeypairManager(self)
        self.networks = networks.NetworkManager(self)
        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.security_groups = security_groups.SecurityGroupManager(self)
        self.security_group_rules = \
            security_group_rules.SecurityGroupRuleManager(self)
        self.usage = usage.UsageManager(self)
        self.virtual_interfaces = \
            virtual_interfaces.VirtualInterfaceManager(self)
        self.aggregates = aggregates.AggregateManager(self)
        self.hosts = hosts.HostManager(self)
        self.hypervisors = hypervisors.HypervisorManager(self)
        self.services = services.ServiceManager(self)
        self.fixed_ips = fixed_ips.FixedIPsManager(self)
        self.floating_ips_bulk = floating_ips_bulk.FloatingIPBulkManager(self)
        self.os_cache = os_cache or not no_cache
        self.availability_zones = \
            availability_zones.AvailabilityZoneManager(self)

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
