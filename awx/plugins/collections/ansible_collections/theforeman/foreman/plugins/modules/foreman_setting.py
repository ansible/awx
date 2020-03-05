#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018 Matthias M Dellweg (ATIX AG)
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
module: foreman_setting
short_description: Manage Foreman Settings
description:
  - "Manage Foreman Setting Entities"
author:
  - "Matthias M Dellweg (@mdellweg) ATIX AG"
options:
  name:
    description:
      - Name of the Setting
    required: true
    type: str
  value:
    description:
      - value to set the Setting to
      - if missing, reset to default
    required: false
    type: raw
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Set a Setting"
  foreman_setting:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "http_proxy"
    value: "http://localhost:8088"

- name: "Reset a Setting"
  foreman_setting:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "http_proxy"
'''

RETURN = '''
foreman_setting:
  description: Created / Updated state of the setting
  returned: success
  type: dict
'''


from ansible.module_utils.foreman_helper import ForemanAnsibleModule, parameter_value_to_str


entity_spec = {
    'name': {},
    'value': {},
}


def main():
    module = ForemanAnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            value=dict(type='raw'),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('settings', entity_dict['name'], failsafe=False)

    if 'value' not in entity_dict:
        entity_dict['value'] = entity['default'] or ''

    settings_type = entity['settings_type']
    new_value = entity_dict['value']
    # Allow to pass integers as string
    if settings_type == 'integer':
        new_value = int(new_value)
    entity_dict['value'] = parameter_value_to_str(new_value, settings_type)
    old_value = entity['value']
    entity['value'] = parameter_value_to_str(old_value, settings_type)

    changed, entity = module.ensure_entity('settings', entity_dict, entity, state='present', entity_spec=entity_spec)

    if entity:
        # Fake the not serialized input value as output
        entity['value'] = new_value

    module.exit_json(changed=changed, foreman_setting=entity)


if __name__ == '__main__':
    main()
