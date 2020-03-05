#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017 Matthias M Dellweg (ATIX AG)
# (c) 2017 Bernhard Hopfenmüller (ATIX AG)
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
module: foreman_operatingsystem
short_description: Manage Foreman Operating Systems
description:
  - "Manage Foreman Operating System Entities"
author:
  - "Matthias M Dellweg (@mdellweg) ATIX AG"
  - "Bernhard Hopfenmüller (@Fobhep) ATIX AG"
options:
  name:
    description:
      - Name of the Operating System
    required: true
    type: str
  updated_name:
    description: New operating system name. When this parameter is set, the module will not be idempotent.
    type: str
  release_name:
    description:
      - Release name of the operating system (recommended for debian)
    type: str
  description:
    description:
      - Description of the Operating System
    required: false
    type: str
  family:
    description:
      - distribution family of the Operating System
    choices:
      - AIX
      - Altlinux
      - Archlinux
      - Coreos
      - Debian
      - Freebsd
      - Gentoo
      - Junos
      - NXOS
      - Rancheros
      - Redhat
      - Solaris
      - Suse
      - Windows
      - Xenserver
    required: false
    type: str
  major:
    description:
      - major version of the Operating System
    required: false
    type: str
  minor:
    description:
      - minor version of the Operating System
    required: false
    type: str
  architectures:
    description:
      - architectures, the operating system can be installed on
    required: false
    type: list
  media:
    description:
      - list of installation media
    required: false
    type: list
  ptables:
    description:
      - list of partitioning tables
    required: false
    type: list
  provisioning_templates:
    description:
      - List of provisioning templates that are associated with the operating system.
      - Specify the full list of template names you want to associate with your OS.
      - For example ["Kickstart default", "Kickstart default finish", "Kickstart default iPXE", "custom"].
      - After specifying the template associations, you can set the default association in
      - the M(foreman_os_default_template) module.
    required: false
    type: list
  password_hash:
    description:
      - hashing algorithm for passwd
    required: false
    choices:
      - MD5
      - SHA256
      - SHA512
    type: str
  parameters:
    description:
      - Operating System specific host parameters
    required: false
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name of the parameter
        required: true
        type: str
      value:
        description:
          - Value of the parameter
        required: true
        type: raw
      parameter_type:
        description:
          - Type of the parameter
        default: 'string'
        choices:
          - 'string'
          - 'boolean'
          - 'integer'
          - 'real'
          - 'array'
          - 'hash'
          - 'yaml'
          - 'json'
        type: str
  state:
    description:
      - State of the Operating System
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
- name: "Create an Operating System"
  foreman_operatingsystem:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: Debian 9
    release_name: stretch
    family: Debian
    major: 9
    parameters:
      - name: additional-packages
        value: python vim
    state: present

- name: "Ensure existence of an Operating System (provide default values)"
  foreman_operatingsystem:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: Centos 7
    family: Redhat
    major: 7
    password_hash: SHA256
    state: present_with_defaults

- name: "Delete an Operating System"
  foreman_operatingsystem:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: Debian 9
    family: Debian
    major: 9
    state: absent
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import (
    ForemanEntityAnsibleModule,
    parameter_entity_spec,
    OS_LIST,
)


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            release_name=dict(),
            description=dict(),
            family=dict(choices=OS_LIST),
            major=dict(),
            minor=dict(),
            architectures=dict(type='entity_list', flat_name='architecture_ids'),
            media=dict(type='entity_list', flat_name='medium_ids'),
            ptables=dict(type='entity_list', flat_name='ptable_ids'),
            provisioning_templates=dict(type='entity_list', flat_name='provisioning_template_ids'),
            password_hash=dict(choices=['MD5', 'SHA256', 'SHA512']),
            parameters=dict(type='nested_list', entity_spec=parameter_entity_spec),
        ),
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'present_with_defaults', 'absent']),
            updated_name=dict(),
        ),
        required_if=[
            ['state', 'present', ['name', 'major', 'family']],
            ['state', 'present_with_defaults', ['name', 'major', 'family']],
        ],
        required_one_of=[
            ['description', 'name'],
            ['description', 'major'],
        ],
    )

    entity_dict = module.clean_params()

    module.connect()

    # Try to find the Operating System to work on
    # name is however not unique, but description is, as well as "<name> <major>[.<minor>]"
    entity = None
    # If we have a description, search for it
    if 'description' in entity_dict and entity_dict['description'] != '':
        search_string = 'description="{0}"'.format(entity_dict['description'])
        entity = module.find_resource('operatingsystems', search_string, failsafe=True)
    # If we did not yet find a unique OS, search by name & version
    # In case of state == absent, those information might be missing, we assume that we did not find an operatingsytem to delete then
    if entity is None and 'name' in entity_dict and 'major' in entity_dict:
        search_string = ','.join('{0}="{1}"'.format(key, entity_dict[key]) for key in ('name', 'major', 'minor') if key in entity_dict)
        entity = module.find_resource('operatingsystems', search_string, failsafe=True)

    if not entity and (module.state == 'present' or module.state == 'present_with_defaults'):
        # we actually attempt to create a new one...
        for param_name in ['major', 'family', 'password_hash']:
            if param_name not in entity_dict.keys():
                module.fail_json(msg='{0} is a required parameter to create a new operating system.'.format(param_name))

    if not module.desired_absent:
        if entity and 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')
        if 'architectures' in entity_dict:
            entity_dict['architectures'] = module.find_resources_by_name('architectures', entity_dict['architectures'], thin=True)

        if 'media' in entity_dict:
            entity_dict['media'] = module.find_resources_by_name('media', entity_dict['media'], thin=True)

        if 'ptables' in entity_dict:
            entity_dict['ptables'] = module.find_resources_by_name('ptables', entity_dict['ptables'], thin=True)

        if 'provisioning_templates' in entity_dict:
            entity_dict['provisioning_templates'] = module.find_resources_by_name('provisioning_templates', entity_dict['provisioning_templates'], thin=True)

    parameters = entity_dict.get('parameters')

    changed, operatingsystem = module.ensure_entity('operatingsystems', entity_dict, entity)

    if operatingsystem:
        scope = {'operatingsystem_id': operatingsystem['id']}
        changed |= module.ensure_scoped_parameters(scope, entity, parameters)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
