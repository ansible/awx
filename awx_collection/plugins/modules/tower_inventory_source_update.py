#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020, Bianca Henderson <bianca@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory_source_update
author: "Bianca Henderson (@beeankha)"
short_description: Update inventory source(s).
description:
    - Update Ansible Tower inventory source(s). See
      U(https://www.ansible.com/tower) for an overview.
options:
    inventory:
      description:
        - Name of the inventory that contains the inventory source(s) to update.
      required: True
      type: str
    inventory_source:
      description:
        - The name of the inventory source to update.
      required: True
      type: str
    organization:
      description:
        - Name of the inventory source's inventory's organization.
      type: str
    wait:
      description:
        - Wait for the job to complete.
      default: False
      type: bool
    interval:
      description:
        - The interval to request an update from Tower.
      required: False
      default: 1
      type: float
    timeout:
      description:
        - If waiting for the job to complete this will abort after this
          amount of seconds
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Update a single inventory source
  tower_inventory_source_update:
    inventory: "My Inventory"
    inventory_source: "Example Inventory Source"
    organization: Default

- name: Update all inventory sources
  tower_inventory_source_update:
    inventory: "My Other Inventory"
    inventory_source: "{{ item }}"
  loop: "{{ query('awx.awx.tower_api', 'inventory_sources', query_params={ 'inventory': 30 }, return_ids=True ) }}"
'''

RETURN = '''
id:
    description: id of the inventory update
    returned: success
    type: int
    sample: 86
status:
    description: status of the inventory update
    returned: success
    type: str
    sample: pending
'''

from ..module_utils.tower_api import TowerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        inventory=dict(required=True),
        inventory_source=dict(required=True),
        organization=dict(),
        wait=dict(default=False, type='bool'),
        interval=dict(default=1.0, type='float'),
        timeout=dict(default=None, type='int'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    inventory = module.params.get('inventory')
    inventory_source = module.params.get('inventory_source')
    organization = module.params.get('organization')
    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    lookup_data = {'name': inventory}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    inventory_object = module.get_one('inventories', data=lookup_data)

    if not inventory_object:
        module.fail_json(msg='The specified inventory, {0}, was not found.'.format(lookup_data))

    inventory_source_object = module.get_one('inventory_sources', **{
        'data': {
            'name': inventory_source,
            'inventory': inventory_object['id'],
        }
    })

    if not inventory_source_object:
        module.fail_json(msg='The specified inventory source was not found.')

    # Sync the inventory source(s)
    inventory_source_update_results = module.post_endpoint(inventory_source_object['related']['update'], **{'data': {}})

    if inventory_source_update_results['status_code'] != 202:
        module.fail_json(msg="Failed to update inventory source, see response for details", **{'response': inventory_source_update_results})

    module.json_output['changed'] = True
    module.json_output['id'] = inventory_source_update_results['json']['id']
    module.json_output['status'] = inventory_source_update_results['json']['status']

    if not wait:
        module.exit_json(**module.json_output)

    # Invoke wait function
    module.wait_on_url(
        url=inventory_source_update_results['json']['url'],
        object_name=inventory_object,
        object_type='inventory_update',
        timeout=timeout, interval=interval
    )

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
