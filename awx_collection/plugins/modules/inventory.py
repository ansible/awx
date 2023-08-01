#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: inventory
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller inventory.
description:
    - Create, update, or destroy Automation Platform Controller inventories. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      type: str
    copy_from:
      description:
        - Name or id to copy the inventory from.
        - This will copy an existing inventory and change any parameters supplied.
        - The new inventory name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple inventories share the same name.
      type: str
    description:
      description:
        - The description to use for the inventory.
      type: str
    organization:
      description:
        - Organization name, ID, or named URL the inventory belongs to.
      required: True
      type: str
    variables:
      description:
        - Inventory variables.
      type: dict
    kind:
      description:
        - The kind field. Cannot be modified after created.
      choices: ["", "smart", "constructed"]
      type: str
    host_filter:
      description:
        - The host_filter field. Only useful when C(kind=smart).
      type: str
    instance_groups:
      description:
        - list of Instance Group names, IDs, or named URLs for this Organization to run on.
      type: list
      elements: str
    input_inventories:
      description:
        - List of Inventory names, IDs, or named URLs to use as input for Constructed Inventory.
      type: list
      elements: str
    prevent_instance_group_fallback:
      description:
        - Prevent falling back to instance groups set on the organization
      type: bool
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent", "exists"]
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add inventory
  inventory:
    name: "Foo Inventory"
    description: "Our Foo Cloud Servers"
    organization: "Bar Org"
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Copy inventory
  inventory:
    name: Copy Foo Inventory
    copy_from: Default Inventory
    description: "Our Foo Cloud Servers"
    organization: Foo
    state: present

# You can create and modify constructed inventories by creating an inventory
# of kind "constructed" and then editing the automatically generated inventory
# source for that inventory.
- name: Add constructed inventory with two existing input inventories
  inventory:
    name: My Constructed Inventory
    organization: Default
    kind: constructed
    input_inventories:
      - "West Datacenter"
      - "East Datacenter"

- name: Edit the constructed inventory source
  inventory_source:
    # The constructed inventory source will always be in the format:
    # "Auto-created source for: <constructed inventory name>"
    name: "Auto-created source for: My Constructed Inventory"
    inventory: My Constructed Inventory
    limit: host3,host4,host6
    source_vars:
      plugin: constructed
      strict: true
      use_vars_plugins: true
      groups:
        shutdown: resolved_state == "shutdown"
        shutdown_in_product_dev: resolved_state == "shutdown" and account_alias == "product_dev"
      compose:
        resolved_state: state | default("running")
'''


from ..module_utils.controller_api import ControllerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        copy_from=dict(),
        description=dict(),
        organization=dict(required=True),
        variables=dict(type='dict'),
        kind=dict(choices=['', 'smart', 'constructed']),
        host_filter=dict(),
        instance_groups=dict(type="list", elements='str'),
        prevent_instance_group_fallback=dict(type='bool'),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),
        input_inventories=dict(type='list', elements='str'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    copy_from = module.params.get('copy_from')
    description = module.params.get('description')
    organization = module.params.get('organization')
    variables = module.params.get('variables')
    state = module.params.get('state')
    kind = module.params.get('kind')
    host_filter = module.params.get('host_filter')
    prevent_instance_group_fallback = module.params.get('prevent_instance_group_fallback')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up inventory based on the provided name and org ID
    inventory = module.get_one('inventories', name_or_id=name, check_exists=(state == 'exists'), **{'data': {'organization': org_id}})

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        inventory = module.copy_item(
            inventory,
            copy_from,
            name,
            endpoint='inventories',
            item_type='inventory',
            copy_lookup_data={},
        )

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory)

    # Create the data that gets sent for create and update
    inventory_fields = {
        'name': new_name if new_name else (module.get_item_name(inventory) if inventory else name),
        'organization': org_id,
        'kind': kind,
        'host_filter': host_filter,
    }
    if prevent_instance_group_fallback is not None:
        inventory_fields['prevent_instance_group_fallback'] = prevent_instance_group_fallback
    if description is not None:
        inventory_fields['description'] = description
    if variables is not None:
        inventory_fields['variables'] = json.dumps(variables)

    association_fields = {}

    instance_group_names = module.params.get('instance_groups')
    if instance_group_names is not None:
        association_fields['instance_groups'] = []
        for item in instance_group_names:
            association_fields['instance_groups'].append(module.resolve_name_to_id('instance_groups', item))

    # We need to perform a check to make sure you are not trying to convert a regular inventory into a smart one.
    if inventory and inventory['kind'] == '' and inventory_fields['kind'] == 'smart':
        module.fail_json(msg='You cannot turn a regular inventory into a "smart" inventory.')

    if kind == 'constructed':
        input_inventory_names = module.params.get('input_inventories')
        if input_inventory_names is not None:
            association_fields['input_inventories'] = []
            for item in input_inventory_names:
                association_fields['input_inventories'].append(module.resolve_name_to_id('inventories', item))

    # If the state was present and we can let the module build or update the existing inventory, this will return on its own
    module.create_or_update_if_needed(
        inventory,
        inventory_fields,
        endpoint='inventories',
        item_type='inventory',
        associations=association_fields,
    )


if __name__ == '__main__':
    main()
