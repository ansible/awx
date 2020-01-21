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
      required: False
      type: str
    kind:
      description:
        - >-
          The type of credential type being added. Note that only cloud and
          net can be used for creating credential types. Refer to the Ansible
          for more information.
      choices: [ 'ssh', 'vault', 'net', 'scm', 'cloud', 'insights' ]
      required: False
      type: str
    inputs:
      description:
        - >-
          Enter inputs using either JSON or YAML syntax. Refer to the Ansible
          Tower documentation for example syntax.
      required: False
      type: dict
    injectors:
      description:
        - >-
          Enter injectors using either JSON or YAML syntax. Refer to the
          Ansible Tower documentation for example syntax.
      required: False
      type: dict
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
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
        description=dict(required=False),
        kind=dict(required=False, choices=KIND_CHOICES.keys()),
        inputs=dict(type='dict', required=False),
        injectors=dict(type='dict', required=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    new_name = None
    kind = module.params.get('kind')
    state = module.params.get('state')

    json_output = {'credential_type': name, 'state': state}

    # Deal with check mode
    module.default_check_mode()

    # These will be passed into the create/updates
    credental_type_params = {
        'name': new_name if new_name else name,
        'kind': kind,
        'managed_by_tower': False,
    }
    if module.params.get('description'):
        credental_type_params['description'] = module.params.get('description')
    if module.params.get('inputs'):
        credental_type_params['inputs'] = module.params.get('inputs')
    if module.params.get('injectors'):
        credental_type_params['injectors'] = module.params.get('injectors')

    # Attempt to lookup credential_type based on the provided name and org ID
    credential_type = module.get_one('credential_types', **{
        'data': {
            'name': name,
        }
    })

    json_output['existing_credential_type'] = credential_type
    if state == 'absent' and not credential_type:
        # If the state was absent and we had no credential_type, we can just return
        module.exit_json(**module.json_output)
    elif state == 'absent' and credential_type:
        # If the state was absent and we had a team, we can try to delete it, the module will handle exiting from this
        module.delete_endpoint('credential_types/{0}'.format(credential_type['id']), item_type='credential type', item_name=name, **{})
    elif state == 'present' and not credential_type:
        # if the state was present and we couldn't find a credential_type we can build one, the module will handle exiting on its own
        module.post_endpoint('credential_types', item_type='credential type', item_name=name, **{
            'data': credental_type_params
        })
    else:
        # If the state was present and we had a credential_type we can see if we need to update it
        # This will handle existing on its own
        module.update_if_needed(credential_type, credental_type_params)


if __name__ == '__main__':
    main()
