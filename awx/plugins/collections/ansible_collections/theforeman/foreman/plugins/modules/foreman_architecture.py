#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Manisha Singhal (ATIX AG)
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
module: foreman_architecture
short_description: Manage Foreman Architectures using Foreman API
description:
  - Create, Update and Delete Foreman Architectures using Foreman API
author:
  - "Manisha Singhal (@Manisha15) ATIX AG"
options:
  name:
    description: Name of architecture
    required: true
    type: str
  updated_name:
    description: New architecture name. When this parameter is set, the module will not be idempotent.
    type: str
  operatingsystems:
    description: List of operating systems the architecture should be assigned to
    required: false
    type: list
  state:
    description: Architecture presence
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create an Architecture"
  foreman_architecture:
    name: "i386"
    operatingsystems:
      - "TestOS1"
      - "TestOS2"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: present

- name: "Update an Architecture"
  foreman_architecture:
    name: "i386"
    operatingsystems:
      - "TestOS3"
      - "TestOS4"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: present

- name: "Delete an Architecture"
  foreman_architecture:
    name: "i386"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: absent
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
            operatingsystems=dict(type='entity_list', flat_name='operatingsystem_ids'),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('architectures', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if entity and 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')
        if 'operatingsystems' in entity_dict:
            entity_dict['operatingsystems'] = module.find_operatingsystems(entity_dict['operatingsystems'], thin=True)

    changed = module.ensure_entity_state('architectures', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
