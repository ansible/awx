#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower inventory.
description:
    - Create, update, or destroy Ansible Tower inventories. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory.
      required: True
      type: str
    description:
      description:
        - The description to use for the inventory.
      type: str
    organization:
      description:
        - Organization the inventory belongs to.
      required: True
      type: str
    variables:
      description:
        - Inventory variables.
      type: dict
    kind:
      description:
        - The kind field. Cannot be modified after created.
      default: ""
      choices: ["", "smart"]
      type: str
    host_filter:
      description:
        - The host_filter field. Only useful when C(kind=smart).
      type: str
    insights_credential:
      description:
        - Credentials to be used by hosts belonging to this inventory when accessing Red Hat Insights API.
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add tower inventory
  tower_inventory:
    name: "Foo Inventory"
    description: "Our Foo Cloud Servers"
    organization: "Bar Org"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''


from ..module_utils.tower_api import TowerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        organization=dict(required=True),
        variables=dict(type='dict'),
        kind=dict(choices=['', 'smart'], default=''),
        host_filter=dict(),
        insights_credential=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    variables = module.params.get('variables')
    state = module.params.get('state')
    kind = module.params.get('kind')
    host_filter = module.params.get('host_filter')
    insights_credential = module.params.get('insights_credential')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up inventory based on the provided name and org ID
    inventory = module.get_one('inventories', name_or_id=name, **{
        'data': {
            'organization': org_id
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory)

    # Create the data that gets sent for create and update
    inventory_fields = {
        'name': module.get_item_name(inventory) if inventory else name,
        'organization': org_id,
        'kind': kind,
        'host_filter': host_filter,
    }
    if description is not None:
        inventory_fields['description'] = description
    if variables is not None:
        inventory_fields['variables'] = json.dumps(variables)
    if insights_credential is not None:
        inventory_fields['insights_credential'] = module.resolve_name_to_id('credentials', insights_credential)

    # We need to perform a check to make sure you are not trying to convert a regular inventory into a smart one.
    if inventory and inventory['kind'] == '' and inventory_fields['kind'] == 'smart':
        module.fail_json(msg='You cannot turn a regular inventory into a "smart" inventory.')

    # If the state was present and we can let the module build or update the existing inventory, this will return on its own
    module.create_or_update_if_needed(inventory, inventory_fields, endpoint='inventories', item_type='inventory')


if __name__ == '__main__':
    main()
