#!/usr/bin/env python3

from awx.main.tests.functional.conftest import _request
import yaml
import os
import re

# Analysis variables
# -----------------------------------------------------------------------------------------------------------

# Read-only endpoints are dynamically created by an options page with no POST section
read_only_endpoint = []

# If a module should not be created for an endpoint and the endpoint is not read-only add it here
# THINK HARD ABOUT DOING THIS
no_module_for_endpoint = []

# Some modules work on the related fields of an endpoint. These modules will not have an auto-associated endpoint
no_endpoint_for_module = [
    'tower_import', 'tower_meta', 'tower_export', 'tower_job_launch', 'tower_job_wait', 'tower_job_list',
    'tower_license', 'tower_ping', 'tower_receive', 'tower_send', 'tower_workflow_launch', 'tower_job_cancel',
]

# Global module parameters we can ignore
ignore_parameters = [ 'state', 'new_name' ]

# Some modules take additional parameters that do not appear in the API
# Add the module name as the key with the value being the list of params to ignore
no_api_parameter_ok = {
    'tower_credential': [
        'authorize', 'authorize_password', 'become_method', 'become_password', 'become_username', 'client', 
        'domain', 'host', 'kind', 'password', 'project', 'secret', 'security_token', 'ssh_key_data',
        'ssh_key_unlock', 'subscription', 'tenant', 'username', 'vault_id', 'vault_password',
    ],
    'tower_project': ['wait', 'timeout'],
    'tower_token': ['existing_token', 'existing_token_id'],
    'tower_settings': ['name', 'settings', 'value'],
}

# When this tool was created we were not feature complete. Adding something in here indicates a module
# that needs to be developed. If the module is found on the file system it will auto-detect that the
# work is being done and will bypass this check. At some point this module should be removed from this list.
needs_development = [
    'tower_ad_hoc_command', 'tower_application', 'tower_instance_group', 'tower_inventory_script',
    'tower_workflow_approval'
]
# -----------------------------------------------------------------------------------------------------------

return_value = 0

def determine_state(module_id, endpoint, module, parameter, api_option, module_option):
    global return_value
    # This is a hierarchical list of things that are ok/failures based on conditions
    if module_id in needs_development and module == 'N/A':
        return "Failed (non-blocking), needs development"
    if module_id in read_only_endpoint and module == 'N/A':
        return "OK, this endpoint is read-only and should not have a module"
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
        return_value = 255
        return 'Failed, option mismatch'
    if api_option == module_option:
        return 'OK'
    return_value = 255
    return "Failed, unknown reason"

def test_completeness(collection_import, request, admin_user):
    option_comparison = {}
    # Load a list of existing module files from disk
    base_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    module_directory = os.path.join(base_folder, 'plugins', 'modules')
    for root, dirs, files in os.walk(module_directory):
        if root == module_directory:
            for filename in files:
                if re.match('^tower_.*\.py$', filename):
                    module_name = filename[:-3]
                    option_comparison[module_name] = {
                        'endpoint': 'N/A',
                        'api_options': {},
                        'module_options': {},
                        'module_name': module_name,
                    }
                    resource_module = collection_import('plugins.modules.{0}'.format(module_name))
                    option_comparison[module_name]['module_options'] = yaml.load(resource_module.DOCUMENTATION, Loader=yaml.SafeLoader)['options']

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
        "End Point", " "*(longest_endpoint-len("End Point")),
        " | Module Name", " "*(longest_module_name-len("Module Name")),
        " | Option", " "*(longest_option_name-len("Option")),
        " | API | Module | State",
        sep=""
    )
    print("-"*longest_endpoint, "-"*longest_module_name, "-"*longest_option_name, "---", "------", "---------------------------------------------", sep="-|-")

    # Print out all of our data
    for module in sorted(option_comparison):
        all_param_names = list(set(option_comparison[module]['api_options']) | set(option_comparison[module]['module_options']))
        for parameter in sorted(all_param_names):
    	    print(
                option_comparison[module]['endpoint'], " "*(longest_endpoint - len(option_comparison[module]['endpoint'])), " | ",
                option_comparison[module]['module_name'], " "*(longest_module_name - len(option_comparison[module]['module_name'])), " | ",
                parameter, " "*(longest_option_name - len(parameter)), " | ",
                " X " if (parameter in option_comparison[module]['api_options']) else '   ', " | ",
                '  X   ' if (parameter in option_comparison[module]['module_options']) else '      ', " | ",
                determine_state(
                    module,
                    option_comparison[module]['endpoint'],
                    option_comparison[module]['module_name'],
                    parameter,
                    'X' if (parameter in option_comparison[module]['api_options']) else '',
                    'X' if (parameter in option_comparison[module]['module_options']) else '',
                ),
                sep=""
            )
        # This handles cases were we got no params from the options page nor from the modules
        if len(all_param_names) == 0:
            print(
                option_comparison[module]['endpoint'], " "*(longest_endpoint - len(option_comparison[module]['endpoint'])), " | ",
                option_comparison[module]['module_name'], " "*(longest_module_name - len(option_comparison[module]['module_name'])), " | ",
                "N/A", " "*(longest_option_name - len("N/A")), " | ",
                '   ', " | ",
                '      ', " | ",
                determine_state(
                    module, option_comparison[module]['endpoint'], option_comparison[module]['module_name'], 'N/A', '', ''
                ),
                sep=""
            )

    if return_value != 0:
        raise Exception("One or more failures caused issues")
