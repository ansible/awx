#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_export
author: "John Westcott IV (@john-westcott-iv)"
version_added: "3.7"
short_description: export resources from Ansible Tower.
description:
    - Export assets from Ansible Tower.
options:
    all:
      description:
        - Export all assets
      type: bool
      default: 'False'
    organizations:
      description:
        - organization name to export
      default: ''
      type: str
    user:
      description:
        - user name to export
      default: ''
      type: str
    team:
      description:
        - team name to export
      default: ''
      type: str
    credential_type:
      description:
        - credential type name to export
      default: ''
      type: str
    credential:
      description:
        - credential name to export
      default: ''
      type: str
    notification_template:
      description:
        - notification template name to export
      default: ''
      type: str
    inventory_script:
      description:
        - inventory script name to export
      default: ''
      type: str
    inventory:
      description:
        - inventory name to export
      default: ''
      type: str
    project:
      description:
        - project name to export
      default: ''
      type: str
    job_template:
      description:
        - job template name to export
      default: ''
      type: str
    workflow:
      description:
        - workflow name to export
      default: ''
      type: str
requirements:
  - "awxkit >= 9.3.0"
notes:
  - Specifying a name of "all" for any asset type will export all items of that asset type.
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Export all tower assets
  tower_export:
    all: True
- name: Export all inventories
  tower_export:
    inventory: 'all'
- name: Export a job template named "My Template" and all Credentials
  tower_export:
    job_template: "My Template"
    credential: 'all'
'''

from os import environ

from ..module_utils.tower_awxkit import TowerAWXKitModule

try:
    from awxkit.api.pages.api import EXPORTABLE_RESOURCES
    HAS_EXPORTABLE_RESOURCES=True
except ImportError:
    HAS_EXPORTABLE_RESOURCES=False


def main():
    argument_spec = dict(
        all=dict(type='bool', default=False),
    )

    # We are not going to raise an error here because the __init__ method of TowerAWXKitModule will do that for us
    if HAS_EXPORTABLE_RESOURCES:
        for resource in EXPORTABLE_RESOURCES:
            argument_spec[resource] = dict()

    module = TowerAWXKitModule(argument_spec=argument_spec)

    if not HAS_EXPORTABLE_RESOURCES:
        module.fail_json(msg="Your version of awxkit does not have import/export")

    # The export process will never change a Tower system
    module.json_output['changed'] = False

    # The exporter code currently works like the following:
    #   Empty list == all assets of that type
    #   string = just one asset of that type (by name)
    #   None = skip asset type
    # Here we are going to setup a dict of values to export
    export_args = {}
    for resource in EXPORTABLE_RESOURCES:
        if module.params.get('all') or module.params.get(resource) == 'all':
            # If we are exporting everything or we got the keyword "all" we pass in an empty list for this asset type
            export_args[resource] = []
        else:
            # Otherwise we take either the string or None (if the parameter was not passed) to get one or no items
            export_args[resource] = module.params.get(resource)

    # Run the export process
    module.json_output['assets'] = module.get_api_v2_object().export_assets(**export_args)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
