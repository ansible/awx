#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ad_hoc_command_cancel
author: "John Westcott IV (@john-westcott-iv)"
short_description: Cancel an Ad Hoc Command.
description:
    - Cancel ad hoc command. See
      U(https://www.ansible.com/tower) for an overview.
options:
    command_id:
      description:
        - ID of the command to cancel
      required: True
      type: int
    fail_if_not_running:
      description:
        - Fail loudly if the I(command_id) can not be canceled
      default: False
      type: bool
    interval:
      description:
        - The interval in seconds, to request an update from .
      required: False
      default: 1
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish.
        - Not specifying means the task will wait until the controller cancels the command.
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Cancel command
  ad_hoc_command_cancel:
    command_id: command.id
'''

RETURN = '''
id:
    description: command id requesting to cancel
    returned: success
    type: int
    sample: 94
'''


import time

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        command_id=dict(type='int', required=True),
        fail_if_not_running=dict(type='bool', default=False),
        interval=dict(type='float', default=1.0),
        timeout=dict(type='int', default=0),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    command_id = module.params.get('command_id')
    fail_if_not_running = module.params.get('fail_if_not_running')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    # Attempt to look up the command based on the provided name
    command = module.get_one(
        'ad_hoc_commands',
        **{
            'data': {
                'id': command_id,
            }
        }
    )

    if command is None:
        module.fail_json(msg="Unable to find command with id {0}".format(command_id))

    cancel_page = module.get_endpoint(command['related']['cancel'])
    if 'json' not in cancel_page or 'can_cancel' not in cancel_page['json']:
        module.fail_json(msg="Failed to cancel command, got unexpected response", **{'response': cancel_page})

    if not cancel_page['json']['can_cancel']:
        if fail_if_not_running:
            module.fail_json(msg="Ad Hoc Command is not running")
        else:
            module.exit_json(**{'changed': False})

    results = module.post_endpoint(command['related']['cancel'], **{'data': {}})

    if results['status_code'] != 202:
        module.fail_json(msg="Failed to cancel command, see response for details", **{'response': results})

    result = module.get_endpoint(command['related']['cancel'])
    start = time.time()
    while result['json']['can_cancel']:
        # If we are past our time out fail with a message
        if timeout and timeout < time.time() - start:
            # Account for Legacy messages
            module.json_output['msg'] = 'Monitoring of ad hoc command aborted due to timeout'
            module.fail_json(**module.json_output)

        # Put the process to sleep for our interval
        time.sleep(interval)

        result = module.get_endpoint(command['related']['cancel'])

    module.exit_json(**{'changed': True})


if __name__ == '__main__':
    main()
