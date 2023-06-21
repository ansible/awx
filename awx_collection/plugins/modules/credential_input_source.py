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
    target_organization:
      description:
        - Organization that should own the target credential.
    target_credential_type:
      description:
        - The credential type of the target to be used for lookup
        - Can be a built-in credential type such as "Machine", or a custom credential type such as "My Credential Type"
        - Choices include Amazon Web Services, Ansible Galaxy/Automation Hub API Token, Centrify Vault Credential Provider Lookup,
          Container Registry, CyberArk Central Credential Provider Lookup, CyberArk Conjur Secret Lookup, Google Compute Engine,
          GitHub Personal Access Token, GitLab Personal Access Token, GPG Public Key, HashiCorp Vault Secret Lookup, HashiCorp Vault Signed SSH,
          Insights, Machine, Microsoft Azure Key Vault, Microsoft Azure Resource Manager, Network, OpenShift or Kubernetes API
          Bearer Token, OpenStack, Red Hat Ansible Automation Platform, Red Hat Satellite 6, Red Hat Virtualization, Source Control,
          Thycotic DevOps Secrets Vault, Thycotic Secret Server, Vault, VMware vCenter, or a custom credential type
      type: str
    source_credential:
      description:
        - The credential which is the source of the credential lookup
      type: str
    source_organization:
      description:
        - Organization that should own the source credential.
      type: str
    source_credential_type:
      description:
        - The credential type of the source to be used for lookup
        - Can be a built-in credential type such as "Machine", or a custom credential type such as "My Credential Type"
        - Choices include Amazon Web Services, Ansible Galaxy/Automation Hub API Token, Centrify Vault Credential Provider Lookup,
          Container Registry, CyberArk Central Credential Provider Lookup, CyberArk Conjur Secret Lookup, Google Compute Engine,
          GitHub Personal Access Token, GitLab Personal Access Token, GPG Public Key, HashiCorp Vault Secret Lookup, HashiCorp Vault Signed SSH,
          Insights, Machine, Microsoft Azure Key Vault, Microsoft Azure Resource Manager, Network, OpenShift or Kubernetes API
          Bearer Token, OpenStack, Red Hat Ansible Automation Platform, Red Hat Satellite 6, Red Hat Virtualization, Source Control,
          Thycotic DevOps Secrets Vault, Thycotic Secret Server, Vault, VMware vCenter, or a custom credential type
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent", "exists"]
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
        target_organization=dict(),
        target_credential_type=dict(),
        source_credential=dict(),
        source_organization=dict(),
        source_credential_type=dict(),
        metadata=dict(type="dict"),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    description = module.params.get('description')
    input_field_name = module.params.get('input_field_name')
    target_credential = module.params.get('target_credential')
    target_organization = module.params.get('target_organization')
    target_credential_type = module.params.get('target_credential_type')
    source_credential = module.params.get('source_credential')
    source_organization = module.params.get('source_organization')
    source_credential_type = module.params.get('source_credential_type')
    metadata = module.params.get('metadata')
    state = module.params.get('state')

    # Set lookup data
    target_lookup_data = {}
    if target_credential_type:
        cred_type_id = module.resolve_name_to_id('credential_types', target_credential_type)
        target_lookup_data['credential_type'] = cred_type_id
    if target_organization:
        target_lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    target_credential_id = module.get_one('credentials', name_or_id=target_credential, **{'data': target_lookup_data})['id']

    # Attempt to look up the object based on the target credential and input field
    target_lookup_data = {
        'target_credential': target_credential_id,
        'input_field_name': input_field_name,
    }

    credential_input_source = module.get_one('credential_input_sources', check_exists=(state == 'exists'), **{'data': lookup_data})

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
