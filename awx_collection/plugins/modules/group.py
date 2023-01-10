#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: group
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller group.
description:
    - Create, update, or destroy Automation Platform Controller groups. See
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
    variables:
      description:
        - Variables to use for the group.
      type: dict
    hosts:
      description:
        - List of hosts that should be put in this group.
      type: list
      elements: str
    children:
      description:
        - List of groups that should be nested inside in this group.
      type: list
      elements: str
      aliases:
        - groups
    preserve_existing_hosts:
      description:
        - Provide option (False by default) to preserves existing hosts in an existing group.
      default: False
      type: bool
    preserve_existing_children:
      description:
        - Provide option (False by default) to preserves existing children in an existing group.
      default: False
      type: bool
      aliases:
        - preserve_existing_groups
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    new_name:
      description:
        - A new name for this group (for renaming)
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add group
  group:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add group
  group:
    name: Cities
    description: "Local Host Group"
    inventory: Default Inventory
    hosts:
      - fda
    children:
      - NewYork
    preserve_existing_hosts: True
    preserve_existing_children: True
'''

from ..module_utils.controller_api import ControllerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        inventory=dict(required=True),
        variables=dict(type='dict'),
        hosts=dict(type='list', elements='str'),
        children=dict(type='list', elements='str', aliases=['groups']),
        preserve_existing_hosts=dict(type='bool', default=False),
        preserve_existing_children=dict(type='bool', default=False, aliases=['preserve_existing_groups']),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    inventory = module.params.get('inventory')
    description = module.params.get('description')
    state = module.params.pop('state')
    preserve_existing_hosts = module.params.get('preserve_existing_hosts')
    preserve_existing_children = module.params.get('preserve_existing_children')
    variables = module.params.get('variables')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory_id = module.resolve_name_to_id('inventories', inventory)

    # Attempt to look up the object based on the provided name and inventory ID
    group = module.get_one('groups', name_or_id=name, **{'data': {'inventory': inventory_id}})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(group)

    # Create the data that gets sent for create and update
    group_fields = {
        'name': new_name if new_name else (module.get_item_name(group) if group else name),
        'inventory': inventory_id,
    }
    if description is not None:
        group_fields['description'] = description
    if variables is not None:
        group_fields['variables'] = json.dumps(variables)

    association_fields = {}
    for resource, relationship in (('hosts', 'hosts'), ('groups', 'children')):
        name_list = module.params.get(relationship)
        if name_list is None:
            continue
        id_list = []
        for sub_name in name_list:
            sub_obj = module.get_one(
                resource,
                name_or_id=sub_name,
                **{
                    'data': {'inventory': inventory_id},
                }
            )
            if sub_obj is None:
                module.fail_json(msg='Could not find {0} with name {1}'.format(resource, sub_name))
            id_list.append(sub_obj['id'])
        # Preserve existing objects
        if (preserve_existing_hosts and relationship == 'hosts') or (preserve_existing_children and relationship == 'children'):
            preserve_existing_check = module.get_all_endpoint(group['related'][relationship])
            for sub_obj in preserve_existing_check['json']['results']:
                id_list.append(sub_obj['id'])
        if id_list:
            association_fields[relationship] = id_list

    # If the state was present we can let the module build or update the existing group, this will return on its own
    module.create_or_update_if_needed(group, group_fields, endpoint='groups', item_type='group', associations=association_fields)


if __name__ == '__main__':
    main()
