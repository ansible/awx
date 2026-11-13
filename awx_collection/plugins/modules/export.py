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
    schedules:
      description:
        - schedule names, IDs, or named URLs to export
      type: list
      elements: str
    exclude_inventory_children:
      description:
        - Names or IDs of inventories whose hosts and groups will be left out of the export.
        - The inventories themselves are still exported.
        - Inventory sources are a separate asset type, so select I(inventory_sources) as well if the omitted
          hosts and groups are meant to be recreated by a source synchronization after an import.
        - Note that manually added hosts and groups are omitted as well, and no source will restore them.
      type: list
      elements: str
    exclude_dynamic_inventory_children:
      description:
        - Leave the hosts and groups of every inventory that has at least one inventory source out of the export.
        - Inventory sources are a separate asset type, so select I(inventory_sources) as well, otherwise the
          export carries neither the children nor the sources that would recreate them.
        - Given that, the omitted hosts and groups are recreated when the sources are synchronized after an import.
        - Note that manually added hosts and groups of such an inventory are omitted as well, and no source will restore them.
      type: bool
      default: false
requirements:
  - "awxkit >= 9.3.0"
notes:
  - Specifying a name of "all" for any asset type will export all items of that asset type.
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Export all assets
  export:
    all: true

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

- name: Export all inventories without the hosts and groups of the dynamic ones
  export:
    inventory: 'all'
    # the sources are what recreate the omitted hosts and groups on the next sync
    inventory_sources: 'all'
    exclude_dynamic_inventory_children: true

- name: Export all assets, skipping the children of two known dynamic inventories
  export:
    all: true
    exclude_inventory_children:
      - 'My Cloud Inventory'
      - 'My Other Cloud Inventory'
'''

import logging
from ansible.module_utils.six.moves import StringIO
from ..module_utils.awxkit import ControllerAWXKitModule

try:
    from awxkit.api.pages.api import EXPORTABLE_RESOURCES

    HAS_EXPORTABLE_RESOURCES = True
except ImportError:
    HAS_EXPORTABLE_RESOURCES = False

try:
    from awxkit.api.pages.api import INVENTORY_CHILDREN  # noqa: F401

    HAS_EXCLUDABLE_INVENTORY_CHILDREN = True
except ImportError:
    HAS_EXCLUDABLE_INVENTORY_CHILDREN = False


def main():
    argument_spec = dict(
        all=dict(type='bool', default=False),
        exclude_inventory_children=dict(type='list', elements='str'),
        exclude_dynamic_inventory_children=dict(type='bool', default=False),
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

    # Only pass the exclusions on when they were asked for, so that an older awxkit,
    # which would reject the unknown keywords, keeps working for everyone else
    exclude_inventory_children = module.params.get('exclude_inventory_children')
    exclude_dynamic_inventory_children = module.params.get('exclude_dynamic_inventory_children')
    if exclude_inventory_children or exclude_dynamic_inventory_children:
        if not HAS_EXCLUDABLE_INVENTORY_CHILDREN:
            module.fail_json(msg="Your version of awxkit does not support excluding the children of an inventory from an export")
        export_args['exclude_inventory_children'] = exclude_inventory_children
        export_args['exclude_dynamic_inventory_children'] = exclude_dynamic_inventory_children

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
