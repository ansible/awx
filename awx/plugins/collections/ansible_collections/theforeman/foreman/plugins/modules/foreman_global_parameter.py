#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017 Matthias Dellweg & Bernhard Hopfenmüller (ATIX AG)
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
module: foreman_global_parameter
short_description: Manage Foreman Global Parameters
description:
  - "Manage Foreman Global Parameter Entities"
author:
  - "Bernhard Hopfenmueller (@Fobhep) ATIX AG"
  - "Matthias Dellweg (@mdellweg) ATIX AG"
  - "Manisha Singhal (@manisha15) ATIX AG"
options:
  name:
    description:
      - Name of the Global Parameter
    required: true
    type: str
  updated_name:
    description:
      - New name of the Global Parameter. When this parameter is set, the module will not be idempotent.
    type: str
  value:
    description:
      - Value of the Global Parameter
    required: false
    type: raw
  parameter_type:
    description:
      - Type of value
    default: string
    choices:
      - string
      - boolean
      - integer
      - real
      - array
      - hash
      - yaml
      - json
    type: str
  state:
    description:
      - State of the Global Parameter
      - C(present_with_defaults) will ensure the entity exists, but won't update existing ones
    default: present
    choices:
      - present
      - present_with_defaults
      - absent
    type: str
notes:
  - The I(parameter_type) only has an effect on Foreman >= 1.22
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create a Global Parameter"
  foreman_global_parameter:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "TheAnswer"
    value: "42"
    state: present_with_defaults

- name: "Update a Global Parameter"
  foreman_global_parameter:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "TheAnswer"
    value: "43"
    state: present

- name: "Delete a Global Parameter"
  foreman_global_parameter:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "TheAnswer"
    state: absent
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule, parameter_value_to_str


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            value=dict(type='raw'),
            parameter_type=dict(default='string', choices=['string', 'boolean', 'integer', 'real', 'array', 'hash', 'yaml', 'json']),
        ),
        argument_spec=dict(
            state=dict(default='present', choices=['present_with_defaults', 'present', 'absent']),
            updated_name=dict(),
        ),
        required_if=(
            ['state', 'present_with_defaults', ['value']],
            ['state', 'present', ['value']],
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('common_parameters', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if entity and 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')
        # Convert values according to their corresponding parameter_type
        if entity and 'parameter_type' not in entity:
            entity['parameter_type'] = 'string'
        entity_dict['value'] = parameter_value_to_str(entity_dict['value'], entity_dict['parameter_type'])
        if entity and 'value' in entity:
            entity['value'] = parameter_value_to_str(entity['value'], entity.get('parameter_type', 'string'))

    changed = module.ensure_entity_state('common_parameters', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
