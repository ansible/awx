#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020,Geoffrey Bachelot <bachelotg@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_application
author: "Geoffrey Bacheot (@jffz)"
short_description: create, update, or destroy Ansible Tower applications
description:
    - Create, update, or destroy Ansible Tower applications. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of the application.
      required: True
      type: str
    description:
      description:
        - Description of the application.
      type: str
    authorization_grant_type:
      description:
        - The grant type the user must use for acquire tokens for this application.
      default: "password"
      choices: ["password", "authorization-code"]
      type: str
      required: True
    client_type:
      description:
        - Set to public or confidential depending on how secure the client device is.
      choices: ["public", "confidential"]
      type: str
      required: True
    organization:
      description:
        - Name of organization for application.
      type: str
      required: True
    redirect_uris:
      description:
        - Allowed urls list, space separated. Required when authorization-grant-type=authorization-code
      default: "present"
      choices: ["present", "absent"]
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    skip_authorization:
      description:
        - Set True to skip authorization step for completely trusted applications.
      default: false
      type: bool
    username:
      description:
        - Username for this credential. ``access_key`` for AWS.
        - Deprecated, please use inputs
      type: str
'''


EXAMPLES = '''
- name: Add Foo application
  tower_application:
    name: "Foo"
    description: "Foo bar application"
    organization: "test"
    state: present
    authorization-grant-type: password
    client-type: public

- name: Add Foo application
  tower_application:
    name: "Foo"
    description: "Foo bar application"
    organization: "test"
    state: present
    authorization-grant-type: authorization-code
    client-type: confidential
    redirect_uris: http://tower.com/api/v2/
'''

import time

from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        authorization_grant_type=dict(required=True),
        client_type=dict(required=True, choices=['public', 'confidential']),
        organization=dict(required=True),
        redirect_uris=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
        skip_authorization=dict(type=bool),
        username=dict()
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    authorization_grant_type = module.params.get('authorization_grant_type')
    client_type = module.params.get('client_type')
    organization = module.params.get('organization')
    redirect_uris = ' '.join(module.params.get('redirect_uris'))
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up application based on the provided name and org ID
    application = module.get_one('applications', **{
        'data': {
            'name': name,
            'organization': org_id
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(application)

    # Attempt to look up associated field items the user specified.
    association_fields = {}

    # Create the data that gets sent for create and update
    application_fields = {
        'name': name,
        'authorization_grant_type': authorization_grant_type,
        'client_type': client_type,
        'organization': org_id,
    }
    if description is not None:
        application_fields['description'] = description
    if redirect_uris is not None:
        application_fields['redirect_uris'] = redirect_uris

    if authorization_grant_type == 'authorization-code' and not redirect_uris:
        module.fail_json(msg='Parameter redirect_uris is required when authorization-grant-type is authorization code based.')

    # If the state was present and we can let the module build or update the existing application, this will return on its own
    module.create_or_update_if_needed(
        application, application_fields,
        endpoint='applications', item_type='application'
    )


if __name__ == '__main__':
    main()
