#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: export
author: "John Westcott IV (@john-westcott-iv)"
version_added: "3.7.0"
short_description: export resources from Automation Platform Controller.
description:
    - Export assets from Automation Platform Controller.
options:
    all:
      description:
        - Export all assets
      type: bool
      default: 'False'
    organizations:
      description:
        - organization names, IDs, or named URLs to export
      type: list
      elements: str
    users:
      description:
        - user names, IDs, or named URLs to export
      type: list
      elements: str
    teams:
      description:
        - team names, IDs, or named URLs to export
      type: list
      elements: str
    credential_types:
      description:
        - credential type names, IDs, or named URLs to export
      type: list
      elements: str
    credentials:
      description:
        - credential names, IDs, or named URLs to export
      type: list
      elements: str
    execution_environments:
      description:
        - execution environment names, IDs, or named URLs to export
      type: list
      elements: str
    notification_templates:
      description:
        - notification template names, IDs, or named URLs to export
      type: list
      elements: str
    inventory_sources:
      description:
        - inventory source name, ID, or named URLs to export
      type: list
      elements: str
    inventory:
      description:
        - inventory names, IDs, or named URLs to export
      type: list
      elements: str
    projects:
      description:
        - project names, IDs, or named URLs to export
      type: list
      elements: str
    job_templates:
      description:
        - job template names, IDs, or named URLs to export
      type: list
      elements: str
    workflow_job_templates:
      description:
        - workflow names, IDs, or named URLs to export
      type: list
      elements: str
    applications:
      description:
        - OAuth2 application names, IDs, or named URLs to export
      type: list
      elements: str
    schedules:
      description:
        - schedule names, IDs, or named URLs to export
      type: list
      elements: str
requirements:
  - "awxkit >= 9.3.0"
notes:
  - Specifying a name of "all" for any asset type will export all items of that asset type.
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Export all assets
  export:
    all: True

- name: Export all inventories
  export:
    inventory: 'all'

- name: Export a job template named "My Template" and all Credentials
  export:
    job_templates: "My Template"
    credentials: 'all'

- name: Export a list of inventories
  export:
    inventory: ['My Inventory 1', 'My Inventory 2']
'''

import logging
from ansible.module_utils.six.moves import StringIO
from ..module_utils.awxkit import ControllerAWXKitModule

try:
    from awxkit.api.pages.api import EXPORTABLE_RESOURCES

    HAS_EXPORTABLE_RESOURCES = True
except ImportError:
    HAS_EXPORTABLE_RESOURCES = False


def main():
    argument_spec = dict(
        all=dict(type='bool', default=False),
    )

    # We are not going to raise an error here because the __init__ method of ControllerAWXKitModule will do that for us
    if HAS_EXPORTABLE_RESOURCES:
        for resource in EXPORTABLE_RESOURCES:
            argument_spec[resource] = dict(type='list', elements='str')

    module = ControllerAWXKitModule(argument_spec=argument_spec)

    if not HAS_EXPORTABLE_RESOURCES:
        module.fail_json(msg="Your version of awxkit does not have import/export")

    # The export process will never change the AWX system
    module.json_output['changed'] = False

    # The exporter code currently works like the following:
    #   Empty string == all assets of that type
    #   Non-Empty string = just a list of assets of that type (by name, ID, or named URL)
    #   Asset type not present or None = skip asset type (unless everything is None, then export all)
    # Here we are going to setup a dict of values to export
    export_args = {}
    for resource in EXPORTABLE_RESOURCES:
        if module.params.get('all') or module.params.get(resource) == ['all']:
            # If we are exporting everything or we got the keyword "all" we pass in an empty string for this asset type
            export_args[resource] = ''
        else:
            # Otherwise we take either the string or None (if the parameter was not passed) to get one or no items
            export_args[resource] = module.params.get(resource)

    # Currently the export process does not return anything on error
    # It simply just logs to Python's logger
    # Set up a log gobbler to get error messages from export_assets
    log_capture_string = StringIO()
    ch = logging.StreamHandler(log_capture_string)
    for logger_name in ['awxkit.api.pages.api', 'awxkit.api.pages.page']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)

    logger.addHandler(ch)
    log_contents = ''

    # Run the export process
    try:
        module.json_output['assets'] = module.get_api_v2_object().export_assets(**export_args)
        module.exit_json(**module.json_output)
    except Exception as e:
        module.fail_json(msg="Failed to export assets {0}".format(e))
    finally:
        # Finally, consume the logs in case there were any errors and die if there were
        log_contents = log_capture_string.getvalue()
        log_capture_string.close()
        if log_contents != '':
            module.fail_json(msg=log_contents)


if __name__ == '__main__':
    main()
