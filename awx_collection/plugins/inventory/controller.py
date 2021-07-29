# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
name: controller
plugin_type: inventory
author:
  - Matthew Jones (@matburt)
  - Yunfan Zhang (@YunfanZhang42)
short_description: Ansible dynamic inventory plugin for the Automation Platform Controller.
description:
    - Reads inventories from the Automation Platform Controller.
    - Supports reading configuration from both YAML config file and environment variables.
    - If reading from the YAML file, the file name must end with controller.(yml|yaml) or controller_inventory.(yml|yaml),
      the path in the command would be /path/to/controller_inventory.(yml|yaml). If some arguments in the config file
      are missing, this plugin will try to fill in missing arguments by reading from environment variables.
    - If reading configurations from environment variables, the path in the command must be @controller_inventory.
extends_documentation_fragment: awx.awx.auth_plugin
options:
    inventory_id:
        description:
            - The ID of the inventory that you wish to import.
            - This is allowed to be either the inventory primary key or its named URL slug.
            - Primary key values will be accepted as strings or integers, and URL slugs must be strings.
            - Named URL slugs follow the syntax of "inventory_name++organization_name".
        type: raw
        env:
            - name: CONTROLLER_INVENTORY
        required: True
    include_metadata:
        description: Make extra requests to provide all group vars with metadata about the source host.
        type: bool
        default: False
'''

EXAMPLES = '''
# Before you execute the following commands, you should make sure this file is in your plugin path,
# and you enabled this plugin.

# Example for using controller_inventory.yml file

plugin: awx.awx.controller
host: your_automation_controller_server_network_address
username: your_automation_controller_username
password: your_automation_controller_password
inventory_id: the_ID_of_targeted_automation_controller_inventory
# Then you can run the following command.
# If some of the arguments are missing, Ansible will attempt to read them from environment variables.
# ansible-inventory -i /path/to/controller_inventory.yml --list

# Example for reading from environment variables:

# Set environment variables:
# export CONTROLLER_HOST=YOUR_AUTOMATION_PLATFORM_CONTROLLER_HOST_ADDRESS
# export CONTROLLER_USERNAME=YOUR_CONTROLLER_USERNAME
# export CONTROLLER_PASSWORD=YOUR_CONTROLLER_PASSWORD
# export CONTROLLER_INVENTORY=THE_ID_OF_TARGETED_INVENTORY
# Read the inventory specified in CONTROLLER_INVENTORY from the controller, and list them.
# The inventory path must always be @controller_inventory if you are reading all settings from environment variables.
# ansible-inventory -i @controller_inventory --list
'''

import os

from ansible.module_utils import six
from ansible.module_utils._text import to_text, to_native
from ansible.errors import AnsibleParserError, AnsibleOptionsError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.config.manager import ensure_type

from ansible.module_utils.six import raise_from
from ..module_utils.controller_api import ControllerAPIModule


def handle_error(**kwargs):
    raise AnsibleParserError(to_native(kwargs.get('msg')))


class InventoryModule(BaseInventoryPlugin):
    NAME = 'awx.awx.controller'  # REPLACE
    # Stays backward compatible with the inventory script.
    # If the user supplies '@controller_inventory' as path, the plugin will read from environment variables.
    no_config_file_supplied = False

    def verify_file(self, path):
        if path.endswith('@controller_inventory') or path.endswith('@tower_inventory'):
            self.no_config_file_supplied = True
            return True
        elif super().verify_file(path):
            return path.endswith(
                (
                    'controller_inventory.yml',
                    'controller_inventory.yaml',
                    'controller.yml',
                    'controller.yaml',
                    'tower_inventory.yml',
                    'tower_inventory.yaml',
                    'tower.yml',
                    'tower.yaml',
                )
            )
        else:
            return False

    def warn_callback(self, warning):
        self.display.warning(warning)

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path)
        if not self.no_config_file_supplied and os.path.isfile(path):
            self._read_config_data(path)

        # Defer processing of params to logic shared with the modules
        module_params = {}
        for plugin_param, module_param in ControllerAPIModule.short_params.items():
            opt_val = self.get_option(plugin_param)
            if opt_val is not None:
                module_params[module_param] = opt_val

        module = ControllerAPIModule(argument_spec={}, direct_params=module_params, error_callback=handle_error, warn_callback=self.warn_callback)

        # validate type of inventory_id because we allow two types as special case
        inventory_id = self.get_option('inventory_id')
        if isinstance(inventory_id, int):
            inventory_id = to_text(inventory_id, nonstring='simplerepr')
        else:
            try:
                inventory_id = ensure_type(inventory_id, 'str')
            except ValueError as e:
                raise_from(AnsibleOptionsError(
                    'Invalid type for configuration option inventory_id, ' 'not integer, and cannot convert to string: {err}'.format(err=to_native(e))
                ), e)
        inventory_id = inventory_id.replace('/', '')
        inventory_url = '/api/v2/inventories/{inv_id}/script/'.format(inv_id=inventory_id)

        inventory = module.get_endpoint(inventory_url, data={'hostvars': '1', 'towervars': '1', 'all': '1'})['json']

        # To start with, create all the groups.
        for group_name in inventory:
            if group_name != '_meta':
                self.inventory.add_group(group_name)

        # Then, create all hosts and add the host vars.
        all_hosts = inventory['_meta']['hostvars']
        for host_name, host_vars in six.iteritems(all_hosts):
            self.inventory.add_host(host_name)
            for var_name, var_value in six.iteritems(host_vars):
                self.inventory.set_variable(host_name, var_name, var_value)

        # Lastly, create to group-host and group-group relationships, and set group vars.
        for group_name, group_content in six.iteritems(inventory):
            if group_name != 'all' and group_name != '_meta':
                # First add hosts to groups
                for host_name in group_content.get('hosts', []):
                    self.inventory.add_host(host_name, group_name)
                # Then add the parent-children group relationships.
                for child_group_name in group_content.get('children', []):
                    # add the child group to groups, if its already there it will just throw a warning
                    self.inventory.add_group(child_group_name)
                    self.inventory.add_child(group_name, child_group_name)
            # Set the group vars. Note we should set group var for 'all', but not '_meta'.
            if group_name != '_meta':
                for var_name, var_value in six.iteritems(group_content.get('vars', {})):
                    self.inventory.set_variable(group_name, var_name, var_value)

        # Fetch extra variables if told to do so
        if self.get_option('include_metadata'):

            config_data = module.get_endpoint('/api/v2/config/')['json']

            server_data = {}
            server_data['license_type'] = config_data.get('license_info', {}).get('license_type', 'unknown')
            for key in ('version', 'ansible_version'):
                server_data[key] = config_data.get(key, 'unknown')
            self.inventory.set_variable('all', 'tower_metadata', server_data)
            self.inventory.set_variable('all', 'controller_metadata', server_data)

        # Clean up the inventory.
        self.inventory.reconcile_inventory()
