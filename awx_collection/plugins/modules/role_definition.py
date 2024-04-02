#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: role_definition
author: "Seth Foster (@fosterseth)"
short_description: Add role definition to Automation Platform Controller
description:
    - Contains a list of permissions and a resource type that can then be assigned to users or teams.
options:
    name:
        description:
            - Name of this role definition.
        required: True
        type: str
    permissions:
        description:
            - List of permissions to include in the role definition.
        required: True
        type: list
        elements: str
    content_type:
        description:
            - The type of resource this applies to.
        required: True
        type: str
    description:
        description:
            - Optional description of this role definition.
        type: str
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
- name: Create Role Definition
  role_definition:
    name: test_view_jt
    permissions:
      - awx.view_jobtemplate
      - awx.execute_jobtemplate
    content_type: awx.jobtemplate
    description: role definition to view and execute jt
    state: present
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, type='str'),
        permissions=dict(required=True, type='list', elements='str'),
        content_type=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = ControllerAPIModule(argument_spec=argument_spec)

    name = module.params.get('name')
    permissions = module.params.get('permissions')
    content_type = module.params.get('content_type')
    description = module.params.get('description')
    state = module.params.get('state')
    if description is None:
        description = ''

    role_definition = module.get_one('role_definitions', name_or_id=name)

    if state == 'absent':
        module.delete_if_needed(
            role_definition,
            item_type='role_definition',
        )

    post_kwargs = {
        'name': name,
        'permissions': permissions,
        'content_type': content_type,
        'description': description
    }

    if state == 'present':
        module.create_or_update_if_needed(
            role_definition,
            post_kwargs,
            endpoint='role_definitions',
            item_type='role_definition',
        )


if __name__ == '__main__':
    main()
