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
module: tower_team
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower team.
description:
    - Create, update, or destroy Ansible Tower teams. See
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
      required: True
      type: str
    description:
      description:
        - The description to use for the team.
      type: str
    organization:
      description:
        - Organization the team should be made a member of.
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Create tower team
  tower_team:
    name: Team Name
    description: Team Description
    organization: test-org
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(required=False),
        description=dict(),
        organization=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    state = module.params.get('state')

    # Attempt to lookup the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to lookup team based on the provided name and org ID
    team = module.get_one('teams', **{
        'data': {
            'name': name,
            'organization': org_id
        }
    })

    # Create data to sent to create and update
    team_fields = {
        'name': new_name if new_name else name,
        'description': description,
        'organization': org_id
    }

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(team)
    elif state == 'present':
        # If the state was present we can let the module build or update the existing team, this will return on its own
        module.create_or_update_if_needed(team, team_fields, endpoint='teams', item_type='team')


if __name__ == '__main__':
    main()
