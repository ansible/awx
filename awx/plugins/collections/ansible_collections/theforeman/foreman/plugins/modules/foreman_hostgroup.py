#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Manisha Singhal (ATIX AG)
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
module: foreman_hostgroup
short_description: Manage Foreman Hostgroups using Foreman API
description:
  - Create, Update and Delete Foreman Hostgroups using Foreman API
author:
  - "Manisha Singhal (@Manisha15) ATIX AG"
  - "Baptiste Agasse (@bagasse)"
options:
  name:
    description: Name of hostgroup
    required: true
    type: str
  updated_name:
    description: New name of hostgroup. When this parameter is set, the module will not be idempotent.
    type: str
  description:
    description: Description of hostgroup
    required: false
    type: str
  parent:
    description: Hostgroup parent name
    required: false
    type: str
  organizations:
    description: List of organizations names
    required: false
    type: list
  locations:
    description: List of locations names
    required: false
    type: list
  compute_resource:
    description: Compute resource name
    required: false
    type: str
  compute_profile:
    description: Compute profile name
    required: false
    type: str
  domain:
    description: Domain name
    required: false
    type: str
  subnet:
    description: IPv4 Subnet name
    required: false
    type: str
  subnet6:
    description: IPv6 Subnet name
    required: false
    type: str
  realm:
    description: Realm name
    required: false
    type: str
  architecture:
    description: Architecture name
    required: False
    type: str
  medium:
    aliases: [ media ]
    description: Medium name
    required: False
    type: str
  operatingsystem:
    description: Operatingsystem title
    required: False
    type: str
  pxe_loader:
    description: PXE Bootloader
    required: false
    choices:
      - PXELinux BIOS
      - PXELinux UEFI
      - Grub UEFI
      - Grub2 BIOS
      - Grub2 ELF
      - Grub2 UEFI
      - Grub2 UEFI SecureBoot
      - Grub2 UEFI HTTP
      - Grub2 UEFI HTTPS
      - Grub2 UEFI HTTPS SecureBoot
      - iPXE Embedded
      - iPXE UEFI HTTP
      - iPXE Chain BIOS
      - iPXE Chain UEFI
    type: str
  ptable:
    description: Partition table name
    required: False
    type: str
  root_pass:
    description: root password
    required: false
    type: str
  environment:
    description: Puppet environment name
    required: false
    type: str
  config_groups:
    description: Config groups list
    required: false
    type: list
  puppet_proxy:
    description: Puppet server proxy name
    required: false
    type: str
  puppet_ca_proxy:
    description: Puppet CA proxy name
    required: false
    type: str
  openscap_proxy:
    description: OpenSCAP proxy name. Only available when the OpenSCAP plugin is installed.
    required: false
    type: str
  organization:
    description:
      - Organization for scoped resources attached to the hostgroup. Only used for katello installations.
      - This organization will implicitly be added to the I(organizations) parameter if needed.
    required: false
    type: str
  content_source:
    description: Katello Content source. Only available for katello installations.
    required: false
    type: str
  lifecycle_environment:
    description: Katello Lifecycle environment. Only available for katello installations.
    required: false
    type: str
  content_view:
    description: Katello Content view. Only available for katello installations.
    required: false
    type: str
  parameters:
    description:
      - Hostgroup specific host parameters
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
    description: Hostgroup presence
    default: present
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create a Hostgroup"
  foreman_hostgroup:
    name: "new_hostgroup"
    architecture: "architecture_name"
    operatingsystem: "operatingsystem_name"
    medium: "media_name"
    ptable: "Partition_table_name"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: present

- name: "Update a Hostgroup"
  foreman_hostgroup:
    name: "new_hostgroup"
    architecture: "updated_architecture_name"
    operatingsystem: "updated_operatingsystem_name"
    organizations:
      - Org One
      - Org Two
    locations:
      - Loc One
      - Loc Two
      - Loc One/Nested loc
    medium: "updated_media_name"
    ptable: "updated_Partition_table_name"
    root_pass: "password"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: present

- name: "My nested hostgroup"
  foreman_hostgroup:
    parent: "new_hostgroup"
    name: "my nested hostgroup"

