#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ad_hoc_command
author: "John Westcott IV (@john-westcott-iv)"
version_added: "4.0.0"
short_description: create, update, or destroy Automation Platform Controller ad hoc commands.
description:
    - Create, update, or destroy Automation Platform Controller ad hoc commands. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_type:
      description:
        - Job_type to use for the ad hoc command.
      type: str
      choices: [ 'run', 'check' ]
    execution_environment:
      description:
        - Execution Environment name, ID, or named URL to use for the ad hoc command.
      required: False
      type: str
    inventory:
      description:
        - Inventory name, ID, or named URL to use for the ad hoc command.
      required: True
      type: str
    limit:
      description:
        - Limit to use for the ad hoc command.
      type: str
    credential:
      description:
        - Credential name, ID, or named URL to use for ad hoc command.
      required: True
      type: str
    module_name:
      description:
        - The Ansible module to execute.
      required: True
      type: str
    module_args:
      description:
        - The arguments to pass to the module.
      type: str
    forks:
      description:
        - The number of forks to use for this ad hoc execution.
      type: int
    verbosity:
      description:
        - Verbosity level for this ad hoc command run
      type: int
      choices: [ 0, 1, 2, 3, 4, 5 ]
    extra_vars:
      description:
        - Extra variables to use for the ad hoc command..
      type: dict
    become_enabled:
      description:
        - If the become flag should be set.
      type: bool
    diff_mode:
      description:
        - Show the changes made by Ansible tasks where supported
      type: bool
    wait:
      description:
        - Wait for the command to complete.
      default: False
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
      default: 2
      type: float
    timeout:
      description:
        - If waiting for the command to complete this will abort after this
          amount of seconds
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Launch an Ad Hoc Command waiting for it to finish
  ad_hoc_command:
    inventory: Demo Inventory
    credential: Demo Credential
    module_name: command
    module_args: echo I <3 Ansible
    wait: true
'''

RETURN = '''
id:
    description: id of the newly launched command
    returned: success
    type: int
    sample: 86
status:
    description: status of newly launched command
    returned: success
    type: str
    sample: pending
'''

from ..module_utils.controller_api import ControllerAPIModule
import json


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        job_type=dict(choices=['run', 'check']),
        inventory=dict(required=True),
        limit=dict(),
        credential=dict(required=True),
        module_name=dict(required=True),
        module_args=dict(),
        forks=dict(type='int'),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4, 5]),
        extra_vars=dict(type='dict'),
        become_enabled=dict(type='bool'),
        diff_mode=dict(type='bool'),
        wait=dict(default=False, type='bool'),
        interval=dict(default=2.0, type='float'),
        timeout=dict(type='int'),
        execution_environment=dict(),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    inventory = module.params.get('inventory')
    credential = module.params.get('credential')
    module_name = module.params.get('module_name')
    module_args = module.params.get('module_args')

    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')
    execution_environment = module.params.get('execution_environment')

    # Create a datastructure to pass into our command launch
    post_data = {
        'module_name': module_name,
        'module_args': module_args,
    }
    for arg in ['job_type', 'limit', 'forks', 'verbosity', 'extra_vars', 'become_enabled', 'diff_mode']:
        if module.params.get(arg):
            # extra_var can receive a dict or a string, if a dict covert it to a string
            if arg == 'extra_vars' and not isinstance(module.params.get(arg), str):
                post_data[arg] = json.dumps(module.params.get(arg))
            else:
                post_data[arg] = module.params.get(arg)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    post_data['inventory'] = module.resolve_name_to_id('inventories', inventory)
    post_data['credential'] = module.resolve_name_to_id('credentials', credential)
    if execution_environment:
        post_data['execution_environment'] = module.resolve_name_to_id('execution_environments', execution_environment)

    # Launch the ad hoc command
    results = module.post_endpoint('ad_hoc_commands', **{'data': post_data})

    if results['status_code'] != 201:
        module.fail_json(msg="Failed to launch command, see response for details", **{'response': results})

    if not wait:
        module.exit_json(
            **{
                'changed': True,
                'id': results['json']['id'],
                'status': results['json']['status'],
            }
        )

    # Invoke wait function
    results = module.wait_on_url(url=results['json']['url'], object_name=module_name, object_type='Ad Hoc Command', timeout=timeout, interval=interval)

    module.exit_json(
        **{
            'changed': True,
            'id': results['json']['id'],
            'status': results['json']['status'],
        }
    )


if __name__ == '__main__':
    main()
