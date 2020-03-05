#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017 Matthias M Dellweg (ATIX AG)
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
module: foreman_os_default_template
short_description: Manage Foreman Default Template Associations To Operating Systems
description:
  - "Manage Foreman OSDefaultTemplate Entities"
author:
  - "Matthias M Dellweg (@mdellweg) ATIX AG"
options:
  operatingsystem:
    description:
      - Name of the Operating System
    required: true
    type: str
  template_kind:
    description:
      - name of the template kind
    required: true
    type: str
  provisioning_template:
    description:
      - name of provisioning template
    required: false
    type: str
  state:
    description:
      - State of the Association
      - C(present_with_defaults) will ensure the entity exists, but won't update existing ones
    default: present
    choices:
      - present
      - present_with_defaults
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create an Association"
  foreman_os_default_template:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    operatingsystem: "CoolOS"
    template_kind: "finish"
    provisioning_template: "CoolOS finish"
    state: present

- name: "Delete an Association"
  foreman_os_default_template:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    operatingsystem: "CoolOS"
    template_kind: "finish"
    state: absent
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        argument_spec=dict(
            operatingsystem=dict(required=True),
            state=dict(default='present', choices=['present', 'present_with_defaults', 'absent']),
        ),
        entity_spec=dict(
            template_kind=dict(required=True, type='entity', flat_name='template_kind_id'),
            provisioning_template=dict(type='entity', flat_name='provisioning_template_id'),
        ),
        required_if=(
            ['state', 'present', ['provisioning_template']],
            ['state', 'present_with_defaults', ['provisioning_template']],
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity_dict['operatingsystem'] = module.find_operatingsystem(entity_dict['operatingsystem'], thin=True)
    entity_dict['template_kind'] = module.find_resource_by_name('template_kinds', entity_dict['template_kind'], thin=True)

    scope = {'operatingsystem_id': entity_dict['operatingsystem']['id']}
    # Default templates do not support a scoped search
    # see: https://projects.theforeman.org/issues/27722
    entities = module.list_resource('os_default_templates', params=scope)
    entity = next((item for item in entities if item['template_kind_id'] == entity_dict['template_kind']['id']), None)

    # Find Provisioning Template
    if 'provisioning_template' in entity_dict:
        if module.desired_absent:
            module.fail_json(msg='Provisioning template must not be specified for deletion.')
        entity_dict['provisioning_template'] = module.find_resource_by_name('provisioning_templates', entity_dict['provisioning_template'])
        if entity_dict['provisioning_template']['template_kind_id'] != entity_dict['template_kind']['id']:
            module.fail_json(msg='Provisioning template kind mismatching.')

    changed = module.ensure_entity_state('os_default_templates', entity_dict, entity, params=scope)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
