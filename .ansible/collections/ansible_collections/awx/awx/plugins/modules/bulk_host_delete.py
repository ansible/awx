#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: bulk_host_delete
author: "Avi Layani (@Avilir)"
short_description: Bulk host delete in Automation Platform Controller
description:
    - Single-request bulk host deletion in Automation Platform Controller.
    - Provides a way to delete many hosts at once from inventories in Controller.
options:
    hosts:
      description:
        - List of hosts id's to delete from inventory.
      required: True
      type: list
      elements: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Bulk host delete
  bulk_host_delete:
    hosts:
      - 1
      - 2
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        hosts=dict(required=True, type='list', elements='int'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    hosts = module.params.get('hosts')

    # Delete the hosts
    result = module.post_endpoint("bulk/host_delete", data={"hosts": hosts})

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to delete hosts, see response for details", response=result)

    module.json_output['changed'] = True

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
