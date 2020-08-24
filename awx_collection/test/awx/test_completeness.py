#!/usr/bin/env python3

from awx.main.tests.functional.conftest import _request
import yaml
import os
import re

# Analysis variables
# -----------------------------------------------------------------------------------------------------------

# Read-only endpoints are dynamically created by an options page with no POST section.
# Noramlly a read-only endpoint should not have a module (i.e. /api/v2/me) but sometimes we reuse a name
# For example, we have a tower_role module but /api/v2/roles is a read only endpoint.
# Rhis list indicates which read-only endpoints have associated modules with them.
read_only_endpoints_with_modules = ['tower_settings', 'tower_role']

# If a module should not be created for an endpoint and the endpoint is not read-only add it here
# THINK HARD ABOUT DOING THIS
no_module_for_endpoint = []

# Some modules work on the related fields of an endpoint. These modules will not have an auto-associated endpoint
no_endpoint_for_module = [
    'tower_import', 'tower_meta', 'tower_export', 'tower_job_launch', 'tower_job_wait', 'tower_job_list',
    'tower_license', 'tower_ping', 'tower_receive', 'tower_send', 'tower_workflow_launch', 'tower_job_cancel',
    'tower_workflow_template',
]

# Global module parameters we can ignore
ignore_parameters = [
    'state', 'new_name',
    # The way we implemented notifications was to add these fileds to modules which can notify
    'notification_templates_approvals',
    'notification_templates_error',
    'notification_templates_started',
    'notification_templates_success',
]

# Some modules take additional parameters that do not appear in the API
# Add the module name as the key with the value being the list of params to ignore
no_api_parameter_ok = {
    # The credential module used to take a lot of parameters which are now combined into "inputs"
    'tower_credential': [
        'authorize', 'authorize_password', 'become_method', 'become_password', 'become_username', 'client',
        'domain', 'host', 'kind', 'password', 'project', 'secret', 'security_token', 'ssh_key_data',
        'ssh_key_unlock', 'subscription', 'tenant', 'username', 'vault_id', 'vault_password',
    ],
    # The wait is for wheter or not to wait for a projec update on change
    'tower_project': ['wait'],
    # Existing_token and id are for working with an exisitng tokens
    'tower_token': ['existing_token', 'existing_token_id'],
    # Children and hosts are how tower_group deals with associations
    'tower_group': ['children', 'hosts'],
    # Credential and Vault Credential are a legacy fields for old Towers
    # Credentials/labels/survey spec is now how we handle associations
    # We take an organization here to help with the lookups only
    'tower_job_template': ['credential', 'vault_credential', 'credentials', 'labels', 'survey_spec', 'organization'],
    # Always_nodes, failure_nodes, success_nodes, credentials is how we handle associations
    # Organization is how we looking job templates
    'tower_workflow_job_template_node': ['always_nodes', 'failure_nodes', 'success_nodes', 'credentials', 'organization'],
    # Survey is how we handle associations
    'tower_workflow_job_template': ['survey'],
}

# When this tool was created we were not feature complete. Adding something in here indicates a module
# that needs to be developed. If the module is found on the file system it will auto-detect that the
# work is being done and will bypass this check. At some point this module should be removed from this list.
needs_development = [
    'tower_ad_hoc_command', 'tower_application', 'tower_instance_group', 'tower_inventory_script',
    'tower_workflow_approval'
]
needs_param_development = {
    'tower_host': ['instance_id'],
    'tower_inventory': ['insights_credential'],
}
# -----------------------------------------------------------------------------------------------------------

return_value = 0
read_only_endpoint = []


def determine_state(module_id, endpoint, module, parameter, api_option, module_option):
    global return_value
    # This is a hierarchical list of things that are ok/failures based on conditions
    if module_id in needs_development and module == 'N/A':
        return "Failed (non-blocking), module needs development"
    if module_id in read_only_endpoint:
        if module == 'N/A':
            # There may be some cases where a read only endpoint has a module 
            return "OK, this endpoint is read-only and should not have a module"
        elif module_id not in read_only_endpoints_with_modules:
            return_value = 255
            return "Failed, read-only endpoint should not have an associated module"
        else:
            return "OK, module params can not be checked to read-only"
    if module_id in no_module_for_endpoint and module == 'N/A':
        return "OK, this endpoint should not have a module"
    if module_id in no_endpoint_for_module and endpoint == 'N/A':
        return "OK, this module does not require an endpoint"
    if module == 'N/A':
        return_value = 255
        return 'Failed, missing module'
    if endpoint == 'N/A':
        return_value = 255
        return 'Failed, why does this module have no endpoint'
    if parameter in ignore_parameters:
        return "OK, globally ignored parameter"
    if api_option == '' and parameter in no_api_parameter_ok.get(module, {}):
        return 'OK, no api parameter is ok'
    if api_option != module_option:
        if module_id in needs_param_development and parameter in needs_param_development[module_id]:
            return "Failed (non-blocking), parameter needs development"
        return_value = 255
        return 'Failed, option mismatch'
    if api_option == module_option:
        return 'OK'
    return_value = 255
    return "Failed, unknown reason"


