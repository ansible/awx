#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2023 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: receptor_address
author: "Seth Foster (@fosterseth)"
version_added: "4.5.0"
short_description: create, update, or destroy Automation Platform Controller receptor addresses.
description:
    - Create, update, or destroy Automation Platform Controller receptor addresses. See
      U(https://www.ansible.com/tower) for an overview.
options:
    address:
      description:
        - Routable address for this instance.
      required: True
      type: str
    instance:
      description:
        - ID or hostname of instance this address belongs to.
      required: True
      type: str
    peers_from_control_nodes:
      description:
        - If True, control plane cluster nodes should automatically peer to it.
      required: False
      type: bool
    port:
      description:
        - Port for the address.
      required: False
      type: int
    protocol:
      description:
        - Protocol to use when connecting.
      required: False
      type: str
      choices: [ 'tcp', 'ws', 'wss' ]
    websocket_path:
      description:
        - Websocket path.
      required: False
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent", "exists"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
  - name: Create receptor address
    awx.awx.receptor_address:
      address: exec1addr
      instance: exec1.example.com
      peers_from_control_nodes: false
      port: 6791
      protocol: ws
      websocket_path: service
      state: present
    register: exec1addr
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        address=dict(required=True, type='str'),
        instance=dict(type='str'),
        peers_from_control_nodes=dict(type='bool'),
        port=dict(type='int'),
        protocol=dict(type='str'),
        websocket_path=dict(type='str'),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),

    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    address = module.params.get('address')
    peers_from_control_nodes = module.params.get('peers_from_control_nodes')
    port = module.params.get('port')
    protocol = module.params.get('protocol', 'tcp')
    websocket_path = module.params.get('websocket_path')
    instance_name_or_id = module.params.get('instance')
    state = module.params.get('state')

    # Attempt to look up an existing instance
    receptor_address = module.get_one('receptor_addresses', allow_none=True, data=dict(address=address, protocol=protocol))
    if receptor_address:
       receptor_address['type'] = 'receptor_address'

    if receptor_address and state == 'absent':
        module.delete_if_needed(receptor_address)

    instance = module.get_one('instances', allow_none=False, name_or_id=instance_name_or_id)

    # Create the data that gets sent for create and update
    new_fields = {'instance': instance['id'], 'address': address}
    if port:
      new_fields['port'] = port
    if protocol:
      new_fields['protocol'] = protocol
    if peers_from_control_nodes:
      new_fields['peers_from_control_nodes'] = peers_from_control_nodes
    if websocket_path:
      new_fields['websocket_path'] = websocket_path

    module.create_or_update_if_needed(
        receptor_address,
        new_fields,
        endpoint='receptor_addresses',
        item_type='receptor_address',
    )


if __name__ == '__main__':
    main()
