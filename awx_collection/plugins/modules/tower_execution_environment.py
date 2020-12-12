#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020, Shane McDonald <shanemcd@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_execution_environment
author: "Shane McDonald"
short_description: create, update, or destroy Execution Environments in Ansible Tower.
description:
    - Create, update, or destroy Execution Environments in Ansible Tower. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the execution environment.
      required: True
      type: str
    image:
      description:
        - The fully qualified url of the container image.
      required: True
      type: str
    description:
      description:
        - Description to use for the execution environment.
      type: str
    organization:
      description:
        - The organization the execution environment belongs to.
      type: str
    credential:
      description:
        - Name of the credential to use for the execution environment.
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add EE to Tower
  tower_execution_environment:
    name: "My EE"
    image: quay.io/ansible/awx-ee
'''


from ..module_utils.tower_api import TowerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        image=dict(required=True),
        description=dict(default=''),
        organization=dict(),
        credential=dict(default=''),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    image = module.params.get('image')
    description = module.params.get('description')
    state = module.params.get('state')

    existing_item = module.get_one('execution_environments', name_or_id=name)

    if state == 'absent':
        module.delete_if_needed(existing_item)

    new_fields = {
        'name': name,
        'image': image,
    }
    if description:
        new_fields['description'] = description

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization = module.params.get('organization')
    if organization:
        new_fields['organization'] = module.resolve_name_to_id('organizations', organization)

    credential = module.params.get('credential')
    if credential:
        new_fields['credential'] = module.resolve_name_to_id('credentials', credential)

    module.create_or_update_if_needed(
        existing_item, new_fields,
        endpoint='execution_environments',
        item_type='execution_environment'
    )


if __name__ == '__main__':
    main()
