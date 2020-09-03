#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_send
deprecated:
  removed_in: "14.0.0"
  why: Deprecated in favor of upcoming C(_import) module.
  alternative: Once published, use M(tower_import) instead.
author: "John Westcott IV (@john-westcott-iv)"
short_description: Send assets to Ansible Tower.
description:
    - Send assets to Ansible Tower. See
      U(https://www.ansible.com/tower) for an overview.
options:
    assets:
      description:
        - The assets to import.
        - This can be the output of tower_receive or loaded from a file
      type: str
    files:
      description:
        - List of files to import.
      default: []
      type: list
      elements: str
    prevent:
      description:
        - A list of asset types to prevent import for
      default: []
      type: list
      elements: str
    password_management:
      description:
        - The password management option to use.
        - The prompt option is not supported.
      default: 'default'
      choices: ["default", "random"]
      type: str

notes:
  - One of assets or files needs to be passed in

requirements:
  - "ansible-tower-cli >= 3.3.0"
  - six.moves.StringIO
  - sys

extends_documentation_fragment: awx.awx.auth_legacy
'''

EXAMPLES = '''
- name: Import all tower assets
  tower_send:
    assets: "{{ export_output.assets }}"
    tower_config_file: "~/tower_cli.cfg"
'''

RETURN = '''
output:
    description: The import messages
    returned: success, fail
    type: list
    sample: [ 'Message 1', 'Message 2' ]
'''

import os
import sys

from ansible.module_utils.six.moves import StringIO
from ..module_utils.tower_legacy import TowerLegacyModule, tower_auth_config, HAS_TOWER_CLI

from tempfile import mkstemp

try:
    from tower_cli.cli.transfer.send import Sender
    from tower_cli.utils.exceptions import TowerCLIError

    from tower_cli.conf import settings
    TOWER_CLI_HAS_EXPORT = True
except ImportError:
    TOWER_CLI_HAS_EXPORT = False


def main():
    argument_spec = dict(
        assets=dict(),
        files=dict(default=[], type='list', elements='str'),
        prevent=dict(default=[], type='list', elements='str'),
        password_management=dict(default='default', choices=['default', 'random']),
    )

    module = TowerLegacyModule(argument_spec=argument_spec, supports_check_mode=False)

    module.deprecate(msg="This module is deprecated and will be replaced by the AWX CLI import command", version="awx.awx:14.0.0")

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    if not TOWER_CLI_HAS_EXPORT:
        module.fail_json(msg='ansible-tower-cli version does not support export')

    assets = module.params.get('assets')
    prevent = module.params.get('prevent')
    password_management = module.params.get('password_management')
    files = module.params.get('files')

    result = dict(
        changed=False,
        msg='',
        output='',
    )

    if not assets and not files:
        result['msg'] = "Assets or files must be specified"
        module.fail_json(**result)

    path = None
    if assets:
        # We got assets so we need to dump this out to a temp file and append that to files
        handle, path = mkstemp(prefix='', suffix='', dir='')
        with open(path, 'w') as f:
            f.write(assets)
        files.append(path)

    tower_auth = tower_auth_config(module)
    failed = False
    with settings.runtime_values(**tower_auth):
        try:
            sender = Sender(no_color=False)
            old_stdout = sys.stdout
            sys.stdout = captured_stdout = StringIO()
            try:
                sender.send(files, prevent, password_management)
            except TypeError:
                # Newer versions of TowerCLI require 4 parameters
                sender.send(files, prevent, [], password_management)

            if sender.error_messages > 0:
                failed = True
                result['msg'] = "Transfer Failed with %d errors" % sender.error_messages
            if sender.changed_messages > 0:
                result['changed'] = True
        except TowerCLIError as e:
            result['msg'] = e.message
            failed = True
        finally:
            if path is not None:
                os.remove(path)
            result['output'] = captured_stdout.getvalue().split("\n")
            sys.stdout = old_stdout

    # Return stdout so that module returns will work
    if failed:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
