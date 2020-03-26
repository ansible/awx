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
module: tower_group
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower group.
description:
    - Create, update, or destroy Ansible Tower groups. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the group.
      required: True
      type: str
    description:
      description:
        - The description to use for the group.
      type: str
    inventory:
      description:
        - Inventory the group should be made a member of.
      required: True
      type: str
    organization:
      description:
        - Organization that the inventory is in.
      required: False
      type: str
    variables:
      description:
        - Variables to use for the group.
      type: dict
    hosts:
      description:
        - List of hosts that should be put in this group.
      required: False
      type: list
      elements: str
    children:
      description:
        - List of groups that should be nested inside in this group.
      required: False
      type: list
      elements: str
      aliases:
        - groups
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    new_name:
      description:
        - A new name for this group (for renaming)
      required: False
      type: str
      version_added: "3.7"
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add tower group
  tower_group:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
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
        organization=dict(),
        variables=dict(type='dict'),
        hosts=dict(type='list', elements='str'),
        children=dict(type='list', elements='str', aliases=['groups']),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    state = module.params.pop('state')
    variables = module.params.get('variables')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    # Attempt to look up the object based on the provided name and inventory ID
    group, related_data = module.lookup_resource_data('groups', module.params)
    inventory_id = related_data['inventory']['id']

    # Create the data that gets sent for create and update
    group_fields = {
        'name': new_name if new_name else name,
        'inventory': inventory_id,
    }
    if description is not None:
        group_fields['description'] = description
    if variables is not None:
        group_fields['variables'] = json.dumps(variables)

    association_fields = {}
    for relationship in ('hosts', 'children'):
        if relationship in related_data:
            association_fields[relationship] = [item['id'] for item in related_data[relationship]]

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(group)
    elif state == 'present':
        # If the state was present we can let the module build or update the existing group, this will return on its own
        module.create_or_update_if_needed(
            group, group_fields, endpoint='groups', item_type='group',
            associations=association_fields
        )


if __name__ == '__main__':
    main()
