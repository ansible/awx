from __future__ import absolute_import, division, print_function

__metaclass__ = type

from awx.main.tests.functional.conftest import _request
from ansible.module_utils.six import string_types
import yaml
import os
import re
import glob

# Analysis variables
# -----------------------------------------------------------------------------------------------------------

# Read-only endpoints are dynamically created by an options page with no POST section.
# Normally a read-only endpoint should not have a module (i.e. /api/v2/me) but sometimes we reuse a name
# For example, we have a role module but /api/v2/roles is a read only endpoint.
# This list indicates which read-only endpoints have associated modules with them.
read_only_endpoints_with_modules = ['settings', 'role', 'project_update', 'workflow_approval']

# If a module should not be created for an endpoint and the endpoint is not read-only add it here
# THINK HARD ABOUT DOING THIS
no_module_for_endpoint = [
    'constructed_inventory',  # This is a view for inventory with kind=constructed
]

# Some modules work on the related fields of an endpoint. These modules will not have an auto-associated endpoint
no_endpoint_for_module = [
    'import',
    'controller_meta',
    'export',
    'inventory_source_update',
    'job_launch',
    'job_wait',
    'job_list',
    'license',
    'ping',
    'receive',
    'send',
    'workflow_launch',
    'workflow_node_wait',
    'job_cancel',
    'workflow_template',
    'ad_hoc_command_wait',
    'ad_hoc_command_cancel',
    'subscriptions',  # Subscription deals with config/subscriptions
]

# Add modules with endpoints that are not at /api/v2
extra_endpoints = {
    'bulk_job_launch': '/api/v2/bulk/job_launch/',
    'bulk_host_create': '/api/v2/bulk/host_create/',
}

# Global module parameters we can ignore
ignore_parameters = ['state', 'new_name', 'update_secrets', 'copy_from']

# Some modules take additional parameters that do not appear in the API
# Add the module name as the key with the value being the list of params to ignore
no_api_parameter_ok = {
    # The wait is for whether or not to wait for a project update on change
    'project': ['wait', 'interval', 'update_project'],
    # Existing_token and id are for working with an existing tokens
    'token': ['existing_token', 'existing_token_id'],
    # /survey spec is now how we handle associations
    # We take an organization here to help with the lookups only
    'job_template': ['survey_spec', 'organization'],
    'inventory_source': ['organization'],
    # Organization is how we are looking up job templates, Approval node is for workflow_approval_templates,
    # lookup_organization is for specifiying the organization for the unified job template lookup
    'workflow_job_template_node': ['organization', 'approval_node', 'lookup_organization'],
    # Survey is how we handle associations
    'workflow_job_template': ['survey_spec', 'destroy_current_nodes'],
    # organization is how we lookup unified job templates
    'schedule': ['organization'],
    # ad hoc commands support interval and timeout since its more like job_launch
    'ad_hoc_command': ['interval', 'timeout', 'wait'],
    # group parameters to perserve hosts and children.
    'group': ['preserve_existing_children', 'preserve_existing_hosts'],
    # new_username parameter to rename a user and organization allows for org admin user creation
    'user': ['new_username', 'organization'],
    # workflow_approval parameters that do not apply when approving an approval node.
    'workflow_approval': ['action', 'interval', 'timeout', 'workflow_job_id'],
    # bulk
    'bulk_job_launch': ['interval', 'wait'],
}

# When this tool was created we were not feature complete. Adding something in here indicates a module
# that needs to be developed. If the module is found on the file system it will auto-detect that the
# work is being done and will bypass this check. At some point this module should be removed from this list.
needs_development = ['inventory_script', 'instance']
needs_param_development = {
    'host': ['instance_id'],
    'workflow_approval': ['description', 'execution_environment'],
}
# -----------------------------------------------------------------------------------------------------------

return_value = 0
read_only_endpoint = []


def cause_error(msg):
    global return_value
    return_value = 255
    return msg