def test_completeness(collection_import, request, admin_user, job_template):
    option_comparison = {}
    # Load a list of existing module files from disk
    base_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    module_directory = os.path.join(base_folder, 'plugins', 'modules')
    for root, dirs, files in os.walk(module_directory):
        if root == module_directory:
            for filename in files:
                if re.match('^tower_.*.py$', filename):
                    module_name = filename[:-3]
                    option_comparison[module_name] = {
                        'endpoint': 'N/A',
                        'api_options': {},
                        'module_options': {},
                        'module_name': module_name,
                    }
                    resource_module = collection_import('plugins.modules.{0}'.format(module_name))
                    option_comparison[module_name]['module_options'] = yaml.load(
                        resource_module.DOCUMENTATION,
                        Loader=yaml.SafeLoader
                    )['options']

    endpoint_response = _request('get')(
        url='/api/v2/',
        user=admin_user,
        expect=None,
    )
    for endpoint in endpoint_response.data.keys():
        # Module names are singular and endpoints are plural so we need to convert to singular
        singular_endpoint = '{}'.format(endpoint)
        if singular_endpoint.endswith('ies'):
            singular_endpoint = singular_endpoint[:-3]
        if singular_endpoint != 'settings' and singular_endpoint.endswith('s'):
            singular_endpoint = singular_endpoint[:-1]
        module_name = 'tower_{}'.format(singular_endpoint)

        endpoint_url = endpoint_response.data.get(endpoint)

        # If we don't have a module for this endpoint then we can create an empty one
        if module_name not in option_comparison:
            option_comparison[module_name] = {}
            option_comparison[module_name]['module_name'] = 'N/A'
            option_comparison[module_name]['module_options'] = {}

        # Add in our endpoint and an empty api_options
        option_comparison[module_name]['endpoint'] = endpoint_url
        option_comparison[module_name]['api_options'] = {}

        # Get out the endpoint, load and parse its options page
        options_response = _request('options')(
            url=endpoint_url,
            user=admin_user,
            expect=None,
        )
        if 'POST' in options_response.data.get('actions', {}):
            option_comparison[module_name]['api_options'] = options_response.data.get('actions').get('POST')
        else:
            read_only_endpoint.append(module_name)

    # Parse through our data to get string lengths to make a pretty report
    longest_module_name = 0
    longest_option_name = 0
    longest_endpoint = 0
    for module in option_comparison:
        if len(option_comparison[module]['module_name']) > longest_module_name:
            longest_module_name = len(option_comparison[module]['module_name'])
        if len(option_comparison[module]['endpoint']) > longest_endpoint:
            longest_endpoint = len(option_comparison[module]['endpoint'])
        for option in option_comparison[module]['api_options'], option_comparison[module]['module_options']:
            if len(option) > longest_option_name:
                longest_option_name = len(option)

    # Print out some headers
    print(
        "End Point", " " * (longest_endpoint - len("End Point")),
        " | Module Name", " " * (longest_module_name - len("Module Name")),
        " | Option", " " * (longest_option_name - len("Option")),
        " | API | Module | State",
        sep=""
    )
    print(
        "-" * longest_endpoint,
        "-" * longest_module_name,
        "-" * longest_option_name,
        "---",
        "------",
        "---------------------------------------------",
        sep="-|-"
    )

    # Print out all of our data
    for module in sorted(option_comparison):
        module_data = option_comparison[module]
        all_param_names = list(set(module_data['api_options']) | set(module_data['module_options']))
        for parameter in sorted(all_param_names):
            print(
                module_data['endpoint'], " " * (longest_endpoint - len(module_data['endpoint'])), " | ",
                module_data['module_name'], " " * (longest_module_name - len(module_data['module_name'])), " | ",
                parameter, " " * (longest_option_name - len(parameter)), " | ",
                " X " if (parameter in module_data['api_options']) else '   ', " | ",
                '  X   ' if (parameter in module_data['module_options']) else '      ', " | ",
                determine_state(
                    module,
                    module_data['endpoint'],
                    module_data['module_name'],
                    parameter,
                    'X' if (parameter in module_data['api_options']) else '',
                    'X' if (parameter in module_data['module_options']) else '',
                ),
                sep=""
            )
        # This handles cases were we got no params from the options page nor from the modules
        if len(all_param_names) == 0:
            print(
                module_data['endpoint'], " " * (longest_endpoint - len(module_data['endpoint'])), " | ",
                module_data['module_name'], " " * (longest_module_name - len(module_data['module_name'])), " | ",
                "N/A", " " * (longest_option_name - len("N/A")), " | ",
                '   ', " | ",
                '      ', " | ",
                determine_state(module, module_data['endpoint'], module_data['module_name'], 'N/A', '', ''),
                sep=""
            )

    if return_value != 0:
        raise Exception("One or more failures caused issues")
