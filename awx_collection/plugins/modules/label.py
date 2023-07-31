#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: label
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller labels.
description:
    - Create, update, or destroy Automation Platform Controller labels. See
      U(https://www.ansible.com/tower) for an overview.
    - Note, labels can only be created via the API, they can not be deleted.
      Once they are fully disassociated the API will clean them up on its own.
options:
    name:
      description:
        - Name of this label.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field).
      type: str
    organization:
      description:
        - Organization name, ID, or named URL this label belongs to.
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "exists"]
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Add label to organization
  label:
    name: Custom Label
    organization: My Organization
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        organization=dict(required=True),
        state=dict(choices=['present', 'exists'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    organization = module.params.get('organization')
    state = module.params.get("state")

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization_id = None
    if organization:
        organization_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one(
        'labels',
        name_or_id=name,
        check_exists=(state == 'exists'),
        **{
            'data': {
                'organization': organization_id,
            }
        }
    )

    # Create the data that gets sent for create and update
    new_fields = {}
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    if organization:
        new_fields['organization'] = organization_id

    module.create_or_update_if_needed(existing_item, new_fields, endpoint='labels', item_type='label', associations={})


if __name__ == '__main__':
    main()
