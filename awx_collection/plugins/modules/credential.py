#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: credential
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller credential.
description:
    - Create, update, or destroy Automation Platform Controller credentials. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the credential.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      required: False
      type: str
    copy_from:
      description:
        - Name or id to copy the credential from.
        - This will copy an existing credential and change any parameters supplied.
        - The new credential name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple credentials share the same name.
      type: str
    description:
      description:
        - The description to use for the credential.
      type: str
    organization:
      description:
        - Organization name, ID, or named URL that should own the credential.
        - This parameter is mutually exclusive with C(team) and C(user).
      type: str
    credential_type:
      description:
        - The credential type being created.
        - Can be a built-in credential type such as "Machine", or a custom credential type such as "My Credential Type"
        - Choices include Amazon Web Services, Ansible Galaxy/Automation Hub API Token, Centrify Vault Credential Provider Lookup,
          Container Registry, CyberArk Central Credential Provider Lookup, CyberArk Conjur Secret Lookup, Google Compute Engine,
          GitHub Personal Access Token, GitLab Personal Access Token, GPG Public Key, HashiCorp Vault Secret Lookup, HashiCorp Vault Signed SSH,
          Insights, Machine, Microsoft Azure Key Vault, Microsoft Azure Resource Manager, Network, OpenShift or Kubernetes API
          Bearer Token, OpenStack, Red Hat Ansible Automation Platform, Red Hat Satellite 6, Red Hat Virtualization, Source Control,
          Thycotic DevOps Secrets Vault, Thycotic Secret Server, Vault, VMware vCenter, or a custom credential type
      required: True
      type: str
    inputs:
      description:
        - >-
          Credential inputs where the keys are var names used in templating.
          Refer to the Automation Platform Controller documentation for example syntax.
        - authorize (use this for net type)
        - authorize_password (password for net credentials that require authorize)
        - client (client or application ID for azure_rm type)
        - security_token (STS token for aws type)
        - secret (secret token for azure_rm type)
        - tenant (tenant ID for azure_rm type)
        - subscription (subscription ID for azure_rm type)
        - domain (domain for openstack type)
        - become_method (become method to use for privilege escalation; some examples are "None", "sudo", "su", "pbrun")
        - become_username (become username; use "ASK" and launch job to be prompted)
        - become_password (become password; use "ASK" and launch job to be prompted)
        - vault_password (the vault password; use "ASK" and launch job to be prompted)
        - project (project that should use this credential for GCP)
        - host (the host for this credential)
        - username (the username for this credential; ``access_key`` for AWS)
        - password (the password for this credential; ``secret_key`` for AWS, ``api_key`` for RAX)
        - ssh_key_data (SSH private key content; to extract the content from a file path, use the lookup function (see examples))
        - vault_id (the vault identifier; this parameter is only valid if C(kind) is specified as C(vault).)
        - ssh_key_unlock (unlock password for ssh_key; use "ASK" and launch job to be prompted)
        - gpg_public_key (GPG Public Key used for signature validation)
      type: dict
    update_secrets:
      description:
        - C(true) will always update encrypted values.
        - C(false) will only update encrypted values if a change is absolutely known to be needed.
      type: bool
      default: true
    user:
      description:
        - User name, ID, or named URL that should own this credential.
        - This parameter is mutually exclusive with C(organization) and C(team).
      type: str
    team:
      description:
        - Team name, ID, or named URL that should own this credential.
        - This parameter is mutually exclusive with C(organization) and C(user).
      type: str
    state:
      description:
        - Desired state of the resource. C(exists) will not modify the resource if it is present.
      choices: ["present", "absent", "exists"]
      default: "present"
      type: str

extends_documentation_fragment: awx.awx.auth

notes:
  - Values `inputs` and the other deprecated fields (such as `tenant`) are replacements of existing values.
    See the last 4 examples for details.
