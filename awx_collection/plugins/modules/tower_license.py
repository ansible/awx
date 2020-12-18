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
    manifest:
      description:
        - file path to a Red Hat subscription manifest (a .zip file)
      required: True
      type: str
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
  tower_license:
    manifest: "/tmp/my_manifest.zip"
    eula_accepted: True
'''

import base64
from ..module_utils.tower_api import TowerAPIModule


def main():

    module = TowerAPIModule(
        argument_spec=dict(
            manifest=dict(type='str', required=True),
            eula_accepted=dict(type='bool', required=True),
        ),
    )

    json_output = {'changed': True}

    if not module.params.get('eula_accepted'):
        module.fail_json(msg='You must accept the EULA by passing in the param eula_accepted as True')

    try:
        manifest = base64.b64encode(
            open(module.params.get('manifest'), 'rb').read()
        )
    except OSError as e:
        module.fail_json(msg=str(e))

    # Deal with check mode
    if module.check_mode:
        module.exit_json(**json_output)

    module.post_endpoint('config', data={
        'eula_accepted': True,
        'manifest': manifest.decode()
    })

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
