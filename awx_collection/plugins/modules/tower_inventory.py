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
version_added: "2.3"
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
        - Inventory variables. Use C(@) to get from file.
      type: str
    kind:
      description:
        - The kind field. Cannot be modified after created.
      default: ""
      choices: ["", "smart"]
      version_added: "2.7"
      type: str
    host_filter:
      description:
        -  The host_filter field. Only useful when C(kind=smart).
      version_added: "2.7"
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
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


from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(default=''),
        organization=dict(required=True),
        variables=dict(default=''),
        kind=dict(choices=['', 'smart'], default=''),
        host_filter=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    variables = module.params.get('variables')
    state = module.params.get('state')
    kind = module.params.get('kind')
    host_filter = module.params.get('host_filter')

    # Attempt to lookup the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to lookup inventory based on the provided name and org ID
    inventory = module.get_one('inventories', **{
        'data': {
            'name': name,
            'organization': org_id
        }
    })

    # Create data to sent to create and update
    inventory_fields = {
        'name': name,
        'description': description,
        'organization': org_id,
        'variables': variables,
        'kind': kind,
        'host_filter': host_filter,
    }

    if state == 'absent' and not inventory:
        # If the state was absent and we had no inventory, we can just return
        module.exit_json(**module.json_output)
    elif state == 'absent' and inventory:
        # If the state was absent and we had a inventory, we can try to delete it, the module will handle exiting from this
        module.delete_endpoint('inventories/{0}'.format(inventory['id']), item_type='inventory', item_name=name, **{})
    elif state == 'present' and not inventory:
        # If the state was present and we couldn't find a inventory we can build one, the module will handle exiting from this
        module.post_endpoint('inventories', item_type='inventory', item_name=name, **{'data': inventory_fields})
    else:
        # Throw a more specific error message than what the API page provides.
        if inventory['kind'] == '' and inventory_fields['kind'] == 'smart':
            module.fail_json(msg='You cannot turn a regular inventory into a "smart" inventory.')
        # If the state was present and we had a inventory, we can see if we need to update it
        # This will return on its own
        module.update_if_needed(inventory, inventory_fields)


if __name__ == '__main__':
    main()
