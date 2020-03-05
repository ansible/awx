#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Eric D Helms <ericdhelms@gmail.com>
# (c) 2017, Matthias M Dellweg <dellweg@atix.de> (ATIX AG)
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
module: foreman_organization
short_description: Manage Foreman Organization
description:
    - Manage Foreman Organization
author:
    - "Eric D Helms (@ehelms)"
    - "Matthias M Dellweg (@mdellweg) ATIX AG"
options:
  name:
    description:
      - Name of the Foreman organization
    required: true
    type: str
  description:
    description:
      - Description of the Foreman organization
    required: false
    type: str
  state:
    description:
      - State of the Organization
    default: present
    choices:
      - present
      - absent
    type: str
  label:
    description:
      - Label of the Foreman organization
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create CI Organization"
  foreman_organization:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "My Cool New Organization"
    state: present
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import ForemanEntityAnsibleModule


def main():
    module = ForemanEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            description=dict(),
            label=dict(),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity = module.find_resource_by_name('organizations', name=entity_dict['name'], failsafe=True)

    changed = module.ensure_entity_state('organizations', entity_dict, entity)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
