#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_license
author: "John Westcott IV (@john-westcott-iv)"
short_description: Set the license for Ansible Tower
description:
    - Get or Set Ansible Tower license. See
      U(https://www.ansible.com/tower) for an overview.
options:
    data:
      description:
        - The contents of the license file
      required: True
      type: dict
    eula_accepted:
      description:
        - Whether or not the EULA is accepted.
      required: True
      type: bool
extends_documentation_fragment: awx.awx.auth
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Set the license using a file
  license:
    data: "{{ lookup('file', '/tmp/my_tower.license') }}"
    eula_accepted: True
'''

from ..module_utils.tower_api import TowerAPIModule


def main():

    module = TowerAPIModule(
        argument_spec=dict(
            data=dict(type='dict', required=True),
            eula_accepted=dict(type='bool', required=True),
        ),
    )

    json_output = {'changed': False}

    if not module.params.get('eula_accepted'):
        module.fail_json(msg='You must accept the EULA by passing in the param eula_accepted as True')

    json_output['old_license'] = module.get_endpoint('settings/system/')['json']['LICENSE']
    new_license = module.params.get('data')

    if json_output['old_license'] != new_license:
        json_output['changed'] = True

        # Deal with check mode
        if module.check_mode:
            module.exit_json(**json_output)

        # We need to add in the EULA
        new_license['eula_accepted'] = True
        module.post_endpoint('config', data=new_license)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
