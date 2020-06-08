# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: tower_api
author: John Westcott IV (@john-westcott-iv)
short_description: Search the API for objects
requirements:
    - None
description:
  - Returns GET requests to the Ansible Tower API. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/index.html) for API usage.
extends_documentation_fragment:
  - awx.awx.auth_plugin
options:
  _terms:
    description:
      - The endpoint to query. i.e. teams, users, tokens, job_templates, etc
    required: True
  query_params:
    description:
      - The query parameters to search for in the form of key/value pairs.
    type: dict
    required: True
  get_all:
    description:
      - If the resulting query is pagenated, retriest all pages
      - note: If the query is not filtered properly this can cause a performance impact
    type: boolean
    default: False
"""

EXAMPLES = """
- name: Lookup any users who are admins
  debug:
    msg: "{{ query('awx.awx.tower_api', 'users', query_params={ 'is_superuser': true }) }}"
"""

RETURN = """
_raw:
  description:
    - Response of objects from API
  type: dict
  contains:
    count:
      description: The number of objects your filter returned in total (not necessarally on this page)
      type: str
    next:
      description: The URL path for the next page
      type: str
    previous:
      description: The URL path for the previous page
      type: str
    results:
      description: An array of results that were returned
      type: list
  returned: on successful create
"""

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.utils.display import Display
from ..module_utils.tower_api import TowerModule

class LookupModule(LookupBase):
    display = Display()

    def handle_error(self, **kwargs):
        raise AnsibleError(to_native(kwargs.get('msg')))

    def warn_callback(self, warning):
        self.display.warning(warning)

    def run(self, terms, variables=None, **kwargs):
        if len(terms) != 1:
            raise AnsibleError('You must pass exactly one endpoint to query')

        # Defer processing of params to logic shared with the modules
        module_params = {}
        for plugin_param, module_param in TowerModule.short_params.items():
            opt_val = self.get_option(plugin_param)
            if opt_val is not None:
                module_params[module_param] = opt_val

        # Create our module
        module = TowerModule(
            argument_spec={}, direct_params=module_params,
            error_callback=self.handle_error, warn_callback=self.warn_callback
        )

        self.set_options(direct=kwargs)

        if self.get_option('get_all'):
            return_data = module.get_all_endpoint(terms[0], data=self.get_option('query_params'))
        else:
            return_data = module.get_endpoint(terms[0], data=self.get_option('query_params'))
        with open('/tmp/john', 'w') as f:
            import json
            f.write(json.dumps(return_data, indent=4))

        if return_data['status_code'] != 200:
            error = return_data
            if return_data.get('json', {}).get('detail', False):
                error = return_data['json']['detail']
            raise AnsibleError("Failed to query the API: {0}".format(error))

        return return_data['json']
