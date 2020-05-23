#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Sean Sullivan <ssulliva@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ..module_utils.tower_api import TowerModule
from json import dumps
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory_script
author: "Sean Sullivan (@Wilk42)"
version_added: "2.9"
short_description: create, update, or destroy Ansible Tower inventory script.
description:
    - Create, update, or destroy Ansible Tower inventory script. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory script.
      required: True
      type: str
    new_name:
      description:
        - A new name for this assets (will rename the asset)
      type: str
      version_added: "3.7"
    description:
      description:
        - The description to use for the inventory script.
      type: str
    script:
      description:
        - Scirpt string to use of the inventory script
      required: True
      type: str
    organization:
      description:
        - Name of organization for inventory script.
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
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
- name: Add an inventory script
  tower_inventory_script:
    name: "Inventory Script"
    description: "Inventory Script"
    organization: "Default"
    script: "{{ lookup('file', 'file.py') }}",
'''


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        organization=dict(required=True),
        description=dict(),
        script=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    organization = module.params.get('organization')
    description = module.params.get('description')
    script = module.params.get('script')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up an existing item based on the provided data
    inventory_script = module.get_one('inventory_scripts', **{
        'data': {
            'name': name,
            'organization': organization_id,
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory_script)

    # Create the data that gets sent for create and update
    new_fields = {}
    new_fields['name'] = new_name if new_name else name
    new_fields['organization'] = organization_id
    if description is not None:
        new_fields['description'] = description
    new_fields['script'] = script

    module.create_or_update_if_needed(
        inventory_script, new_fields,
        endpoint='inventory_scripts', item_type='inventory_script',
        associations={
        }
    )

if __name__ == '__main__':
    main()
