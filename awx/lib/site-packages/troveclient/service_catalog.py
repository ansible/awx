# Copyright 2011 OpenStack LLC.
# Copyright 2011, Piston Cloud Computing, Inc.
# Copyright 2013 Rackspace Hosting
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from troveclient.openstack.common.apiclient import exceptions


class ServiceCatalog(object):
    """Helper methods for dealing with a Keystone Service Catalog."""

    def __init__(self, resource_dict):
        self.catalog = resource_dict

    def get_token(self):
        return self.catalog['access']['token']['id']

    def url_for(self, attr=None, filter_value=None,
                service_type=None, endpoint_type='publicURL',
                service_name=None, database_service_name=None):
        """Fetch the public URL from the Compute service for
        a particular endpoint attribute. If none given, return
        the first. See tests for sample service catalog.
        """
        matching_endpoints = []
        if 'endpoints' in self.catalog:
            # We have a bastardized service catalog. Treat it special. :/
            for endpoint in self.catalog['endpoints']:
                if not filter_value or endpoint[attr] == filter_value:
                    matching_endpoints.append(endpoint)
            if not matching_endpoints:
                raise exceptions.EndpointNotFound()

        # We don't always get a service catalog back ...
        if 'serviceCatalog' not in self.catalog['access']:
            return None

        # Full catalog ...
        catalog = self.catalog['access']['serviceCatalog']

        for service in catalog:

            # NOTE(thingee): For backwards compatibility, if they have v2
            # enabled and the service_type is set to 'database', go ahead and
            # accept that.
            skip_service_type_check = False
            if service_type == 'databasev2' and service['type'] == 'database':
                version = service['endpoints'][0]['publicURL'].split('/')[3]
                if version == 'v2':
                    skip_service_type_check = True

            if (not skip_service_type_check
                    and service.get("type") != service_type):
                continue

            if (database_service_name and service_type in ('database',
                                                           'databasev2')
                    and service.get('name') != database_service_name):
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if not filter_value or endpoint.get(attr) == filter_value:
                    endpoint["serviceName"] = service.get("name")
                    matching_endpoints.append(endpoint)

        if not matching_endpoints:
            raise exceptions.EndpointNotFound()
        elif len(matching_endpoints) > 1:
            raise exceptions.AmbiguousEndpoints(
                endpoints=matching_endpoints)
        else:
            return matching_endpoints[0][endpoint_type]
