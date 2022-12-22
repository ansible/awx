# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
name: controller_api
author: John Westcott IV (@john-westcott-iv)
short_description: Search the API for objects
requirements:
  - None
description:
  - Returns GET requests from the Automation Platform Controller API. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/index.html) for API usage.
  - For use that is cross-compatible between the awx.awx and ansible.controller collection
    see the controller_meta module
options:
  _terms:
    description:
      - The endpoint to query, i.e. teams, users, tokens, job_templates, etc.
    required: True
  query_params:
    description:
      - The query parameters to search for in the form of key/value pairs.
    type: dict
    required: False
    aliases: [query, data, filter, params]
  expect_objects:
    description:
      - Error if the response does not contain either a detail view or a list view.
    type: boolean
    default: False
    aliases: [expect_object]
  expect_one:
    description:
      - Error if the response contains more than one object.
    type: boolean
    default: False
  return_objects:
    description:
      - If a list view is returned, promote the list of results to the top-level of list returned.
      - Allows using this lookup plugin to loop over objects without additional work.
    type: boolean
    default: True
  return_all:
    description:
      - If the response is paginated, return all pages.
    type: boolean
    default: False
  return_ids:
    description:
      - If response contains objects, promote the id key to the top-level entries in the list.
      - Allows looking up a related object and passing it as a parameter to another module.
      - This will convert the return to a string or list of strings depending on the number of selected items.
    type: boolean
    aliases: [return_id]
    default: False
  max_objects:
    description:
      - if C(return_all) is true, this is the maximum of number of objects to return from the list.
      - If a list view returns more an max_objects an exception will be raised
    type: integer
    default: 1000
extends_documentation_fragment: awx.awx.auth_plugin
notes:
  - If the query is not filtered properly this can cause a performance impact.
"""

EXAMPLES = """
- name: Load the UI settings
  set_fact:
    controller_settings: "{{ lookup('awx.awx.controller_api', 'settings/ui') }}"

- name: Load the UI settings specifying the connection info
  set_fact:
    controller_settings: "{{ lookup('awx.awx.controller_api', 'settings/ui', host='controller.example.com',
                             username='admin', password=my_pass_var, verify_ssl=False) }}"

- name: Report the usernames of all users with admin privs
  debug:
    msg: "Admin users: {{ query('awx.awx.controller_api', 'users', query_params={ 'is_superuser': true }) | map(attribute='username') | join(', ') }}"

- name: debug all organizations in a loop  # use query to return a list
  debug:
    msg: "Organization description={{ item['description'] }} id={{ item['id'] }}"
  loop: "{{ query('awx.awx.controller_api', 'organizations') }}"
  loop_control:
    label: "{{ item['name'] }}"

- name: Make sure user 'john' is an org admin of the default org if the user exists
  role:
    organization: Default
    role: admin
    user: john
  when: "lookup('awx.awx.controller_api', 'users', query_params={ 'username': 'john' }) | length == 1"

- name: Create an inventory group with all 'foo' hosts
  group:
    name: "Foo Group"
    inventory: "Demo Inventory"
    hosts: >-
      {{ query(
           'awx.awx.controller_api',
            'hosts',
            query_params={ 'name__startswith' : 'foo', },
        ) | map(attribute='name') | list }}
  register: group_creation
"""

RETURN = """
_raw:
  description:
    - Response from the API
  type: dict
  returned: on successful request
"""

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.utils.display import Display
from ..module_utils.controller_api import ControllerAPIModule


class LookupModule(LookupBase):
    display = Display()

    def handle_error(self, **kwargs):
        raise AnsibleError(to_native(kwargs.get('msg')))

    def warn_callback(self, warning):
        self.display.warning(warning)

    def run(self, terms, variables=None, **kwargs):
        if len(terms) != 1:
            raise AnsibleError('You must pass exactly one endpoint to query')

        self.set_options(direct=kwargs)

        # Defer processing of params to logic shared with the modules
        module_params = {}
        for plugin_param, module_param in ControllerAPIModule.short_params.items():
            opt_val = self.get_option(plugin_param)
            if opt_val is not None:
                module_params[module_param] = opt_val

        # Create our module
        module = ControllerAPIModule(argument_spec={}, direct_params=module_params, error_callback=self.handle_error, warn_callback=self.warn_callback)

        response = module.get_endpoint(terms[0], data=self.get_option('query_params', {}))

        if 'status_code' not in response:
            raise AnsibleError("Unclear response from API: {0}".format(response))

        if response['status_code'] != 200:
            raise AnsibleError("Failed to query the API: {0}".format(response['json'].get('detail', response['json'])))

        return_data = response['json']

        if self.get_option('expect_objects') or self.get_option('expect_one'):
            if ('id' not in return_data) and ('results' not in return_data):
                raise AnsibleError('Did not obtain a list or detail view at {0}, and ' 'expect_objects or expect_one is set to True'.format(terms[0]))

        if self.get_option('expect_one'):
            if 'results' in return_data and len(return_data['results']) != 1:
                raise AnsibleError('Expected one object from endpoint {0}, ' 'but obtained {1} from API'.format(terms[0], len(return_data['results'])))

        if self.get_option('return_all') and 'results' in return_data:
            if return_data['count'] > self.get_option('max_objects'):
                raise AnsibleError(
                    'List view at {0} returned {1} objects, which is more than the maximum allowed '
                    'by max_objects, {2}'.format(terms[0], return_data['count'], self.get_option('max_objects'))
                )

            next_page = return_data['next']
            while next_page is not None:
                next_response = module.get_endpoint(next_page)
                return_data['results'] += next_response['json']['results']
                next_page = next_response['json']['next']
            return_data['next'] = None

        if self.get_option('return_ids'):
            if 'results' in return_data:
                return_data['results'] = [str(item['id']) for item in return_data['results']]
            elif 'id' in return_data:
                return_data = str(return_data['id'])

        if self.get_option('return_objects') and 'results' in return_data:
            return return_data['results']
        else:
            return [return_data]
