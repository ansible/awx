#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2022 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: instance
author: "Rick Elrod (@relrod)"
version_added: "4.3.0"
short_description: create, update, or destroy Automation Platform Controller instances.
description:
    - Create, update, or destroy Automation Platform Controller instances. See
      U(https://www.ansible.com/tower) for an overview.
options:
    hostname:
      description:
        - Hostname of this instance.
      required: True
      type: str
    capacity_adjustment:
      description:
        - Capacity adjustment (0 <= capacity_adjustment <= 1)
      required: False
      type: float
    enabled:
      description:
        - If true, the instance will be enabled and used.
      required: False
      type: bool
    managed_by_policy:
      description:
        - Managed by policy
      required: False
      type: bool
    node_type:
      description:
        - Role that this node plays in the mesh.
      choices:
        - execution
        - hop
      required: False
      type: str
    node_state:
      description:
        - Indicates the current life cycle stage of this instance.
      choices:
        - deprovisioning
        - installed
      required: False
      type: str
    listener_port:
      description:
        - Port that Receptor will listen for incoming connections on.
      required: False
      type: int
    peers:
      description:
        - List of peers to connect outbound to. Only configurable for hop and execution nodes.
        - To remove all current peers, set value to an empty list, [].
        - Each item is an ID or address of a receptor address.
        - If item is address, it must be unique across all receptor addresses.
      required: False
      type: list
      elements: str
    peers_from_control_nodes:
      description:
        - If enabled, control plane nodes will automatically peer to this node.
      required: False
      type: bool
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Create an instance
  awx.awx.instance:
    hostname: my-instance.prod.example.com
    capacity_adjustment: 0.4

- name: Deprovision the instance
  awx.awx.instance:
    hostname: my-instance.prod.example.com
    node_state: deprovisioning

- name: Create execution node
  awx.awx.instance:
    hostname: execution.example.com
    node_type: execution
    peers:
      - 12
      - route.to.hop.example.com

- name: Remove peers
  awx.awx.instance:
    hostname: execution.example.com
    peers:
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        hostname=dict(required=True),
        capacity_adjustment=dict(type='float'),
        enabled=dict(type='bool'),
        managed_by_policy=dict(type='bool'),
        node_type=dict(type='str', choices=['execution', 'hop']),
        node_state=dict(type='str', choices=['deprovisioning', 'installed']),
        listener_port=dict(type='int'),
        peers=dict(required=False, type='list', elements='str'),
        peers_from_control_nodes=dict(required=False, type='bool'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    hostname = module.params.get('hostname')
    capacity_adjustment = module.params.get('capacity_adjustment')
    enabled = module.params.get('enabled')
    managed_by_policy = module.params.get('managed_by_policy')
    node_type = module.params.get('node_type')
    node_state = module.params.get('node_state')
    listener_port = module.params.get('listener_port')
    peers = module.params.get('peers')
    peers_from_control_nodes = module.params.get('peers_from_control_nodes')
    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('instances', name_or_id=hostname)

    # peer item can be an id or address
    # if address, get the id
    peers_ids = []
    if peers:
        for p in peers:
            if not p.isdigit():
                p_id = module.get_one('receptor_addresses', allow_none=False, data={'address': p})
                peers_ids.append(p_id['id'])
            else:
                peers_ids.append(p)

    # Create the data that gets sent for create and update
    new_fields = {'hostname': hostname}
    if capacity_adjustment is not None:
        new_fields['capacity_adjustment'] = capacity_adjustment
    if enabled is not None:
        new_fields['enabled'] = enabled
    if managed_by_policy is not None:
        new_fields['managed_by_policy'] = managed_by_policy
    if node_type is not None:
        new_fields['node_type'] = node_type
    if node_state is not None:
        new_fields['node_state'] = node_state
    if listener_port is not None:
        new_fields['listener_port'] = listener_port
    if peers is not None:
        new_fields['peers'] = peers_ids
    if peers_from_control_nodes is not None:
        new_fields['peers_from_control_nodes'] = peers_from_control_nodes

    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint='instances',
        item_type='instance',
    )


if __name__ == '__main__':
    main()
