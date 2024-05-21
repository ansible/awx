#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: import
author: "John Westcott (@john-westcott-iv)"
version_added: "3.7.0"
short_description: import resources into Automation Platform Controller.
description:
    - Import assets into Automation Platform Controller. See
      U(https://www.ansible.com/tower) for an overview.
options:
    assets:
      description:
        - The assets to import.
        - This can be the output of the export module or loaded from a file
      required: True
      type: dict
requirements:
  - "awxkit >= 9.3.0"
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Export all assets
  export:
    all: True
  register: export_output

- name: Import all assets from our export
  import:
    assets: "{{ export_output.assets }}"

- name: Load data from a json file created by a command like awx export --organization Default
  import:
    assets: "{{ lookup('file', 'org.json') | from_json() }}"
'''

from ..module_utils.awxkit import ControllerAWXKitModule

# These two lines are not needed if awxkit changes to do programatic notifications on issues
from ansible.module_utils.six.moves import StringIO
import logging

# In this module we don't use EXPORTABLE_RESOURCES, we just want to validate that our installed awxkit has import/export
try:
    from awxkit.api.pages.api import EXPORTABLE_RESOURCES  # noqa: F401; pylint: disable=unused-import

    HAS_EXPORTABLE_RESOURCES = True
except ImportError:
    HAS_EXPORTABLE_RESOURCES = False


def main():
    argument_spec = dict(assets=dict(type='dict', required=True))

    module = ControllerAWXKitModule(argument_spec=argument_spec, supports_check_mode=False)

    assets = module.params.get('assets')

    if not HAS_EXPORTABLE_RESOURCES:
        module.fail_json(msg="Your version of awxkit does not appear to have import/export")

    # Currently the import process does not return anything on error
    # It simply just logs to Python's logger
    # Set up a log gobbler to get error messages from import_assets
    logger = logging.getLogger('awxkit.api.pages.api')
    logger.setLevel(logging.ERROR)

    log_capture_string = StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.ERROR)

    logger.addHandler(ch)
    log_contents = ''

    # Run the import process
    try:
        module.json_output['changed'] = module.get_api_v2_object().import_assets(assets)
    except Exception as e:
        module.fail_json(msg="Failed to import assets {0}".format(e))
    finally:
        # Finally, consume the logs in case there were any errors and die if there were
        log_contents = log_capture_string.getvalue()
        log_capture_string.close()
        if log_contents != '':
            module.fail_json(msg=log_contents)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
