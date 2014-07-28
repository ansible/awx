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
    WindowsAzureError,
    MANAGEMENT_HOST,
    _str,
    _validate_not_none,
    )
from azure.servicemanagement import (
    AffinityGroups,
    AffinityGroup,
    AvailabilityResponse,
    Certificate,
    Certificates,
    DataVirtualHardDisk,
    Deployment,
    Disk,
    Disks,
    Locations,
    Operation,
    HostedService,
    HostedServices,
    Images,
    OperatingSystems,
    OperatingSystemFamilies,
    OSImage,
    PersistentVMRole,
    StorageService,
    StorageServices,
    Subscription,
    SubscriptionCertificate,
    SubscriptionCertificates,
    VirtualNetworkSites,
    _XmlSerializer,
    )
from azure.servicemanagement.servicemanagementclient import (
    _ServiceManagementClient,
    )

class ServiceManagementService(_ServiceManagementClient):

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST):
        super(ServiceManagementService, self).__init__(
            subscription_id, cert_file, host)

    #--Operations for storage accounts -----------------------------------
    def list_storage_accounts(self):
        '''
        Lists the storage accounts available under the current subscription.
        '''
        return self._perform_get(self._get_storage_service_path(),
                                 StorageServices)

    def get_storage_account_properties(self, service_name):
        '''
        Returns system properties for the specified storage account.

        service_name: Name of the storage service account.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_get(self._get_storage_service_path(service_name),
                                 StorageService)

    def get_storage_account_keys(self, service_name):
        '''
        Returns the primary and secondary access keys for the specified
        storage account.

        service_name: Name of the storage service account.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_get(
            self._get_storage_service_path(service_name) + '/keys',
            StorageService)

    def regenerate_storage_account_keys(self, service_name, key_type):
        '''
        Regenerates the primary or secondary access key for the specified
        storage account.

        service_name: Name of the storage service account.
        key_type:
            Specifies which key to regenerate. Valid values are:
            Primary, Secondary
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('key_type', key_type)
        return self._perform_post(
            self._get_storage_service_path(
                service_name) + '/keys?action=regenerate',
            _XmlSerializer.regenerate_keys_to_xml(
                key_type),
            StorageService)

    def create_storage_account(self, service_name, description, label,
                               affinity_group=None, location=None,
                               geo_replication_enabled=True,
                               extended_properties=None):
        '''
        Creates a new storage account in Windows Azure.

        service_name:
            A name for the storage account that is unique within Windows Azure.
            Storage account names must be between 3 and 24 characters in length
            and use numbers and lower-case letters only.
        description:
            A description for the storage account. The description may be up
            to 1024 characters in length.
        label:
            A name for the storage account. The name may be up to 100
            characters in length. The name can be used to identify the storage
            account for your tracking purposes.
        affinity_group:
            The name of an existing affinity group in the specified
            subscription. You can specify either a location or affinity_group,
            but not both.
        location:
            The location where the storage account is created. You can specify
            either a location or affinity_group, but not both.
        geo_replication_enabled:
            Specifies whether the storage account is created with the
            geo-replication enabled. If the element is not included in the
            request body, the default value is true. If set to true, the data
            in the storage account is replicated across more than one
            geographic location so as to enable resilience in the face of
            catastrophic service loss.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('description', description)
        _validate_not_none('label', label)
        if affinity_group is None and location is None:
            raise WindowsAzureError(
                'location or affinity_group must be specified')
        if affinity_group is not None and location is not None:
            raise WindowsAzureError(
                'Only one of location or affinity_group needs to be specified')
        return self._perform_post(
            self._get_storage_service_path(),
            _XmlSerializer.create_storage_service_input_to_xml(
                service_name,
                description,
                label,
                affinity_group,
                location,
                geo_replication_enabled,
                extended_properties),
            async=True)

    def update_storage_account(self, service_name, description=None,
                               label=None, geo_replication_enabled=None,
                               extended_properties=None):
        '''
        Updates the label, the description, and enables or disables the
        geo-replication status for a storage account in Windows Azure.

        service_name: Name of the storage service account.
        description:
            A description for the storage account. The description may be up
            to 1024 characters in length.
        label:
            A name for the storage account. The name may be up to 100
            characters in length. The name can be used to identify the storage
            account for your tracking purposes.
        geo_replication_enabled:
            Specifies whether the storage account is created with the
            geo-replication enabled. If the element is not included in the
            request body, the default value is true. If set to true, the data
            in the storage account is replicated across more than one
            geographic location so as to enable resilience in the face of
            catastrophic service loss.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_put(
            self._get_storage_service_path(service_name),
            _XmlSerializer.update_storage_service_input_to_xml(
                description,
                label,
                geo_replication_enabled,
                extended_properties))

    def delete_storage_account(self, service_name):
        '''
        Deletes the specified storage account from Windows Azure.

        service_name: Name of the storage service account.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_delete(
            self._get_storage_service_path(service_name))

    def check_storage_account_name_availability(self, service_name):
        '''
        Checks to see if the specified storage account name is available, or
        if it has already been taken.

        service_name: Name of the storage service account.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_get(
            self._get_storage_service_path() +
            '/operations/isavailable/' +
            _str(service_name) + '',
            AvailabilityResponse)

    #--Operations for hosted services ------------------------------------
    def list_hosted_services(self):
        '''
        Lists the hosted services available under the current subscription.
        '''
        return self._perform_get(self._get_hosted_service_path(),
                                 HostedServices)

    def get_hosted_service_properties(self, service_name, embed_detail=False):
        '''
        Retrieves system properties for the specified hosted service. These
        properties include the service name and service type; the name of the
        affinity group to which the service belongs, or its location if it is
        not part of an affinity group; and optionally, information on the
        service's deployments.

        service_name: Name of the hosted service.
        embed_detail:
            When True, the management service returns properties for all
            deployments of the service, as well as for the service itself.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('embed_detail', embed_detail)
        return self._perform_get(
            self._get_hosted_service_path(service_name) +
            '?embed-detail=' +
            _str(embed_detail).lower(),
            HostedService)

    def create_hosted_service(self, service_name, label, description=None,
                              location=None, affinity_group=None,
                              extended_properties=None):
        '''
        Creates a new hosted service in Windows Azure.

        service_name:
            A name for the hosted service that is unique within Windows Azure.
            This name is the DNS prefix name and can be used to access the
            hosted service.
        label:
            A name for the hosted service. The name can be up to 100 characters
            in length. The name can be used to identify the storage account for
            your tracking purposes.
        description:
            A description for the hosted service. The description can be up to
            1024 characters in length.
        location:
            The location where the hosted service will be created. You can
            specify either a location or affinity_group, but not both.
        affinity_group:
            The name of an existing affinity group associated with this
            subscription. This name is a GUID and can be retrieved by examining
            the name element of the response body returned by
            list_affinity_groups. You can specify either a location or
            affinity_group, but not both.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('label', label)
        if affinity_group is None and location is None:
            raise WindowsAzureError(
                'location or affinity_group must be specified')
        if affinity_group is not None and location is not None:
            raise WindowsAzureError(
                'Only one of location or affinity_group needs to be specified')
        return self._perform_post(self._get_hosted_service_path(),
                                  _XmlSerializer.create_hosted_service_to_xml(
                                      service_name,
                                      label,
                                      description,
                                      location,
                                      affinity_group,
                                      extended_properties))

    def update_hosted_service(self, service_name, label=None, description=None,
                              extended_properties=None):
        '''
        Updates the label and/or the description for a hosted service in
        Windows Azure.

        service_name: Name of the hosted service.
        label:
            A name for the hosted service. The name may be up to 100 characters
            in length. You must specify a value for either Label or
            Description, or for both. It is recommended that the label be
            unique within the subscription. The name can be used
            identify the hosted service for your tracking purposes.
        description:
            A description for the hosted service. The description may be up to
            1024 characters in length. You must specify a value for either
            Label or Description, or for both.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_put(self._get_hosted_service_path(service_name),
                                 _XmlSerializer.update_hosted_service_to_xml(
                                     label,
                                     description,
                                     extended_properties))

    def delete_hosted_service(self, service_name):
        '''
        Deletes the specified hosted service from Windows Azure.

        service_name: Name of the hosted service.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_delete(self._get_hosted_service_path(service_name))

    def get_deployment_by_slot(self, service_name, deployment_slot):
        '''
        Returns configuration information, status, and system properties for
        a deployment.

        service_name: Name of the hosted service.
        deployment_slot:
            The environment to which the hosted service is deployed. Valid
            values are: staging, production
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_slot', deployment_slot)
        return self._perform_get(
            self._get_deployment_path_using_slot(
                service_name, deployment_slot),
            Deployment)

    def get_deployment_by_name(self, service_name, deployment_name):
        '''
        Returns configuration information, status, and system properties for a
        deployment.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        return self._perform_get(
            self._get_deployment_path_using_name(
                service_name, deployment_name),
            Deployment)

    def create_deployment(self, service_name, deployment_slot, name,
                          package_url, label, configuration,
                          start_deployment=False,
                          treat_warnings_as_error=False,
                          extended_properties=None):
        '''
        Uploads a new service package and creates a new deployment on staging
        or production.

        service_name: Name of the hosted service.
        deployment_slot:
            The environment to which the hosted service is deployed. Valid
            values are: staging, production
        name:
            The name for the deployment. The deployment name must be unique
            among other deployments for the hosted service.
        package_url:
            A URL that refers to the location of the service package in the
            Blob service. The service package can be located either in a
            storage account beneath the same subscription or a Shared Access
            Signature (SAS) URI from any storage account.
        label:
            A name for the hosted service. The name can be up to 100 characters
            in length. It is recommended that the label be unique within the
            subscription. The name can be used to identify the hosted service
            for your tracking purposes.
        configuration:
            The base-64 encoded service configuration file for the deployment.
        start_deployment:
            Indicates whether to start the deployment immediately after it is
            created. If false, the service model is still deployed to the
            virtual machines but the code is not run immediately. Instead, the
            service is Suspended until you call Update Deployment Status and
            set the status to Running, at which time the service will be
            started. A deployed service still incurs charges, even if it is
            suspended.
        treat_warnings_as_error:
            Indicates whether to treat package validation warnings as errors.
            If set to true, the Created Deployment operation fails if there
            are validation warnings on the service package.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_slot', deployment_slot)
        _validate_not_none('name', name)
        _validate_not_none('package_url', package_url)
        _validate_not_none('label', label)
        _validate_not_none('configuration', configuration)
        return self._perform_post(
            self._get_deployment_path_using_slot(
                service_name, deployment_slot),
            _XmlSerializer.create_deployment_to_xml(
                name,
                package_url,
                label,
                configuration,
                start_deployment,
                treat_warnings_as_error,
                extended_properties),
            async=True)

    def delete_deployment(self, service_name, deployment_name):
        '''
        Deletes the specified deployment.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        return self._perform_delete(
            self._get_deployment_path_using_name(
                service_name, deployment_name),
            async=True)

    def swap_deployment(self, service_name, production, source_deployment):
        '''
        Initiates a virtual IP swap between the staging and production
        deployment environments for a service. If the service is currently
        running in the staging environment, it will be swapped to the
        production environment. If it is running in the production
        environment, it will be swapped to staging.

        service_name: Name of the hosted service.
        production: The name of the production deployment.
        source_deployment: The name of the source deployment.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('production', production)
        _validate_not_none('source_deployment', source_deployment)
        return self._perform_post(self._get_hosted_service_path(service_name),
                                  _XmlSerializer.swap_deployment_to_xml(
                                      production, source_deployment),
                                  async=True)

    def change_deployment_configuration(self, service_name, deployment_name,
                                        configuration,
                                        treat_warnings_as_error=False,
                                        mode='Auto', extended_properties=None):
        '''
        Initiates a change to the deployment configuration.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        configuration:
            The base-64 encoded service configuration file for the deployment.
        treat_warnings_as_error:
            Indicates whether to treat package validation warnings as errors.
            If set to true, the Created Deployment operation fails if there
            are validation warnings on the service package.
        mode:
            If set to Manual, WalkUpgradeDomain must be called to apply the
            update. If set to Auto, the Windows Azure platform will
            automatically apply the update To each upgrade domain for the
            service. Possible values are: Auto, Manual
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('configuration', configuration)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + '/?comp=config',
            _XmlSerializer.change_deployment_to_xml(
                configuration,
                treat_warnings_as_error,
                mode,
                extended_properties),
            async=True)

    def update_deployment_status(self, service_name, deployment_name, status):
        '''
        Initiates a change in deployment status.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        status:
            The change to initiate to the deployment status. Possible values
            include: Running, Suspended
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('status', status)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + '/?comp=status',
            _XmlSerializer.update_deployment_status_to_xml(
                status),
            async=True)

    def upgrade_deployment(self, service_name, deployment_name, mode,
                           package_url, configuration, label, force,
                           role_to_upgrade=None, extended_properties=None):
        '''
        Initiates an upgrade.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        mode:
            If set to Manual, WalkUpgradeDomain must be called to apply the
            update. If set to Auto, the Windows Azure platform will
            automatically apply the update To each upgrade domain for the
            service. Possible values are: Auto, Manual
        package_url:
            A URL that refers to the location of the service package in the
            Blob service. The service package can be located either in a
            storage account beneath the same subscription or a Shared Access
            Signature (SAS) URI from any storage account.
        configuration:
            The base-64 encoded service configuration file for the deployment.
        label:
            A name for the hosted service. The name can be up to 100 characters
            in length. It is recommended that the label be unique within the
            subscription. The name can be used to identify the hosted service
            for your tracking purposes.
        force:
            Specifies whether the rollback should proceed even when it will
            cause local data to be lost from some role instances. True if the
            rollback should proceed; otherwise false if the rollback should
            fail.
        role_to_upgrade: The name of the specific role to upgrade.
        extended_properties:
            Dictionary containing name/value pairs of storage account
            properties. You can have a maximum of 50 extended property
            name/value pairs. The maximum length of the Name element is 64
            characters, only alphanumeric characters and underscores are valid
            in the Name, and the name must start with a letter. The value has
            a maximum length of 255 characters.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('mode', mode)
        _validate_not_none('package_url', package_url)
        _validate_not_none('configuration', configuration)
        _validate_not_none('label', label)
        _validate_not_none('force', force)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + '/?comp=upgrade',
            _XmlSerializer.upgrade_deployment_to_xml(
                mode,
                package_url,
                configuration,
                label,
                role_to_upgrade,
                force,
                extended_properties),
            async=True)

    def walk_upgrade_domain(self, service_name, deployment_name,
                            upgrade_domain):
        '''
        Specifies the next upgrade domain to be walked during manual in-place
        upgrade or configuration change.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        upgrade_domain:
            An integer value that identifies the upgrade domain to walk.
            Upgrade domains are identified with a zero-based index: the first
            upgrade domain has an ID of 0, the second has an ID of 1, and so on.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('upgrade_domain', upgrade_domain)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + '/?comp=walkupgradedomain',
            _XmlSerializer.walk_upgrade_domain_to_xml(
                upgrade_domain),
            async=True)

    def rollback_update_or_upgrade(self, service_name, deployment_name, mode,
                                   force):
        '''
        Cancels an in progress configuration change (update) or upgrade and
        returns the deployment to its state before the upgrade or
        configuration change was started.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        mode:
            Specifies whether the rollback should proceed automatically.
                auto - The rollback proceeds without further user input.
                manual - You must call the Walk Upgrade Domain operation to
                         apply the rollback to each upgrade domain.
        force:
            Specifies whether the rollback should proceed even when it will
            cause local data to be lost from some role instances. True if the
            rollback should proceed; otherwise false if the rollback should
            fail.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('mode', mode)
        _validate_not_none('force', force)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + '/?comp=rollback',
            _XmlSerializer.rollback_upgrade_to_xml(
                mode, force),
            async=True)

    def reboot_role_instance(self, service_name, deployment_name,
                             role_instance_name):
        '''
        Requests a reboot of a role instance that is running in a deployment.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        role_instance_name: The name of the role instance.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_instance_name', role_instance_name)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + \
                    '/roleinstances/' + _str(role_instance_name) + \
                    '?comp=reboot',
            '',
            async=True)

    def reimage_role_instance(self, service_name, deployment_name,
                              role_instance_name):
        '''
        Requests a reimage of a role instance that is running in a deployment.

        service_name: Name of the hosted service.
        deployment_name: The name of the deployment.
        role_instance_name: The name of the role instance.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_instance_name', role_instance_name)
        return self._perform_post(
            self._get_deployment_path_using_name(
                service_name, deployment_name) + \
                    '/roleinstances/' + _str(role_instance_name) + \
                    '?comp=reimage',
            '',
            async=True)

    def check_hosted_service_name_availability(self, service_name):
        '''
        Checks to see if the specified hosted service name is available, or if
        it has already been taken.

        service_name: Name of the hosted service.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_get(
            '/' + self.subscription_id +
            '/services/hostedservices/operations/isavailable/' +
            _str(service_name) + '',
            AvailabilityResponse)

    #--Operations for service certificates -------------------------------
    def list_service_certificates(self, service_name):
        '''
        Lists all of the service certificates associated with the specified
        hosted service.

        service_name: Name of the hosted service.
        '''
        _validate_not_none('service_name', service_name)
        return self._perform_get(
            '/' + self.subscription_id + '/services/hostedservices/' +
            _str(service_name) + '/certificates',
            Certificates)

    def get_service_certificate(self, service_name, thumbalgorithm, thumbprint):
        '''
        Returns the public data for the specified X.509 certificate associated
        with a hosted service.

        service_name: Name of the hosted service.
        thumbalgorithm: The algorithm for the certificate's thumbprint.
        thumbprint: The hexadecimal representation of the thumbprint.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('thumbalgorithm', thumbalgorithm)
        _validate_not_none('thumbprint', thumbprint)
        return self._perform_get(
            '/' + self.subscription_id + '/services/hostedservices/' +
            _str(service_name) + '/certificates/' +
            _str(thumbalgorithm) + '-' + _str(thumbprint) + '',
            Certificate)

    def add_service_certificate(self, service_name, data, certificate_format,
                                password):
        '''
        Adds a certificate to a hosted service.

        service_name: Name of the hosted service.
        data: The base-64 encoded form of the pfx file.
        certificate_format:
            The service certificate format. The only supported value is pfx.
        password: The certificate password.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('data', data)
        _validate_not_none('certificate_format', certificate_format)
        _validate_not_none('password', password)
        return self._perform_post(
            '/' + self.subscription_id + '/services/hostedservices/' +
            _str(service_name) + '/certificates',
            _XmlSerializer.certificate_file_to_xml(
                data, certificate_format, password),
            async=True)

    def delete_service_certificate(self, service_name, thumbalgorithm,
                                   thumbprint):
        '''
        Deletes a service certificate from the certificate store of a hosted
        service.

        service_name: Name of the hosted service.
        thumbalgorithm: The algorithm for the certificate's thumbprint.
        thumbprint: The hexadecimal representation of the thumbprint.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('thumbalgorithm', thumbalgorithm)
        _validate_not_none('thumbprint', thumbprint)
        return self._perform_delete(
            '/' + self.subscription_id + '/services/hostedservices/' +
            _str(service_name) + '/certificates/' +
            _str(thumbalgorithm) + '-' + _str(thumbprint),
            async=True)

    #--Operations for management certificates ----------------------------
    def list_management_certificates(self):
        '''
        The List Management Certificates operation lists and returns basic
        information about all of the management certificates associated with
        the specified subscription. Management certificates, which are also
        known as subscription certificates, authenticate clients attempting to
        connect to resources associated with your Windows Azure subscription.
        '''
        return self._perform_get('/' + self.subscription_id + '/certificates',
                                 SubscriptionCertificates)

    def get_management_certificate(self, thumbprint):
        '''
        The Get Management Certificate operation retrieves information about
        the management certificate with the specified thumbprint. Management
        certificates, which are also known as subscription certificates,
        authenticate clients attempting to connect to resources associated
        with your Windows Azure subscription.

        thumbprint: The thumbprint value of the certificate.
        '''
        _validate_not_none('thumbprint', thumbprint)
        return self._perform_get(
            '/' + self.subscription_id + '/certificates/' + _str(thumbprint),
            SubscriptionCertificate)

    def add_management_certificate(self, public_key, thumbprint, data):
        '''
        The Add Management Certificate operation adds a certificate to the
        list of management certificates. Management certificates, which are
        also known as subscription certificates, authenticate clients
        attempting to connect to resources associated with your Windows Azure
        subscription.

        public_key:
            A base64 representation of the management certificate public key.
        thumbprint:
            The thumb print that uniquely identifies the management
            certificate.
        data: The certificate's raw data in base-64 encoded .cer format.
        '''
        _validate_not_none('public_key', public_key)
        _validate_not_none('thumbprint', thumbprint)
        _validate_not_none('data', data)
        return self._perform_post(
            '/' + self.subscription_id + '/certificates',
            _XmlSerializer.subscription_certificate_to_xml(
                public_key, thumbprint, data))

    def delete_management_certificate(self, thumbprint):
        '''
        The Delete Management Certificate operation deletes a certificate from
        the list of management certificates. Management certificates, which
        are also known as subscription certificates, authenticate clients
        attempting to connect to resources associated with your Windows Azure
        subscription.

        thumbprint:
            The thumb print that uniquely identifies the management
            certificate.
        '''
        _validate_not_none('thumbprint', thumbprint)
        return self._perform_delete(
            '/' + self.subscription_id + '/certificates/' + _str(thumbprint))

    #--Operations for affinity groups ------------------------------------
    def list_affinity_groups(self):
        '''
        Lists the affinity groups associated with the specified subscription.
        '''
        return self._perform_get(
            '/' + self.subscription_id + '/affinitygroups',
            AffinityGroups)

    def get_affinity_group_properties(self, affinity_group_name):
        '''
        Returns the system properties associated with the specified affinity
        group.

        affinity_group_name: The name of the affinity group.
        '''
        _validate_not_none('affinity_group_name', affinity_group_name)
        return self._perform_get(
            '/' + self.subscription_id + '/affinitygroups/' +
            _str(affinity_group_name) + '',
            AffinityGroup)

    def create_affinity_group(self, name, label, location, description=None):
        '''
        Creates a new affinity group for the specified subscription.

        name: A name for the affinity group that is unique to the subscription.
        label:
            A name for the affinity group. The name can be up to 100 characters
            in length.
        location:
            The data center location where the affinity group will be created.
            To list available locations, use the list_location function.
        description:
            A description for the affinity group. The description can be up to
            1024 characters in length.
        '''
        _validate_not_none('name', name)
        _validate_not_none('label', label)
        _validate_not_none('location', location)
        return self._perform_post(
            '/' + self.subscription_id + '/affinitygroups',
            _XmlSerializer.create_affinity_group_to_xml(name,
                                                        label,
                                                        description,
                                                        location))

    def update_affinity_group(self, affinity_group_name, label,
                              description=None):
        '''
        Updates the label and/or the description for an affinity group for the
        specified subscription.

        affinity_group_name: The name of the affinity group.
        label:
            A name for the affinity group. The name can be up to 100 characters
            in length.
        description:
            A description for the affinity group. The description can be up to
            1024 characters in length.
        '''
        _validate_not_none('affinity_group_name', affinity_group_name)
        _validate_not_none('label', label)
        return self._perform_put(
            '/' + self.subscription_id + '/affinitygroups/' +
            _str(affinity_group_name),
            _XmlSerializer.update_affinity_group_to_xml(label, description))

    def delete_affinity_group(self, affinity_group_name):
        '''
        Deletes an affinity group in the specified subscription.

        affinity_group_name: The name of the affinity group.
        '''
        _validate_not_none('affinity_group_name', affinity_group_name)
        return self._perform_delete('/' + self.subscription_id + \
                                    '/affinitygroups/' + \
                                    _str(affinity_group_name))

    #--Operations for locations ------------------------------------------
    def list_locations(self):
        '''
        Lists all of the data center locations that are valid for your
        subscription.
        '''
        return self._perform_get('/' + self.subscription_id + '/locations',
                                 Locations)

    #--Operations for tracking asynchronous requests ---------------------
    def get_operation_status(self, request_id):
        '''
        Returns the status of the specified operation. After calling an
        asynchronous operation, you can call Get Operation Status to determine
        whether the operation has succeeded, failed, or is still in progress.

        request_id: The request ID for the request you wish to track.
        '''
        _validate_not_none('request_id', request_id)
        return self._perform_get(
            '/' + self.subscription_id + '/operations/' + _str(request_id),
            Operation)

    #--Operations for retrieving operating system information ------------
    def list_operating_systems(self):
        '''
        Lists the versions of the guest operating system that are currently
        available in Windows Azure.
        '''
        return self._perform_get(
            '/' + self.subscription_id + '/operatingsystems',
            OperatingSystems)

    def list_operating_system_families(self):
        '''
        Lists the guest operating system families available in Windows Azure,
        and also lists the operating system versions available for each family.
        '''
        return self._perform_get(
            '/' + self.subscription_id + '/operatingsystemfamilies',
            OperatingSystemFamilies)

    #--Operations for retrieving subscription history --------------------
    def get_subscription(self):
        '''
        Returns account and resource allocation information on the specified
        subscription.
        '''
        return self._perform_get('/' + self.subscription_id + '',
                                 Subscription)

    #--Operations for virtual machines -----------------------------------
    def get_role(self, service_name, deployment_name, role_name):
        '''
        Retrieves the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        return self._perform_get(
            self._get_role_path(service_name, deployment_name, role_name),
            PersistentVMRole)

    def create_virtual_machine_deployment(self, service_name, deployment_name,
                                          deployment_slot, label, role_name,
                                          system_config, os_virtual_hard_disk,
                                          network_config=None,
                                          availability_set_name=None,
                                          data_virtual_hard_disks=None,
                                          role_size=None,
                                          role_type='PersistentVMRole',
                                          virtual_network_name=None):
        '''
        Provisions a virtual machine based on the supplied configuration.

        service_name: Name of the hosted service.
        deployment_name:
            The name for the deployment. The deployment name must be unique
            among other deployments for the hosted service.
        deployment_slot:
            The environment to which the hosted service is deployed. Valid
            values are: staging, production
        label:
            Specifies an identifier for the deployment. The label can be up to
            100 characters long. The label can be used for tracking purposes.
        role_name: The name of the role.
        system_config:
            Contains the metadata required to provision a virtual machine from
            a Windows or Linux OS image.  Use an instance of
            WindowsConfigurationSet or LinuxConfigurationSet.
        os_virtual_hard_disk:
            Contains the parameters Windows Azure uses to create the operating
            system disk for the virtual machine.
        network_config:
            Encapsulates the metadata required to create the virtual network
            configuration for a virtual machine. If you do not include a
            network configuration set you will not be able to access the VM
            through VIPs over the internet. If your virtual machine belongs to
            a virtual network you can not specify which subnet address space
            it resides under.
        availability_set_name:
            Specifies the name of an availability set to which to add the
            virtual machine. This value controls the virtual machine
            allocation in the Windows Azure environment. Virtual machines
            specified in the same availability set are allocated to different
            nodes to maximize availability.
        data_virtual_hard_disks:
            Contains the parameters Windows Azure uses to create a data disk
            for a virtual machine.
        role_size:
            The size of the virtual machine to allocate. The default value is
            Small. Possible values are: ExtraSmall, Small, Medium, Large,
            ExtraLarge. The specified value must be compatible with the disk
            selected in the OSVirtualHardDisk values.
        role_type:
            The type of the role for the virtual machine. The only supported
            value is PersistentVMRole.
        virtual_network_name:
            Specifies the name of an existing virtual network to which the
            deployment will belong.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('deployment_slot', deployment_slot)
        _validate_not_none('label', label)
        _validate_not_none('role_name', role_name)
        _validate_not_none('system_config', system_config)
        _validate_not_none('os_virtual_hard_disk', os_virtual_hard_disk)
        return self._perform_post(
            self._get_deployment_path_using_name(service_name),
            _XmlSerializer.virtual_machine_deployment_to_xml(
                deployment_name,
                deployment_slot,
                label,
                role_name,
                system_config,
                os_virtual_hard_disk,
                role_type,
                network_config,
                availability_set_name,
                data_virtual_hard_disks,
                role_size,
                virtual_network_name),
            async=True)

    def add_role(self, service_name, deployment_name, role_name, system_config,
                 os_virtual_hard_disk, network_config=None,
                 availability_set_name=None, data_virtual_hard_disks=None,
                 role_size=None, role_type='PersistentVMRole'):
        '''
        Adds a virtual machine to an existing deployment.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        system_config:
            Contains the metadata required to provision a virtual machine from
            a Windows or Linux OS image.  Use an instance of
            WindowsConfigurationSet or LinuxConfigurationSet.
        os_virtual_hard_disk:
            Contains the parameters Windows Azure uses to create the operating
            system disk for the virtual machine.
        network_config:
            Encapsulates the metadata required to create the virtual network
            configuration for a virtual machine. If you do not include a
            network configuration set you will not be able to access the VM
            through VIPs over the internet. If your virtual machine belongs to
            a virtual network you can not specify which subnet address space
            it resides under.
        availability_set_name:
            Specifies the name of an availability set to which to add the
            virtual machine. This value controls the virtual machine allocation
            in the Windows Azure environment. Virtual machines specified in the
            same availability set are allocated to different nodes to maximize
            availability.
        data_virtual_hard_disks:
            Contains the parameters Windows Azure uses to create a data disk
            for a virtual machine.
        role_size:
            The size of the virtual machine to allocate. The default value is
            Small. Possible values are: ExtraSmall, Small, Medium, Large,
            ExtraLarge. The specified value must be compatible with the disk
            selected in the OSVirtualHardDisk values.
        role_type:
            The type of the role for the virtual machine. The only supported
            value is PersistentVMRole.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('system_config', system_config)
        _validate_not_none('os_virtual_hard_disk', os_virtual_hard_disk)
        return self._perform_post(
            self._get_role_path(service_name, deployment_name),
            _XmlSerializer.add_role_to_xml(
                role_name,
                system_config,
                os_virtual_hard_disk,
                role_type,
                network_config,
                availability_set_name,
                data_virtual_hard_disks,
                role_size),
            async=True)

    def update_role(self, service_name, deployment_name, role_name,
                    os_virtual_hard_disk=None, network_config=None,
                    availability_set_name=None, data_virtual_hard_disks=None,
                    role_size=None, role_type='PersistentVMRole'):
        '''
        Updates the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        os_virtual_hard_disk:
            Contains the parameters Windows Azure uses to create the operating
            system disk for the virtual machine.
        network_config:
            Encapsulates the metadata required to create the virtual network
            configuration for a virtual machine. If you do not include a
            network configuration set you will not be able to access the VM
            through VIPs over the internet. If your virtual machine belongs to
            a virtual network you can not specify which subnet address space
            it resides under.
        availability_set_name:
            Specifies the name of an availability set to which to add the
            virtual machine. This value controls the virtual machine allocation
            in the Windows Azure environment. Virtual machines specified in the
            same availability set are allocated to different nodes to maximize
            availability.
        data_virtual_hard_disks:
            Contains the parameters Windows Azure uses to create a data disk
            for a virtual machine.
        role_size:
            The size of the virtual machine to allocate. The default value is
            Small. Possible values are: ExtraSmall, Small, Medium, Large,
            ExtraLarge. The specified value must be compatible with the disk
            selected in the OSVirtualHardDisk values.
        role_type:
            The type of the role for the virtual machine. The only supported
            value is PersistentVMRole.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        return self._perform_put(
            self._get_role_path(service_name, deployment_name, role_name),
            _XmlSerializer.update_role_to_xml(
                role_name,
                os_virtual_hard_disk,
                role_type,
                network_config,
                availability_set_name,
                data_virtual_hard_disks,
                role_size),
            async=True)

    def delete_role(self, service_name, deployment_name, role_name):
        '''
        Deletes the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        return self._perform_delete(
            self._get_role_path(service_name, deployment_name, role_name),
            async=True)

    def capture_role(self, service_name, deployment_name, role_name,
                     post_capture_action, target_image_name,
                     target_image_label, provisioning_configuration=None):
        '''
        The Capture Role operation captures a virtual machine image to your
        image gallery. From the captured image, you can create additional
        customized virtual machines.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        post_capture_action:
            Specifies the action after capture operation completes. Possible
            values are: Delete, Reprovision.
        target_image_name:
            Specifies the image name of the captured virtual machine.
        target_image_label:
            Specifies the friendly name of the captured virtual machine.
        provisioning_configuration:
            Use an instance of WindowsConfigurationSet or LinuxConfigurationSet.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('post_capture_action', post_capture_action)
        _validate_not_none('target_image_name', target_image_name)
        _validate_not_none('target_image_label', target_image_label)
        return self._perform_post(
            self._get_role_instance_operations_path(
                service_name, deployment_name, role_name),
            _XmlSerializer.capture_role_to_xml(
                post_capture_action,
                target_image_name,
                target_image_label,
                provisioning_configuration),
            async=True)

    def start_role(self, service_name, deployment_name, role_name):
        '''
        Starts the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        return self._perform_post(
            self._get_role_instance_operations_path(
                service_name, deployment_name, role_name),
            _XmlSerializer.start_role_operation_to_xml(),
            async=True)

    def start_roles(self, service_name, deployment_name, role_names):
        '''
        Starts the specified virtual machines.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_names: The names of the roles, as an enumerable of strings.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_names', role_names)
        return self._perform_post(
            self._get_roles_operations_path(service_name, deployment_name),
            _XmlSerializer.start_roles_operation_to_xml(role_names),
            async=True)

    def restart_role(self, service_name, deployment_name, role_name):
        '''
        Restarts the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        return self._perform_post(
            self._get_role_instance_operations_path(
                service_name, deployment_name, role_name),
            _XmlSerializer.restart_role_operation_to_xml(
            ),
            async=True)

    def shutdown_role(self, service_name, deployment_name, role_name,
                      post_shutdown_action='Stopped'):
        '''
        Shuts down the specified virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        post_shutdown_action:
            Specifies how the Virtual Machine should be shut down. Values are:
                Stopped
                    Shuts down the Virtual Machine but retains the compute
                    resources. You will continue to be billed for the resources
                    that the stopped machine uses.
                StoppedDeallocated
                    Shuts down the Virtual Machine and releases the compute
                    resources. You are not billed for the compute resources that
                    this Virtual Machine uses. If a static Virtual Network IP
                    address is assigned to the Virtual Machine, it is reserved.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('post_shutdown_action', post_shutdown_action)
        return self._perform_post(
            self._get_role_instance_operations_path(
                service_name, deployment_name, role_name),
            _XmlSerializer.shutdown_role_operation_to_xml(post_shutdown_action),
            async=True)

    def shutdown_roles(self, service_name, deployment_name, role_names,
                       post_shutdown_action='Stopped'):
        '''
        Shuts down the specified virtual machines.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_names: The names of the roles, as an enumerable of strings.
        post_shutdown_action:
            Specifies how the Virtual Machine should be shut down. Values are:
                Stopped
                    Shuts down the Virtual Machine but retains the compute
                    resources. You will continue to be billed for the resources
                    that the stopped machine uses.
                StoppedDeallocated
                    Shuts down the Virtual Machine and releases the compute
                    resources. You are not billed for the compute resources that
                    this Virtual Machine uses. If a static Virtual Network IP
                    address is assigned to the Virtual Machine, it is reserved.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_names', role_names)
        _validate_not_none('post_shutdown_action', post_shutdown_action)
        return self._perform_post(
            self._get_roles_operations_path(service_name, deployment_name),
            _XmlSerializer.shutdown_roles_operation_to_xml(
                role_names, post_shutdown_action),
            async=True)

    #--Operations for virtual machine images -----------------------------
    def list_os_images(self):
        '''
        Retrieves a list of the OS images from the image repository.
        '''
        return self._perform_get(self._get_image_path(),
                                 Images)

    def get_os_image(self, image_name):
        '''
        Retrieves an OS image from the image repository.
        '''
        return self._perform_get(self._get_image_path(image_name),
                                 OSImage)

    def add_os_image(self, label, media_link, name, os):
        '''
        Adds an OS image that is currently stored in a storage account in your
        subscription to the image repository.

        label: Specifies the friendly name of the image.
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the image is located. The blob location must
            belong to a storage account in the subscription specified by the
            <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        name:
            Specifies a name for the OS image that Windows Azure uses to
            identify the image when creating one or more virtual machines.
        os:
            The operating system type of the OS image. Possible values are:
            Linux, Windows
        '''
        _validate_not_none('label', label)
        _validate_not_none('media_link', media_link)
        _validate_not_none('name', name)
        _validate_not_none('os', os)
        return self._perform_post(self._get_image_path(),
                                  _XmlSerializer.os_image_to_xml(
                                      label, media_link, name, os),
                                  async=True)

    def update_os_image(self, image_name, label, media_link, name, os):
        '''
        Updates an OS image that in your image repository.

        image_name: The name of the image to update.
        label:
            Specifies the friendly name of the image to be updated. You cannot
            use this operation to update images provided by the Windows Azure
            platform.
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the image is located. The blob location must
            belong to a storage account in the subscription specified by the
            <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        name:
            Specifies a name for the OS image that Windows Azure uses to
            identify the image when creating one or more VM Roles.
        os:
            The operating system type of the OS image. Possible values are:
            Linux, Windows
        '''
        _validate_not_none('image_name', image_name)
        _validate_not_none('label', label)
        _validate_not_none('media_link', media_link)
        _validate_not_none('name', name)
        _validate_not_none('os', os)
        return self._perform_put(self._get_image_path(image_name),
                                 _XmlSerializer.os_image_to_xml(
                                     label, media_link, name, os),
                                 async=True)

    def delete_os_image(self, image_name, delete_vhd=False):
        '''
        Deletes the specified OS image from your image repository.

        image_name: The name of the image.
        delete_vhd: Deletes the underlying vhd blob in Azure storage.
        '''
        _validate_not_none('image_name', image_name)
        path = self._get_image_path(image_name)
        if delete_vhd:
            path += '?comp=media'
        return self._perform_delete(path, async=True)

    #--Operations for virtual machine disks ------------------------------
    def get_data_disk(self, service_name, deployment_name, role_name, lun):
        '''
        Retrieves the specified data disk from a virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        lun: The Logical Unit Number (LUN) for the disk.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('lun', lun)
        return self._perform_get(
            self._get_data_disk_path(
                service_name, deployment_name, role_name, lun),
            DataVirtualHardDisk)

    def add_data_disk(self, service_name, deployment_name, role_name, lun,
                      host_caching=None, media_link=None, disk_label=None,
                      disk_name=None, logical_disk_size_in_gb=None,
                      source_media_link=None):
        '''
        Adds a data disk to a virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        lun:
            Specifies the Logical Unit Number (LUN) for the disk. The LUN
            specifies the slot in which the data drive appears when mounted
            for usage by the virtual machine. Valid LUN values are 0 through 15.
        host_caching:
            Specifies the platform caching behavior of data disk blob for
            read/write efficiency. The default vault is ReadOnly. Possible
            values are: None, ReadOnly, ReadWrite
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the disk is located. The blob location must
            belong to the storage account in the subscription specified by the
            <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        disk_label:
            Specifies the description of the data disk. When you attach a disk,
            either by directly referencing a media using the MediaLink element
            or specifying the target disk size, you can use the DiskLabel
            element to customize the name property of the target data disk.
        disk_name:
            Specifies the name of the disk. Windows Azure uses the specified
            disk to create the data disk for the machine and populates this
            field with the disk name.
        logical_disk_size_in_gb:
            Specifies the size, in GB, of an empty disk to be attached to the
            role. The disk can be created as part of disk attach or create VM
            role call by specifying the value for this property. Windows Azure
            creates the empty disk based on size preference and attaches the
            newly created disk to the Role.
        source_media_link:
            Specifies the location of a blob in account storage which is
            mounted as a data disk when the virtual machine is created.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('lun', lun)
        return self._perform_post(
            self._get_data_disk_path(service_name, deployment_name, role_name),
            _XmlSerializer.data_virtual_hard_disk_to_xml(
                host_caching,
                disk_label,
                disk_name,
                lun,
                logical_disk_size_in_gb,
                media_link,
                source_media_link),
            async=True)

    def update_data_disk(self, service_name, deployment_name, role_name, lun,
                         host_caching=None, media_link=None, updated_lun=None,
                         disk_label=None, disk_name=None,
                         logical_disk_size_in_gb=None):
        '''
        Updates the specified data disk attached to the specified virtual
        machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        lun:
            Specifies the Logical Unit Number (LUN) for the disk. The LUN
            specifies the slot in which the data drive appears when mounted
            for usage by the virtual machine. Valid LUN values are 0 through
            15.
        host_caching:
            Specifies the platform caching behavior of data disk blob for
            read/write efficiency. The default vault is ReadOnly. Possible
            values are: None, ReadOnly, ReadWrite
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the disk is located. The blob location must
            belong to the storage account in the subscription specified by
            the <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        updated_lun:
            Specifies the Logical Unit Number (LUN) for the disk. The LUN
            specifies the slot in which the data drive appears when mounted
            for usage by the virtual machine. Valid LUN values are 0 through 15.
        disk_label:
            Specifies the description of the data disk. When you attach a disk,
            either by directly referencing a media using the MediaLink element
            or specifying the target disk size, you can use the DiskLabel
            element to customize the name property of the target data disk.
        disk_name:
            Specifies the name of the disk. Windows Azure uses the specified
            disk to create the data disk for the machine and populates this
            field with the disk name.
        logical_disk_size_in_gb:
            Specifies the size, in GB, of an empty disk to be attached to the
            role. The disk can be created as part of disk attach or create VM
            role call by specifying the value for this property. Windows Azure
            creates the empty disk based on size preference and attaches the
            newly created disk to the Role.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('lun', lun)
        return self._perform_put(
            self._get_data_disk_path(
                service_name, deployment_name, role_name, lun),
            _XmlSerializer.data_virtual_hard_disk_to_xml(
                host_caching,
                disk_label,
                disk_name,
                updated_lun,
                logical_disk_size_in_gb,
                media_link,
                None),
            async=True)

    def delete_data_disk(self, service_name, deployment_name, role_name, lun, delete_vhd=False):
        '''
        Removes the specified data disk from a virtual machine.

        service_name: The name of the service.
        deployment_name: The name of the deployment.
        role_name: The name of the role.
        lun: The Logical Unit Number (LUN) for the disk.
        delete_vhd: Deletes the underlying vhd blob in Azure storage.
        '''
        _validate_not_none('service_name', service_name)
        _validate_not_none('deployment_name', deployment_name)
        _validate_not_none('role_name', role_name)
        _validate_not_none('lun', lun)
        path = self._get_data_disk_path(service_name, deployment_name, role_name, lun)
        if delete_vhd:
            path += '?comp=media'
        return self._perform_delete(path, async=True)

    #--Operations for virtual machine disks ------------------------------
    def list_disks(self):
        '''
        Retrieves a list of the disks in your image repository.
        '''
        return self._perform_get(self._get_disk_path(),
                                 Disks)

    def get_disk(self, disk_name):
        '''
        Retrieves a disk from your image repository.
        '''
        return self._perform_get(self._get_disk_path(disk_name),
                                 Disk)

    def add_disk(self, has_operating_system, label, media_link, name, os):
        '''
        Adds a disk to the user image repository. The disk can be an OS disk
        or a data disk.

        has_operating_system:
            Specifies whether the disk contains an operation system. Only a
            disk with an operating system installed can be mounted as OS Drive.
        label: Specifies the description of the disk.
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the disk is located. The blob location must
            belong to the storage account in the current subscription specified
            by the <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        name:
            Specifies a name for the disk. Windows Azure uses the name to
            identify the disk when creating virtual machines from the disk.
        os: The OS type of the disk. Possible values are: Linux, Windows
        '''
        _validate_not_none('has_operating_system', has_operating_system)
        _validate_not_none('label', label)
        _validate_not_none('media_link', media_link)
        _validate_not_none('name', name)
        _validate_not_none('os', os)
        return self._perform_post(self._get_disk_path(),
                                  _XmlSerializer.disk_to_xml(
                                      has_operating_system,
                                      label,
                                      media_link,
                                      name,
                                      os))

    def update_disk(self, disk_name, has_operating_system, label, media_link,
                    name, os):
        '''
        Updates an existing disk in your image repository.

        disk_name: The name of the disk to update.
        has_operating_system:
            Specifies whether the disk contains an operation system. Only a
            disk with an operating system installed can be mounted as OS Drive.
        label: Specifies the description of the disk.
        media_link:
            Specifies the location of the blob in Windows Azure blob store
            where the media for the disk is located. The blob location must
            belong to the storage account in the current subscription specified
            by the <subscription-id> value in the operation call. Example:
            http://example.blob.core.windows.net/disks/mydisk.vhd
        name:
            Specifies a name for the disk. Windows Azure uses the name to
            identify the disk when creating virtual machines from the disk.
        os: The OS type of the disk. Possible values are: Linux, Windows
        '''
        _validate_not_none('disk_name', disk_name)
        _validate_not_none('has_operating_system', has_operating_system)
        _validate_not_none('label', label)
        _validate_not_none('media_link', media_link)
        _validate_not_none('name', name)
        _validate_not_none('os', os)
        return self._perform_put(self._get_disk_path(disk_name),
                                 _XmlSerializer.disk_to_xml(
                                     has_operating_system,
                                     label,
                                     media_link,
                                     name,
                                     os))

    def delete_disk(self, disk_name, delete_vhd=False):
        '''
        Deletes the specified data or operating system disk from your image
        repository.

        disk_name: The name of the disk to delete.
        delete_vhd: Deletes the underlying vhd blob in Azure storage.
        '''
        _validate_not_none('disk_name', disk_name)
        path = self._get_disk_path(disk_name)
        if delete_vhd:
            path += '?comp=media'
        return self._perform_delete(path)

    #--Operations for virtual networks  ------------------------------
    def list_virtual_network_sites(self):
        '''
        Retrieves a list of the virtual networks.
        '''
        return self._perform_get(self._get_virtual_network_site_path(), VirtualNetworkSites)
  
      #--Helper functions --------------------------------------------------
    def _get_virtual_network_site_path(self):
        return self._get_path('services/networking/virtualnetwork', None)

    def _get_storage_service_path(self, service_name=None):
        return self._get_path('services/storageservices', service_name)

    def _get_hosted_service_path(self, service_name=None):
        return self._get_path('services/hostedservices', service_name)

    def _get_deployment_path_using_slot(self, service_name, slot=None):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deploymentslots', slot)

    def _get_deployment_path_using_name(self, service_name,
                                        deployment_name=None):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deployments', deployment_name)

    def _get_role_path(self, service_name, deployment_name, role_name=None):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deployments/' + deployment_name +
                              '/roles', role_name)

    def _get_role_instance_operations_path(self, service_name, deployment_name,
                                           role_name=None):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deployments/' + deployment_name +
                              '/roleinstances', role_name) + '/Operations'

    def _get_roles_operations_path(self, service_name, deployment_name):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deployments/' + deployment_name +
                              '/roles/Operations', None)

    def _get_data_disk_path(self, service_name, deployment_name, role_name,
                            lun=None):
        return self._get_path('services/hostedservices/' + _str(service_name) +
                              '/deployments/' + _str(deployment_name) +
                              '/roles/' + _str(role_name) + '/DataDisks', lun)

    def _get_disk_path(self, disk_name=None):
        return self._get_path('services/disks', disk_name)

    def _get_image_path(self, image_name=None):
        return self._get_path('services/images', image_name)
