9#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Sean Sullivan <ssulliva@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
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
    name: "source-inventory"
    description: Source for inventory
    organization: previously-created-inventory
    script: previously-created-credential
'''

from ..module_utils.tower_api import TowerModule
from json import dumps


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        script=dict(required=True),
        organization=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    inventory = module.params.get('inventory')
    script = module.params.get('source_script')
    credential = module.params.get('credential')
    source_project = module.params.get('source_project')
    state = module.params.get('state')


    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory_script)


    # Create the data that gets sent for create and update
    inventory_script_fields = {
        'name': new_name if new_name else name,
        'inventory': inventory_id,
    }

    OPTIONAL_VARS = (
        'description'
    )

    # Layer in all remaining optional information
    for field_name in OPTIONAL_VARS:
        field_val = module.params.get(field_name)
        if field_val:
            inventory_script_fields[field_name] = field_val

    # Attempt to JSON encode source vars
    if inventory_script_fields.get('source_vars', None):
        inventory_script_fields['source_vars'] = dumps(inventory_script_fields['source_vars'])

    # Sanity check on arguments
    if state == 'present' and not inventory_script and not inventory_script_fields['source']:
        module.fail_json(msg="If creating a new inventory source, the source param must be present")

    # If the state was present we can let the module build or update the existing inventory_script, this will return on its own
    module.create_or_update_if_needed(
        inventory_script, inventory_script_fields,
        endpoint='inventory_scripts', item_type='inventory script',
    )


if __name__ == '__main__':
    main()
