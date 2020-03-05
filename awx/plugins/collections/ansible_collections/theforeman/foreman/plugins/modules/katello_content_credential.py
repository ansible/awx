#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018, Baptiste Agasse <baptiste.agagsse@gmail.com>
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
module: katello_content_credential
short_description: Create and Manage Katello content credentials
description:
  - Create and Manage Katello content credentials
author: "Baptiste Agasse (@bagasse)"
options:
  name:
    description:
      - Name of the content credential
    required: true
    type: str
  organization:
    description:
      - Organization name that the content credential is in
    required: true
    type: str
  content_type:
    description:
    - Type of credential
    choices:
    - gpg_key
    - cert
    required: true
    type: str
  content:
    description:
    - Content of the content credential
    required: true
    type: str
  state:
    description:
      - State of the content credential.
    default: present
    choices:
      - present
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create katello client GPG key"
  katello_content_credential:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "RPM-GPG-KEY-my-repo"
    content_type: gpg_key
    organization: "Default Organization"
    content: "{{ lookup('file', 'RPM-GPG-KEY-my-repo') }}"
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import KatelloEntityAnsibleModule


def main():
    module = KatelloEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            content_type=dict(required=True, choices=['gpg_key', 'cert']),
            content=dict(required=True),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity_dict['organization'] = module.find_resource_by_name('organizations', entity_dict['organization'], thin=True)
    scope = {'organization_id': entity_dict['organization']['id']}
    entity = module.find_resource_by_name('content_credentials', name=entity_dict['name'], params=scope, failsafe=True)

    changed = module.ensure_entity_state('content_credentials', entity_dict, entity, params=scope)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
