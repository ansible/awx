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
module: tower_host
version_added: "2.3"
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower host.
description:
    - Create, update, or destroy Ansible Tower hosts. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the host.
      required: True
      type: str
    new_name:
      description:
        - To use when changing a hosts's name.
      type: str
      version_added: "3.7"
    description:
      description:
        - The description to use for the host.
      type: str
    inventory:
      description:
        - Inventory the host should be made a member of.
      required: True
      type: str
    enabled:
      description:
        - If the host should be enabled.
      type: bool
      default: 'yes'
    variables:
      description:
        - Variables to use for the host.
      type: dict
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
        - If value not set, will try environment variable C(TOWER_OAUTH_TOKEN) and then config files
      type: str
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add tower host
  tower_host:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
    variables:
      example_var: 123
'''


from ..module_utils.tower_api import TowerModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        inventory=dict(required=True),
        enabled=dict(type='bool', default=True),
        variables=dict(type='dict'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    inventory = module.params.get('inventory')
    enabled = module.params.get('enabled')
    state = module.params.get('state')
    variables = module.params.get('variables')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory_id = module.resolve_name_to_id('inventories', inventory)

    # Attempt to look up host based on the provided name and inventory ID
    host = module.get_one('hosts', **{
        'data': {
            'name': name,
            'inventory': inventory_id
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(host)

    # Create the data that gets sent for create and update
    host_fields = {
        'name': new_name if new_name else name,
        'inventory': inventory_id,
        'enabled': enabled,
    }
    if description is not None:
        host_fields['description'] = description
    if variables is not None:
        host_fields['variables'] = json.dumps(variables)

    # If the state was present and we can let the module build or update the existing host, this will return on its own
    module.create_or_update_if_needed(host, host_fields, endpoint='hosts', item_type='host')


if __name__ == '__main__':
    main()
