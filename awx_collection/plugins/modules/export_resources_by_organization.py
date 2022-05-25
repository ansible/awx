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
    validate_certs:
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
import json

from ..module_utils.awx_credential import get_project_credential
from ..module_utils.export_tools import transform_users_set_to_objects
from ..module_utils.awx_workflow import get_workflow_job_templates
from ..module_utils.awx_request import get_awx_resource_by_name, get_awx_resource_by_id, get_awx_resources
from ..module_utils.awx_organization import get_organization_teams, get_organization_roles
from ..module_utils.awxkit import ControllerAWXKitModule

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
        lookup_credentials=[],
        labels = []
    )
    organization = get_awx_resource_by_name(resource='organization', name=awx_platform_inputs['organization'])
    result['teams'], members_info_set = get_organization_teams(organization, awx_auth)
    result['roles'], users_info_set = get_organization_roles(organization, awx_auth)
    users_info_set.update(members_info_set)

    result['users'] = transform_users_set_to_objects(users_info_set)
    
    result['projects'] = get_awx_resources(uri='/api/v2/projects/?organization='+organization['id'], previousPageResults=[], awx_auth=awx_auth)
    result['labels'] = get_awx_resources(uri='/api/v2/labels/?organization='+organization['id'], previousPageResults=[], awx_auth=awx_auth)
    result['workflow_job_templates'], result['notification_templates'], result['inventories'] = get_workflow_job_templates(organization=organization, notification_templates=[], awx_auth=awx_auth)

    credential_ids = set()

    for project_index, project in enumerate(result['projects']):
        scm_credential_id_set, project = get_project_credential(project, awx_auth)
        result['projects'][project_index] = project
        credential_ids.add(scm_credential_id_set)
    return has_changed, result

def awx_auth_config(module):
    config_file = module.params.get('controller_config_file')
    if config_file:
        config_file = os.path.expanduser(config_file)
        if not os.path.exists(config_file):
            module.fail_json(msg='file not found: %s' % config_file)
        if os.path.isdir(config_file):
            module.fail_json(msg='directory can not be used as config file: %s' % config_file)

        with open(config_file, 'r') as f:
            return json.load(f.read().rstrip())
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
        validate_certs = module.params.get('validate_certs')
        if validate_certs:
            auth_config['validate_certs'] = validate_certs
        return auth_config

def main():
    argument_spec = dict(
        organization=dict(type='str', required=True),
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

    module = ControllerAWXKitModule(
        argument_spec=argument_spec
    )

    if module.check_mode:
        return result

    awx_platform_inputs = dict(
        organization = module.params.get('organization'),
        controller_host = module.params.get('controller_host'),
        controller_username = module.params.get('controller_username'),
        controller_password = module.params.get('controller_password'),
        validate_certs = module.params.get('validate_certs')
    )

    awx_decryption_inputs = dict(
        controller_secret_key = module.params.get('controller_secret_key'),
        controller_database = module.params.get('controller_database'),
        controller_database_user = module.params.get('controller_database_user'),
        controller_database_password = module.params.get('controller_database_password'),
        controller_database_port = module.params.get('controller_database_port')
    )

    awx_auth = awx_auth_config(module)

    has_changed, result = export_resources_by_organization(awx_auth, awx_platform_inputs, awx_decryption_inputs, module)

    module.exit_json(changed=has_changed, **result)

if __name__ == '__main__':
    main()

