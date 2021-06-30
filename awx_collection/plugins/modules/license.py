#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: license
author: "John Westcott IV (@john-westcott-iv)"
short_description: Set the license for Automation Platform Controller
description:
    - Get or Set Automation Platform Controller license. See
      U(https://www.ansible.com/tower) for an overview.
options:
    manifest:
      description:
        - file path to a Red Hat subscription manifest (a .zip file)
      required: True
      type: str
    force:
      description:
        - By default, the license manifest will only be applied if Tower is currently
          unlicensed or trial licensed.  When force=true, the license is always applied.
      type: bool
      default: 'False'
extends_documentation_fragment: awx.awx.auth
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Set the license using a file
  license:
    manifest: "/tmp/my_manifest.zip"
'''

import base64
from ..module_utils.controller_api import ControllerAPIModule


def main():

    module = ControllerAPIModule(
        argument_spec=dict(
            manifest=dict(type='str', required=True),
            force=dict(type='bool', default=False),
        ),
    )

    json_output = {'changed': False}

    try:
        with open(module.params.get('manifest'), 'rb') as fid:
            manifest = base64.b64encode(fid.read())
    except OSError as e:
        module.fail_json(msg=str(e))

    # Check if Tower is already licensed
    config = module.get_endpoint('config')['json']
    already_licensed = (
        'license_info' in config
        and 'instance_count' in config['license_info']
        and config['license_info']['instance_count'] > 0
        and 'trial' in config['license_info']
        and not config['license_info']['trial']
    )

    # Determine if we will install the license
    perform_install = bool((not already_licensed) or module.params.get('force'))

    # Handle check mode
    if module.check_mode:
        json_output['changed'] = perform_install
        module.exit_json(**json_output)

    # Do the actual install, if we need to
    if perform_install:
        json_output['changed'] = True
        module.post_endpoint('config', data={'manifest': manifest.decode()})

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
