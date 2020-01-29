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
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
extends_documentation_fragment: awx.awx.auth
'''


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

    org_fields = {'name': name}
    if description:
        org_fields['description'] = description
    if custom_virtualenv:
        org_fields['custom_virtualenv'] = custom_virtualenv
    if max_hosts:
        int_max_hosts = 0
        try:
            int_max_hosts = int(max_hosts)
        except Exception:
            module.fail_json(msg="Unable to convert max_hosts to an integer")
        org_fields['max_hosts'] = int_max_hosts

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(organization)
    elif state == 'present':
        # If the state was present we can let the module build or update the existing team, this will return on its own
        module.create_or_update_if_needed(organization, org_fields, endpoint='organizations', item_type='organization')


if __name__ == '__main__':
    main()
