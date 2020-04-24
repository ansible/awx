#!/usr/bin/python
# coding: utf-8 -*-
#
# (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_credential_type
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: Create, update, or destroy custom Ansible Tower credential type.
description:
    - Create, update, or destroy Ansible Tower credential type. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the credential type.
      required: True
      type: str
    description:
      description:
        - The description of the credential type to give more detail about it.
      type: str
    kind:
      description:
        - >-
          The type of credential type being added. Note that only cloud and
          net can be used for creating credential types. Refer to the Ansible
          for more information.
      choices: [ 'ssh', 'vault', 'net', 'scm', 'cloud', 'insights' ]
      type: str
    inputs:
      description:
        - >-
          Enter inputs using either JSON or YAML syntax. Refer to the Ansible
          Tower documentation for example syntax.
      type: dict
    injectors:
      description:
        - >-
          Enter injectors using either JSON or YAML syntax. Refer to the
          Ansible Tower documentation for example syntax.
      type: dict
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
        - If value not set, will try environment variable C(TOWER_OAUTH_TOKEN) and then config files
      type: str
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- tower_credential_type:
    name: Nexus
    description: Credentials type for Nexus
    kind: cloud
    inputs: "{{ lookup('file', 'tower_credential_inputs_nexus.json') }}"
    injectors: {'extra_vars': {'nexus_credential': 'test' }}
    state: present
    validate_certs: false

- tower_credential_type:
    name: Nexus
    state: absent
'''


RETURN = ''' # '''


from ..module_utils.tower_api import TowerModule

KIND_CHOICES = {
    'ssh': 'Machine',
    'vault': 'Ansible Vault',
    'net': 'Network',
    'scm': 'Source Control',
    'cloud': 'Lots of others',
    'insights': 'Insights'
}


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        kind=dict(choices=list(KIND_CHOICES.keys())),
        inputs=dict(type='dict'),
        injectors=dict(type='dict'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = None
    kind = module.params.get('kind')
    state = module.params.get('state')

    # These will be passed into the create/updates
    credential_type_params = {
        'name': new_name if new_name else name,
        'managed_by_tower': False,
    }
    if kind:
        credential_type_params['kind'] = kind
    if module.params.get('description'):
        credential_type_params['description'] = module.params.get('description')
    if module.params.get('inputs'):
        credential_type_params['inputs'] = module.params.get('inputs')
    if module.params.get('injectors'):
        credential_type_params['injectors'] = module.params.get('injectors')

    # Attempt to look up credential_type based on the provided name
    credential_type = module.get_one('credential_types', **{
        'data': {
            'name': name,
        }
    })

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(credential_type)

    # If the state was present and we can let the module build or update the existing credential type, this will return on its own
    module.create_or_update_if_needed(credential_type, credential_type_params, endpoint='credential_types', item_type='credential type')


if __name__ == '__main__':
    main()
