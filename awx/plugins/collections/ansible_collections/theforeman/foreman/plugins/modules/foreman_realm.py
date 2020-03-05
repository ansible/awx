#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Lester R Claudio <claudiol@redhat.com>
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
module: foreman_realm
short_description: Manage Foreman Realms
description:
  - Manage Foreman Realms
author:
  - "Lester R Claudio (@claudiol1)"
options:
  name:
    description:
      - Name of the Foreman realm
    required: true
    type: str
  realm_proxy:
    description:
      - Proxy to use for this realm
    required: true
    type: str
  realm_type:
    description:
      - Realm type
    choices:
      - Red Hat Identity Management
      - FreeIPA
      - Active Directory
    required: true
    type: str
  state:
    description:
      - State of the Realm
    default: present
    choices:
      - present
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create EXAMPLE.LOCAL Realm"
  foreman_realm:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "EXAMPLE.COM"
    realm_proxy: "foreman.example.com"
    realm_type: "Red Hat Identity Management"
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            realm_proxy=dict(type='entity', flat_name='realm_proxy_id', required=True),
            realm_type=dict(required=True, choices=['Red Hat Identity Management', 'FreeIPA', 'Active Directory']),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('realms', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        entity_dict['realm_proxy'] = module.find_resource_by_name('smart_proxies', entity_dict['realm_proxy'], thin=True)

    changed = module.ensure_entity_state('realms', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
