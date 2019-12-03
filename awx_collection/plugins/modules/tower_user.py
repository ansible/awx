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
module: tower_user
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower user.
description:
    - Create, update, or destroy Ansible Tower users. See
      U(https://www.ansible.com/tower) for an overview.
options:
    username:
      description:
        - The username of the user.
      required: True
      type: str
    first_name:
      description:
        - First name of the user.
      type: str
    last_name:
      description:
        - Last name of the user.
      type: str
    email:
      description:
        - Email address of the user.
      required: True
      type: str
    password:
      description:
        - Password of the user.
      type: str
    superuser:
      description:
        - User is a system wide administrator.
      type: bool
      default: 'no'
    auditor:
      description:
        - User is a system wide auditor.
      type: bool
      default: 'no'
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str

requirements:
  - ansible-tower-cli >= 3.2.0

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

from ..module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        username=dict(required=True),
        first_name=dict(),
        last_name=dict(),
        password=dict(no_log=True),
        email=dict(required=True),
        superuser=dict(type='bool', default=False),
        auditor=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    username = module.params.get('username')
    first_name = module.params.get('first_name')
    last_name = module.params.get('last_name')
    password = module.params.get('password')
    email = module.params.get('email')
    superuser = module.params.get('superuser')
    auditor = module.params.get('auditor')
    state = module.params.get('state')

    json_output = {'username': username, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        user = tower_cli.get_resource('user')
        try:
            if state == 'present':
                result = user.modify(username=username, first_name=first_name, last_name=last_name,
                                     email=email, password=password, is_superuser=superuser,
                                     is_system_auditor=auditor, create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = user.delete(username=username)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update the user: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
