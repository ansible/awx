#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Baptiste AGASSE (baptiste.agasse@gmail.com)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: foreman_usergroup
short_description: Manage Foreman User groups
description:
  - Create and delete user groups in Foreman
author:
  - "Baptiste Agasse (@bagasse)"
options:
  name:
    description:
      - Name of the group
    required: true
    type: str
  updated_name:
    description:
      - New user group name. When this parameter is set, the module will not be idempotent.
    required: false
    type: str
  admin:
    description:
      - Whether or not the users in this group are administrators
    required: false
    default: false
    type: bool
  roles:
    description:
      - List of roles assigned to the group
    required: false
    type: list
  users:
    description:
      - List of users assigned to the group
    required: false
    type: list
  usergroups:
    description:
      - List of other groups assigned to the group
    required: false
    type: list
  state:
    description:
      - State of the user
    default: present
    choices:
      - present
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: Create a user group
  foreman_usergroup:
    name: test
    admin: no
    roles:
      - Manager
    users:
      - myuser1
      - myuser2
    usergroups:
      - mynestedgroup
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        argument_spec=dict(
            updated_name=dict(),
        ),
        entity_spec=dict(
            name=dict(required=True),
            admin=dict(required=False, type='bool', default=False),
            users=dict(required=False, type='entity_list', flat_name='user_ids'),
            usergroups=dict(required=False, type='entity_list', flat_name='usergroup_ids'),
            roles=dict(required=False, type='entity_list', flat_name='role_ids'),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('usergroups', entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if entity and 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')

        if 'roles' in entity_dict:
            entity_dict['roles'] = module.find_resources_by_name('roles', entity_dict['roles'], thin=True)

        if 'users' in entity_dict:
            entity_dict['users'] = module.find_resources('users', ['login="{0}"'.format(login) for login in entity_dict['users']], thin=True)

        if 'usergroups' in entity_dict:
            entity_dict['usergroups'] = module.find_resources_by_name('usergroups', entity_dict['usergroups'], thin=True)

    changed = module.ensure_entity_state('usergroups', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
