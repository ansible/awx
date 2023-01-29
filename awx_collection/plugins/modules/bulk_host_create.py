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
    - Designed to efficiently add many hosts to an inventory.
options:
    hosts:
      description:
        - List of hosts to add to inventory.
      required: True
      type: str
    inventory:
      description:
        - Inventory the hosts should be made a member of.
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
        hosts=dict(required=True, type='list'),
        inventory=dict(),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    inventory = module.params.get('inventory')
    hosts = module.params.get('hosts')

    # Launch the jobs
    result = module.post_endpoint("bulk/host_create", data={"inventory": inventory, "hosts": hosts})

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to create hosts, see response for details", response=result)

    module.json_output['changed'] = True

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()