#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: export_resources_by_organization
short_description: This module is intended for exporting awx resources within the scope of an organization
version_added: "3.7.0"
description
    - Export assets from Automation Platform Controller within the scope of an organization facilitating for huge enterprise with manny organizations.
options:
    organization:
        description:
            - organization name to export
        required: true
    controller_host:
        description:
            - The host of Automation Platform Controller
        required: false
    controller_username:
        description:
            - The username of Automation Platform Controller
        required: false
    controller_password:
        description:
            - The password of Automation Platform Controller
        required: false
    verify_ssl:
        description:
            - Boolean for validating ssl certs
        required: false
        default: True
    controller_config_file:
        description:
            - Controller configuration file for connection
        required: false 
    controller_secret_key:
        description:
            - Automation Platform Controller secret key required for decrypting credential inputs
        required: true
    controller_database:
        description:
            - Automation Platform Controller database name required for decrypting credential inputs
        required: true 
    controller_database_user:
        description:
            - Automation Platform Controller database username required for decrypting credential inputs
        required: true 
    controller_database_password:
        description:
            - Automation Platform Controller database password required for decrypting credential inputs
        required: true 
    controller_database_port:
        description:
            - Automation Platform Controller database port required for decrypting credential inputs
        required: false 
        default: 5432
'''

EXAMPLES = '''
- name: Export my organization resources
  export_resources_by_organization:
    organization: AWX-ORG-1
    controller_host: "https://www.automation-platform.com"
    controller_username: awx_user
    controller_password: "{{ awx_password }}"
    controller_secret_key: "{{ awx_secret_key }}"
    controller_database: "{{ awx_database_name }}"
    controller_database_user: "{{ awx_database_user }}"
    controller_database_password: "{{ awx_database_password }}"
'''
import os
from ansible.module_utils.basic import AnsibleModule

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from tower_cli.utils import parser

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def export_resources_by_organization(awx_auth, awx_platform_inputs, awx_decryption_inputs, module):
    has_changed = False
    result = dict(
        projects=[],
        job_templates=[],
        workflow_job_templates=[],
        notification_templates = dict(),
        inventories=[],
        credentials=[],
        users=[],
        teams=[],
        roles=[],
        credential_input_source=[],
        lookup_credentials=[]
    )


    return has_changed, result

def awx_auth_config(module):
    config_file = module.params.get('controller_config_file')
    if config_file:
        config_file = os.path.expanduser(config_file)
        if not os.path.exists(config_file):
            module.fail_json(msg='file not found: %s' % config_file)
        if os.path.isdir(config_file):
            module.fail_json(msg='directory can not be used as config file: %s' % config_file)

        with open(config_file, 'rb') as f:
            return parser.string_to_dict(f.read())
    else:
        auth_config = {}
        host = module.params.get('controller_host')
        if host:
            auth_config['host'] = host
        username = module.params.get('controller_username')
        if username:
            auth_config['username'] = username
        password = module.params.get('controller_password')
        if password:
            auth_config['password'] = password
        verify_ssl = module.params.get('verify_ssl')
        if verify_ssl:
            auth_config['verify_ssl'] = verify_ssl
        return auth_config

def main():
    argument_spec = dict(
        organization=dict(type='str', required=True),
        controller_host=dict(type='str', no_log=True),
        controller_username=dict(type='str'),
        controller_password=dict(type='str'),
        verify_ssl=dict(type='bool', required=False, default=True),
        controller_secret_key=dict(type='str', required=True, no_log=True),
        controller_database=dict(type='str', required=True),
        controller_database_user=dict(type='str', required=True, no_log=True),
        controller_database_password=dict(type='str', required=True, no_log=True),
        controller_database_port=dict(type='str', required=False, default="5432")
    )

    result = dict(
        changed=False,
        message='Module requirements are met and syntax ok'
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    awx_platform_inputs = dict(
        organization = module.params['organization'],
        controller_host = module.params['controller_host'],
        controller_username = module.params['controller_username'],
        controller_password = module.params['controller_password'],
        verify_ssl = module.params['verify_ssl']
    )

    awx_decryption_inputs = dict(
        controller_secret_key = module.params['controller_secret_key'],
        controller_database = module.params['controller_database'],
        controller_database_user = module.params['controller_database_user'],
        controller_database_password = module.params['controller_database_password'],
        controller_database_port = module.params['controller_database_port']
    )

    awx_auth = awx_auth_config(module)

    has_changed, result = export_resources_by_organization(awx_auth, awx_platform_inputs, awx_decryption_inputs, module)

    module.exit_json(changed=has_changed, **result)

if __name__ == '__main__':
    main()

