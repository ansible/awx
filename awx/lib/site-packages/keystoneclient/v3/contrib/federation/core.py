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

from keystoneclient.v3.contrib.federation import domains
from keystoneclient.v3.contrib.federation import identity_providers
from keystoneclient.v3.contrib.federation import mappings
from keystoneclient.v3.contrib.federation import projects
from keystoneclient.v3.contrib.federation import protocols
from keystoneclient.v3.contrib.federation import service_providers


class FederationManager(object):
    def __init__(self, api):
        self.identity_providers = identity_providers.IdentityProviderManager(
            api)
        self.mappings = mappings.MappingManager(api)
        self.protocols = protocols.ProtocolManager(api)
        self.projects = projects.ProjectManager(api)
        self.domains = domains.DomainManager(api)
        self.service_providers = service_providers.ServiceProviderManager(api)
