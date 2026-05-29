#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: role_user_assignment
author: "Seth Foster (@fosterseth)"
short_description: Gives a user permission to a resource or an organization.
description:
    - Use this endpoint to give a user permission to a resource or an organization.
    - After creation, the assignment cannot be edited, but can be deleted to remove those permissions.
options:
    role_definition:
        description:
            - The name or id of the role definition to assign to the user.
        required: True
        type: str
    object_id:
        description:
            - Primary key of the object this assignment applies to.
        required: True
        type: int
    user:
        description:
            - The name or id of the user to assign to the object.
        required: False
        type: str
    object_ansible_id:
        description:
            - Resource id of the object this role applies to. Alternative to the object_id field.
        required: False
        type: int
    user_ansible_id:
        description:
            - Resource id of the user who will receive permissions from this assignment. Alternative to user field.
        required: False
        type: int
    state:
        description:
            - The desired state of the role definition.
        default: present
        choices:
            - present
            - absent
        type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Give Bob JT permissions
  role_user_assignment:
    role_definition: launch JT
    object_id: 1
    user: bob
    state: present
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        user=dict(required=False, type='str'),
        object_id=dict(required=True, type='int'),
        role_definition=dict(required=True, type='str'),
        object_ansible_id=dict(required=False, type='int'),
        user_ansible_id=dict(required=False, type='int'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = ControllerAPIModule(argument_spec=argument_spec)

    user = module.params.get('user')
    object_id = module.params.get('object_id')
    role_definition_str = module.params.get('role_definition')
    object_ansible_id = module.params.get('object_ansible_id')
    user_ansible_id = module.params.get('user_ansible_id')
    state = module.params.get('state')

    role_definition = module.get_one('role_definitions', allow_none=False, name_or_id=role_definition_str)
    user = module.get_one('users', allow_none=False, name_or_id=user)

    kwargs = {
        'role_definition': role_definition['id'],
        'object_id': object_id,
        'user': user['id'],
        'object_ansible_id': object_ansible_id,
        'user_ansible_id': user_ansible_id,
    }

    # get rid of None type values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    role_user_assignment = module.get_one('role_user_assignments', **{'data': kwargs})

    if state == 'absent':
        module.delete_if_needed(
            role_user_assignment,
            item_type='role_user_assignment',
        )

    if state == 'present':
        module.create_if_needed(
            role_user_assignment,
            kwargs,
            endpoint='role_user_assignments',
            item_type='role_user_assignment',
        )


if __name__ == '__main__':
    main()
