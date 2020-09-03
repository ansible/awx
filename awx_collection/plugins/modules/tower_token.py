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
    - In addition, the module sets an Ansible fact which can be passed into other
      tower_* modules as the parameter tower_oauthtoken. See examples for usage.
    - Because of the sensitive nature of tokens, the created token value is only available once
      through the Ansible fact. (See RETURN for details)
    - Due to the nature of tokens in Tower this module is not idempotent. A second will
      with the same parameters will create a new token.
    - If you are creating a temporary token for use with modules you should delete the token
      when you are done with it. See the example for how to do it.
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
      description: The data structure produced from tower_token in create mode to be used with state absent.
      type: dict
    existing_token_id:
      description: A token ID (number) which can be used to delete an arbitrary token with state absent.
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
- block:
    - name: Create a new token using an existing token
      tower_token:
        description: '{{ token_description }}'
        scope: "write"
        state: present
        tower_oauthtoken: "{{ my_existing_token }}"

    - name: Delete this token
      tower_token:
        existing_token: "{{ tower_token }}"
        state: absent

    - name: Create a new token using username/password
      tower_token:
        description: '{{ token_description }}'
        scope: "write"
        state: present
        tower_username: "{{ my_username }}"
        tower_password: "{{ my_password }}"

    - name: Use our new token to make another call
      tower_job_list:
        tower_oauthtoken: "{{ tower_token }}"

  always:
    - name: Delete our Token with the token we created
      tower_token:
        existing_token: "{{ tower_token }}"
        state: absent
      when: tower_token is defined

- name: Delete a token by its id
  tower_token:
    existing_token_id: 4
    state: absent
'''

RETURN = '''
tower_token:
  type: dict
  description: An Ansible Fact variable representing a Tower token object which can be used for auth in subsequent modules. See examples for usage.
  contains:
    token:
      description: The token that was generated. This token can never be accessed again, make sure this value is noted before it is lost.
      type: str
    id:
      description: The numeric ID of the token created
      type: str
  returned: on successful create
'''

from ..module_utils.tower_api import TowerAPIModule


def return_token(module, last_response):
    # A token is special because you can never get the actual token ID back from the API.
    # So the default module return would give you an ID but then the token would forever be masked on you.
    # This method will return the entire token object we got back so that a user has access to the token

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
        existing_token_id=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ('existing_token', 'existing_token_id'),
        ],
        # If we are state absent make sure one of existing_token or existing_token_id are present
        required_if=[
            ['state', 'absent', ('existing_token', 'existing_token_id'), True, ],
        ],
    )

    # Extract our parameters
    description = module.params.get('description')
    application = module.params.get('application')
    scope = module.params.get('scope')
    existing_token = module.params.get('existing_token')
    existing_token_id = module.params.get('existing_token_id')
    state = module.params.get('state')

    if state == 'absent':
        if not existing_token:
            existing_token = module.get_one('tokens', **{
                'data': {
                    'id': existing_token_id,
                }
            })

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
