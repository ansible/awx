#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020, Shane McDonald <shanemcd@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: execution_environment
author: "Shane McDonald (@shanemcd)"
short_description: create, update, or destroy Execution Environments in Automation Platform Controller.
description:
    - Create, update, or destroy Execution Environments in Automation Platform Controller. See
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
    pull:
      description:
        - determine image pull behavior
      choices: ["always", "missing", "never"]
      default: 'missing'
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add EE to the controller instance
  execution_environment:
    name: "My EE"
    image: quay.io/ansible/awx-ee
'''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        image=dict(required=True),
        description=dict(default=''),
        organization=dict(),
        credential=dict(default=''),
        state=dict(choices=['present', 'absent'], default='present'),
        pull=dict(choices=['always', 'missing', 'never'], default='missing'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    image = module.params.get('image')
    description = module.params.get('description')
    state = module.params.get('state')
    pull = module.params.get('pull')

    existing_item = module.get_one('execution_environments', name_or_id=name)

    if state == 'absent':
        module.delete_if_needed(existing_item)

    new_fields = {
        'name': name,
        'image': image,
    }
    if description:
        new_fields['description'] = description

    if pull:
        new_fields['pull'] = pull

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization = module.params.get('organization')
    if organization:
        new_fields['organization'] = module.resolve_name_to_id('organizations', organization)

    credential = module.params.get('credential')
    if credential:
        new_fields['credential'] = module.resolve_name_to_id('credentials', credential)

    module.create_or_update_if_needed(existing_item, new_fields, endpoint='execution_environments', item_type='execution_environment')


if __name__ == '__main__':
    main()
