# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

from troveclient import client as trove_client
from troveclient.v1 import backups
from troveclient.v1 import clusters
from troveclient.v1 import configurations
from troveclient.v1 import databases
from troveclient.v1 import datastores
from troveclient.v1 import flavors
from troveclient.v1 import instances
from troveclient.v1 import limits
# from troveclient.v1 import management
from troveclient.v1 import metadata
from troveclient.v1 import root
from troveclient.v1 import security_groups
from troveclient.v1 import users


class Client(object):
    """Top-level object to access the OpenStack Database API.

    Create an instance with your creds::

        >> client = Client(USERNAME,
                           PASSWORD,
                           project_id=TENANT_NAME,
                           auth_url=AUTH_URL)

    Then call methods on its managers::

        >> client.instances.list()
        ...

    """

    def __init__(self, username, password, project_id=None, auth_url='',
                 insecure=False, timeout=None, tenant_id=None,
                 proxy_tenant_id=None, proxy_token=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='database', service_name=None,
                 database_service_name=None, retries=None,
                 http_log_debug=False,
                 cacert=None, bypass_url=None,
                 auth_system='keystone', auth_plugin=None, session=None,
                 auth=None, **kwargs):
        # self.limits = limits.LimitsManager(self)

        # extensions
        self.flavors = flavors.Flavors(self)
        self.users = users.Users(self)
        self.databases = databases.Databases(self)
        self.backups = backups.Backups(self)
        self.clusters = clusters.Clusters(self)
        self.instances = instances.Instances(self)
        self.limits = limits.Limits(self)
        self.root = root.Root(self)
        self.security_group_rules = security_groups.SecurityGroupRules(self)
        self.security_groups = security_groups.SecurityGroups(self)
        self.datastores = datastores.Datastores(self)
        self.datastore_versions = datastores.DatastoreVersions(self)
        self.configurations = configurations.Configurations(self)
        config_parameters = configurations.ConfigurationParameters(self)
        self.configuration_parameters = config_parameters
        self.metadata = metadata.Metadata(self)

        # self.hosts = Hosts(self)
        # self.quota = Quotas(self)
        # self.storage = StorageInfo(self)
        # self.management = Management(self)
        # self.management = MgmtClusters(self)
        # self.mgmt_flavor = MgmtFlavors(self)
        # self.accounts = Accounts(self)
        # self.diagnostics = DiagnosticsInterrogator(self)
        # self.hwinfo = HwInfoInterrogator(self)
        # self.mgmt_config_params =
        #       management.MgmtConfigurationParameters(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = trove_client._construct_http_client(
            username=username,
            password=password,
            project_id=project_id,
            auth_url=auth_url,
            insecure=insecure,
            timeout=timeout,
            tenant_id=tenant_id,
            proxy_token=proxy_token,
            proxy_tenant_id=proxy_tenant_id,
            region_name=region_name,
            endpoint_type=endpoint_type,
            service_type=service_type,
            service_name=service_name,
            database_service_name=database_service_name,
            retries=retries,
            http_log_debug=http_log_debug,
            cacert=cacert,
            bypass_url=bypass_url,
            auth_system=auth_system,
            auth_plugin=auth_plugin,
            session=session,
            auth=auth,
            **kwargs)

    def authenticate(self):
        """Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

    def get_database_api_version_from_endpoint(self):
        return self.client.get_database_api_version_from_endpoint()
