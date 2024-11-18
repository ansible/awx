# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.

"""
This module contains the code responsible for extracting the lists of dynamically discovered plugins.
"""

from functools import cache


@cache
def discover_available_cloud_provider_plugin_names() -> list[str]:
    """
    Return a list of cloud plugin names available in runtime.

    The discovery result is cached since it does not change throughout
    the life cycle of the server run.

    :returns: List of plugin cloud names.
    :rtype: list[str]
    """
    from awx.main.models.inventory import InventorySourceOptions

    plugin_names = list(InventorySourceOptions.injectors.keys())

    plugin_names.remove('constructed')

    return plugin_names


@cache
def compute_cloud_inventory_sources() -> dict[str, str]:
    """
    Return a dictionary of cloud provider plugin names
    available plus source control management and constructed.

    :returns: Dictionary of plugin cloud names plus source control.
    :rtype: dict[str, str]
    """

    plugins = discover_available_cloud_provider_plugin_names()

    return dict(zip(plugins, plugins), scm='scm', constructed='constructed')


@cache
def load_combined_inventory_source_options() -> dict[str, str]:
    """
    Return a dictionary of cloud provider plugin names and 'file'.

    The 'file' entry is included separately since it needs to be consumed directly by the serializer.

    :returns: A dictionary of cloud provider plugin names (as both keys and values) plus the 'file' entry.
    :rtype: dict[str, str]
    """

    plugins = compute_cloud_inventory_sources()

    plugin_descriptions = {
        'azure_rm': 'Microsoft Azure Resource Manager',
        'ec2': 'Amazon EC2',
        'gce': 'Google Compute Engine',
        'vmware': 'VMware vCenter',
        'satellite6': 'Red Hat Satellite 6',
        'satellite6_supported': 'Supported Red Hat Satellite 6',
        'openstack': 'OpenStack',
        'rhv': 'Red Hat Virtualization',
        'rhv_supported': 'Supported Red Hat Virtualization',
        'foreman': 'Red Hat Satellite 6',
        'terraform': 'Terraform',
        'controller': 'Red Hat Ansible Automation Platform',
        'controller_supported': 'Supported Red Hat Ansible Automation Platform',
        'openshift_virtualization': 'OpenShift Virtualization',
        'openshift_virtualization_supported': 'Supported OpenShift Virtualization',
        'scm': 'Sourced from a Project',
        'insights': 'Red Hat Insights',
        'insights_supported': 'Red Hat Insights',
        'kubevirt': 'OpenShift Virtualization',
        'constructed': 'Template additional groups and hostvars at runtime',
    }

    result = {plugin: plugin_descriptions.get(plugin, plugin) for plugin in plugins}

    result['file'] = 'File-based inventory source'

    return result
