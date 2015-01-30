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
from xml.dom import minidom
from azure import (
    WindowsAzureData,
    _Base64String,
    _create_entry,
    _dict_of,
    _encode_base64,
    _general_error_handler,
    _get_children_from_path,
    _get_first_child_node_value,
    _list_of,
    _scalar_list_of,
    _str,
    _xml_attribute,
    _get_entry_properties_from_node,
    _get_child_nodes,
    _get_serialization_name,
    )

#-----------------------------------------------------------------------------
# Constants for Azure app environment settings.
AZURE_MANAGEMENT_CERTFILE = 'AZURE_MANAGEMENT_CERTFILE'
AZURE_MANAGEMENT_SUBSCRIPTIONID = 'AZURE_MANAGEMENT_SUBSCRIPTIONID'

# x-ms-version for service management.
X_MS_VERSION = '2014-06-01'

#-----------------------------------------------------------------------------
# Data classes


class StorageServices(WindowsAzureData):

    def __init__(self):
        self.storage_services = _list_of(StorageService)

    def __iter__(self):
        return iter(self.storage_services)

    def __len__(self):
        return len(self.storage_services)

    def __getitem__(self, index):
        return self.storage_services[index]


class StorageService(WindowsAzureData):

    def __init__(self):
        self.url = ''
        self.service_name = ''
        self.storage_service_properties = StorageAccountProperties()
        self.storage_service_keys = StorageServiceKeys()
        self.extended_properties = _dict_of(
            'ExtendedProperty', 'Name', 'Value')
        self.capabilities = _scalar_list_of(str, 'Capability')


class StorageAccountProperties(WindowsAzureData):

    def __init__(self):
        self.description = u''
        self.affinity_group = u''
        self.location = u''
        self.label = _Base64String()
        self.status = u''
        self.endpoints = _scalar_list_of(str, 'Endpoint')
        self.geo_replication_enabled = False
        self.geo_primary_region = u''
        self.status_of_primary = u''
        self.geo_secondary_region = u''
        self.status_of_secondary = u''
        self.last_geo_failover_time = u''
        self.creation_time = u''
        self.account_type = u''


class StorageServiceKeys(WindowsAzureData):

    def __init__(self):
        self.primary = u''
        self.secondary = u''


class Locations(WindowsAzureData):

    def __init__(self):
        self.locations = _list_of(Location)

    def __iter__(self):
        return iter(self.locations)

    def __len__(self):
        return len(self.locations)

    def __getitem__(self, index):
        return self.locations[index]


