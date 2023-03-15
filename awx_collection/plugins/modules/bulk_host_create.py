#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: bulk_host_create
author: "Seth Foster (@fosterseth)"
short_description: Bulk host create in Automation Platform Controller
description:
    - Single-request bulk host creation in Automation Platform Controller.
    - Provides a way to add many hosts at once to an inventory in Controller.
options:
    hosts:
      description:
        - List of hosts to add to inventory.
      required: True
      type: list
      elements: dict
      suboptions:
        name:
          description:
            - The name to use for the host.
          type: str
          required: True
        description:
          description:
            - The description to use for the host.
          type: str
        enabled:
          description:
            - If the host should be enabled.
          type: bool
        variables:
          description:
            - Variables to use for the host.
          type: dict
        instance_id:
          description:
            - instance_id to use for the host.
          type: str
    inventory:
      description:
        - Inventory name or ID the hosts should be made a member of.
      required: True
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Bulk host create
  bulk_host_create:
    inventory: 1
    hosts:
      - name: foobar.org
      - name: 127.0.0.1
'''

from ..module_utils.controller_api import ControllerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        hosts=dict(required=True, type='list', elements='dict'),
        inventory=dict(required=True, type='str'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    inv_name = module.params.get('inventory')
    hosts = module.params.get('hosts')

    for h in hosts:
        if 'variables' in h:
            h['variables'] = json.dumps(h['variables'])

    inv_id = module.resolve_name_to_id('inventories', inv_name)

    # Launch the jobs
    result = module.post_endpoint("bulk/host_create", data={"inventory": inv_id, "hosts": hosts})

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to create hosts, see response for details", response=result)

    module.json_output['changed'] = True

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
