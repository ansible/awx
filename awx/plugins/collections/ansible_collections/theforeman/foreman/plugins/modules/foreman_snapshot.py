#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2019 Manisha Singhal (ATIX AG)
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
module: foreman_snapshot
short_description: Manage Foreman Snapshots
description:
  - "Manage Foreman Snapshots for Host Entities"
  - "This module can create, update, revert and delete snapshots"
  - "This module requires the foreman_snapshot_management plugin set up in the server"
  - "See: U(https://github.com/ATIX-AG/foreman_snapshot_management)"
author:
  - "Manisha Singhal (@Manisha15) ATIX AG"
options:
  name:
    description:
      - Name of Snapshot
    required: true
    type: str
  description:
    description:
      - Description of Snapshot
    required: false
    type: str
  host:
    description:
      - Name of related Host
    required: true
    type: str
  state:
    description:
      - State of Snapshot
    default: present
    choices: ["present", "reverted", "absent"]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create a Snapshot"
  foreman_snapshot:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "snapshot_before_software_upgrade"
    host: "server.example.com"
    state: present

- name: "Update a Snapshot"
  foreman_snapshot:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "snapshot_before_software_upgrade"
    host: "server.example.com"
    description: "description of snapshot"
    state: present

- name: "Revert a Snapshot"
  foreman_snapshot:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "snapshot_before_software_upgrade"
    host: "server.example.com"
    state: reverted

- name: "Delete a Snapshot"
  foreman_snapshot:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "snapshot_before_software_upgrade"
    host: "server.example.com"
    state: absent
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        argument_spec=dict(
            host=dict(required=True),
            state=dict(default='present', choices=['present', 'absent', 'reverted']),
        ),
        entity_spec=dict(
            name=dict(required=True),
            description=dict(),
        ),
    )
    snapshot_dict = module.clean_params()

    module.connect()

    host = module.find_resource_by_name('hosts', name=snapshot_dict['host'], failsafe=False, thin=True)
    scope = {'host_id': host['id']}

    entity = module.find_resource_by_name('snapshots', name=snapshot_dict['name'], params=scope, failsafe=True)

    changed = module.ensure_entity_state('snapshots', snapshot_dict, entity, params=scope)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