'''


EXAMPLES = '''
- name: Add machine credential
  credential:
    name: Team Name
    description: Team Description
    organization: test-org
    credential_type: Machine
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Create a valid SCM credential from a private_key file
  credential:
    name: SCM Credential
    organization: Default
    state: present
    credential_type: Source Control
    inputs:
      username: joe
      password: secret
      ssh_key_data: "{{ lookup('file', '/tmp/id_rsa') }}"
      ssh_key_unlock: "passphrase"

- name: Fetch private key
  slurp:
    src: '$HOME/.ssh/aws-private.pem'
  register: aws_ssh_key

- name: Add Credential
  credential:
    name: Workshop Credential
    credential_type: Machine
    organization: Default
    inputs:
      ssh_key_data: "{{ aws_ssh_key['content'] | b64decode }}"
  run_once: true
  delegate_to: localhost

- name: Add Credential with Custom Credential Type
  credential:
    name: Workshop Credential
    credential_type: MyCloudCredential
    organization: Default
    controller_username: admin
    controller_password: ansible
    controller_host: https://localhost

- name: Create a Vault credential (example for notes)
  credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'hello'
      vault_id: 'My ID'

- name: Bad password update (will replace vault_id)
  credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'new_password'

- name: Another bad password update (will replace vault_id)
  credential:
    name: Example password
    credential_type: Vault
    organization: Default
    vault_password: 'new_password'

- name: A safe way to update a password and keep vault_id
  credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'new_password'
      vault_id: 'My ID'

- name: Copy Credential
  credential:
    name: Copy password
    copy_from: Example password
    credential_type: Vault
    organization: Foo
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        copy_from=dict(),
        description=dict(),
        organization=dict(),
        credential_type=dict(required=True),
        inputs=dict(type='dict', no_log=True),
        update_secrets=dict(type='bool', default=True, no_log=False),
        user=dict(),
        team=dict(),
        state=dict(choices=['present', 'absent', 'exists'], default='present'),
    )

    mutually_exclusive = [("organization", "user", "team")]

    # Create a module for ourselves
    module = ControllerAPIModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive
    )

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    copy_from = module.params.get('copy_from')
    description = module.params.get('description')
    organization = module.params.get('organization')
    credential_type = module.params.get('credential_type')
    inputs = module.params.get('inputs')
    user = module.params.get('user')
    team = module.params.get('team')
    state = module.params.get('state')

    cred_type_id = module.resolve_name_to_id('credential_types', credential_type)
    if organization:
        org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up the object based on the provided name, credential type and optional organization
    lookup_data = {
        'credential_type': cred_type_id,
    }
    # Create a copy of lookup data for copying without org.
    copy_lookup_data = lookup_data
    if organization:
        lookup_data['organization'] = org_id

    credential = module.get_one('credentials', name_or_id=name, check_exists=(state == 'exists'), **{'data': lookup_data})

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        credential = module.copy_item(
            credential,
            copy_from,
            name,
            endpoint='credentials',
            item_type='credential',
            copy_lookup_data=copy_lookup_data,
        )

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(credential)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if user:
        user_id = module.resolve_name_to_id('users', user)
    if team:
        team_id = module.resolve_name_to_id('teams', team)

    # Create the data that gets sent for create and update
    credential_fields = {
        'name': new_name if new_name else (module.get_item_name(credential) if credential else name),
        'credential_type': cred_type_id,
    }

    if inputs:
        credential_fields['inputs'] = inputs
    if description:
        credential_fields['description'] = description
    if organization:
        credential_fields['organization'] = org_id

    # If we don't already have a credential (and we are creating one) we can add user/team
    # The API does not appear to do anything with these after creation anyway
    # NOTE: We can't just add these on a modification because they are never returned from a GET so it would always cause a changed=True
    if not credential:
        if user:
            credential_fields['user'] = user_id
        if team:
            credential_fields['team'] = team_id

    # If the state was present we can let the module build or update the existing group, this will return on its own
    module.create_or_update_if_needed(credential, credential_fields, endpoint='credentials', item_type='credential')


if __name__ == '__main__':
    main()
