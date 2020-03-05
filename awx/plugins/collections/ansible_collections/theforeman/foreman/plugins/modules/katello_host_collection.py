#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019, Maxim Burgerhout <maxim@wzzrd.com>
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
module: katello_host_collection
short_description: Create and Manage host collections
description:
    - Create and Manage host collections
author:
    - "Maxim Burgerhout (@wzzrd)"
    - "Christoffer Reijer (@ephracis)"
options:
  description:
    description:
      - Description of the host collection
    required: false
    type: str
  organization:
    description:
      - Organization that the host collection is in
    required: true
    type: str
  name:
    description:
      - Name of the host collection
    required: true
    type: str
  updated_name:
    description:
      - New name of the host collection. When this parameter is set, the module will not be idempotent.
    type: str
  state:
    description:
      - State of the host collection
    default: present
    choices:
      - present
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create Foo host collection"
  katello_host_collection:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "Foo"
    description: "Foo host collection for Foo servers"
    organization: "My Cool new Organization"
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import KatelloEntityAnsibleModule


def main():
    module = KatelloEntityAnsibleModule(
        argument_spec=dict(
            updated_name=dict(),
        ),
        entity_spec=dict(
            name=dict(required=True),
            description=dict(),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity_dict['organization'] = module.find_resource_by_name('organizations', entity_dict['organization'], thin=True)
    scope = {'organization_id': entity_dict['organization']['id']}
    entity = module.find_resource_by_name('host_collections', name=entity_dict['name'], params=scope, failsafe=True)

    if entity and 'updated_name' in entity_dict:
        entity_dict['name'] = entity_dict.pop('updated_name')

    changed = module.ensure_entity_state('host_collections', entity_dict, entity, params=scope)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