class Location(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.display_name = u''
        self.available_services = _scalar_list_of(str, 'AvailableService')
        self.compute_capabilities = ComputeCapabilities()


class ComputeCapabilities(WindowsAzureData):

    def __init__(self):
        self.web_worker_role_sizes = _scalar_list_of(str, 'RoleSize')
        self.virtual_machines_role_sizes = _scalar_list_of(str, 'RoleSize')


class AffinityGroup(WindowsAzureData):

    def __init__(self):
        self.name = ''
        self.label = _Base64String()
        self.description = u''
        self.location = u''
        self.hosted_services = HostedServices()
        self.storage_services = StorageServices()
        self.capabilities = _scalar_list_of(str, 'Capability')


class AffinityGroups(WindowsAzureData):

    def __init__(self):
        self.affinity_groups = _list_of(AffinityGroup)

    def __iter__(self):
        return iter(self.affinity_groups)

    def __len__(self):
        return len(self.affinity_groups)

    def __getitem__(self, index):
        return self.affinity_groups[index]


class HostedServices(WindowsAzureData):

    def __init__(self):
        self.hosted_services = _list_of(HostedService)

    def __iter__(self):
        return iter(self.hosted_services)

    def __len__(self):
        return len(self.hosted_services)

    def __getitem__(self, index):
        return self.hosted_services[index]


class HostedService(WindowsAzureData):

    def __init__(self):
        self.url = u''
        self.service_name = u''
        self.hosted_service_properties = HostedServiceProperties()
        self.deployments = Deployments()


class HostedServiceProperties(WindowsAzureData):

    def __init__(self):
        self.description = u''
        self.location = u''
        self.affinity_group = u''
        self.label = _Base64String()
        self.status = u''
        self.date_created = u''
        self.date_last_modified = u''
        self.extended_properties = _dict_of(
            'ExtendedProperty', 'Name', 'Value')


class VirtualNetworkSites(WindowsAzureData):

    def __init__(self):
        self.virtual_network_sites = _list_of(VirtualNetworkSite)

    def __iter__(self):
        return iter(self.virtual_network_sites)

    def __len__(self):
        return len(self.virtual_network_sites)

    def __getitem__(self, index):
        return self.virtual_network_sites[index]


class VirtualNetworkSite(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.id = u''
        self.affinity_group = u''
        self.subnets = Subnets()


class Subnets(WindowsAzureData):

    def __init__(self):
        self.subnets = _list_of(Subnet)

    def __iter__(self):
        return iter(self.subnets)

    def __len__(self):
        return len(self.subnets)

    def __getitem__(self, index):
        return self.subnets[index]


class Subnet(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.address_prefix = u''



class Deployments(WindowsAzureData):

    def __init__(self):
        self.deployments = _list_of(Deployment)

    def __iter__(self):
        return iter(self.deployments)

    def __len__(self):
        return len(self.deployments)

    def __getitem__(self, index):
        return self.deployments[index]


class Deployment(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.deployment_slot = u''
        self.private_id = u''
        self.status = u''
        self.label = _Base64String()
        self.url = u''
        self.configuration = _Base64String()
        self.role_instance_list = RoleInstanceList()
        self.upgrade_status = UpgradeStatus()
        self.upgrade_domain_count = u''
        self.role_list = RoleList()
        self.sdk_version = u''
        self.input_endpoint_list = InputEndpoints()
        self.locked = False
        self.rollback_allowed = False
        self.persistent_vm_downtime_info = PersistentVMDowntimeInfo()
        self.created_time = u''
        self.virtual_network_name = u''
        self.last_modified_time = u''
        self.extended_properties = _dict_of(
            'ExtendedProperty', 'Name', 'Value')


class RoleInstanceList(WindowsAzureData):

    def __init__(self):
        self.role_instances = _list_of(RoleInstance)

    def __iter__(self):
        return iter(self.role_instances)

    def __len__(self):
        return len(self.role_instances)

    def __getitem__(self, index):
        return self.role_instances[index]


class RoleInstance(WindowsAzureData):

    def __init__(self):
        self.role_name = u''
        self.instance_name = u''
        self.instance_status = u''
        self.instance_upgrade_domain = 0
        self.instance_fault_domain = 0
        self.instance_size = u''
        self.instance_state_details = u''
        self.instance_error_code = u''
        self.ip_address = u''
        self.instance_endpoints = InstanceEndpoints()
        self.power_state = u''
        self.fqdn = u''
        self.host_name = u''
        self.public_ips = PublicIPs()

class InstanceEndpoints(WindowsAzureData):

    def __init__(self):
        self.instance_endpoints = _list_of(InstanceEndpoint)

    def __iter__(self):
        return iter(self.instance_endpoints)

    def __len__(self):
        return len(self.instance_endpoints)

    def __getitem__(self, index):
        return self.instance_endpoints[index]


class InstanceEndpoint(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.vip = u''
        self.public_port = u''
        self.local_port = u''
        self.protocol = u''


class UpgradeStatus(WindowsAzureData):

    def __init__(self):
        self.upgrade_type = u''
        self.current_upgrade_domain_state = u''
        self.current_upgrade_domain = u''


class InputEndpoints(WindowsAzureData):

    def __init__(self):
        self.input_endpoints = _list_of(InputEndpoint)

    def __iter__(self):
        return iter(self.input_endpoints)

    def __len__(self):
        return len(self.input_endpoints)

    def __getitem__(self, index):
        return self.input_endpoints[index]


class InputEndpoint(WindowsAzureData):

    def __init__(self):
        self.role_name = u''
        self.vip = u''
        self.port = u''


class RoleList(WindowsAzureData):

    def __init__(self):
        self.roles = _list_of(Role)

    def __iter__(self):
        return iter(self.roles)

    def __len__(self):
        return len(self.roles)

    def __getitem__(self, index):
        return self.roles[index]


class Role(WindowsAzureData):

    def __init__(self):
        self.role_name = u''
        self.role_type = u''
        self.os_version = u''
        self.configuration_sets = ConfigurationSets()
        self.availability_set_name = u''
        self.data_virtual_hard_disks = DataVirtualHardDisks()
        self.os_virtual_hard_disk = OSVirtualHardDisk()
        self.role_size = u''
        self.default_win_rm_certificate_thumbprint = u''


class CaptureRoleAsVMImage:

    def __init__(self, os_state=None, vm_image_name=None, vm_image_label=None,
                 description=None, language=None, image_family=None,
                 recommended_vm_size=None):
        self.os_state = os_state
        self.vm_image_name = vm_image_name
        self.vm_image_label = vm_image_label
        self.description = description
        self.language = language
        self.image_family = image_family
        self.recommended_vm_size = recommended_vm_size


class OSDiskConfiguration(WindowsAzureData):

    def __init__(self):
        self.name = None
        self.host_caching = None
        self.os_state = None
        self.os = None
        self.media_link = None
        self.logical_disk_size_in_gb = -1


class DataDiskConfigurations(WindowsAzureData):

    def __init__(self):
        self.data_disk_configurations = _list_of(DataDiskConfiguration)

    def __iter__(self):
        return iter(self.data_disk_configurations)

    def __len__(self):
        return len(self.data_disk_configurations)

    def __getitem__(self, index):
        return self.data_disk_configurations[index]


class DataDiskConfiguration(WindowsAzureData):

    def __init__(self):
        self.name = None
        self.host_caching = None
        self.lun = -1
        self.media_link = None
        self.logical_disk_size_in_gb = -1


class VMImages(WindowsAzureData):

    def __init__(self):
        self.vm_images = _list_of(VMImage)

    def __iter__(self):
        return iter(self.vm_images)

    def __len__(self):
        return len(self.vm_images)

    def __getitem__(self, index):
        return self.vm_images[index]


class VMImage(WindowsAzureData):

    def __init__(self, name=None, label=None, description=None):
        self.name = name
        self.label = label
        self.category = None # read-only
        self.description = description
        self.os_disk_configuration = OSDiskConfiguration()
        self.data_disk_configurations = DataDiskConfigurations()
        self.service_name = None # read-only
        self.deployment_name = None # read-only
        self.role_name = None # read-only
        self.location = None # read-only
        self.affinity_group = None # read-only
        self.created_time = None # read-only
        self.modified_time = None # read-only
        self.language = None
        self.image_family = None
        self.recommended_vm_size = None
        self.is_premium = False # read-only
        self.eula = None
        self.icon_uri = None
        self.small_icon_uri = None
        self.privacy_uri = None
        self.publisher_name = None # read-only
        self.published_date = None
        self.show_in_gui = False
        self.pricing_detail_link = None # read-only


class ResourceExtensions(WindowsAzureData):

    def __init__(self):
        self.resource_extensions = _list_of(ResourceExtension)

    def __iter__(self):
        return iter(self.resource_extensions)

    def __len__(self):
        return len(self.resource_extensions)

    def __getitem__(self, index):
        return self.resource_extensions[index]


class ResourceExtension(WindowsAzureData):

    def __init__(self):
        self.publisher = u''
        self.name = u''
        self.version = u''
        self.label = u''
        self.description = u''
        self.public_configuration_schema = u''
        self.private_configuration_schema = u''
        self.sample_config = u''
        self.replication_completed = False
        self.eula = u''
        self.privacy_uri = u''
        self.homepage_uri = u''
        self.is_json_extension = False
        self.is_internal_extension = False
        self.disallow_major_version_upgrade = False
        self.company_name = u''
        self.supported_os = u''
        self.published_date = u''


class ResourceExtensionParameterValues(WindowsAzureData):

    def __init__(self):
        self.resource_extension_parameter_values = _list_of(ResourceExtensionParameterValue)

    def __iter__(self):
        return iter(self.resource_extension_parameter_values)

    def __len__(self):
        return len(self.resource_extension_parameter_values)

    def __getitem__(self, index):
        return self.resource_extension_parameter_values[index]


class ResourceExtensionParameterValue(WindowsAzureData):

    def __init__(self):
        self.key = u''
        self.value = u''
        self.type = u''


class ResourceExtensionReferences(WindowsAzureData):

    def __init__(self):
        self.resource_extension_references = _list_of(ResourceExtensionReference)

    def __iter__(self):
        return iter(self.resource_extension_references)

    def __len__(self):
        return len(self.resource_extension_references)

    def __getitem__(self, index):
        return self.resource_extension_references[index]


class ResourceExtensionReference(WindowsAzureData):

    def __init__(self, reference_name=u'', publisher=u'', name=u'', version=u''):
        self.reference_name = reference_name
        self.publisher = publisher
        self.name = name
        self.version = version
        self.resource_extension_parameter_values = ResourceExtensionParameterValues()
        self.state = u''
        self.certificates = Certificates()


class AdditionalUnattendContent(WindowsAzureData):

    def __init__(self):
        self.passes = Passes()


class Passes(WindowsAzureData):

    def __init__(self):
        self.passes = _list_of(UnattendPass)

    def __iter__(self):
        return iter(self.passes)

    def __len__(self):
        return len(self.passes)

    def __getitem__(self, index):
        return self.passes[index]


class UnattendPass(WindowsAzureData):

    def __init__(self):
        self.pass_name = u''
        self.components = Components()


class Components(WindowsAzureData):

    def __init__(self):
        self.components = _list_of(UnattendComponent)

    def __iter__(self):
        return iter(self.components)

    def __len__(self):
        return len(self.components)

    def __getitem__(self, index):
        return self.components[index]


class UnattendComponent(WindowsAzureData):

    def __init__(self):
        self.component_name = u''
        self.component_settings = ComponentSettings()


class ComponentSettings(WindowsAzureData):

    def __init__(self):
        self.component_settings = _list_of(ComponentSetting)

    def __iter__(self):
        return iter(self.component_settings)

    def __len__(self):
        return len(self.component_settings)

    def __getitem__(self, index):
        return self.component_settings[index]


class ComponentSetting(WindowsAzureData):

    def __init__(self):
        self.setting_name = u''
        self.content = u''


class DnsServer(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.address = u''


class ReservedIPs(WindowsAzureData):

    def __init__(self):
        self.reserved_ips = _list_of(ReservedIP)

    def __iter__(self):
        return iter(self.reserved_ips)

    def __len__(self):
        return len(self.reserved_ips)

    def __getitem__(self, index):
        return self.reserved_ips[index]


class ReservedIP(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.address = u''
        self.id = u''
        self.label = u''
        self.state = u''
        self.in_use = False
        self.service_name = u''
        self.deployment_name = u''
        self.location = u''


class PersistentVMDowntimeInfo(WindowsAzureData):

    def __init__(self):
        self.start_time = u''
        self.end_time = u''
        self.status = u''


class Certificates(WindowsAzureData):

    def __init__(self):
        self.certificates = _list_of(Certificate)

    def __iter__(self):
        return iter(self.certificates)

    def __len__(self):
        return len(self.certificates)

    def __getitem__(self, index):
        return self.certificates[index]


class Certificate(WindowsAzureData):

    def __init__(self):
        self.certificate_url = u''
        self.thumbprint = u''
        self.thumbprint_algorithm = u''
        self.data = u''


class OperationError(WindowsAzureData):

    def __init__(self):
        self.code = u''
        self.message = u''


class Operation(WindowsAzureData):

    def __init__(self):
        self.id = u''
        self.status = u''
        self.http_status_code = u''
        self.error = OperationError()


class OperatingSystem(WindowsAzureData):

    def __init__(self):
        self.version = u''
        self.label = _Base64String()
        self.is_default = True
        self.is_active = True
        self.family = 0
        self.family_label = _Base64String()


class OperatingSystems(WindowsAzureData):

    def __init__(self):
        self.operating_systems = _list_of(OperatingSystem)

    def __iter__(self):
        return iter(self.operating_systems)

    def __len__(self):
        return len(self.operating_systems)

    def __getitem__(self, index):
        return self.operating_systems[index]


class OperatingSystemFamily(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.label = _Base64String()
        self.operating_systems = OperatingSystems()


class OperatingSystemFamilies(WindowsAzureData):

    def __init__(self):
        self.operating_system_families = _list_of(OperatingSystemFamily)

    def __iter__(self):
        return iter(self.operating_system_families)

    def __len__(self):
        return len(self.operating_system_families)

    def __getitem__(self, index):
        return self.operating_system_families[index]


class Subscriptions(WindowsAzureData):

    def __init__(self):
        self.subscriptions = _list_of(Subscription)

    def __iter__(self):
        return iter(self.subscriptions)

    def __len__(self):
        return len(self.subscriptions)

    def __getitem__(self, index):
        return self.subscriptions[index]


class Subscription(WindowsAzureData):

    def __init__(self):
        self.subscription_id = u''
        self.subscription_name = u''
        self.subscription_status = u''
        self.account_admin_live_email_id = u''
        self.service_admin_live_email_id = u''
        self.max_core_count = 0
        self.max_storage_accounts = 0
        self.max_hosted_services = 0
        self.current_core_count = 0
        self.current_hosted_services = 0
        self.current_storage_accounts = 0
        self.max_virtual_network_sites = 0
        self.current_virtual_network_sites = 0
        self.max_local_network_sites = 0
        self.max_dns_servers = 0
        self.aad_tenant_id = u''
        self.created_time = u''


class AvailabilityResponse(WindowsAzureData):

    def __init__(self):
        self.result = False
        self.reason = False


class SubscriptionCertificates(WindowsAzureData):

    def __init__(self):
        self.subscription_certificates = _list_of(SubscriptionCertificate)

    def __iter__(self):
        return iter(self.subscription_certificates)

    def __len__(self):
        return len(self.subscription_certificates)

    def __getitem__(self, index):
        return self.subscription_certificates[index]


class SubscriptionCertificate(WindowsAzureData):

    def __init__(self):
        self.subscription_certificate_public_key = u''
        self.subscription_certificate_thumbprint = u''
        self.subscription_certificate_data = u''
        self.created = u''


class RoleSizes(WindowsAzureData):

    def __init__(self):
        self.role_sizes = _list_of(RoleSize)

    def __iter__(self):
        return iter(self.role_sizes)

    def __len__(self):
        return len(self.role_sizes)

    def __getitem__(self, index):
        return self.role_sizes[index]


class RoleSize(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.label = u''
        self.cores = 0
        self.memory_in_mb = 0
        self.supported_by_web_worker_roles = False
        self.supported_by_virtual_machines = False
        self.max_data_disk_count = 0
        self.web_worker_resource_disk_size_in_mb = 0
        self.virtual_machine_resource_disk_size_in_mb = 0


class Images(WindowsAzureData):

    def __init__(self):
        self.images = _list_of(OSImage)

    def __iter__(self):
        return iter(self.images)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        return self.images[index]


class OSImage(WindowsAzureData):

    def __init__(self):
        self.affinity_group = u''
        self.category = u''
        self.location = u''
        self.logical_size_in_gb = 0
        self.label = u''
        self.media_link = u''
        self.name = u''
        self.os = u''
        self.eula = u''
        self.description = u''
        self.image_family = u''
        self.show_in_gui = True
        self.published_date = u''
        self.is_premium = True
        self.icon_uri = u''
        self.privacy_uri = u''
        self.recommended_vm_size = u''
        self.publisher_name = u''
        self.pricing_detail_link = u''
        self.small_icon_uri = u''
        self.os_state = u''
        self.language = u''


class Disks(WindowsAzureData):

    def __init__(self):
        self.disks = _list_of(Disk)

    def __iter__(self):
        return iter(self.disks)

    def __len__(self):
        return len(self.disks)

    def __getitem__(self, index):
        return self.disks[index]


class Disk(WindowsAzureData):

    def __init__(self):
        self.affinity_group = u''
        self.attached_to = AttachedTo()
        self.has_operating_system = u''
        self.is_corrupted = u''
        self.location = u''
        self.logical_disk_size_in_gb = 0
        self.label = u''
        self.media_link = u''
        self.name = u''
        self.os = u''
        self.source_image_name = u''


class AttachedTo(WindowsAzureData):

    def __init__(self):
        self.hosted_service_name = u''
        self.deployment_name = u''
        self.role_name = u''


class PersistentVMRole(WindowsAzureData):

    def __init__(self):
        self.role_name = u''
        self.role_type = u''
        self.os_version = u''  # undocumented
        self.configuration_sets = ConfigurationSets()
        self.availability_set_name = u''
        self.data_virtual_hard_disks = DataVirtualHardDisks()
        self.os_virtual_hard_disk = OSVirtualHardDisk()
        self.role_size = u''
        self.default_win_rm_certificate_thumbprint = u''


class ConfigurationSets(WindowsAzureData):

    def __init__(self):
        self.configuration_sets = _list_of(ConfigurationSet)

    def __iter__(self):
        return iter(self.configuration_sets)

    def __len__(self):
        return len(self.configuration_sets)

    def __getitem__(self, index):
        return self.configuration_sets[index]


class PublicIPs(WindowsAzureData):

    def __init__(self):
        self.public_ips = _list_of(PublicIP)

    def __iter__(self):
        return iter(self.public_ips)

    def __len__(self):
        return len(self.public_ips)

    def __getitem__(self, index):
        return self.public_ips[index]


class PublicIP(WindowsAzureData):

    def __init__(self, name=u''):
        self.name = name
        self.idle_timeout_in_minutes = 4
        self.address = None

class ConfigurationSet(WindowsAzureData):

    def __init__(self):
        self.configuration_set_type = u'NetworkConfiguration'
        self.role_type = u''
        self.input_endpoints = ConfigurationSetInputEndpoints()
        self.subnet_names = _scalar_list_of(str, 'SubnetName')
        self.public_ips = PublicIPs()


class ConfigurationSetInputEndpoints(WindowsAzureData):

    def __init__(self):
        self.input_endpoints = _list_of(
            ConfigurationSetInputEndpoint, 'InputEndpoint')

    def __iter__(self):
        return iter(self.input_endpoints)

    def __len__(self):
        return len(self.input_endpoints)

    def __getitem__(self, index):
        return self.input_endpoints[index]


class ConfigurationSetInputEndpoint(WindowsAzureData):

    '''
    Initializes a network configuration input endpoint.

    name: Specifies the name for the external endpoint.
    protocol:
        Specifies the protocol to use to inspect the virtual machine
        availability status. Possible values are: HTTP, TCP.
    port: Specifies the external port to use for the endpoint.
    local_port:
        Specifies the internal port on which the virtual machine is listening
        to serve the endpoint.
    load_balanced_endpoint_set_name:
        Specifies a name for a set of load-balanced endpoints. Specifying this
        element for a given endpoint adds it to the set. If you are setting an
        endpoint to use to connect to the virtual machine via the Remote
        Desktop, do not set this property.
    enable_direct_server_return:
        Specifies whether direct server return load balancing is enabled.
    '''

    def __init__(self, name=u'', protocol=u'', port=u'', local_port=u'',
                 load_balanced_endpoint_set_name=u'',
                 enable_direct_server_return=False):
        self.enable_direct_server_return = enable_direct_server_return
        self.load_balanced_endpoint_set_name = load_balanced_endpoint_set_name
        self.local_port = local_port
        self.name = name
        self.port = port
        self.load_balancer_probe = LoadBalancerProbe()
        self.protocol = protocol


class WindowsConfigurationSet(WindowsAzureData):

    def __init__(self, computer_name=None, admin_password=None,
                 reset_password_on_first_logon=None,
                 enable_automatic_updates=None, time_zone=None,
                 admin_username=None, custom_data=None):
        self.configuration_set_type = u'WindowsProvisioningConfiguration'
        self.computer_name = computer_name
        self.admin_password = admin_password
        self.admin_username = admin_username
        self.reset_password_on_first_logon = reset_password_on_first_logon
        self.enable_automatic_updates = enable_automatic_updates
        self.time_zone = time_zone
        self.domain_join = DomainJoin()
        self.stored_certificate_settings = StoredCertificateSettings()
        self.win_rm = WinRM()
        self.custom_data = custom_data
        self.additional_unattend_content = AdditionalUnattendContent()


class DomainJoin(WindowsAzureData):

    def __init__(self):
        self.credentials = Credentials()
        self.join_domain = u''
        self.machine_object_ou = u''


class Credentials(WindowsAzureData):

    def __init__(self):
        self.domain = u''
        self.username = u''
        self.password = u''


class StoredCertificateSettings(WindowsAzureData):

    def __init__(self):
        self.stored_certificate_settings = _list_of(CertificateSetting)

    def __iter__(self):
        return iter(self.stored_certificate_settings)

    def __len__(self):
        return len(self.stored_certificate_settings)

    def __getitem__(self, index):
        return self.stored_certificate_settings[index]


class CertificateSetting(WindowsAzureData):

    '''
    Initializes a certificate setting.

    thumbprint:
        Specifies the thumbprint of the certificate to be provisioned. The
        thumbprint must specify an existing service certificate.
    store_name:
        Specifies the name of the certificate store from which retrieve
        certificate.
    store_location:
        Specifies the target certificate store location on the virtual machine.
        The only supported value is LocalMachine.
    '''

    def __init__(self, thumbprint=u'', store_name=u'', store_location=u''):
        self.thumbprint = thumbprint
        self.store_name = store_name
        self.store_location = store_location


class WinRM(WindowsAzureData):

    '''
    Contains configuration settings for the Windows Remote Management service on
    the Virtual Machine.
    '''

    def __init__(self):
        self.listeners = Listeners()


class Listeners(WindowsAzureData):

    def __init__(self):
        self.listeners = _list_of(Listener)

    def __iter__(self):
        return iter(self.listeners)

    def __len__(self):
        return len(self.listeners)

    def __getitem__(self, index):
        return self.listeners[index]


class Listener(WindowsAzureData):

    '''
    Specifies the protocol and certificate information for the listener.

    protocol:
        Specifies the protocol of listener.  Possible values are: Http, Https.
        The value is case sensitive.
    certificate_thumbprint:
        Optional. Specifies the certificate thumbprint for the secure
        connection. If this value is not specified, a self-signed certificate is
        generated and used for the Virtual Machine.
    '''

    def __init__(self, protocol=u'', certificate_thumbprint=u''):
        self.protocol = protocol
        self.certificate_thumbprint = certificate_thumbprint


class LinuxConfigurationSet(WindowsAzureData):

    def __init__(self, host_name=None, user_name=None, user_password=None,
                 disable_ssh_password_authentication=None, custom_data=None):
        self.configuration_set_type = u'LinuxProvisioningConfiguration'
        self.host_name = host_name
        self.user_name = user_name
        self.user_password = user_password
        self.disable_ssh_password_authentication =\
            disable_ssh_password_authentication
        self.ssh = SSH()
        self.custom_data = custom_data


class SSH(WindowsAzureData):

    def __init__(self):
        self.public_keys = PublicKeys()
        self.key_pairs = KeyPairs()


class PublicKeys(WindowsAzureData):

    def __init__(self):
        self.public_keys = _list_of(PublicKey)

    def __iter__(self):
        return iter(self.public_keys)

    def __len__(self):
        return len(self.public_keys)

    def __getitem__(self, index):
        return self.public_keys[index]


class PublicKey(WindowsAzureData):

    def __init__(self, fingerprint=u'', path=u''):
        self.fingerprint = fingerprint
        self.path = path


class KeyPairs(WindowsAzureData):

    def __init__(self):
        self.key_pairs = _list_of(KeyPair)

    def __iter__(self):
        return iter(self.key_pairs)

    def __len__(self):
        return len(self.key_pairs)

    def __getitem__(self, index):
        return self.key_pairs[index]


class KeyPair(WindowsAzureData):

    def __init__(self, fingerprint=u'', path=u''):
        self.fingerprint = fingerprint
        self.path = path


class LoadBalancerProbe(WindowsAzureData):

    def __init__(self):
        self.path = u''
        self.port = u''
        self.protocol = u''


class DataVirtualHardDisks(WindowsAzureData):

    def __init__(self):
        self.data_virtual_hard_disks = _list_of(DataVirtualHardDisk)

    def __iter__(self):
        return iter(self.data_virtual_hard_disks)

    def __len__(self):
        return len(self.data_virtual_hard_disks)

    def __getitem__(self, index):
        return self.data_virtual_hard_disks[index]


class DataVirtualHardDisk(WindowsAzureData):

    def __init__(self):
        self.host_caching = None
        self.disk_label = u''
        self.disk_name = u''
        self.lun = 0
        self.logical_disk_size_in_gb = 0
        self.media_link = u''


class OSVirtualHardDisk(WindowsAzureData):

    def __init__(self, source_image_name=None, media_link=None,
                 host_caching=None, disk_label=None, disk_name=None,
                 os=None, remote_source_image_link=None):
        self.source_image_name = source_image_name
        self.media_link = media_link
        self.host_caching = host_caching
        self.disk_label = disk_label
        self.disk_name = disk_name
        self.os = os
        self.remote_source_image_link = remote_source_image_link

class AsynchronousOperationResult(WindowsAzureData):

    def __init__(self, request_id=None):
        self.request_id = request_id


class ServiceBusRegion(WindowsAzureData):

    def __init__(self):
        self.code = u''
        self.fullname = u''


class ServiceBusNamespace(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.region = u''
        self.default_key = u''
        self.status = u''
        self.created_at = u''
        self.acs_management_endpoint = u''
        self.servicebus_endpoint = u''
        self.connection_string = u''
        self.subscription_id = u''
        self.enabled = False


class MetricProperties(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.primary_aggregation = u''
        self.unit = u''
        self.display_name = u''


class MetricValues(WindowsAzureData):

    def __init__(self):
        self.timestamp = u''
        self.min = 0
        self.max = 0
        self.average = 0
        self.total = 0


class MetricRollups(WindowsAzureData):

    def __init__(self):
        self.time_grain = u''
        self.retention = u''


class WebSpaces(WindowsAzureData):

    def __init__(self):
        self.web_space = _list_of(WebSpace)

    def __iter__(self):
        return iter(self.web_space)

    def __len__(self):
        return len(self.web_space)

    def __getitem__(self, index):
        return self.web_space[index]
    

class WebSpace(WindowsAzureData):
    
    def __init__(self):
        self.availability_state = u''
        self.geo_location = u''
        self.geo_region = u''
        self.name = u''
        self.plan = u''
        self.status = u''
        self.subscription = u''


class Sites(WindowsAzureData):

    def __init__(self):
        self.site = _list_of(Site)

    def __iter__(self):
        return iter(self.site)

    def __len__(self):
        return len(self.site)

    def __getitem__(self, index):
        return self.site[index]
    

class Site(WindowsAzureData):
    
    def __init__(self):
        self.admin_enabled = False
        self.availability_state = ''
        self.compute_mode = ''
        self.enabled = False
        self.enabled_host_names = _scalar_list_of(str, 'a:string')
        self.host_name_ssl_states = HostNameSslStates()
        self.host_names = _scalar_list_of(str, 'a:string')
        self.last_modified_time_utc = ''
        self.name = ''
        self.repository_site_name = ''
        self.self_link = ''
        self.server_farm = ''
        self.site_mode = ''
        self.state = ''
        self.storage_recovery_default_state = ''
        self.usage_state = ''
        self.web_space = ''


class HostNameSslStates(WindowsAzureData):

    def __init__(self):
        self.host_name_ssl_state = _list_of(HostNameSslState)

    def __iter__(self):
        return iter(self.host_name_ssl_state)

    def __len__(self):
        return len(self.host_name_ssl_state)

    def __getitem__(self, index):
        return self.host_name_ssl_state[index]


class HostNameSslState(WindowsAzureData):
    
    def __init__(self):
        self.name = u''
        self.ssl_state = u''
    

class PublishData(WindowsAzureData):
    _xml_name = 'publishData'
    
    def __init__(self):
        self.publish_profiles = _list_of(PublishProfile, 'publishProfile')

class PublishProfile(WindowsAzureData):
    
    def __init__(self):
        self.profile_name = _xml_attribute('profileName')
        self.publish_method = _xml_attribute('publishMethod')
        self.publish_url = _xml_attribute('publishUrl')
        self.msdeploysite = _xml_attribute('msdeploySite')
        self.user_name = _xml_attribute('userName')
        self.user_pwd = _xml_attribute('userPWD')
        self.destination_app_url = _xml_attribute('destinationAppUrl')
        self.sql_server_db_connection_string = _xml_attribute('SQLServerDBConnectionString')
        self.my_sqldb_connection_string = _xml_attribute('mySQLDBConnectionString')
        self.hosting_provider_forum_link = _xml_attribute('hostingProviderForumLink')
        self.control_panel_link = _xml_attribute('controlPanelLink')
    
class QueueDescription(WindowsAzureData):
    
    def __init__(self):
        self.lock_duration = u''
        self.max_size_in_megabytes = 0
        self.requires_duplicate_detection = False
        self.requires_session = False
        self.default_message_time_to_live = u''
        self.dead_lettering_on_message_expiration = False
        self.duplicate_detection_history_time_window = u''
        self.max_delivery_count = 0
        self.enable_batched_operations = False
        self.size_in_bytes = 0
        self.message_count = 0
        self.is_anonymous_accessible = False
        self.authorization_rules = AuthorizationRules()
        self.status = u''
        self.created_at = u''
        self.updated_at = u''
        self.accessed_at = u''
        self.support_ordering = False
        self.auto_delete_on_idle = u''
        self.count_details = CountDetails()
        self.entity_availability_status = u''
    
class TopicDescription(WindowsAzureData):
    
    def __init__(self):
        self.default_message_time_to_live = u''
        self.max_size_in_megabytes = 0
        self.requires_duplicate_detection = False
        self.duplicate_detection_history_time_window = u''
        self.enable_batched_operations = False
        self.size_in_bytes = 0
        self.filtering_messages_before_publishing = False
        self.is_anonymous_accessible = False
        self.authorization_rules = AuthorizationRules()
        self.status = u''
        self.created_at = u''
        self.updated_at = u''
        self.accessed_at = u''
        self.support_ordering = False
        self.count_details = CountDetails()
        self.subscription_count = 0

class CountDetails(WindowsAzureData):
    
    def __init__(self):
        self.active_message_count = 0
        self.dead_letter_message_count = 0
        self.scheduled_message_count = 0
        self.transfer_message_count = 0
        self.transfer_dead_letter_message_count = 0

class NotificationHubDescription(WindowsAzureData):
    
    def __init__(self):
        self.registration_ttl = u''
        self.authorization_rules = AuthorizationRules()

class AuthorizationRules(WindowsAzureData):

    def __init__(self):
        self.authorization_rule = _list_of(AuthorizationRule)

    def __iter__(self):
        return iter(self.authorization_rule)

    def __len__(self):
        return len(self.authorization_rule)

    def __getitem__(self, index):
        return self.authorization_rule[index]
    
class AuthorizationRule(WindowsAzureData):
    
    def __init__(self):
        self.claim_type = u''
        self.claim_value = u''
        self.rights = _scalar_list_of(str, 'AccessRights')
        self.created_time = u''
        self.modified_time = u''
        self.key_name = u''
        self.primary_key = u''
        self.secondary_keu = u''

class RelayDescription(WindowsAzureData):
    
    def __init__(self):
        self.path = u''
        self.listener_type = u''
        self.listener_count = 0
        self.created_at = u''
        self.updated_at = u''


class MetricResponses(WindowsAzureData):

    def __init__(self):
        self.metric_response = _list_of(MetricResponse)

    def __iter__(self):
        return iter(self.metric_response)

    def __len__(self):
        return len(self.metric_response)

    def __getitem__(self, index):
        return self.metric_response[index]


class MetricResponse(WindowsAzureData):

    def __init__(self):
        self.code = u''
        self.data = Data()
        self.message = u''


class Data(WindowsAzureData):

    def __init__(self):
        self.display_name = u''
        self.end_time = u''
        self.name = u''
        self.primary_aggregation_type = u''
        self.start_time = u''
        self.time_grain = u''
        self.unit = u''
        self.values = Values()


class Values(WindowsAzureData):

    def __init__(self):
        self.metric_sample = _list_of(MetricSample)

    def __iter__(self):
        return iter(self.metric_sample)

    def __len__(self):
        return len(self.metric_sample)

    def __getitem__(self, index):
        return self.metric_sample[index]


class MetricSample(WindowsAzureData):

    def __init__(self):
        self.count = 0
        self.time_created = u''
        self.total = 0


class MetricDefinitions(WindowsAzureData):

    def __init__(self):
        self.metric_definition = _list_of(MetricDefinition)

    def __iter__(self):
        return iter(self.metric_definition)

    def __len__(self):
        return len(self.metric_definition)

    def __getitem__(self, index):
        return self.metric_definition[index]


class MetricDefinition(WindowsAzureData):

    def __init__(self):
        self.display_name = u''
        self.metric_availabilities = MetricAvailabilities()
        self.name = u''
        self.primary_aggregation_type = u''
        self.unit = u''


class MetricAvailabilities(WindowsAzureData):

    def __init__(self):
        self.metric_availability = _list_of(MetricAvailability, 'MetricAvailabilily')

    def __iter__(self):
        return iter(self.metric_availability)

    def __len__(self):
        return len(self.metric_availability)

    def __getitem__(self, index):
        return self.metric_availability[index]


class MetricAvailability(WindowsAzureData):

    def __init__(self):
        self.retention = u''
        self.time_grain = u''


class Servers(WindowsAzureData):

    def __init__(self):
        self.server = _list_of(Server)

    def __iter__(self):
        return iter(self.server)

    def __len__(self):
        return len(self.server)

    def __getitem__(self, index):
        return self.server[index]


class Server(WindowsAzureData):
    
    def __init__(self):
        self.name = u''
        self.administrator_login = u''
        self.location = u''
        self.geo_paired_region = u''
        self.fully_qualified_domain_name = u''
        self.version = u''


class ServerQuota(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.type = u''
        self.state = u''
        self.self_link = u''
        self.parent_link = u''
        self.value = 0


class EventLog(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.type = u''
        self.state = u''
        self.self_link = u''
        self.parent_link = u''
        self.database_name = u''
        self.name = u''
        self.start_time_utc = u''
        self.interval_size_in_minutes = 0
        self.event_category = u''
        self.event_type = u''
        self.event_subtype = 0
        self.event_subtype_description = u''
        self.number_of_events = 0
        self.severity = 0
        self.description = u''
        self.additional_data = u''


class CreateServerResponse(WindowsAzureData):
    
    def __init__(self):
        self.server_name = u''


class Database(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.type = u''
        self.state = u''
        self.self_link = u''
        self.parent_link = u''
        self.id = 0
        self.edition = u''
        self.collation_name = u''
        self.creation_date = u''
        self.is_federation_root = False
        self.is_system_object = False
        self.max_size_bytes = 0


class FirewallRule(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.type = u''
        self.state = u''
        self.self_link = u''
        self.parent_link = u''
        self.start_ip_address = u''
        self.end_ip_address = u''


class ServiceObjective(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.type = u''
        self.state = u''
        self.self_link = u''
        self.parent_link = u''
        self.id = u''
        self.is_default = False
        self.is_system = False
        self.description = u''
        self.enabled = False


class CloudServices(WindowsAzureData):

    def __init__(self):
        self.cloud_service = _list_of(CloudService)

    def __iter__(self):
        return iter(self.cloud_service)

    def __len__(self):
        return len(self.cloud_service)

    def __getitem__(self, index):
        return self.cloud_service[index]


class CloudService(WindowsAzureData):

    def __init__(self):
        self.name = u''
        self.label = u''
        self.description = u''
        self.geo_region = u''
        self.resources = Resources()


class Resources(WindowsAzureData):

    def __init__(self):
        self.resource = _list_of(Resource)

    def __iter__(self):
        return iter(self.resource)

    def __len__(self):
        return len(self.resource)

    def __getitem__(self, index):
        return self.resource[index]


class Resource(WindowsAzureData):

    def __init__(self):
        self.resource_provider_namespace = u''
        self.type = u''
        self.name = u''
        self.schema_version = u''
        self.e_tag = u''
        self.state = u''
        self.intrinsic_settings = IntrinsicSettings()
        self.operation_status = OperationStatus()


class IntrinsicSettings(WindowsAzureData):

    def __init__(self):
        self.plan = u''
        self.quota = Quota()


class Quota(WindowsAzureData):

    def __init__(self):
        self.max_job_count = 0
        self.max_recurrence = MaxRecurrence()


class MaxRecurrence(WindowsAzureData):

    def __init__(self):
        self.frequency = u''
        self.interval = 0


class OperationStatus(WindowsAzureData):

    def __init__(self):
        self.type = u''
        self.result = u''


def parse_response_for_async_op(response):
    ''' Extracts request id from response header. '''

    if response is None:
        return None

    result = AsynchronousOperationResult()
    if response.headers:
        for name, value in response.headers:
            if name.lower() == 'x-ms-request-id':
                result.request_id = value

    return result


def _management_error_handler(http_error):
    ''' Simple error handler for management service. '''
    return _general_error_handler(http_error)


def _lower(text):
    return text.lower()


def _data_to_xml(data):
    '''Creates an xml fragment from the specified data.
        data: Array of tuples, where first: xml element name
                                    second: xml element text
                                    third: conversion function
    '''
    xml = ''
    for element in data:
        name = element[0]
        val = element[1]
        if len(element) > 2:
            converter = element[2]
        else:
            converter = None

        if val is not None:
            if converter is not None:
                text = _str(converter(_str(val)))
            else:
                text = _str(val)

            xml += ''.join(['<', name, '>', text, '</', name, '>'])
    return xml


class _XmlSerializer(object):

    @staticmethod
    def create_storage_service_input_to_xml(service_name, description, label,
                                            affinity_group, location,
                                            account_type,
                                            extended_properties):
        xml = _XmlSerializer.data_to_xml(
            [('ServiceName', service_name),
             ('Description', description),
             ('Label', label, _encode_base64),
             ('AffinityGroup', affinity_group),
             ('Location', location)])
        if extended_properties is not None:
            xml += _XmlSerializer.extended_properties_dict_to_xml_fragment(
                extended_properties)
        xml += _XmlSerializer.data_to_xml([('AccountType', account_type)])
        return _XmlSerializer.doc_from_xml('CreateStorageServiceInput', xml)

    @staticmethod
    def update_storage_service_input_to_xml(description, label,
                                            account_type,
                                            extended_properties):
        xml = _XmlSerializer.data_to_xml(
            [('Description', description),
             ('Label', label, _encode_base64)])
        if extended_properties is not None:
            xml += _XmlSerializer.extended_properties_dict_to_xml_fragment(
                extended_properties)
        xml += _XmlSerializer.data_to_xml([('AccountType', account_type)])
        return _XmlSerializer.doc_from_xml('UpdateStorageServiceInput', xml)

    @staticmethod
    def regenerate_keys_to_xml(key_type):
        return _XmlSerializer.doc_from_data('RegenerateKeys',
                                            [('KeyType', key_type)])

    @staticmethod
    def update_hosted_service_to_xml(label, description, extended_properties):
        return _XmlSerializer.doc_from_data('UpdateHostedService',
                                            [('Label', label, _encode_base64),
                                             ('Description', description)],
                                            extended_properties)

    @staticmethod
    def create_hosted_service_to_xml(service_name, label, description,
                                     location, affinity_group,
                                     extended_properties):
        return _XmlSerializer.doc_from_data(
            'CreateHostedService',
            [('ServiceName', service_name),
             ('Label', label, _encode_base64),
             ('Description', description),
             ('Location', location),
             ('AffinityGroup', affinity_group)],
            extended_properties)

    @staticmethod
    def create_deployment_to_xml(name, package_url, label, configuration,
                                 start_deployment, treat_warnings_as_error,
                                 extended_properties):
        return _XmlSerializer.doc_from_data(
            'CreateDeployment',
            [('Name', name),
             ('PackageUrl', package_url),
             ('Label', label, _encode_base64),
             ('Configuration', configuration),
             ('StartDeployment',
             start_deployment, _lower),
             ('TreatWarningsAsError', treat_warnings_as_error, _lower)],
            extended_properties)

    @staticmethod
    def swap_deployment_to_xml(production, source_deployment):
        return _XmlSerializer.doc_from_data(
            'Swap',
            [('Production', production),
             ('SourceDeployment', source_deployment)])

    @staticmethod
    def update_deployment_status_to_xml(status):
        return _XmlSerializer.doc_from_data(
            'UpdateDeploymentStatus',
            [('Status', status)])

    @staticmethod
    def change_deployment_to_xml(configuration, treat_warnings_as_error, mode,
                                 extended_properties):
        return _XmlSerializer.doc_from_data(
            'ChangeConfiguration',
            [('Configuration', configuration),
             ('TreatWarningsAsError', treat_warnings_as_error, _lower),
             ('Mode', mode)],
            extended_properties)

    @staticmethod
    def upgrade_deployment_to_xml(mode, package_url, configuration, label,
                                  role_to_upgrade, force, extended_properties):
        return _XmlSerializer.doc_from_data(
            'UpgradeDeployment',
            [('Mode', mode),
             ('PackageUrl', package_url),
             ('Configuration', configuration),
             ('Label', label, _encode_base64),
             ('RoleToUpgrade', role_to_upgrade),
             ('Force', force, _lower)],
            extended_properties)

    @staticmethod
    def rollback_upgrade_to_xml(mode, force):
        return _XmlSerializer.doc_from_data(
            'RollbackUpdateOrUpgrade',
            [('Mode', mode),
             ('Force', force, _lower)])

    @staticmethod
    def walk_upgrade_domain_to_xml(upgrade_domain):
        return _XmlSerializer.doc_from_data(
            'WalkUpgradeDomain',
            [('UpgradeDomain', upgrade_domain)])

    @staticmethod
    def certificate_file_to_xml(data, certificate_format, password):
        return _XmlSerializer.doc_from_data(
            'CertificateFile',
            [('Data', data),
             ('CertificateFormat', certificate_format),
             ('Password', password)])

    @staticmethod
    def create_affinity_group_to_xml(name, label, description, location):
        return _XmlSerializer.doc_from_data(
            'CreateAffinityGroup',
            [('Name', name),
             ('Label', label, _encode_base64),
             ('Description', description),
             ('Location', location)])

    @staticmethod
    def update_affinity_group_to_xml(label, description):
        return _XmlSerializer.doc_from_data(
            'UpdateAffinityGroup',
            [('Label', label, _encode_base64),
             ('Description', description)])

    @staticmethod
    def subscription_certificate_to_xml(public_key, thumbprint, data):
        return _XmlSerializer.doc_from_data(
            'SubscriptionCertificate',
            [('SubscriptionCertificatePublicKey', public_key),
             ('SubscriptionCertificateThumbprint', thumbprint),
             ('SubscriptionCertificateData', data)])

    @staticmethod
    def os_image_to_xml(label, media_link, name, os):
        return _XmlSerializer.doc_from_data(
            'OSImage',
            [('Label', label),
             ('MediaLink', media_link),
             ('Name', name),
             ('OS', os)])

    @staticmethod
    def data_virtual_hard_disk_to_xml(host_caching, disk_label, disk_name, lun,
                                      logical_disk_size_in_gb, media_link,
                                      source_media_link):
        return _XmlSerializer.doc_from_data(
            'DataVirtualHardDisk',
            [('HostCaching', host_caching),
             ('DiskLabel', disk_label),
             ('DiskName', disk_name),
             ('Lun', lun),
             ('LogicalDiskSizeInGB', logical_disk_size_in_gb),
             ('MediaLink', media_link),
             ('SourceMediaLink', source_media_link)])

    @staticmethod
    def disk_to_xml(has_operating_system, label, media_link, name, os):
        return _XmlSerializer.doc_from_data(
            'Disk',
            [('HasOperatingSystem', has_operating_system, _lower),
             ('Label', label),
             ('MediaLink', media_link),
             ('Name', name),
             ('OS', os)])

    @staticmethod
    def restart_role_operation_to_xml():
        return _XmlSerializer.doc_from_xml(
            'RestartRoleOperation',
            '<OperationType>RestartRoleOperation</OperationType>')

    @staticmethod
    def shutdown_role_operation_to_xml(post_shutdown_action):
        xml = _XmlSerializer.data_to_xml(
            [('OperationType', 'ShutdownRoleOperation'),
             ('PostShutdownAction', post_shutdown_action)])
        return _XmlSerializer.doc_from_xml('ShutdownRoleOperation', xml)

    @staticmethod
    def shutdown_roles_operation_to_xml(role_names, post_shutdown_action):
        xml = _XmlSerializer.data_to_xml(
            [('OperationType', 'ShutdownRolesOperation')])
        xml += '<Roles>'
        for role_name in role_names:
            xml += _XmlSerializer.data_to_xml([('Name', role_name)])
        xml += '</Roles>'
        xml += _XmlSerializer.data_to_xml(
             [('PostShutdownAction', post_shutdown_action)])
        return _XmlSerializer.doc_from_xml('ShutdownRolesOperation', xml)

    @staticmethod
    def start_role_operation_to_xml():
        return _XmlSerializer.doc_from_xml(
            'StartRoleOperation',
            '<OperationType>StartRoleOperation</OperationType>')

    @staticmethod
    def start_roles_operation_to_xml(role_names):
        xml = _XmlSerializer.data_to_xml(
            [('OperationType', 'StartRolesOperation')])
        xml += '<Roles>'
        for role_name in role_names:
            xml += _XmlSerializer.data_to_xml([('Name', role_name)])
        xml += '</Roles>'
        return _XmlSerializer.doc_from_xml('StartRolesOperation', xml)

    @staticmethod
    def windows_configuration_to_xml(configuration):
        xml = _XmlSerializer.data_to_xml(
            [('ConfigurationSetType', configuration.configuration_set_type),
             ('ComputerName', configuration.computer_name),
             ('AdminPassword', configuration.admin_password),
             ('ResetPasswordOnFirstLogon',
              configuration.reset_password_on_first_logon,
              _lower),
             ('EnableAutomaticUpdates',
              configuration.enable_automatic_updates,
              _lower),
             ('TimeZone', configuration.time_zone)])

        if configuration.domain_join is not None:
            xml += '<DomainJoin>'
            xml += '<Credentials>'
            xml += _XmlSerializer.data_to_xml(
                [('Domain', configuration.domain_join.credentials.domain),
                 ('Username', configuration.domain_join.credentials.username),
                 ('Password', configuration.domain_join.credentials.password)])
            xml += '</Credentials>'
            xml += _XmlSerializer.data_to_xml(
                [('JoinDomain', configuration.domain_join.join_domain),
                 ('MachineObjectOU',
                  configuration.domain_join.machine_object_ou)])
            xml += '</DomainJoin>'
        if configuration.stored_certificate_settings is not None:
            xml += '<StoredCertificateSettings>'
            for cert in configuration.stored_certificate_settings:
                xml += '<CertificateSetting>'
                xml += _XmlSerializer.data_to_xml(
                    [('StoreLocation', cert.store_location),
                     ('StoreName', cert.store_name),
                     ('Thumbprint', cert.thumbprint)])
                xml += '</CertificateSetting>'
            xml += '</StoredCertificateSettings>'
        if configuration.win_rm is not None:
            xml += '<WinRM><Listeners>'
            for listener in configuration.win_rm.listeners:
                xml += '<Listener>'
                xml += _XmlSerializer.data_to_xml(
                    [('Protocol', listener.protocol),
                     ('CertificateThumbprint', listener.certificate_thumbprint)])
                xml += '</Listener>'
            xml += '</Listeners></WinRM>'
        xml += _XmlSerializer.data_to_xml(
            [('AdminUsername', configuration.admin_username),
             ('CustomData', configuration.custom_data, _encode_base64)])
        if configuration.additional_unattend_content and configuration.additional_unattend_content.passes:
            xml += '<AdditionalUnattendContent><Passes>'
            for unattend_pass in configuration.additional_unattend_content.passes:
                xml += _XmlSerializer.data_to_xml(
                    [('PassName', unattend_pass.pass_name)])
                if unattend_pass.components:
                    xml += '<Components>'
                    for comp in unattend_pass.components:
                        xml += '<UnattendComponent>'
                        xml += _XmlSerializer.data_to_xml(
                            [('ComponentName', comp.component_name)])
                        if comp.component_settings:
                            xml += '<ComponentSettings>'
                            for setting in comp.component_settings:
                                xml += '<ComponentSetting>'
                                xml += _XmlSerializer.data_to_xml(
                                    [('SettingName', setting.setting_name),
                                     ('Content', setting.content)])
                                xml += '</ComponentSetting>'
                            xml += '</ComponentSettings>'
                        xml += '</UnattendComponent>'
                    xml += '</Components>'
            xml += '</Passes></AdditionalUnattendContent>'

        return xml

    @staticmethod
    def linux_configuration_to_xml(configuration):
        xml = _XmlSerializer.data_to_xml(
            [('ConfigurationSetType', configuration.configuration_set_type),
             ('HostName', configuration.host_name),
             ('UserName', configuration.user_name),
             ('UserPassword', configuration.user_password),
             ('DisableSshPasswordAuthentication',
              configuration.disable_ssh_password_authentication,
              _lower)])

        if configuration.ssh is not None:
            xml += '<SSH>'
            xml += '<PublicKeys>'
            for key in configuration.ssh.public_keys:
                xml += '<PublicKey>'
                xml += _XmlSerializer.data_to_xml(
                    [('Fingerprint', key.fingerprint),
                     ('Path', key.path)])
                xml += '</PublicKey>'
            xml += '</PublicKeys>'
            xml += '<KeyPairs>'
            for key in configuration.ssh.key_pairs:
                xml += '<KeyPair>'
                xml += _XmlSerializer.data_to_xml(
                    [('Fingerprint', key.fingerprint),
                     ('Path', key.path)])
                xml += '</KeyPair>'
            xml += '</KeyPairs>'
            xml += '</SSH>'

        xml += _XmlSerializer.data_to_xml(
            [('CustomData', configuration.custom_data, _encode_base64)])

        return xml

    @staticmethod
    def network_configuration_to_xml(configuration):
        xml = _XmlSerializer.data_to_xml(
            [('ConfigurationSetType', configuration.configuration_set_type)])
        xml += '<InputEndpoints>'
        for endpoint in configuration.input_endpoints:
            xml += '<InputEndpoint>'
            xml += _XmlSerializer.data_to_xml(
                [('LoadBalancedEndpointSetName',
                  endpoint.load_balanced_endpoint_set_name),
                 ('LocalPort', endpoint.local_port),
                 ('Name', endpoint.name),
                 ('Port', endpoint.port)])

            if endpoint.load_balancer_probe.path or\
                endpoint.load_balancer_probe.port or\
                endpoint.load_balancer_probe.protocol:
                xml += '<LoadBalancerProbe>'
                xml += _XmlSerializer.data_to_xml(
                    [('Path', endpoint.load_balancer_probe.path),
                     ('Port', endpoint.load_balancer_probe.port),
                     ('Protocol', endpoint.load_balancer_probe.protocol)])
                xml += '</LoadBalancerProbe>'

            xml += _XmlSerializer.data_to_xml(
                [('Protocol', endpoint.protocol),
                 ('EnableDirectServerReturn',
                  endpoint.enable_direct_server_return,
                  _lower)])

            xml += '</InputEndpoint>'
        xml += '</InputEndpoints>'
        xml += '<SubnetNames>'
        for name in configuration.subnet_names:
            xml += _XmlSerializer.data_to_xml([('SubnetName', name)])
        xml += '</SubnetNames>'

        if configuration.public_ips:
            xml += '<PublicIPs>'
            for public_ip in configuration.public_ips:
                xml += '<PublicIP>'
                xml += _XmlSerializer.data_to_xml(
                    [('Name', public_ip.name),
                     ('IdleTimeoutInMinutes', public_ip.idle_timeout_in_minutes)])
                xml += '</PublicIP>'
            xml += '</PublicIPs>'

        return xml

    @staticmethod
    def role_to_xml(availability_set_name, data_virtual_hard_disks,
                    network_configuration_set, os_virtual_hard_disk, role_name,
                    role_size, role_type, system_configuration_set,
                    resource_extension_references,
                    provision_guest_agent, vm_image_name, media_location):
        xml = _XmlSerializer.data_to_xml([('RoleName', role_name),
                                          ('RoleType', role_type)])

        if system_configuration_set or network_configuration_set:
            xml += '<ConfigurationSets>'

            if system_configuration_set is not None:
                xml += '<ConfigurationSet>'
                if isinstance(system_configuration_set, WindowsConfigurationSet):
                    xml += _XmlSerializer.windows_configuration_to_xml(
                        system_configuration_set)
                elif isinstance(system_configuration_set, LinuxConfigurationSet):
                    xml += _XmlSerializer.linux_configuration_to_xml(
                        system_configuration_set)
                xml += '</ConfigurationSet>'

            if network_configuration_set is not None:
                xml += '<ConfigurationSet>'
                xml += _XmlSerializer.network_configuration_to_xml(
                    network_configuration_set)
                xml += '</ConfigurationSet>'

            xml += '</ConfigurationSets>'

        if resource_extension_references:
            xml += '<ResourceExtensionReferences>'
            for ext in resource_extension_references:
                xml += '<ResourceExtensionReference>'
                xml += _XmlSerializer.data_to_xml(
                    [('ReferenceName', ext.reference_name),
                     ('Publisher', ext.publisher),
                     ('Name', ext.name),
                     ('Version', ext.version)])
                if ext.resource_extension_parameter_values:
                    xml += '<ResourceExtensionParameterValues>'
                    for val in ext.resource_extension_parameter_values:
                        xml += '<ResourceExtensionParameterValue>'
                        xml += _XmlSerializer.data_to_xml(
                            [('Key', val.key),
                             ('Value', val.value),
                             ('Type', val.type)])
                        xml += '</ResourceExtensionParameterValue>'
                    xml += '</ResourceExtensionParameterValues>'
                xml += '</ResourceExtensionReference>'
            xml += '</ResourceExtensionReferences>'

        xml += _XmlSerializer.data_to_xml(
            [('VMImageName', vm_image_name),
             ('MediaLocation', media_location),
             ('AvailabilitySetName', availability_set_name)])

        if data_virtual_hard_disks is not None:
            xml += '<DataVirtualHardDisks>'
            for hd in data_virtual_hard_disks:
                xml += '<DataVirtualHardDisk>'
                xml += _XmlSerializer.data_to_xml(
                    [('HostCaching', hd.host_caching),
                     ('DiskLabel', hd.disk_label),
                     ('DiskName', hd.disk_name),
                     ('Lun', hd.lun),
                     ('LogicalDiskSizeInGB', hd.logical_disk_size_in_gb),
                     ('MediaLink', hd.media_link)])
                xml += '</DataVirtualHardDisk>'
            xml += '</DataVirtualHardDisks>'

        if os_virtual_hard_disk is not None:
            xml += '<OSVirtualHardDisk>'
            xml += _XmlSerializer.data_to_xml(
                [('HostCaching', os_virtual_hard_disk.host_caching),
                 ('DiskLabel', os_virtual_hard_disk.disk_label),
                 ('DiskName', os_virtual_hard_disk.disk_name),
                 ('MediaLink', os_virtual_hard_disk.media_link),
                 ('SourceImageName', os_virtual_hard_disk.source_image_name),
                 ('OS', os_virtual_hard_disk.os),
                 ('RemoteSourceImageLink', os_virtual_hard_disk.remote_source_image_link)])
            xml += '</OSVirtualHardDisk>'

        xml += _XmlSerializer.data_to_xml(
            [('RoleSize', role_size),
             ('ProvisionGuestAgent', provision_guest_agent, _lower)])

        return xml

    @staticmethod
    def add_role_to_xml(role_name, system_configuration_set,
                        os_virtual_hard_disk, role_type,
                        network_configuration_set, availability_set_name,
                        data_virtual_hard_disks, role_size,
                        resource_extension_references, provision_guest_agent,
                        vm_image_name, media_location):
        xml = _XmlSerializer.role_to_xml(
            availability_set_name,
            data_virtual_hard_disks,
            network_configuration_set,
            os_virtual_hard_disk,
            role_name,
            role_size,
            role_type,
            system_configuration_set,
            resource_extension_references,
            provision_guest_agent,
            vm_image_name,
            media_location)
        return _XmlSerializer.doc_from_xml('PersistentVMRole', xml)

    @staticmethod
    def update_role_to_xml(role_name, os_virtual_hard_disk, role_type,
                           network_configuration_set, availability_set_name,
                           data_virtual_hard_disks, role_size,
                           resource_extension_references,
                           provision_guest_agent):
        xml = _XmlSerializer.role_to_xml(
            availability_set_name,
            data_virtual_hard_disks,
            network_configuration_set,
            os_virtual_hard_disk,
            role_name,
            role_size,
            role_type,
            None,
            resource_extension_references,
            provision_guest_agent,
            None,
            None)
        return _XmlSerializer.doc_from_xml('PersistentVMRole', xml)

    @staticmethod
    def capture_role_to_xml(post_capture_action, target_image_name,
                            target_image_label, provisioning_configuration):
        xml = _XmlSerializer.data_to_xml(
            [('OperationType', 'CaptureRoleOperation'),
             ('PostCaptureAction', post_capture_action)])

        if provisioning_configuration is not None:
            xml += '<ProvisioningConfiguration>'
            if isinstance(provisioning_configuration, WindowsConfigurationSet):
                xml += _XmlSerializer.windows_configuration_to_xml(
                    provisioning_configuration)
            elif isinstance(provisioning_configuration, LinuxConfigurationSet):
                xml += _XmlSerializer.linux_configuration_to_xml(
                    provisioning_configuration)
            xml += '</ProvisioningConfiguration>'

        xml += _XmlSerializer.data_to_xml(
            [('TargetImageLabel', target_image_label),
             ('TargetImageName', target_image_name)])

        return _XmlSerializer.doc_from_xml('CaptureRoleOperation', xml)

    @staticmethod
    def virtual_machine_deployment_to_xml(deployment_name, deployment_slot,
                                          label, role_name,
                                          system_configuration_set,
                                          os_virtual_hard_disk, role_type,
                                          network_configuration_set,
                                          availability_set_name,
                                          data_virtual_hard_disks, role_size,
                                          virtual_network_name,
                                          resource_extension_references,
                                          provision_guest_agent,
                                          vm_image_name,
                                          media_location,
                                          dns_servers,
                                          reserved_ip_name):
        xml = _XmlSerializer.data_to_xml([('Name', deployment_name),
                                          ('DeploymentSlot', deployment_slot),
                                          ('Label', label)])
        xml += '<RoleList>'
        xml += '<Role>'
        xml += _XmlSerializer.role_to_xml(
            availability_set_name,
            data_virtual_hard_disks,
            network_configuration_set,
            os_virtual_hard_disk,
            role_name,
            role_size,
            role_type,
            system_configuration_set,
            resource_extension_references,
            provision_guest_agent,
            vm_image_name,
            media_location)
        xml += '</Role>'
        xml += '</RoleList>'

        xml += _XmlSerializer.data_to_xml(
            [('VirtualNetworkName', virtual_network_name)])

        if dns_servers:
            xml += '<Dns><DnsServers>'
            for dns_server in dns_servers:
                xml += '<DnsServer>'
                xml += _XmlSerializer.data_to_xml(
                    [('Name', dns_server.name),
                     ('Address', dns_server.address)])
                xml += '</DnsServer>'
            xml += '</DnsServers></Dns>'

        xml += _XmlSerializer.data_to_xml(
            [('ReservedIPName', reserved_ip_name)])

        return _XmlSerializer.doc_from_xml('Deployment', xml)

    @staticmethod
    def capture_vm_image_to_xml(options):
        return _XmlSerializer.doc_from_data(
            'CaptureRoleAsVMImageOperation ',
            [('OperationType', 'CaptureRoleAsVMImageOperation'),
             ('OSState', options.os_state),
             ('VMImageName', options.vm_image_name),
             ('VMImageLabel', options.vm_image_label),
             ('Description', options.description),
             ('Language', options.language),
             ('ImageFamily', options.image_family),
             ('RecommendedVMSize', options.recommended_vm_size)])

    @staticmethod
    def create_vm_image_to_xml(image):
        xml = _XmlSerializer.data_to_xml(
            [('Name', image.name),
            ('Label', image.label),
            ('Description', image.description)])

        os_disk = image.os_disk_configuration
        xml += '<OSDiskConfiguration>'
        xml += _XmlSerializer.data_to_xml(
            [('HostCaching', os_disk.host_caching),
            ('OSState', os_disk.os_state),
            ('OS', os_disk.os),
            ('MediaLink', os_disk.media_link)])
        xml += '</OSDiskConfiguration>'

        if image.data_disk_configurations:
            xml += '<DataDiskConfigurations>'
            for data_disk in image.data_disk_configurations:
                xml += '<DataDiskConfiguration>'
                xml += _XmlSerializer.data_to_xml(
                    [('HostCaching', data_disk.host_caching),
                    ('Lun', data_disk.lun),
                    ('MediaLink', data_disk.media_link),
                    ('LogicalDiskSizeInGB', data_disk.logical_disk_size_in_gb)])
                xml += '</DataDiskConfiguration>'
            xml += '</DataDiskConfigurations>'

        xml += _XmlSerializer.data_to_xml(
            [('Language', image.language),
            ('ImageFamily', image.image_family),
            ('RecommendedVMSize', image.recommended_vm_size),
            ('Eula', image.eula),
            ('IconUri', image.icon_uri),
            ('SmallIconUri', image.small_icon_uri),
            ('PrivacyUri', image.privacy_uri),
            ('PublishedDate', image.published_date),
            ('ShowInGui', image.show_in_gui, _lower)])

        return _XmlSerializer.doc_from_xml('VMImage', xml)

    @staticmethod
    def update_vm_image_to_xml(image):
        xml = _XmlSerializer.data_to_xml(
            [('Label', image.label),
            ('Description', image.description)])

        os_disk = image.os_disk_configuration
        xml += '<OSDiskConfiguration>'
        xml += _XmlSerializer.data_to_xml(
            [('HostCaching', os_disk.host_caching)])
        xml += '</OSDiskConfiguration>'

        xml += '<DataDiskConfigurations>'
        for data_disk in image.data_disk_configurations:
            xml += '<DataDiskConfiguration>'
            xml += _XmlSerializer.data_to_xml(
                [('Name', data_disk.name),
                ('HostCaching', data_disk.host_caching),
                ('Lun', data_disk.lun)])
            xml += '</DataDiskConfiguration>'
        xml += '</DataDiskConfigurations>'

        xml += _XmlSerializer.data_to_xml(
            [('Language', image.language),
            ('ImageFamily', image.image_family),
            ('RecommendedVMSize', image.recommended_vm_size),
            ('Eula', image.eula),
            ('IconUri', image.icon_uri),
            ('SmallIconUri', image.small_icon_uri),
            ('PrivacyUri', image.privacy_uri),
            ('PublishedDate', image.published_date),
            ('ShowInGui', image.show_in_gui, _lower)])

        return _XmlSerializer.doc_from_xml('VMImage', xml)

    @staticmethod
    def create_website_to_xml(webspace_name, website_name, geo_region, plan,
                              host_names, compute_mode, server_farm, site_mode):
        xml = '<HostNames xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays">'
        for host_name in host_names:
            xml += '<a:string>{0}</a:string>'.format(host_name)
        xml += '</HostNames>'
        xml += _XmlSerializer.data_to_xml(
            [('Name', website_name),
             ('ComputeMode', compute_mode),
             ('ServerFarm', server_farm),
             ('SiteMode', site_mode)])
        xml += '<WebSpaceToCreate>'
        xml += _XmlSerializer.data_to_xml(
            [('GeoRegion', geo_region),
             ('Name', webspace_name),
             ('Plan', plan)])
        xml += '</WebSpaceToCreate>'
        return _XmlSerializer.doc_from_xml('Site', xml)

    @staticmethod
    def create_reserved_ip_to_xml(name, label, location):
        return _XmlSerializer.doc_from_data(
            'ReservedIP',
            [('Name', name),
             ('Label', label),
             ('Location', location)])

    @staticmethod
    def dns_server_to_xml(name, address):
        return _XmlSerializer.doc_from_data(
            'DnsServer',
            [('Name', name),
             ('Address', address)])

    @staticmethod
    def role_instances_to_xml(role_instances):
        xml = ''
        for name in role_instances:
            xml += _XmlSerializer.data_to_xml([('Name', name)])
        return _XmlSerializer.doc_from_xml('RoleInstances ', xml)

    @staticmethod
    def data_to_xml(data):
        return _data_to_xml(data)

    @staticmethod
    def doc_from_xml(document_element_name, inner_xml):
        '''Wraps the specified xml in an xml root element with default azure
        namespaces'''
        xml = ''.join(['<', document_element_name,
                      ' xmlns:i="http://www.w3.org/2001/XMLSchema-instance"',
                      ' xmlns="http://schemas.microsoft.com/windowsazure">'])
        xml += inner_xml
        xml += ''.join(['</', document_element_name, '>'])
        return xml

    @staticmethod
    def doc_from_data(document_element_name, data, extended_properties=None):
        xml = _XmlSerializer.data_to_xml(data)
        if extended_properties is not None:
            xml += _XmlSerializer.extended_properties_dict_to_xml_fragment(
                extended_properties)
        return _XmlSerializer.doc_from_xml(document_element_name, xml)

    @staticmethod
    def extended_properties_dict_to_xml_fragment(extended_properties):
        xml = ''
        if extended_properties is not None and len(extended_properties) > 0:
            xml += '<ExtendedProperties>'
            for key, val in extended_properties.items():
                xml += ''.join(['<ExtendedProperty>',
                                '<Name>',
                                _str(key),
                                '</Name>',
                               '<Value>',
                               _str(val),
                               '</Value>',
                               '</ExtendedProperty>'])
            xml += '</ExtendedProperties>'
        return xml


class _SqlManagementXmlSerializer(object):

    @staticmethod
    def create_server_to_xml(admin_login, admin_password, location):
        return _SqlManagementXmlSerializer.doc_from_data(
            'Server',
            [('AdministratorLogin', admin_login),
             ('AdministratorLoginPassword', admin_password),
             ('Location', location)],
             'http://schemas.microsoft.com/sqlazure/2010/12/')

    @staticmethod
    def set_server_admin_password_to_xml(admin_password):
        return _SqlManagementXmlSerializer.doc_from_xml(
            'AdministratorLoginPassword', admin_password,
            'http://schemas.microsoft.com/sqlazure/2010/12/')

    @staticmethod
    def create_firewall_rule_to_xml(name, start_ip_address, end_ip_address):
        return _SqlManagementXmlSerializer.doc_from_data(
            'ServiceResource',
            [('Name', name),
             ('StartIPAddress', start_ip_address),
             ('EndIPAddress', end_ip_address)])

    @staticmethod
    def update_firewall_rule_to_xml(name, start_ip_address, end_ip_address):
        return _SqlManagementXmlSerializer.doc_from_data(
            'ServiceResource',
            [('Name', name),
             ('StartIPAddress', start_ip_address),
             ('EndIPAddress', end_ip_address)])

    @staticmethod
    def create_database_to_xml(name, service_objective_id, edition, collation_name,
                max_size_bytes):
        return _SqlManagementXmlSerializer.doc_from_data(
            'ServiceResource',
            [('Name', name),
             ('Edition', edition),
             ('CollationName', collation_name),
             ('MaxSizeBytes', max_size_bytes),
             ('ServiceObjectiveId', service_objective_id)])

    @staticmethod
    def update_database_to_xml(name, service_objective_id, edition,
                               max_size_bytes):
        return _SqlManagementXmlSerializer.doc_from_data(
            'ServiceResource',
            [('Name', name),
             ('Edition', edition),
             ('MaxSizeBytes', max_size_bytes),
             ('ServiceObjectiveId', service_objective_id)])

    @staticmethod
    def xml_to_create_server_response(xmlstr):
        xmldoc = minidom.parseString(xmlstr)
        element = xmldoc.documentElement

        response = CreateServerResponse()
        response.server_name = element.firstChild.nodeValue
        response.fully_qualified_domain_name = element.getAttribute('FullyQualifiedDomainName')

        return response

    @staticmethod
    def data_to_xml(data):
        return _data_to_xml(data)

    @staticmethod
    def doc_from_xml(document_element_name, inner_xml,
                     xmlns='http://schemas.microsoft.com/windowsazure'):
        '''Wraps the specified xml in an xml root element with default azure
        namespaces'''
        xml = ''.join(['<', document_element_name,
                      ' xmlns="{0}">'.format(xmlns)])
        xml += inner_xml
        xml += ''.join(['</', document_element_name, '>'])
        return xml

    @staticmethod
    def doc_from_data(document_element_name, data,
                      xmlns='http://schemas.microsoft.com/windowsazure'):
        xml = _SqlManagementXmlSerializer.data_to_xml(data)
        return _SqlManagementXmlSerializer.doc_from_xml(
            document_element_name, xml, xmlns)


def _parse_bool(value):
    if value.lower() == 'true':
        return True
    return False


class _ServiceBusManagementXmlSerializer(object):

    @staticmethod
    def namespace_to_xml(region):
        '''Converts a service bus namespace description to xml

        The xml format:
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<entry xmlns="http://www.w3.org/2005/Atom">
    <content type="application/xml">
        <NamespaceDescription
            xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">
            <Region>West US</Region>
        </NamespaceDescription>
    </content>
</entry>
        '''
        body = '<NamespaceDescription xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">'
        body += ''.join(['<Region>', region, '</Region>'])
        body += '</NamespaceDescription>'

        return _create_entry(body)

    @staticmethod
    def xml_to_namespace(xmlstr):
        '''Converts xml response to service bus namespace

        The xml format for namespace:
<entry>
<id>uuid:00000000-0000-0000-0000-000000000000;id=0000000</id>
<title type="text">myunittests</title>
<updated>2012-08-22T16:48:10Z</updated>
<content type="application/xml">
    <NamespaceDescription
        xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect"
        xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
    <Name>myunittests</Name>
    <Region>West US</Region>
    <DefaultKey>0000000000000000000000000000000000000000000=</DefaultKey>
    <Status>Active</Status>
    <CreatedAt>2012-08-22T16:48:10.217Z</CreatedAt>
    <AcsManagementEndpoint>https://myunittests-sb.accesscontrol.windows.net/</AcsManagementEndpoint>
    <ServiceBusEndpoint>https://myunittests.servicebus.windows.net/</ServiceBusEndpoint>
    <ConnectionString>Endpoint=sb://myunittests.servicebus.windows.net/;SharedSecretIssuer=owner;SharedSecretValue=0000000000000000000000000000000000000000000=</ConnectionString>
    <SubscriptionId>00000000000000000000000000000000</SubscriptionId>
    <Enabled>true</Enabled>
    </NamespaceDescription>
</content>
</entry>
        '''
        xmldoc = minidom.parseString(xmlstr)
        namespace = ServiceBusNamespace()

        mappings = (
            ('Name', 'name', None),
            ('Region', 'region', None),
            ('DefaultKey', 'default_key', None),
            ('Status', 'status', None),
            ('CreatedAt', 'created_at', None),
            ('AcsManagementEndpoint', 'acs_management_endpoint', None),
            ('ServiceBusEndpoint', 'servicebus_endpoint', None),
            ('ConnectionString', 'connection_string', None),
            ('SubscriptionId', 'subscription_id', None),
            ('Enabled', 'enabled', _parse_bool),
        )

        for desc in _get_children_from_path(xmldoc,
                                            'entry',
                                            'content',
                                            'NamespaceDescription'):
            for xml_name, field_name, conversion_func in mappings:
                node_value = _get_first_child_node_value(desc, xml_name)
                if node_value is not None:
                    if conversion_func is not None:
                        node_value = conversion_func(node_value)
                    setattr(namespace, field_name, node_value)

        return namespace

    @staticmethod
    def xml_to_region(xmlstr):
        '''Converts xml response to service bus region

        The xml format for region:
<entry>
<id>uuid:157c311f-081f-4b4a-a0ba-a8f990ffd2a3;id=1756759</id>
<title type="text"></title>
<updated>2013-04-10T18:25:29Z</updated>
<content type="application/xml">
    <RegionCodeDescription
        xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect"
        xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
    <Code>East Asia</Code>
    <FullName>East Asia</FullName>
    </RegionCodeDescription>
</content>
</entry>
          '''
        xmldoc = minidom.parseString(xmlstr)
        region = ServiceBusRegion()

        for desc in _get_children_from_path(xmldoc, 'entry', 'content',
                                            'RegionCodeDescription'):
            node_value = _get_first_child_node_value(desc, 'Code')
            if node_value is not None:
                region.code = node_value
            node_value = _get_first_child_node_value(desc, 'FullName')
            if node_value is not None:
                region.fullname = node_value

        return region

    @staticmethod
    def xml_to_namespace_availability(xmlstr):
        '''Converts xml response to service bus namespace availability

        The xml format:
<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
    <id>uuid:9fc7c652-1856-47ab-8d74-cd31502ea8e6;id=3683292</id>
    <title type="text"></title>
    <updated>2013-04-16T03:03:37Z</updated>
    <content type="application/xml">
        <NamespaceAvailability
            xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect"
            xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
            <Result>false</Result>
        </NamespaceAvailability>
    </content>
</entry>
        '''
        xmldoc = minidom.parseString(xmlstr)
        availability = AvailabilityResponse()

        for desc in _get_children_from_path(xmldoc, 'entry', 'content',
                                            'NamespaceAvailability'):
            node_value = _get_first_child_node_value(desc, 'Result')
            if node_value is not None:
                availability.result = _parse_bool(node_value)

        return availability

    @staticmethod
    def odata_converter(data, str_type):
        ''' Convert odata type
        http://www.odata.org/documentation/odata-version-2-0/overview#AbstractTypeSystem
        To be completed
        '''
        if not str_type:
            return _str(data)
        if str_type in ["Edm.Single", "Edm.Double"]:
            return float(data)
        elif "Edm.Int" in str_type:
            return int(data)
        else:
            return _str(data)

    @staticmethod
    def xml_to_metrics(xmlstr, object_type):
        '''Converts xml response to service bus metrics objects

        The xml format for MetricProperties
<entry>
    <id>https://sbgm.windows.net/Metrics(\'listeners.active\')</id>
    <title/>
    <updated>2014-10-09T11:56:50Z</updated>
    <author>
        <name/>
    </author>
    <content type="application/xml">
        <m:properties>
            <d:Name>listeners.active</d:Name>
            <d:PrimaryAggregation>Average</d:PrimaryAggregation>
            <d:Unit>Count</d:Unit>
            <d:DisplayName>Active listeners</d:DisplayName>
        </m:properties>
    </content>
</entry>

        The xml format for MetricValues
    <entry>
        <id>https://sbgm.windows.net/MetricValues(datetime\'2014-10-02T00:00:00Z\')</id>
        <title/>
        <updated>2014-10-09T18:38:28Z</updated>
        <author>
            <name/>
        </author>
        <content type="application/xml">
            <m:properties>
                <d:Timestamp m:type="Edm.DateTime">2014-10-02T00:00:00Z</d:Timestamp>
                <d:Min m:type="Edm.Int64">-118</d:Min>
                <d:Max m:type="Edm.Int64">15</d:Max>
                <d:Average m:type="Edm.Single">-78.44444</d:Average>
                <d:Total m:type="Edm.Int64">0</d:Total>
            </m:properties>
        </content>
    </entry>
        '''

        xmldoc = minidom.parseString(xmlstr)
        return_obj = object_type()

        members = dict(vars(return_obj))

        # Only one entry here
        for xml_entry in _get_children_from_path(xmldoc,
                                                 'entry'):
            for node in _get_children_from_path(xml_entry,
                                                'content',
                                                'm:properties'):
                for name in members:
                    xml_name = "d:" + _get_serialization_name(name)
                    children = _get_child_nodes(node, xml_name)
                    if not children:
                        continue
                    child = children[0]
                    node_type = child.getAttributeNS("http://schemas.microsoft.com/ado/2007/08/dataservices/metadata", 'type')
                    node_value = _ServiceBusManagementXmlSerializer.odata_converter(child.firstChild.nodeValue, node_type)
                    setattr(return_obj, name, node_value)
            for name, value in _get_entry_properties_from_node(xml_entry,
                                                               include_id=True,
                                                               use_title_as_id=False).items():
                if name in members:
                    continue  # Do not override if already members
                setattr(return_obj, name, value)
        return return_obj

from azure.servicemanagement.servicemanagementservice import (
    ServiceManagementService)
from azure.servicemanagement.servicebusmanagementservice import (
    ServiceBusManagementService)
from azure.servicemanagement.websitemanagementservice import (
    WebsiteManagementService)
