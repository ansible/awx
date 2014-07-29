#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
from azure import (
    MANAGEMENT_HOST,
    _convert_response_to_feeds,
    _str,
    _validate_not_none,
    )
from azure.servicemanagement import (
    _ServiceBusManagementXmlSerializer,
    )
from azure.servicemanagement.servicemanagementclient import (
    _ServiceManagementClient,
    )


class ServiceBusManagementService(_ServiceManagementClient):

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST):
        super(ServiceBusManagementService, self).__init__(
            subscription_id, cert_file, host)

    #--Operations for service bus ----------------------------------------
    def get_regions(self):
        '''
        Get list of available service bus regions.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Regions/', None),
            None)

        return _convert_response_to_feeds(
            response,
            _ServiceBusManagementXmlSerializer.xml_to_region)

    def list_namespaces(self):
        '''
        List the service bus namespaces defined on the account.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Namespaces/', None),
            None)

        return _convert_response_to_feeds(
            response,
            _ServiceBusManagementXmlSerializer.xml_to_namespace)

    def get_namespace(self, name):
        '''
        Get details about a specific namespace.

        name: Name of the service bus namespace.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Namespaces', name),
            None)

        return _ServiceBusManagementXmlSerializer.xml_to_namespace(
            response.body)

    def create_namespace(self, name, region):
        '''
        Create a new service bus namespace.

        name: Name of the service bus namespace to create.
        region: Region to create the namespace in.
        '''
        _validate_not_none('name', name)

        return self._perform_put(
            self._get_path('services/serviceBus/Namespaces', name),
            _ServiceBusManagementXmlSerializer.namespace_to_xml(region))

    def delete_namespace(self, name):
        '''
        Delete a service bus namespace.

        name: Name of the service bus namespace to delete.
        '''
        _validate_not_none('name', name)

        return self._perform_delete(
            self._get_path('services/serviceBus/Namespaces', name),
            None)

    def check_namespace_availability(self, name):
        '''
        Checks to see if the specified service bus namespace is available, or
        if it has already been taken.

        name: Name of the service bus namespace to validate.
        '''
        _validate_not_none('name', name)

        response = self._perform_get(
            self._get_path('services/serviceBus/CheckNamespaceAvailability',
                           None) + '/?namespace=' + _str(name), None)

        return _ServiceBusManagementXmlSerializer.xml_to_namespace_availability(
            response.body)
