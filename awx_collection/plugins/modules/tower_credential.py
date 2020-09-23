#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_credential
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower credential.
description:
    - Create, update, or destroy Ansible Tower credentials. See
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
    description:
      description:
        - The description to use for the credential.
      type: str
    organization:
      description:
        - Organization that should own the credential.
      type: str
    credential_type:
      description:
        - Name of credential type.
        - Will be preferred over kind
      type: str
    inputs:
      description:
        - >-
          Credential inputs where the keys are var names used in templating.
          Refer to the Ansible Tower documentation for example syntax.
        - Any fields in this dict will take prescedence over any fields mentioned below (i.e. host, username, etc)
      type: dict
    update_secrets:
      description:
        - C(true) will always update encrypted values.
        - C(false) will only updated encrypted values if a change is absolutely known to be needed.
      type: bool
      default: true
    user:
      description:
        - User that should own this credential.
      type: str
    team:
      description:
        - Team that should own this credential.
      type: str

    kind:
      description:
        - Type of credential being added.
        - The ssh choice refers to a Tower Machine credential.
        - Deprecated, please use credential_type
      required: False
      type: str
      choices: ["ssh", "vault", "net", "scm", "aws", "vmware", "satellite6", "cloudforms", "gce", "azure_rm", "openstack", "rhv", "insights", "tower"]
    host:
      description:
        - Host for this credential.
        - Deprecated, will be removed in a future release
      type: str
    username:
      description:
        - Username for this credential. ``access_key`` for AWS.
        - Deprecated, please use inputs
      type: str
    password:
      description:
        - Password for this credential. ``secret_key`` for AWS. ``api_key`` for RAX.
        - Use "ASK" and launch in Tower to be prompted.
        - Deprecated, please use inputs
      type: str
    project:
      description:
        - Project that should use this credential for GCP.
        - Deprecated, will be removed in a future release
      type: str
    ssh_key_data:
      description:
        - SSH private key content. To extract the content from a file path, use the lookup function (see examples).
        - Deprecated, please use inputs
      type: str
    ssh_key_unlock:
      description:
        - Unlock password for ssh_key.
        - Use "ASK" and launch in Tower to be prompted.
        - Deprecated, please use inputs
      type: str
    authorize:
      description:
        - Should use authorize for net type.
        - Deprecated, please use inputs
      type: bool
      default: 'no'
    authorize_password:
      description:
        - Password for net credentials that require authorize.
        - Deprecated, please use inputs
      type: str
    client:
      description:
        - Client or application ID for azure_rm type.
        - Deprecated, please use inputs
      type: str
    security_token:
      description:
        - STS token for aws type.
        - Deprecated, please use inputs
      type: str
    secret:
      description:
        - Secret token for azure_rm type.
        - Deprecated, please use inputs
      type: str
    subscription:
      description:
        - Subscription ID for azure_rm type.
        - Deprecated, please use inputs
      type: str
    tenant:
      description:
        - Tenant ID for azure_rm type.
        - Deprecated, please use inputs
      type: str
    domain:
      description:
        - Domain for openstack type.
        - Deprecated, please use inputs
      type: str
    become_method:
      description:
        - Become method to use for privilege escalation.
        - Some examples are "None", "sudo", "su", "pbrun"
        - Due to become plugins, these can be arbitrary
        - Deprecated, please use inputs
      type: str
    become_username:
      description:
        - Become username.
        - Use "ASK" and launch in Tower to be prompted.
        - Deprecated, please use inputs
      type: str
    become_password:
      description:
        - Become password.
        - Use "ASK" and launch in Tower to be prompted.
        - Deprecated, please use inputs
      type: str
    vault_password:
      description:
        - Vault password.
        - Use "ASK" and launch in Tower to be prompted.
        - Deprecated, please use inputs
      type: str
    vault_id:
      description:
        - Vault identifier.
        - This parameter is only valid if C(kind) is specified as C(vault).
        - Deprecated, please use inputs
      type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str

extends_documentation_fragment: awx.awx.auth

notes:
  - Values `inputs` and the other deprecated fields (such as `tenant`) are replacements of existing values.
    See the last 4 examples for details.
'''


EXAMPLES = '''
- name: Add tower machine credential
  tower_credential:
    name: Team Name
    description: Team Description
    organization: test-org
    credential_type: Machine
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Create a valid SCM credential from a private_key file
  tower_credential:
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

- name: Add Credential Into Tower
  tower_credential:
    name: Workshop Credential
    credential_type: Machine
    organization: Default
    inputs:
      ssh_key_data: "{{ aws_ssh_key['content'] | b64decode }}"
  run_once: true
  delegate_to: localhost

