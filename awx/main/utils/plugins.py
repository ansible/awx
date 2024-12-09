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
def discover_available_cloud_provider_descriptions() -> dict[str, str]:
    """
    Return a dictionary of cloud provider plugin descriptions
    available.

    :returns: Dictionary of plugin cloud descriptions.
    :rtype: dict[str, str]
    """
    from awx.main.models.inventory import InventorySourceOptions

    plugin_description_list = [(plugin_name, plugin.plugin_description) for plugin_name, plugin in InventorySourceOptions.injectors.items()]

    plugin_description = dict(plugin_description_list)

    return plugin_description


@cache
def load_combined_inventory_source_options() -> dict[str, str]:
    """
    Return a dictionary of cloud provider plugin names and 'file'.

    The 'file' entry is included separately since it needs to be consumed directly by the serializer.

    :returns: A dictionary of cloud provider plugin names (as both keys and values) plus the 'file' entry.
    :rtype: dict[str, str]
    """

    plugins = compute_cloud_inventory_sources()

    plugin_description = discover_available_cloud_provider_descriptions()

    if 'scm' in plugins:
        plugin_description['scm'] = 'Sourced from a Project'

    if 'file' in plugins:
        plugin_description['file'] = 'File-based inventory source'

    result = {plugin: plugin_description.get(plugin, plugin) for plugin in plugins}

    return result
