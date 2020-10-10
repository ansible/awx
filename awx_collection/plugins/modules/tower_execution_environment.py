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
    image:
      description:
        - The fully qualified name of the container image
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
    credential:
      description:
        - Name of the credential to use for the job template.
        - Deprecated, use 'credentials'.
      type: str
    description:
      description:
        - Description to use for the job template.
      type: str
    organization:
      description:
        - TODO
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add EE to Tower
  tower_execution_environment:
    image: quay.io/awx/ee
'''


from ..module_utils.tower_api import TowerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        image=dict(required=True),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    image = module.params.get('image')
    state = module.params.get('state')

    existing_item = module.get_one('execution_environments', name_or_id=image)

    if state == 'absent':
        module.delete_if_needed(image)

    module.create_or_update_if_needed(existing_item, image, endpoint='execution_environments', item_type='execution_environment')


if __name__ == '__main__':
    main()
