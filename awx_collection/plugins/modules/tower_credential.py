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
version_added: "2.3"
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
    description:
      description:
        - The description to use for the credential.
      type: str
    user:
      description:
        - User that should own this credential.
      type: str
    team:
      description:
        - Team that should own this credential.
      type: str
    project:
      description:
        - Project that should use this credential.
      type: str
    organization:
      description:
        - Organization that should own the credential.
      required: True
      type: str
    kind:
      description:
        - Type of credential being added.
        - The ssh choice refers to a Tower Machine credential.
      required: False
      type: str
      choices: ["ssh", "vault", "net", "scm", "aws", "vmware", "satellite6", "cloudforms", "gce", "azure_rm", "openstack", "rhv", "insights", "tower"]
    credential_type:
      description:
        - Name of credential type.
      required: False
      version_added: "2.10"
      type: str
    inputs:
      description:
        - >-
          Credential inputs where the keys are var names used in templating.
          Refer to the Ansible Tower documentation for example syntax.
      required: False
      version_added: "2.9"
      type: dict
    host:
      description:
        - Host for this credential.
      type: str
    username:
      description:
        - Username for this credential. ``access_key`` for AWS.
      type: str
    password:
      description:
        - Password for this credential. ``secret_key`` for AWS. ``api_key`` for RAX.
        - Use "ASK" and launch in Tower to be prompted.
      type: str
    ssh_key_data:
      description:
        - SSH private key content. To extract the content from a file path, use the lookup function (see examples).
      required: False
      type: str
    ssh_key_unlock:
      description:
        - Unlock password for ssh_key.
        - Use "ASK" and launch in Tower to be prompted.
      type: str
    authorize:
      description:
        - Should use authorize for net type.
      type: bool
      default: 'no'
    authorize_password:
      description:
        - Password for net credentials that require authorize.
      type: str
    client:
      description:
        - Client or application ID for azure_rm type.
      type: str
    security_token:
      description:
        - STS token for aws type.
      version_added: "2.6"
      type: str
    secret:
      description:
        - Secret token for azure_rm type.
      type: str
    subscription:
      description:
        - Subscription ID for azure_rm type.
      type: str
    tenant:
      description:
        - Tenant ID for azure_rm type.
      type: str
    domain:
      description:
        - Domain for openstack type.
      type: str
    become_method:
      description:
        - Become method to use for privilege escalation.
        - Some examples are "None", "sudo", "su", "pbrun"
        - Due to become plugins, these can be arbitrary
      type: str
    become_username:
      description:
        - Become username.
        - Use "ASK" and launch in Tower to be prompted.
      type: str
    become_password:
      description:
        - Become password.
        - Use "ASK" and launch in Tower to be prompted.
      type: str
    vault_password:
      description:
        - Vault password.
        - Use "ASK" and launch in Tower to be prompted.
      type: str
    vault_id:
      description:
        - Vault identifier.
        - This parameter is only valid if C(kind) is specified as C(vault).
      type: str
      version_added: "2.8"
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add tower credential
  tower_credential:
    name: Team Name
    description: Team Description
    organization: test-org
    kind: ssh
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Create a valid SCM credential from a private_key file
  tower_credential:
    name: SCM Credential
    organization: Default
    state: present
    kind: scm
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
    ssh_key_data: "{{ aws_ssh_key['content'] | b64decode }}"
    kind: ssh
    organization: Default
    tower_username: admin
    tower_password: ansible
    tower_host: https://localhost
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
'''

import os

from ansible.module_utils._text import to_text
from ..module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


KIND_CHOICES = {
    'ssh': 'Machine',
    'vault': 'Ansible Vault',
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


def credential_type_for_kind(params):
    credential_type_res = tower_cli.get_resource('credential_type')
    kind = params.get('kind')
    arguments = {'managed_by_tower': True}
    if kind == 'ssh':
        if params.get('vault_password'):
            arguments['kind'] = 'vault'
        else:
            arguments['kind'] = 'ssh'
    elif kind in ('net', 'scm', 'insights', 'vault'):
        arguments['kind'] = kind
    elif kind in KIND_CHOICES:
        arguments.update(dict(
            kind='cloud',
            name=KIND_CHOICES[kind]
        ))
    return credential_type_res.get(**arguments)


def main():

    argument_spec = dict(
        name=dict(required=True),
        user=dict(),
        team=dict(),
        kind=dict(choices=KIND_CHOICES.keys()),
        credential_type=dict(),
        inputs=dict(type='dict'),
        host=dict(),
        username=dict(),
        password=dict(no_log=True),
        ssh_key_data=dict(no_log=True, type='str'),
        ssh_key_unlock=dict(no_log=True),
        authorize=dict(type='bool', default=False),
        authorize_password=dict(no_log=True),
        client=dict(),
        security_token=dict(),
        secret=dict(),
        tenant=dict(),
        subscription=dict(),
        domain=dict(),
        become_method=dict(),
        become_username=dict(),
        become_password=dict(no_log=True),
        vault_password=dict(no_log=True),
        description=dict(),
        organization=dict(required=True),
        project=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        vault_id=dict(),
    )

    mutually_exclusive = [
        ('kind', 'credential_type')
    ]
    for input_name in OLD_INPUT_NAMES:
        mutually_exclusive.append(('inputs', input_name))

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True,
                         mutually_exclusive=mutually_exclusive)

    name = module.params.get('name')
    organization = module.params.get('organization')
    state = module.params.get('state')

    json_output = {'credential': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        credential = tower_cli.get_resource('credential')
        try:
            params = {}
            params['create_on_missing'] = True
            params['name'] = name

            if organization:
                org_res = tower_cli.get_resource('organization')
                org = org_res.get(name=organization)
                params['organization'] = org['id']

            try:
                tower_cli.get_resource('credential_type')
            except (ImportError, AttributeError):
                # /api/v1/ backwards compat
                # older versions of tower-cli don't *have* a credential_type
                # resource
                params['kind'] = module.params.get('kind')
            else:
                if module.params.get('credential_type'):
                    credential_type_res = tower_cli.get_resource('credential_type')
                    try:
                        credential_type = credential_type_res.get(name=module.params['credential_type'])
                    except (exc.NotFound) as excinfo:
                        module.fail_json(msg=(
                            'Failed to update credential, credential_type not found: {0}'
                        ).format(excinfo), changed=False)
                    params['credential_type'] = credential_type['id']

                    if module.params.get('inputs'):
                        params['inputs'] = module.params.get('inputs')

                elif module.params.get('kind'):
                    credential_type = credential_type_for_kind(module.params)
                    params['credential_type'] = credential_type['id']
                else:
                    module.fail_json(msg='must either specify credential_type or kind', changed=False)

            if module.params.get('description'):
                params['description'] = module.params.get('description')

            if module.params.get('user'):
                user_res = tower_cli.get_resource('user')
                user = user_res.get(username=module.params.get('user'))
                params['user'] = user['id']

            if module.params.get('team'):
                team_res = tower_cli.get_resource('team')
                team = team_res.get(name=module.params.get('team'))
                params['team'] = team['id']

            if module.params.get('ssh_key_data'):
                data = module.params.get('ssh_key_data')
                if os.path.exists(data):
                    module.deprecate(
                        msg='ssh_key_data should be a string, not a path to a file.',
                        version="2.12"
                    )
                    if os.path.isdir(data):
                        module.fail_json(msg='attempted to read contents of directory: %s' % data)
                    with open(data, 'rb') as f:
                        module.params['ssh_key_data'] = to_text(f.read())
                else:
                    module.params['ssh_key_data'] = data

            if module.params.get('vault_id', None) and module.params.get('kind') != 'vault':
                module.fail_json(msg="Parameter 'vault_id' is only valid if parameter 'kind' is specified as 'vault'")

            for key in OLD_INPUT_NAMES:
                if 'kind' in params:
                    params[key] = module.params.get(key)
                elif module.params.get(key):
                    params.setdefault('inputs', {})[key] = module.params.get(key)

            if state == 'present':
                result = credential.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = credential.delete(**params)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update credential, organization not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update credential: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
