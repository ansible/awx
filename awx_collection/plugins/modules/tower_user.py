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
module: tower_user
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower users.
description:
    - Create, update, or destroy Ansible Tower users. See
      U(https://www.ansible.com/tower) for an overview.
options:
    username:
      description:
        - Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
      required: True
      type: str
    first_name:
      description:
        - First name of the user.
      required: False
      type: str
    last_name:
      description:
        - Last name of the user.
      required: False
      type: str
    email:
      description:
        - Email address of the user.
      required: False
      type: str
    is_superuser:
      description:
        - User is a system wide administrator.
      required: False
      type: bool
      default: False
      aliases: ['superuser']
    is_system_auditor:
      description:
        - User is a system wide auditor.
      required: False
      type: bool
      default: False
      aliases: ['auditor']
    password:
      description:
        - Password of the user; write-only field.
      required: False
      type: str
      default: ''
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
- name: Add tower user
  tower_user:
    username: jdoe
    password: foobarbaz
    email: jdoe@example.org
    first_name: John
    last_name: Doe
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add tower user as a system administrator
  tower_user:
    username: jdoe
    password: foobarbaz
    email: jdoe@example.org
    superuser: yes
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add tower user as a system auditor
  tower_user:
    username: jdoe
    password: foobarbaz
    email: jdoe@example.org
    auditor: yes
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Delete tower user
  tower_user:
    username: jdoe
    email: jdoe@example.org
    state: absent
    tower_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        username=dict(required=True, type='str'),
        first_name=dict(required=False, type='str'),
        last_name=dict(required=False, type='str'),
        email=dict(required=False, type='str'),
        is_superuser=dict(required=False, type='bool', default=False, aliases=['superuser']),
        is_system_auditor=dict(required=False, type='bool', default=False, aliases=['auditor']),
        password=dict(required=False, type='str', default=''),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    username = module.params.get('username')
    first_name = module.params.get('first_name')
    last_name = module.params.get('last_name')
    email = module.params.get('email')
    password = module.params.get('password')
    first_name = module.params.get('first_name')
    last_name = module.params.get('last_name')
    superuser = module.params.get('superuser')
    auditor = module.params.get('auditor')

    # Create the data that gets sent for create and update
    user_fields = {
        'username': module.params.get('username'),
    }
    if email is not None:
        user_fields['email'] = email
    if password is not None:
        user_fields['password'] = password
    if first_name is not None:
        user_fields['first_name'] = first_name
    if last_name is not None:
        user_fields['last_name'] = last_name
    if superuser is not None:
        user_fields['is_superuser'] = superuser
    if auditor is not None:
        user_fields['is_system_auditor'] = auditor

    # Attempt to look up user based on the provided username
    user = module.get_one('users', **{
        'data': {
            'username': username,
        }
    })

    # Create the data that gets sent for create and update
    new_fields = {}
    if username:
        new_fields['username'] = username
    if first_name:
        new_fields['first_name'] = first_name
    if last_name:
        new_fields['last_name'] = last_name
    if email:
        new_fields['email'] = email
    if is_superuser:
        new_fields['is_superuser'] = is_superuser
    if is_system_auditor:
        new_fields['is_system_auditor'] = is_system_auditor
    if password:
        new_fields['password'] = password

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)
    elif state == 'present':
        # If the state was present and we can let the module build or update the existing item, this will return on its own
        module.create_or_update_if_needed(existing_item, new_fields, endpoint='users', item_type='user')


if __name__ == '__main__':
    main()
