#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_token
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower tokens.
description:
    - Create or destroy Ansible Tower tokens. See
      U(https://www.ansible.com/tower) for an overview.
    - If you create a token it is your responsibility to delete the token.
options:
    description:
      description:
        - Optional description of this access token.
      required: False
      type: str
      default: ''
    application:
      description:
        - The application tied to this token.
      required: False
      type: str
    scope:
      description:
        - Allowed scopes, further restricts user's permissions. Must be a simple space-separated string with allowed scopes ['read', 'write'].
      required: False
      type: str
      default: 'write'
      choices: ["read", "write"]
    existing_token:
      description: An existing token (for use with state absent)
      type: dict
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
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- block:
    - name: Create a new token using an existing token
      tower_token:
        description: '{{ token_description }}'
        scope: "write"
        state: present
        tower_oauthtoken: "{{ ny_existing_token }}"

    - name: Delete this token
      tower_token:
        existing_token: "{{ tower_token }}"
        state: absent

    - name: Create a new token using username/password
      tower_token:
        description: '{{ token_description }}'
        scope: "write"
        state: present
        tower_username: "{{ ny_username }}"
        tower_password: "{{ ny_password }}"

    - name: Use our new token to make another call
      tower_job_list:
        tower_oauthtoken: "{{ tower_token }}"

  always:
    - name: Delete our Token with the token we created
      tower_token:
        existing_token: "{{ tower_token }}"
        state: absent
      when: tower_token is defined
'''

RETURNS = '''
tower_token:
  type: dict
  description: A Tower token object which can be used for auth or token deletion
  returned: on successful create
'''

from ..module_utils.tower_api import TowerModule


def return_token(module, last_response):
    # A token is special because you can never get the actual token ID back from the API.
    # So the default module return would give you an ID but then the token would forever be masked on you.
    # This method will return the entire token object we got back so that a user has access to the token

    module.json_output['token'] = last_response['token']
    module.json_output['ansible_facts'] = {
        'tower_token': last_response,
    }
    module.exit_json(**module.json_output)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        description=dict(),
        application=dict(),
        scope=dict(choices=['read', 'write'], default='write'),
        existing_token=dict(type='dict'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    description = module.params.get('description')
    application = module.params.get('application')
    scope = module.params.get('scope')
    existing_token = module.params.get('existing_token')
    state = module.params.get('state')

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_token)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    application_id = None
    if application:
        application_id = module.resolve_name_to_id('applications', application)

    # Create the data that gets sent for create and update
    new_fields = {}
    if description is not None:
        new_fields['description'] = description
    if application is not None:
        new_fields['application'] = application_id
    if scope is not None:
        new_fields['scope'] = scope

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        None, new_fields,
        endpoint='tokens', item_type='token',
        associations={
        },
        on_create=return_token,
    )


if __name__ == '__main__':
    main()