def test_meta_runtime():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    meta_filename = 'meta/runtime.yml'
    module_dir = 'plugins/modules'

    print("\nMeta check:")

    with open('{0}/{1}'.format(base_dir, meta_filename), 'r') as f:
        meta_data_string = f.read()

    meta_data = yaml.load(meta_data_string, Loader=yaml.Loader)

    needs_grouping = []
    for file_name in glob.glob('{0}/{1}/*'.format(base_dir, module_dir)):
        if not os.path.isfile(file_name) or os.path.islink(file_name):
            continue
        with open(file_name, 'r') as f:
            if 'extends_documentation_fragment: awx.awx.auth' in f.read():
                needs_grouping.append(os.path.splitext(os.path.basename(file_name))[0])

    needs_to_be_removed = list(set(meta_data['action_groups']['controller']) - set(needs_grouping))
    needs_to_be_added = list(set(needs_grouping) - set(meta_data['action_groups']['controller']))

    needs_to_be_removed.sort()
    needs_to_be_added.sort()

    group = 'action-groups.controller'
    if needs_to_be_removed:
        print(cause_error("The following items should be removed from the {0} {1}:\n    {2}".format(meta_filename, group, '\n    '.join(needs_to_be_removed))))

    if needs_to_be_added:
        print(cause_error("The following items should be added to the {0} {1}:\n    {2}".format(meta_filename, group, '\n    '.join(needs_to_be_added))))


def determine_state(module_id, endpoint, module, parameter, api_option, module_option):
    # This is a hierarchical list of things that are ok/failures based on conditions

    # If we know this module needs development this is a non-blocking failure
    if module_id in needs_development and module == 'N/A':
        return "Failed (non-blocking), module needs development"

    # If the module is a read only endpoint:
    #    If it has no module on disk that is ok.
    #    If it has a module on disk but its listed in read_only_endpoints_with_modules that is ok
    #    Else we have a module for a read only endpoint that should not exit
    if module_id in read_only_endpoint:
        if module == 'N/A':
            # There may be some cases where a read only endpoint has a module
            return "OK, this endpoint is read-only and should not have a module"
        elif module_id in read_only_endpoints_with_modules:
            return "OK, module params can not be checked to read-only"
        else:
            return cause_error("Failed, read-only endpoint should not have an associated module")

    # If the endpoint is listed as not needing a module and we don't have one we are ok
    if module_id in no_module_for_endpoint and module == 'N/A':
        return "OK, this endpoint should not have a module"

    # If module is listed as not needing an endpoint and we don't have one we are ok
    if module_id in no_endpoint_for_module and endpoint == 'N/A':
        return "OK, this module does not require an endpoint"

    # All of the end/point module conditionals are done so if we don't have a module or endpoint we have a problem
    if module == 'N/A':
        return cause_error('Failed, missing module')
    if endpoint == 'N/A':
        return cause_error('Failed, why does this module have no endpoint')

    # Now perform parameter checks

    # First, if the parameter is in the ignore_parameters list we are ok
    if parameter in ignore_parameters:
        return "OK, globally ignored parameter"

    # If both the api option and the module option are both either objects or none
    if (api_option is None) ^ (module_option is None):
        # If the API option is node and the parameter is in the no_api_parameter list we are ok
        if api_option is None and parameter in no_api_parameter_ok.get(module, {}):
            return 'OK, no api parameter is ok'
        # If we know this parameter needs development and we don't have a module option we are non-blocking
        if module_option is None and parameter in needs_param_development.get(module_id, {}):
            return "Failed (non-blocking), parameter needs development"
        # Check for deprecated in the node, if its deprecated and has no api option we are ok, otherwise we have a problem
        if module_option and module_option.get('description'):
            description = ''
            if isinstance(module_option.get('description'), string_types):
                description = module_option.get('description')
            else:
                description = " ".join(module_option.get('description'))

            if 'deprecated' in description.lower():
                if api_option is None:
                    return 'OK, deprecated module option'
                else:
                    return cause_error('Failed, module marks option as deprecated but option still exists in API')
        # If we don't have a corresponding API option but we are a list then we are likely a relation
        if not api_option and module_option and module_option.get('type', 'str') == 'list':
            return "OK, Field appears to be relation"
            # TODO, at some point try and check the object model to confirm its actually a relation

        return cause_error('Failed, option mismatch')

    # We made it through all of the checks so we are ok
    return 'OK'


