#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory_source
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: create, update, or destroy Ansible Tower inventory source.
description:
    - Create, update, or destroy Ansible Tower inventory source. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory source.
      required: True
      type: str
    new_name:
      description:
        - A new name for this assets (will rename the asset)
      required: False
      type: str
      version_added: "3.7"
    description:
      description:
        - The description to use for the inventory source.
      type: str
    inventory:
      description:
        - Inventory the group should be made a member of.
      required: True
      type: str
    source:
      description:
        - The source to use for this group.
      choices: [ "scm", "ec2", "gce", "azure_rm", "vmware", "satellite6", "cloudforms", "openstack", "rhv", "tower", "custom" ]
      type: str
      required: False
    source_path:
      description:
        - For an SCM based inventory source, the source path points to the file within the repo to use as an inventory.
      type: str
    source_script:
      description:
        - Inventory script to be used when group type is C(custom).
      type: str
      required: False
    source_vars:
      description:
        - The variables or environment fields to apply to this source type.
      type: dict
    credential:
      description:
        - Credential to use for the source.
      type: str
    source_regions:
      description:
        - Regions for cloud provider.
      type: str
    instance_filters:
      description:
        - Comma-separated list of filter expressions for matching hosts.
      type: str
    group_by:
      description:
        - Limit groups automatically created from inventory source.
      type: str
    overwrite:
      description:
        - Delete child groups and hosts not found in source.
      type: bool
      default: 'no'
    overwrite_vars:
      description:
        - Override vars in child groups and hosts with those from external source.
      type: bool
    custom_virtualenv:
      version_added: "2.9"
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
      type: str
      required: False
      default: ''
    timeout:
      description: The amount of time (in seconds) to run before the task is canceled.
      type: int
    verbosity:
      description: The verbosity level to run this inventory source under.
      type: int
      choices: [ 0, 1, 2 ]
    update_on_launch:
      description:
        - Refresh inventory data from its source each time a job is run.
      type: bool
      default: 'no'
    update_cache_timeout:
      description:
        - Time in seconds to consider an inventory sync to be current.
      type: int
    source_project:
      description:
        - Project to use as source with scm option
      type: str
    update_on_project_update:
      description: Update this source when the related project updates if source is C(scm)
      type: bool
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
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Add an inventory source
  tower_inventory_source:
    name: "source-inventory"
    description: Source for inventory
    inventory: previously-created-inventory
    credential: previously-created-credential
    overwrite: True
    update_on_launch: True
    source_vars:
      private: false
'''

from ..module_utils.tower_api import TowerModule
from json import dumps


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(type='str'),
        description=dict(required=False),
        inventory=dict(required=True),
        #
        # How do we handle manual and file? Tower does not seem to be able to activate them
        #
        source=dict(choices=["scm", "ec2", "gce",
                             "azure_rm", "vmware", "satellite6", "cloudforms",
                             "openstack", "rhv", "tower", "custom"], required=False),
        source_path=dict(),
        source_script=dict(required=False),
        source_vars=dict(type='dict'),
        credential=dict(),
        source_regions=dict(),
        instance_filters=dict(),
        group_by=dict(),
        overwrite=dict(type='bool'),
        overwrite_vars=dict(type='bool'),
        custom_virtualenv=dict(type='str', default=''),
        timeout=dict(type='int'),
        verbosity=dict(type='int', choices=[0, 1, 2]),
        update_on_launch=dict(type='bool'),
        update_cache_timeout=dict(type='int'),
        source_project=dict(type='str'),
        update_on_project_update=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    inventory = module.params.get('inventory')
    source_script = module.params.get('source_script')
    credential = module.params.get('credential')
    source_project = module.params.get('source_project')
    state = module.params.get('state')

    # Attempt to look up inventory source based on the provided name and inventory ID
    inventory_id = module.resolve_name_to_id('inventories', inventory)
    inventory_source = module.get_one('inventory_sources', **{
        'data': {
            'name': name,
            'inventory': inventory_id,
        }
    })

    # Create the data that gets sent for create and update
    inventory_source_fields = {
        'name': new_name if new_name else name,
        'inventory': inventory_id,
    }

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if credential is not None:
        inventory_source_fields['credential'] = module.resolve_name_to_id('credentials', credential)
    if source_project is not None:
        inventory_source_fields['source_project'] = module.resolve_name_to_id('projects', source_project)
    if source_script is not None:
        inventory_source_fields['source_script'] = module.resolve_name_to_id('inventory_scripts', source_script)

    OPTIONAL_VARS = (
        'description', 'source', 'source_path', 'source_vars',
        'source_regions', 'instance_filters', 'group_by',
        'overwrite', 'overwrite_vars', 'custom_virtualenv',
        'timeout', 'verbosity', 'update_on_launch', 'update_cache_timeout',
        'update_on_project_update'
    )

    # Layer in all remaining optional information
    for field_name in OPTIONAL_VARS:
        field_val = module.params.get(field_name)
        if field_val:
            inventory_source_fields[field_name] = field_val

    # Attempt to JSON encode source vars
    if inventory_source_fields.get('source_vars', None):
        inventory_source_fields['source_vars'] = dumps(inventory_source_fields['source_vars'])

    # Sanity check on arguments
    if state == 'present' and not inventory_source and not inventory_source_fields['source']:
        module.fail_json(msg="If creating a new inventory source, the source param must be present")

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory_source)
    elif state == 'present':
        # If the state was present we can let the module build or update the existing inventory_source, this will return on its own
        module.create_or_update_if_needed(inventory_source, inventory_source_fields, endpoint='inventory_sources', item_type='inventory source')


if __name__ == '__main__':
    main()
