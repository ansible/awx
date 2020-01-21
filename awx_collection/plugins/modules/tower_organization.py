#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_organization
version_added: "2.3"
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower organizations
description:
    - Create, update, or destroy Ansible Tower organizations. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the organization.
      required: True
      type: str
    description:
      description:
        - The description to use for the organization.
      type: str
    custom_virtualenv:
      version_added: "2.9"
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
      type: str
      required: False
      default: ''
    max_hosts:
      description:
        - The max hosts allowed in this organizations
      default: "0"
      type: str
      required: False
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
extends_documentation_fragment: awx.awx.auth
'''
#    instance_groups:
#      description:
#        - The name of instance groups to tie to this organization
#      type: list
#      default: []
#      required: False


EXAMPLES = '''
- name: Create tower organization
  tower_organization:
    name: "Foo"
    description: "Foo bar organization"
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Create tower organization using 'foo-venv' as default Python virtualenv
  tower_organization:
    name: "Foo"
    description: "Foo bar organization using foo-venv"
    custom_virtualenv: "/var/lib/awx/venv/foo-venv/"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', required=False),
        custom_virtualenv=dict(type='str', required=False),
        max_hosts=dict(type='str', required=False, default="0"),
        # instance_groups=dict(type='list', required=False, default=[]),
        state=dict(type='str', choices=['present', 'absent'], default='present', required=False),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    custom_virtualenv = module.params.get('custom_virtualenv')
    max_hosts = module.params.get('max_hosts')
    # instance_group_names = module.params.get('instance_groups')
    state = module.params.get('state')

    # Attempt to lookup the related items the user specified (these will fail the module if not found)
    # instance_group_objects = []
    # for instance_name in instance_group_names:
    #     instance_group_objects.append(module.resolve_name_to_id('instance_groups', instance_name))

    # Attempt to lookup organization based on the provided name and org ID
    organization = module.get_one('organizations', **{
        'data': {
            'name': name,
        }
    })

    new_org_data = { 'name': name }
    if description:
        new_org_data['description'] = description
    if custom_virtualenv:
        new_org_data['custom_virtualenv'] = custom_virtualenv
    if max_hosts:
        int_max_hosts = 0
        try:
            int_max_hosts = int(max_hosts)
        except Exception as e:
            module.fail_json(msg="Unable to convert max_hosts to an integer")
        new_org_data['max_hosts'] = int_max_hosts
    # if instance_group_objects:
    #     new_org_data['instance_groups'] = instance_group_objects

    if state == 'absent' and not organization:
        # If the state was absent and we had no organization, we can just return
        module.exit_json(**module.json_output)
    elif state == 'absent' and organization:
        # If the state was absent and we had a organization, we can try to delete it, the module will handle exiting from this
        module.delete_endpoint('organizations/{0}'.format(organization['id']), item_type='organization', item_name=name, **{})
    elif state == 'present' and not organization:
        # if the state was present and we couldn't find a organization we can build one, the module wikl handle exiting from this
        module.post_endpoint('organizations', item_type='organization', item_name=name, **{
            'data': new_org_data,
        })
    else:
        # If the state was present and we had a organization we can see if we need to update it
        # This will return on its own
        module.update_if_needed(organization, new_org_data)

if __name__ == '__main__':
    main()
