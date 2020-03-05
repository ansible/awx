#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Christoffer Reijer (Basalt AB)
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
module: foreman_role
short_description: Manage Foreman Roles using Foreman API
description:
  - Create and Delete Foreman Roles using Foreman API
author:
  - "Christoffer Reijer (@ephracis) Basalt AB"
options:
  name:
    description: The name of the role
    required: true
    type: str
  description:
    description: Description of the role
    required: false
    type: str
  locations:
    description: List of locations the role should be assigned to
    required: false
    type: list
  organizations:
    description: List of organizations the role should be assigned to
    required: false
    type: list
  filters:
    description: Filters with permissions for this role
    required: false
    type: list
  state:
    description: role presence
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: role
  foreman_role:
    name: "Provisioner"
    description: "Only provision on libvirt"
    locations:
      - "Uppsala"
    organizations:
      - "Basalt"
    filters:
      - resource: 'Host'
        permissions:
          - view_hosts
        search: "owner_type = Usergroup and owner_id = 4"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: present
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            description=dict(),
            locations=dict(type='entity_list', flat_name='location_ids'),
            organizations=dict(type='entity_list', flat_name='organization_ids'),
            filters=dict(type='entity_list', flat_name='filter_ids'),
        ),
    )

    filters_entity_spec = dict(
        permissions=dict(type='entity_list', flat_name='permission_ids'),
        resource=dict(),
        search=dict(),
        role_id=dict(required=True)
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('roles', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if 'locations' in entity_dict:
            entity_dict['locations'] = module.find_resources_by_title('locations', entity_dict['locations'], thin=True)

        if 'organizations' in entity_dict:
            entity_dict['organizations'] = module.find_resources_by_name('organizations', entity_dict['organizations'], thin=True)

    filters = entity_dict.pop("filters", None)

    changed, entity = module.ensure_entity('roles', entity_dict, entity)

    if not module.desired_absent and not module.check_mode:
        if filters is not None:
            for role_filter in filters:
                role_filter['role_id'] = entity['id']
                role_filter['permissions'] = module.find_resources_by_name('permissions', role_filter['permissions'], thin=True)
                module.ensure_entity_state('filters', role_filter, None, None, 'present', filters_entity_spec)
            old_filters = entity.get('filter_ids', [])
            for old_filter in old_filters:
                module.ensure_entity('filters', None, {'id': old_filter}, {}, 'absent')
            if len(old_filters) != len(filters):
                changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
