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
      default: ''
    max_hosts:
      description:
        - The max hosts allowed in this organizations
      default: "0"
      type: int
      version_added: "3.7"
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
        - If value not set, will try environment variable C(TOWER_OAUTH_TOKEN) and then config files
      type: str
      version_added: "3.7"
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
        name=dict(required=True),
        description=dict(),
        custom_virtualenv=dict(),
        max_hosts=dict(type='int', default="0"),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    custom_virtualenv = module.params.get('custom_virtualenv')
    max_hosts = module.params.get('max_hosts')
    # instance_group_names = module.params.get('instance_groups')
    state = module.params.get('state')

    # Attempt to look up organization based on the provided name
    organization = module.get_one('organizations', **{
        'data': {
            'name': name,
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(organization)

    # Create the data that gets sent for create and update
    org_fields = {'name': name}
    if description is not None:
        org_fields['description'] = description
    if custom_virtualenv is not None:
        org_fields['custom_virtualenv'] = custom_virtualenv
    if max_hosts is not None:
        org_fields['max_hosts'] = max_hosts

    # If the state was present and we can let the module build or update the existing organization, this will return on its own
    module.create_or_update_if_needed(organization, org_fields, endpoint='organizations', item_type='organization')


if __name__ == '__main__':
    main()
