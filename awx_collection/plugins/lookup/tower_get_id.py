# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: tower_get_id
author: John Westcott IV (@john-westcott-iv)
short_description: Search for a specific ID of an option
requirements:
    - None
description:
  - Returns an ID of an object found in tower by the fiter criteria. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/index.html) for API usage.
    Raises an exception if not exactly one object is found.
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
"""

EXAMPLES = """
- name: Lookup a users ID
  debug:
    msg: "{{ query('awx.awx.tower_api', 'users', query_params={ 'username': 'admin' }) }}"
"""

RETURN = """
_raw:
  description:
    - The ID found for the filter criteria
  type: str
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

        found_object = module.get_one(terms[0], data=self.get_option('query_params'))
        if found_object is None:
            self.handle_error(msg='No objects matched that criteria')
        else:
            return found_object['id']
