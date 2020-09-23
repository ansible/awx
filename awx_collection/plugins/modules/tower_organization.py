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
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
      type: str
      default: ''
    max_hosts:
      description:
        - The max hosts allowed in this organizations
      default: "0"
      type: int
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    notification_templates_started:
      description:
        - list of notifications to send on start
      type: list
      elements: str
    notification_templates_success:
      description:
        - list of notifications to send on success
      type: list
      elements: str
    notification_templates_error:
      description:
        - list of notifications to send on error
      type: list
      elements: str
    notification_templates_approvals:
      description:
        - list of notifications to send on start
      type: list
      elements: str
    galaxy_credentials:
      description:
        - list of Ansible Galaxy credentials to associate to the organization
      type: list
      elements: str
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

- name: Create tower organization that pulls content from galaxy.ansible.com
  tower_organization:
    name: "Foo"
    state: present
    galaxy_credentials:
      - Ansible Galaxy
    tower_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.tower_api import TowerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        custom_virtualenv=dict(),
        max_hosts=dict(type='int', default="0"),
        notification_templates_started=dict(type="list", elements='str'),
        notification_templates_success=dict(type="list", elements='str'),
        notification_templates_error=dict(type="list", elements='str'),
        notification_templates_approvals=dict(type="list", elements='str'),
        galaxy_credentials=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    custom_virtualenv = module.params.get('custom_virtualenv')
    max_hosts = module.params.get('max_hosts')
    # instance_group_names = module.params.get('instance_groups')
    state = module.params.get('state')

    # Attempt to look up organization based on the provided name
    organization = module.get_one('organizations', name_or_id=name)

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(organization)
    # Attempt to look up associated field items the user specified.
    association_fields = {}

    notifications_start = module.params.get('notification_templates_started')
    if notifications_start is not None:
        association_fields['notification_templates_started'] = []
        for item in notifications_start:
            association_fields['notification_templates_started'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_success = module.params.get('notification_templates_success')
    if notifications_success is not None:
        association_fields['notification_templates_success'] = []
        for item in notifications_success:
            association_fields['notification_templates_success'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_error = module.params.get('notification_templates_error')
    if notifications_error is not None:
        association_fields['notification_templates_error'] = []
        for item in notifications_error:
            association_fields['notification_templates_error'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_approval = module.params.get('notification_templates_approvals')
    if notifications_approval is not None:
        association_fields['notification_templates_approvals'] = []
        for item in notifications_approval:
            association_fields['notification_templates_approvals'].append(module.resolve_name_to_id('notification_templates', item))

    galaxy_credentials = module.params.get('galaxy_credentials')
    if galaxy_credentials is not None:
        association_fields['galaxy_credentials'] = []
        for item in galaxy_credentials:
            association_fields['galaxy_credentials'].append(module.resolve_name_to_id('credentials', item))

    # Create the data that gets sent for create and update
    org_fields = {'name': module.get_item_name(organization) if organization else name}
    if description is not None:
        org_fields['description'] = description
    if custom_virtualenv is not None:
        org_fields['custom_virtualenv'] = custom_virtualenv
    if max_hosts is not None:
        org_fields['max_hosts'] = max_hosts

    # If the state was present and we can let the module build or update the existing organization, this will return on its own
    module.create_or_update_if_needed(
        organization, org_fields,
        endpoint='organizations', item_type='organization',
        associations=association_fields,
    )


if __name__ == '__main__':
    main()
