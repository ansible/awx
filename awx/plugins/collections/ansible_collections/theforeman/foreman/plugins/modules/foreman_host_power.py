#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Bernhard Hopfenmüller (ATIX AG)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: foreman_host_power
short_description: Manage Foreman hosts power state
description:
  - "Manage power state of Foreman host"
  - "This beta version can start and stop an existing foreman host and question the current power state."
author:
  - "Bernhard Hopfenmueller (@Fobhep) ATIX AG"
  - "Baptiste Agasse (@bagasse)"
options:
  name:
    description: Name (FQDN) of the host
    required: true
    aliases:
      - hostname
    type: str
  state:
    description: Desired power state
    default: state
    choices:
      - 'on'
      - 'start'
      - 'off'
      - 'stop'
      - 'soft'
      - 'reboot'
      - 'cycle'
      - 'reset'
      - 'state'
      - 'status'
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Switch a host on"
  foreman_host_power:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    hostname: "test-host.domain.test"
    state: on

- name: "Switch a host off"
  foreman_host_power:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    hostname: "test-host.domain.test"
    state: off

- name: "Query host power state"
  foreman_host_power:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    hostname: "test-host.domain.test"
    state: state
    register: result
- debug:
    msg: "Host power state is {{ result.power_state }}"


'''

RETURN = '''
power_state:
    description: current power state of host
    returned: always
    type: str
    sample: "off"
 '''

from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(aliases=['hostname'], required=True),
            state=dict(default='state', choices=['on', 'start', 'off', 'stop', 'soft', 'reboot', 'cycle', 'reset', 'state', 'status']),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    params = {'id': entity_dict['name']}
    _power_state_changed, power_state = module.resource_action('hosts', 'power_status', params=params, ignore_check_mode=True)
    if module.state in ['state', 'status']:
        module.exit_json(changed=False, power_state=power_state['state'])
    elif ((module.state in ['on', 'start'] and power_state['state'] == 'on')
          or (module.state in ['off', 'stop'] and power_state['state'] == 'off')):
        module.exit_json(changed=False)
    else:
        params['power_action'] = module.state
        changed, power_state = module.resource_action('hosts', 'power', params=params)
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
