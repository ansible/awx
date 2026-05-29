#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: team
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller team.
description:
    - Create, update, or destroy Automation Platform Controller teams. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the team.
      required: True
      type: str
    new_name:
      description:
        - To use when changing a team's name.
      type: str
    description:
      description:
        - The description to use for the team.
      type: str
    organization:
      description:
        - Organization name, ID, or named URL the team should be made a member of.
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent", "exists"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Create team
  team:
    name: Team Name
    description: Team Description
    organization: test-org
    state: present
    controller_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        organization=dict(required=True),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up team based on the provided name and org ID
    team = module.get_one('teams', name_or_id=name, check_exists=(state == 'exists'), **{'data': {'organization': org_id}})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(team)

    # Create the data that gets sent for create and update
    team_fields = {'name': new_name if new_name else (module.get_item_name(team) if team else name), 'organization': org_id}
    if description is not None:
        team_fields['description'] = description

    # If the state was present and we can let the module build or update the existing team, this will return on its own
    module.create_or_update_if_needed(team, team_fields, endpoint='teams', item_type='team')


if __name__ == '__main__':
    main()
