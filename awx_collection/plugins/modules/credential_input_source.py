#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2020, Tom Page <tpage@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: credential_input_source
author: "Tom Page (@Tompage1994)"
version_added: "2.3.0"
short_description: create, update, or destroy Automation Platform Controller credential input sources.
description:
    - Create, update, or destroy Automation Platform Controller credential input sources. See
      U(https://www.ansible.com/tower) for an overview.
options:
    description:
      description:
        - The description to use for the credential input source.
      type: str
    input_field_name:
      description:
        - The input field the credential source will be used for
      required: True
      type: str
    metadata:
      description:
        - A JSON or YAML string
      required: False
      type: dict
    target_credential:
      description:
        - The credential which will have its input defined by this source
      required: true
      type: str
    source_credential:
      description:
        - The credential which is the source of the credential lookup
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str

extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Use CyberArk Lookup credential as password source
  credential_input_source:
    input_field_name: password
    target_credential: new_cred
    source_credential: cyberark_lookup
    metadata:
      object_query: "Safe=MY_SAFE;Object=awxuser"
      object_query_format: "Exact"
    state: present

'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        description=dict(),
        input_field_name=dict(required=True),
        target_credential=dict(required=True),
        source_credential=dict(),
        metadata=dict(type="dict"),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    description = module.params.get('description')
    input_field_name = module.params.get('input_field_name')
    target_credential = module.params.get('target_credential')
    source_credential = module.params.get('source_credential')
    metadata = module.params.get('metadata')
    state = module.params.get('state')

    target_credential_id = module.resolve_name_to_id('credentials', target_credential)

    # Attempt to look up the object based on the target credential and input field
    lookup_data = {
        'target_credential': target_credential_id,
        'input_field_name': input_field_name,
    }
    credential_input_source = module.get_one('credential_input_sources', **{'data': lookup_data})

    if state == 'absent':
        module.delete_if_needed(credential_input_source)

    # Create the data that gets sent for create and update
    credential_input_source_fields = {
        'target_credential': target_credential_id,
        'input_field_name': input_field_name,
    }
    if source_credential:
        credential_input_source_fields['source_credential'] = module.resolve_name_to_id('credentials', source_credential)
    if metadata:
        credential_input_source_fields['metadata'] = metadata
    if description:
        credential_input_source_fields['description'] = description

    # If the state was present we can let the module build or update the existing group, this will return on its own
    module.create_or_update_if_needed(
        credential_input_source, credential_input_source_fields, endpoint='credential_input_sources', item_type='credential_input_source'
    )


if __name__ == '__main__':
    main()
