#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Philipp Joos 2017
# (c) Baptiste Agasse 2019
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
module: foreman_compute_resource
short_description: Manage Foreman Compute resources using Foreman API
description:
  - Create, update and delete Foreman Compute Resources using Foreman API
author:
  - "Philipp Joos (@philippj)"
  - "Baptiste Agasse (@bagasse)"
  - "Manisha Singhal (@Manisha15) ATIX AG"
options:
  name:
    description: compute resource name
    required: true
    type: str
  updated_name:
    description: new compute resource name
    required: false
    type: str
  description:
    description: compute resource description
    required: false
    type: str
  provider:
    description: Compute resource provider. Required if I(state=present_with_defaults).
    required: false
    choices: ["vmware", "libvirt", "ovirt"]
    type: str
  provider_params:
    description: Parameter specific to compute resource provider. Required if I(state=present_with_defaults).
    required: false
    type: dict
    suboptions:
      url:
        description:
          - URL of the compute resource
        type: str
      user:
        description:
          - Username for the compute resource connection, not valid for I(provider=libvirt)
        type: str
      password:
        description:
          - Password for the compute resource connection, not valid for I(provider=libvirt)
        type: str
      datacenter:
        description:
          - Datacenter the compute resource is in, not valid for I(provider=libvirt)
        type: str
      display_type:
        description:
          - Display type to use for the remote console, only valid for I(provider=libvirt)
        type: str
      use_v4:
        description:
          - Use oVirt API v4, only valid for I(provider=ovirt)
        type: bool
      ovirt_quota:
        description:
          - oVirt quota ID, only valid for I(provider=ovirt)
        type: str
  locations:
    description: List of locations the compute resource should be assigned to
    required: false
    type: list
  organizations:
    description: List of organizations the compute resource should be assigned to
    required: false
    type: list
  state:
    description:
      - compute resource presence
      - C(present_with_defaults) will ensure the entity exists, but won't update existing ones
    required: false
    default: present
    choices: ["present", "absent", "present_with_defaults"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: Create livirt compute resource
  foreman_compute_resource:
    name: example_compute_resource
    locations:
      - Munich
    organizations:
      - ATIX
    provider: libvirt
    provider_params:
      url: libvirt.example.com
      display_type: vnc
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: Update livirt compute resource
  foreman_compute_resource:
    name: example_compute_resource
    description: updated compute resource
    locations:
      - Munich
    organizations:
      - ATIX
    provider: libvirt
    provider_params:
      url: libvirt.example.com
      display_type: vnc
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: Delete livirt compute resource
  foreman_compute_resource:
    name: example_compute_resource
    server_url: foreman.example.com
    username: admin
    password: secret
    state: absent

- name: Create vmware compute resource
  foreman_compute_resource:
    name: example_compute_resource
    locations:
      - Munich
    organizations:
      - ATIX
    provider: vmware
    provider_params:
      url: vsphere.example.com
      user: admin
      password: secret
      datacenter: ax01
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: Create ovirt compute resource
  foreman_compute_resource:
    name: ovirt_compute_resource
    locations:
      - France/Toulouse
    organizations:
      - Example Org
    provider: ovirt
    provider_params:
      url: ovirt.example.com
      user: ovirt-admin@example.com
      password: ovirtsecret
      datacenter: aa92fb54-0736-4066-8fa8-b8b9e3bd75ac
      ovirt_quota: 24868ab9-c2a1-47c3-87e7-706f17d215ac
      use_v4: true
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def get_provider_info(provider):
    provider_name = provider.lower()

    if provider_name == 'libvirt':
        return 'Libvirt', ['url', 'display_type']

    elif provider_name == 'ovirt':
        return 'Ovirt', ['url', 'user', 'password', 'datacenter', 'use_v4', 'ovirt_quota']

    elif provider_name == 'vmware':
        return 'Vmware', ['url', 'user', 'password', 'datacenter']

    else:
        return '', []


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            updated_name=dict(),
            description=dict(),
            organizations=dict(type='entity_list', flat_name='organization_ids'),
            locations=dict(type='entity_list', flat_name='location_ids'),
            provider=dict(choices=['vmware', 'libvirt', 'ovirt']),
            display_type=dict(type='invisible'),
            datacenter=dict(type='invisible'),
            url=dict(type='invisible'),
            user=dict(type='invisible'),
            password=dict(type='invisible'),
            use_v4=dict(type='invisible'),
            ovirt_quota=dict(type='invisible'),
        ),
        argument_spec=dict(
            provider_params=dict(type='dict', options=dict(
                url=dict(),
                display_type=dict(),
                user=dict(),
                password=dict(no_log=True),
                datacenter=dict(),
                use_v4=dict(type='bool'),
                ovirt_quota=dict(),
            )),
            state=dict(type='str', default='present', choices=['present', 'absent', 'present_with_defaults']),
        ),
        required_if=(
            ['state', 'present_with_defaults', ['provider', 'provider_params']],
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('compute_resources', name=entity_dict['name'], failsafe=True)

    if not module.desired_absent:
        if 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict['updated_name']

        if 'organizations' in entity_dict:
            entity_dict['organizations'] = module.find_resources_by_name('organizations', entity_dict['organizations'], thin=True)

        if 'locations' in entity_dict:
            entity_dict['locations'] = module.find_resources_by_title('locations', entity_dict['locations'], thin=True)

        if 'provider' in entity_dict:
            entity_dict['provider'], provider_param_keys = get_provider_info(provider=entity_dict['provider'])
            provider_params = {k: v for k, v in entity_dict.pop('provider_params', dict()).items() if v is not None}

            for key in provider_param_keys:
                if key in provider_params:
                    entity_dict[key] = provider_params.pop(key)
            if provider_params:
                module.fail_json(msg="Provider {0} does not support the following given parameters: {1}".format(
                    entity_dict['provider'], list(provider_params.keys())))

        # Add provider specific params
        elif entity is None:
            module.fail_json(msg='To create a compute resource a valid provider must be supplied')

    changed = module.ensure_entity_state('compute_resources', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