- name: Add Credential with Custom Credential Type
  tower_credential:
    name: Workshop Credential
    credential_type: MyCloudCredential
    organization: Default
    tower_username: admin
    tower_password: ansible
    tower_host: https://localhost

- name: Create a Vaiult credential (example for notes)
  tower_credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'hello'
      vault_id: 'My ID'

- name: Bad password update (will replace vault_id)
  tower_credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'new_password'

- name: Another bad password update (will replace vault_id)
  tower_credential:
    name: Example password
    credential_type: Vault
    organization: Default
    vault_password: 'new_password'

- name: A safe way to update a password and keep vault_id
  tower_credential:
    name: Example password
    credential_type: Vault
    organization: Default
    inputs:
      vault_password: 'new_password'
      vault_id: 'My ID'

'''

from ..module_utils.tower_api import TowerAPIModule

KIND_CHOICES = {
    'ssh': 'Machine',
    'vault': 'Vault',
    'net': 'Network',
    'scm': 'Source Control',
    'aws': 'Amazon Web Services',
    'vmware': 'VMware vCenter',
    'satellite6': 'Red Hat Satellite 6',
    'cloudforms': 'Red Hat CloudForms',
    'gce': 'Google Compute Engine',
    'azure_rm': 'Microsoft Azure Resource Manager',
    'openstack': 'OpenStack',
    'rhv': 'Red Hat Virtualization',
    'insights': 'Insights',
    'tower': 'Ansible Tower',
}


OLD_INPUT_NAMES = (
    'authorize', 'authorize_password', 'client',
    'security_token', 'secret', 'tenant', 'subscription',
    'domain', 'become_method', 'become_username',
    'become_password', 'vault_password', 'project', 'host',
    'username', 'password', 'ssh_key_data', 'vault_id',
    'ssh_key_unlock'
)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        organization=dict(),
        credential_type=dict(),
        inputs=dict(type='dict', no_log=True),
        update_secrets=dict(type='bool', default=True, no_log=False),
        user=dict(),
        team=dict(),
        # These are for backwards compatability
        kind=dict(choices=list(KIND_CHOICES.keys())),
        host=dict(),
        username=dict(),
        password=dict(no_log=True),
        project=dict(),
        ssh_key_data=dict(no_log=True),
        ssh_key_unlock=dict(no_log=True),
        authorize=dict(type='bool'),
        authorize_password=dict(no_log=True),
        client=dict(),
        security_token=dict(),
        secret=dict(no_log=True),
        subscription=dict(),
        tenant=dict(),
        domain=dict(),
        become_method=dict(),
        become_username=dict(),
        become_password=dict(no_log=True),
        vault_password=dict(no_log=True),
        vault_id=dict(),
        # End backwards compatability
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec, required_one_of=[['kind', 'credential_type']])

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    credential_type = module.params.get('credential_type')
    inputs = module.params.get('inputs')
    user = module.params.get('user')
    team = module.params.get('team')
    # The legacy arguments are put into a hash down below
    kind = module.params.get('kind')
    # End backwards compatability
    state = module.params.get('state')

    # Deprication warnings
    for legacy_input in OLD_INPUT_NAMES:
        if module.params.get(legacy_input) is not None:
            module.deprecate(msg='{0} parameter has been deprecated, please use inputs instead'.format(legacy_input), version="ansible.tower:4.0.0")
    if kind:
        module.deprecate(msg='The kind parameter has been deprecated, please use credential_type instead', version="ansible.tower:4.0.0")

    cred_type_id = module.resolve_name_to_id('credential_types', credential_type if credential_type else KIND_CHOICES[kind])
    if organization:
        org_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up the object based on the provided name, credential type and optional organization
    lookup_data = {
        'credential_type': cred_type_id,
    }
    if organization:
        lookup_data['organization'] = org_id

    credential = module.get_one('credentials', name_or_id=name, **{'data': lookup_data})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(credential)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if user:
        user_id = module.resolve_name_to_id('users', user)
    if team:
        team_id = module.resolve_name_to_id('teams', team)

    # Create credential input from legacy inputs
    has_inputs = False
    credential_inputs = {}
    for legacy_input in OLD_INPUT_NAMES:
        if module.params.get(legacy_input) is not None:
            has_inputs = True
            credential_inputs[legacy_input] = module.params.get(legacy_input)

    if inputs:
        has_inputs = True
        credential_inputs.update(inputs)

    # Create the data that gets sent for create and update
    credential_fields = {
        'name': new_name if new_name else (module.get_item_name(credential) if credential else name),
        'credential_type': cred_type_id,
    }
    if has_inputs:
        credential_fields['inputs'] = credential_inputs

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
    module.create_or_update_if_needed(
        credential, credential_fields, endpoint='credentials', item_type='credential'
    )


if __name__ == '__main__':
    main()
