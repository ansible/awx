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
module: foreman_compute_profile
short_description: Manage Foreman Compute Profiles using Foreman API
description:
  - Create and delete Foreman Compute Profiles using Foreman API
author:
  - "Philipp Joos (@philippj)"
  - "Baptiste Agasse (@bagasse)"
options:
  name:
    description: compute profile name
    required: true
    type: str
  updated_name:
    description: new compute profile name
    required: false
    type: str
  compute_attributes:
    description: Compute attributes related to this compute profile. Some of these attributes are specific to the underlying compute resource type
    required: false
    type: list
    suboptions:
      compute_resource:
        description:
          - Name of the compute resource the attribute should be for
        type: str
      vm_attrs:
        description:
          - Hash containing the data of vm_attrs
        aliases:
          - vm_attributes
        type: dict
  state:
    description: compute profile presence
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: compute profile
  foreman_compute_profile:
    name: example_compute_profile
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: another compute profile
  foreman_compute_profile:
    name: another_example_compute_profile
    compute_attributes:
    - compute_resource: ovirt_compute_resource1
      vm_attrs:
        cluster: 'a96d44a4-f14a-1015-82c6-f80354acdf01'
        template: 'c88af4b7-a24a-453b-9ac2-bc647ca2ef99'
        instance_type: 'cb8927e7-a404-40fb-a6c1-06cbfc92e077'
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: compute profile2
  foreman_compute_profile:
    name: example_compute_profile2
    compute_attributes:
    - compute_resource: ovirt_compute_resource01
      vm_attrs:
        cluster: a96d44a4-f14a-1015-82c6-f80354acdf01
        cores: 1
        sockets: 1
        memory: 1073741824
        ha: 0
        interfaces_attributes:
          0:
            name: ""
            network: 390666e1-dab3-4c99-9f96-006b2e2fd801
            interface: virtio
        volumes_attributes:
          0:
            size_gb: 16
            storage_domain: 19c50090-1ab4-4023-a63f-75ee1018ed5e
            preallocate: '1'
            wipe_after_delete: '0'
            interface: virtio_scsi
            bootable: 'true'
    - compute_resource: libvirt_compute_resource03
      vm_attrs:
        cpus: 1
        memory: 2147483648
        nics_attributes:
          0:
            type: bridge
            bridge: ""
            model: virtio
        volumes_attributes:
          0:
            pool_name: default
            capacity: 16G
            allocation: 16G
            format_type: raw
    server_url: foreman.example.com
    username: admin
    password: secret
    state: present

- name: Remove compute profile
  foreman_compute_profile:
    name: example_compute_profile2
    state: absent
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


compute_attribute_entity_spec = {
    'compute_resource': {'type': 'entity', 'flat_name': 'compute_resource_id'},
    'vm_attrs': {'type': 'dict', 'aliases': ['vm_attributes']},
}


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            compute_attributes=dict(type='nested_list', entity_spec=compute_attribute_entity_spec),
        ),
        argument_spec=dict(
            updated_name=dict(),
        ),
    )

    entity_dict = module.clean_params()
    updated_name = entity_dict.get('updated_name')
    compute_attributes = entity_dict.pop('compute_attributes', None)

    module.connect()

    entity = module.find_resource_by_name('compute_profiles', name=entity_dict['name'], failsafe=True)

    if module.state == 'present' and updated_name:
        entity_dict['name'] = updated_name

    changed, compute_profile = module.ensure_entity('compute_profiles', entity_dict, entity)

    # Apply changes on underlying compute attributes only when present
    if module.state == 'present' and compute_attributes is not None:
        # Update or create compute attributes
        scope = {'compute_profile_id': compute_profile['id']}
        for ca_entity_dict in compute_attributes:
            ca_entity_dict['compute_resource'] = module.find_resource_by_name(
                'compute_resources', name=ca_entity_dict['compute_resource'], failsafe=False, thin=False)
            ca_entities = ca_entity_dict['compute_resource'].get('compute_attributes', [])
            ca_entity = next((item for item in ca_entities if item.get('compute_profile_id') == compute_profile['id']), None)
            changed |= module.ensure_entity_state('compute_attributes', ca_entity_dict, ca_entity, entity_spec=compute_attribute_entity_spec, params=scope)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
