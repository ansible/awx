#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020,Geoffrey Bachelot <bachelotg@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: application
author: "Geoffrey Bacheot (@jffz)"
short_description: create, update, or destroy Automation Platform Controller applications
description:
    - Create, update, or destroy Automation Platform Controller applications. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of the application.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      type: str
    description:
      description:
        - Description of the application.
      type: str
    authorization_grant_type:
      description:
        - The grant type the user must use for acquire tokens for this application.
      choices: ["password", "authorization-code"]
      type: str
      required: False
    client_type:
      description:
        - Set to public or confidential depending on how secure the client device is.
      choices: ["public", "confidential"]
      type: str
      required: False
    organization:
      description:
        - Name, ID, or named URL of organization for application.
      type: str
      required: True
    redirect_uris:
      description:
        - Allowed urls list, space separated. Required when authorization-grant-type=authorization-code
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent", "exists"]
      type: str
    skip_authorization:
      description:
        - Set True to skip authorization step for completely trusted applications.
      type: bool

extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add Foo application
  application:
    name: "Foo"
    description: "Foo bar application"
    organization: "test"
    state: present
    authorization_grant_type: password
    client_type: public

- name: Add Foo application
  application:
    name: "Foo"
    description: "Foo bar application"
    organization: "test"
    state: present
    authorization_grant_type: authorization-code
    client_type: confidential
    redirect_uris:
      - http://tower.com/api/v2/
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        authorization_grant_type=dict(choices=["password", "authorization-code"]),
        client_type=dict(choices=['public', 'confidential']),
        organization=dict(required=True),
        redirect_uris=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),
        skip_authorization=dict(type='bool'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    description = module.params.get('description')
    authorization_grant_type = module.params.get('authorization_grant_type')
    client_type = module.params.get('client_type')
    organization = module.params.get('organization')
    redirect_uris = module.params.get('redirect_uris')
    skip_authorization = module.params.get('skip_authorization')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up application based on the provided name and org ID
    application = module.get_one('applications', name_or_id=name, check_exists=(state == 'exists'), **{'data': {'organization': org_id}})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(application)

    # Create the data that gets sent for create and update
    application_fields = {
        'name': new_name if new_name else (module.get_item_name(application) if application else name),
        'organization': org_id,
    }
    if authorization_grant_type is not None:
        application_fields['authorization_grant_type'] = authorization_grant_type
    if client_type is not None:
        application_fields['client_type'] = client_type
    if description is not None:
        application_fields['description'] = description
    if redirect_uris is not None:
        application_fields['redirect_uris'] = ' '.join(redirect_uris)
    if skip_authorization is not None:
        application_fields['skip_authorization'] = skip_authorization

    response = module.create_or_update_if_needed(application, application_fields, endpoint='applications', item_type='application', auto_exit=False)
    if 'client_id' in response:
        module.json_output['client_id'] = response['client_id']
    if 'client_secret' in response:
        module.json_output['client_secret'] = response['client_secret']
    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
