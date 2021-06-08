#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ad_hoc_command_wait
author: "John Westcott IV (@john-westcott-iv)"
short_description: Wait for Automation Platform Controller Ad Hoc Command to finish.
description:
    - Wait for Automation Platform Controller ad hoc command to finish and report success or failure. See
      U(https://www.ansible.com/tower) for an overview.
options:
    command_id:
      description:
        - ID of the ad hoc command to monitor.
      required: True
      type: int
    interval:
      description:
        - The interval in sections, to request an update from the controller.
      required: False
      default: 1
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a ad hoc command to finish.
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Launch an ad hoc command
  ad_hoc_command:
    inventory: "Demo Inventory"
    credential: "Demo Credential"
    wait: false
  register: command

- name: Wait for ad joc command max 120s
  ad_hoc_command_wait:
    command_id: "{{ command.id }}"
    timeout: 120
'''

RETURN = '''
id:
    description: Ad hoc command id that is being waited on
    returned: success
    type: int
    sample: 99
elapsed:
    description: total time in seconds the command took to run
    returned: success
    type: float
    sample: 10.879
started:
    description: timestamp of when the command started running
    returned: success
    type: str
    sample: "2017-03-01T17:03:53.200234Z"
finished:
    description: timestamp of when the command finished running
    returned: success
    type: str
    sample: "2017-03-01T17:04:04.078782Z"
status:
    description: current status of command
    returned: success
    type: str
    sample: successful
'''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        command_id=dict(type='int', required=True),
        timeout=dict(type='int'),
        interval=dict(type='float', default=1),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    command_id = module.params.get('command_id')
    timeout = module.params.get('timeout')
    interval = module.params.get('interval')

    # Attempt to look up command based on the provided id
    command = module.get_one(
        'ad_hoc_commands',
        **{
            'data': {
                'id': command_id,
            }
        }
    )

    if command is None:
        module.fail_json(msg='Unable to wait on ad hoc command {0}; that ID does not exist.'.format(command_id))

    # Invoke wait function
    module.wait_on_url(url=command['url'], object_name=command_id, object_type='ad hoc command', timeout=timeout, interval=interval)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
