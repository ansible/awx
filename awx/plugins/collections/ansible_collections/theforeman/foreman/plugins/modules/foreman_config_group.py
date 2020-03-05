#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Baptiste Agasse
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
module: foreman_config_group
short_description: Manage (Puppet) config groups using Foreman API
description:
  - Create and Delete Foreman (Puppet) config groups using Foreman API
author:
  - "Baptiste Agasse (@bagasse)"
options:
  name:
    description: The config group name
    required: true
    type: str
  updated_name:
    description: New config group name. When this parameter is set, the module will not be idempotent.
    type: str
  puppetclasses:
    description: List of puppet classes to include in this group
    required: false
    type: list
  state:
    description: config group presence
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: create new config group
  foreman_config_group:
    name: "My config group"
    puppetclasses:
      - ntp
      - mymodule::myclass
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
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
            puppetclasses=dict(type='entity_list', flat_name='puppetclass_ids'),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('config_groups', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if entity and 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')
        if 'puppetclasses' in entity_dict:
            # puppet classes API return puppet classes grouped by puppet module name
            puppet_classes = []
            for puppet_class in entity_dict['puppetclasses']:
                search = 'name="{0}"'.format(puppet_class)
                results = module.list_resource('puppetclasses', search)

                # verify that only one puppet module is returned with only one puppet class inside
                # as provided search results have to be like "results": { "ntp": [{"id": 1, "name": "ntp" ...}]}
                # and get the puppet class id
                if len(results) == 1 and len(list(results.values())[0]) == 1:
                    puppet_classes.append({'id': list(results.values())[0][0]['id']})
                else:
                    module.fail_json(msg='No data found for name="%s"' % search)

            entity_dict['puppetclasses'] = puppet_classes

    changed = module.ensure_entity_state('config_groups', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
