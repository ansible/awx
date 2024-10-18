# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.

"""
This module contains the code responsible for extracting the lists of dynamically discovered plugins.
"""

from functools import cache


@cache
def discover_available_cloud_provider_plugin_names() -> list[str]:
    """Return a list of cloud plugin names available in runtime.

    The discovery result is cached since it does not change throughout
    the life cycle of the server run.

    :returns: List of plugin cloud names.
    :rtype: list[str]
    """
    from awx.main.models.inventory import InventorySourceOptions

    return list(InventorySourceOptions.injectors.keys())


@cache
def compute_cloud_inventory_sources() -> dict[str, str]:
    """Return a dictionary of cloud provider plugin names
    available plus source control management.

    :returns: Dictionary of plugin cloud names plus source control.
    :rtype: dict[str, str]
    """

    plugins = discover_available_cloud_provider_plugin_names()

    return dict(zip(plugins, plugins), scm='scm')
