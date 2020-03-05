#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Kirill Shirinkin (kirill@mkdev.me)
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
module: foreman_external_usergroup
short_description: Manage external user groups in Foreman
description:
  - Create and delete external user groups in Foreman
author:
  - "Kirill Shirinkin (@Fodoj)"
options:
  name:
    description:
      - Name of the group
    required: true
    type: str
  usergroup:
    description:
      - Name of the linked usergroup
    required: true
    type: str
  auth_source_ldap:
    description:
      - Name of the authentication source to be used for this group
    required: true
    type: str
  state:
    description:
      - State of the external user group
    default: present
    choices:
      - present
      - absent
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: Create an external user group
  foreman_external_usergroup:
    name: test
    auth_source_ldap: "My LDAP server"
    usergroup: "Internal Usergroup"
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            usergroup=dict(required=True),
            auth_source_ldap=dict(required=True, type='entity', flat_name='auth_source_id'),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    params = {"usergroup_id": entity_dict.pop('usergroup')}

    entity = None

    # There is no way to find by name via API search, so we need
    # to iterate over all external user groups of a given usergroup
    for external_usergroup in module.list_resource("external_usergroups", params=params):
        if external_usergroup['name'] == entity_dict['name']:
            entity = external_usergroup

    entity_dict['auth_source_ldap'] = module.find_resource_by_name('auth_sources', entity_dict['auth_source_ldap'], thin=True)

    changed = module.ensure_entity_state('external_usergroups', entity_dict, entity, params)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
