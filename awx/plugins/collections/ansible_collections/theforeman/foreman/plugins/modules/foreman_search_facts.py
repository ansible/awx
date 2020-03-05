#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018, Sean O'Keeffe <seanokeeffe797@gmail.com>
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
module: foreman_search_facts
short_description: Gather facts about Foreman resources
description:
  - "Gather facts about Foreman resources"
author:
  - "Sean O'Keeffe (@sean797)"
options:
  resource:
    description:
      - Resource to search
      - Set to an invalid choice like I(foo) see all available options.
    required: true
    type: str
  search:
    description:
      - Search query to use
      - If None, all resources are returned
    type: str
  params:
    description:
      - Add parameters to the API call if necessary
      - If not specified, no additional parameters are passed
    type: dict
  organization:
    description:
      - Scope the searched resource by organization
    type: str
  full_details:
    description:
      - If C(True) all details about the found resources are returned
    type: bool
    default: false
    aliases: [ info ]
notes:
  - Some resources don't support scoping and will return errors when you pass I(organization) or unknown data in I(params).
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Read a Setting"
  foreman_search_facts:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    resource: settings
    search: name = http_proxy
  register: result
- debug:
    var: result.resources[0].value

- name: "Read all Registries"
  foreman_search_facts:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    resource: registries
  register: result
- debug:
    var: item.name
  with_items: result.resources

- name: "Read all Organizations with full details"
  foreman_search_facts:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    resource: organizations
    full_details: true
  register: result
- debug:
    var: result.resources

- name: Get all existing subscriptions for organization with id 1
  foreman_search_facts:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    resource: subscriptions
    params:
      organization_id: 1
  register: result
- debug:
    var: result

- name: Get all existing activation keys for organization ACME
  foreman_search_facts:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    resource: activation_keys
    organization: ACME
  register: result
- debug:
    var: result
'''

RETURN = '''
resources:
  description: Search results from Foreman
  returned: always
  type: list
'''

from ansible.module_utils.foreman_helper import ForemanAnsibleModule


def main():

    module = ForemanAnsibleModule(
        argument_spec=dict(
            resource=dict(type='str', required=True),
            search=dict(default=""),
            full_details=dict(type='bool', aliases=['info'], default='false'),
            params=dict(type='dict'),
            organization=dict(),
        ),
    )

    module_params = module.clean_params()
    resource = module_params['resource']
    search = module_params['search']
    params = module_params.get('params', {})

    module.connect()

    if 'organization' in module_params:
        params['organization_id'] = module.find_resource_by_name('organizations', module_params['organization'], thin=True)['id']

    response = module.list_resource(resource, search, params)

    if module_params['full_details']:
        resources = []
        for found_resource in response:
            resources.append(module.show_resource(resource, found_resource['id']))
    else:
        resources = response

    module.exit_json(changed=False, resources=resources)


if __name__ == '__main__':
    main()