def test_completeness(collection_import, request, admin_user, job_template, execution_environment):
    option_comparison = {}
    # Load a list of existing module files from disk
    base_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    module_directory = os.path.join(base_folder, 'plugins', 'modules')
    for root, dirs, files in os.walk(module_directory):
        if root == module_directory:
            for filename in files:
                if os.path.islink(os.path.join(root, filename)):
                    continue
                # must begin with a letter a-z, and end in .py
                if re.match(r'^[a-z].*.py$', filename):
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

    for key, val in extra_endpoints.items():
        endpoint_response.data[key] = val

    for endpoint in endpoint_response.data.keys():
        # Module names are singular and endpoints are plural so we need to convert to singular
        singular_endpoint = '{0}'.format(endpoint)
        if singular_endpoint.endswith('ies'):
            singular_endpoint = singular_endpoint[:-3]
        if singular_endpoint != 'settings' and singular_endpoint.endswith('s'):
            singular_endpoint = singular_endpoint[:-1]
        module_name = '{0}'.format(singular_endpoint)

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
    for module, module_value in option_comparison.items():
        if len(module_value['module_name']) > longest_module_name:
            longest_module_name = len(module_value['module_name'])
        if len(module_value['endpoint']) > longest_endpoint:
            longest_endpoint = len(module_value['endpoint'])
        for option in module_value['api_options'], module_value['module_options']:
            if len(option) > longest_option_name:
                longest_option_name = len(option)

    # Print out some headers
    print(
        "".join(
            [
                "End Point",
                " " * (longest_endpoint - len("End Point")),
                " | Module Name",
                " " * (longest_module_name - len("Module Name")),
                " | Option",
                " " * (longest_option_name - len("Option")),
                " | API | Module | State",
            ]
        )
    )
    print(
        "-|-".join(
            [
                "-" * longest_endpoint,
                "-" * longest_module_name,
                "-" * longest_option_name,
                "---",
                "------",
                "---------------------------------------------",
            ]
        )
    )

    # Print out all of our data
    for module in sorted(option_comparison):
        module_data = option_comparison[module]
        all_param_names = list(set(module_data['api_options']) | set(module_data['module_options']))
        for parameter in sorted(all_param_names):
            print(
                "".join(
                    [
                        module_data['endpoint'],
                        " " * (longest_endpoint - len(module_data['endpoint'])),
                        " | ",
                        module_data['module_name'],
                        " " * (longest_module_name - len(module_data['module_name'])),
                        " | ",
                        parameter,
                        " " * (longest_option_name - len(parameter)),
                        " | ",
                        " X " if (parameter in module_data['api_options']) else '   ',
                        " | ",
                        '  X   ' if (parameter in module_data['module_options']) else '      ',
                        " | ",
                        determine_state(
                            module,
                            module_data['endpoint'],
                            module_data['module_name'],
                            parameter,
                            module_data['api_options'][parameter] if (parameter in module_data['api_options']) else None,
                            module_data['module_options'][parameter] if (parameter in module_data['module_options']) else None,
                        ),
                    ]
                )
            )
        # This handles cases were we got no params from the options page nor from the modules
        if len(all_param_names) == 0:
            print(
                "".join(
                    [
                        module_data['endpoint'],
                        " " * (longest_endpoint - len(module_data['endpoint'])),
                        " | ",
                        module_data['module_name'],
                        " " * (longest_module_name - len(module_data['module_name'])),
                        " | ",
                        "N/A",
                        " " * (longest_option_name - len("N/A")),
                        " | ",
                        '   ',
                        " | ",
                        '      ',
                        " | ",
                        determine_state(module, module_data['endpoint'], module_data['module_name'], 'N/A', None, None),
                    ]
                )
            )

    test_meta_runtime()

    if return_value != 0:
        raise Exception("One or more failures caused issues")
