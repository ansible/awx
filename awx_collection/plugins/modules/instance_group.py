#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: instance_group
author: "John Westcott IV (@john-westcott-iv)"
version_added: "4.0.0"
short_description: create, update, or destroy Automation Platform Controller instance groups.
description:
    - Create, update, or destroy Automation Platform Controller instance groups. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of this instance group.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      type: str
    credential:
      description:
        - Credential to authenticate with Kubernetes or OpenShift.  Must be of type "Kubernetes/OpenShift API Bearer Token".
      required: False
      type: str
    is_container_group:
      description:
        - Signifies that this InstanceGroup should act as a ContainerGroup. If no credential is specified, the underlying Pod's ServiceAccount will be used.
      required: False
      type: bool
      default: False
    policy_instance_percentage:
      description:
        - Minimum percentage of all instances that will be automatically assigned to this group when new instances come online.
      required: False
      type: int
      default: '0'
    policy_instance_minimum:
      description:
        - Static minimum number of Instances that will be automatically assign to this group when new instances come online.
      required: False
      type: int
      default: '0'
    policy_instance_list:
      description:
        - List of exact-match Instances that will be assigned to this group
      required: False
      type: list
      elements: str
    pod_spec_override:
      description:
        - A custom Kubernetes or OpenShift Pod specification.
      required: False
      type: str
    instances:
      description:
        - The instances associated with this instance_group
      required: False
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        credential=dict(),
        is_container_group=dict(type='bool', default=False),
        policy_instance_percentage=dict(type='int', default='0'),
        policy_instance_minimum=dict(type='int', default='0'),
        policy_instance_list=dict(type='list', elements='str'),
        pod_spec_override=dict(),
        instances=dict(required=False, type="list", elements='str', default=None),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    credential = module.params.get('credential')
    is_container_group = module.params.get('is_container_group')
    policy_instance_percentage = module.params.get('policy_instance_percentage')
    policy_instance_minimum = module.params.get('policy_instance_minimum')
    policy_instance_list = module.params.get('policy_instance_list')
    pod_spec_override = module.params.get('pod_spec_override')
    instances = module.params.get('instances')
    state = module.params.get('state')

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('instance_groups', name_or_id=name)

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    credential_id = None
    if credential:
        credential_id = module.resolve_name_to_id('credentials', credential)
    instances_ids = None
    if instances is not None:
        instances_ids = []
        for item in instances:
            instances_ids.append(module.resolve_name_to_id('instances', item))

    # Create the data that gets sent for create and update
    new_fields = {}
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    if credential is not None:
        new_fields['credential'] = credential_id
    if is_container_group is not None:
        new_fields['is_container_group'] = is_container_group
    if policy_instance_percentage is not None:
        new_fields['policy_instance_percentage'] = policy_instance_percentage
    if policy_instance_minimum is not None:
        new_fields['policy_instance_minimum'] = policy_instance_minimum
    if policy_instance_list is not None:
        new_fields['policy_instance_list'] = policy_instance_list
    if pod_spec_override is not None:
        new_fields['pod_spec_override'] = pod_spec_override

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint='instance_groups',
        item_type='instance_group',
        associations={
            'instances': instances_ids,
        },
    )


if __name__ == '__main__':
    main()