- name: "My hostgroup with ome proxies"
  foreman_hostgroup:
    name: "my hostgroup"
    environment: production
    puppet_proxy: puppet-proxy.example.com
    puppet_ca_proxy: puppet-proxy.example.com
    openscap_proxy: openscap-proxy.example.com

- name: "My katello related hostgroup"
  foreman_hostgroup:
    organization: "My Org"
    name: "kt hostgroup"
    content_source: capsule.example.com
    lifecycle_environment: "Production"
    content_view: "My content view"
    parameters:
      - name: "kt_activation_keys"
        value: "my_prod_ak"

- name: "Delete a Hostgroup"
  foreman_hostgroup:
    name: "new_hostgroup"
    server_url: "https://foreman.example.com"
    username: "admin"
    password: "secret"
    state: absent
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import (
    build_fqn,
    ForemanEntityAnsibleModule,
    parameter_entity_spec,
    split_fqn,
)


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            description=dict(),
            parent=dict(type='entity', flat_name='parent_id'),
            organizations=dict(type='entity_list', flat_name='organization_ids'),
            locations=dict(type='entity_list', flat_name='location_ids'),
            compute_resource=dict(type='entity', flat_name='compute_resource_id'),
            compute_profile=dict(type='entity', flat_name='compute_profile_id'),
            domain=dict(type='entity', flat_name='domain_id'),
            subnet=dict(type='entity', flat_name='subnet_id'),
            subnet6=dict(type='entity', flat_name='subnet6_id'),
            realm=dict(type='entity', flat_name='realm_id'),
            architecture=dict(type='entity', flat_name='architecture_id'),
            operatingsystem=dict(type='entity', flat_name='operatingsystem_id'),
            medium=dict(aliases=['media'], type='entity', flat_name='medium_id'),
            ptable=dict(type='entity', flat_name='ptable_id'),
            pxe_loader=dict(choices=['PXELinux BIOS', 'PXELinux UEFI', 'Grub UEFI', 'Grub2 BIOS', 'Grub2 ELF',
                                     'Grub2 UEFI', 'Grub2 UEFI SecureBoot', 'Grub2 UEFI HTTP', 'Grub2 UEFI HTTPS',
                                     'Grub2 UEFI HTTPS SecureBoot', 'iPXE Embedded', 'iPXE UEFI HTTP', 'iPXE Chain BIOS', 'iPXE Chain UEFI']),
            root_pass=dict(no_log=True),
            environment=dict(type='entity', flat_name='environment_id'),
            config_groups=dict(type='entity_list', flat_name='config_group_ids'),
            puppet_proxy=dict(type='entity', flat_name='puppet_proxy_id'),
            puppet_ca_proxy=dict(type='entity', flat_name='puppet_ca_proxy_id'),
            openscap_proxy=dict(type='entity', flat_name='openscap_proxy_id'),
            parameters=dict(type='nested_list', entity_spec=parameter_entity_spec),
            content_source=dict(type='entity', flat_name='content_source_id'),
            lifecycle_environment=dict(type='entity', flat_name='lifecycle_environment_id'),
            content_view=dict(type='entity', flat_name='content_view_id'),
        ),
        argument_spec=dict(
            organization=dict(),
            updated_name=dict(),
        ),
    )
    entity_dict = module.clean_params()

    module.connect()

    # Get short name and parent from provided name
    name, parent = split_fqn(entity_dict['name'])
    entity_dict['name'] = name

    katello_params = ['content_source', 'lifecycle_environment', 'content_view']

    if 'organization' not in entity_dict and list(set(katello_params) & set(entity_dict.keys())):
        module.fail_json(msg="Please specify the organization when using katello parameters.")

    if 'parent' in entity_dict:
        if parent:
            module.fail_json(msg="Please specify the parent either separately, or as part of the title.")
        parent = entity_dict['parent']
    if parent:
        entity_dict['parent'] = module.find_resource_by_title('hostgroups', title=parent, thin=True, failsafe=module.desired_absent)

        if module.desired_absent and entity_dict['parent'] is None:
            # Parent hostgroup does not exist so just exit here
            module.exit_json(changed=False)

    if not module.desired_absent:
        if 'locations' in entity_dict:
            entity_dict['locations'] = module.find_resources_by_title('locations', entity_dict['locations'], thin=True)

        if 'compute_resource' in entity_dict:
            entity_dict['compute_resource'] = module.find_resource_by_name('compute_resources', name=entity_dict['compute_resource'], failsafe=False, thin=True)

        if 'compute_profile' in entity_dict:
            entity_dict['compute_profile'] = module.find_resource_by_name('compute_profiles', name=entity_dict['compute_profile'], failsafe=False, thin=True)

        if 'domain' in entity_dict:
            entity_dict['domain'] = module.find_resource_by_name('domains', name=entity_dict['domain'], failsafe=False, thin=True)

        if 'subnet' in entity_dict:
            entity_dict['subnet'] = module.find_resource_by_name('subnets', name=entity_dict['subnet'], failsafe=False, thin=True)

        if 'subnet6' in entity_dict:
            entity_dict['subnet6'] = module.find_resource_by_name('subnets', name=entity_dict['subnet6'], failsafe=False, thin=True)

        if 'realm' in entity_dict:
            entity_dict['realm'] = module.find_resource_by_name('realms', name=entity_dict['realm'], failsafe=False, thin=True)

        if 'architecture' in entity_dict:
            entity_dict['architecture'] = module.find_resource_by_name('architectures', name=entity_dict['architecture'], failsafe=False, thin=True)

        if 'operatingsystem' in entity_dict:
            entity_dict['operatingsystem'] = module.find_operatingsystem(entity_dict['operatingsystem'], thin=True)

        if 'medium' in entity_dict:
            entity_dict['medium'] = module.find_resource_by_name('media', name=entity_dict['medium'], failsafe=False, thin=True)

        if 'ptable' in entity_dict:
            entity_dict['ptable'] = module.find_resource_by_name('ptables', name=entity_dict['ptable'], failsafe=False, thin=True)

        if 'environment' in entity_dict:
            entity_dict['environment'] = module.find_resource_by_name('environments', name=entity_dict['environment'], failsafe=False, thin=True)

        if 'config_groups' in entity_dict:
            entity_dict['config_groups'] = module.find_resources_by_name('config_groups', entity_dict['config_groups'], failsafe=False, thin=True)

        for proxy in ['puppet_proxy', 'puppet_ca_proxy', 'openscap_proxy', 'content_source']:
            if proxy in entity_dict:
                entity_dict[proxy] = module.find_resource_by_name('smart_proxies', entity_dict[proxy], thin=True)

        if 'organization' in entity_dict:
            if 'organizations' in entity_dict:
                if entity_dict['organization'] not in entity_dict['organizations']:
                    entity_dict['organizations'].append(entity_dict['organization'])
            else:
                entity_dict['organizations'] = [entity_dict['organization']]
            entity_dict['organization'] = module.find_resource_by_name('organizations', name=entity_dict['organization'], failsafe=False, thin=True)
            scope = {'organization_id': entity_dict['organization']['id']}

        if 'organizations' in entity_dict:
            entity_dict['organizations'] = module.find_resources_by_name('organizations', entity_dict['organizations'], thin=True)

        if 'lifecycle_environment' in entity_dict:
            entity_dict['lifecycle_environment'] = module.find_resource_by_name('lifecycle_environments', name=entity_dict['lifecycle_environment'],
                                                                                params=scope, failsafe=False, thin=True)

        if 'content_view' in entity_dict:
            entity_dict['content_view'] = module.find_resource_by_name('content_views', name=entity_dict['content_view'],
                                                                       params=scope, failsafe=False, thin=True)

    entity = module.find_resource_by_title('hostgroups', title=build_fqn(name, parent), failsafe=True)
    if entity:
        entity['root_pass'] = None
        if 'updated_name' in entity_dict:
            entity_dict['name'] = entity_dict.pop('updated_name')

    parameters = entity_dict.get('parameters')

    changed, hostgroup = module.ensure_entity('hostgroups', entity_dict, entity)

    if hostgroup:
        scope = {'hostgroup_id': hostgroup['id']}
        changed |= module.ensure_scoped_parameters(scope, entity, parameters)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
