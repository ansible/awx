# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: tower_api
    author: AWX contributors
    version_added: "3.7"
    short_description: Lookup API data from Ansible Tower or AWX API
    description:
      - Retrieves API data from the Ansible Tower or AWX server about an object.
      - You can use this to lookup items based on non-identity properties.
    options:
      _terms:
        description:
          - The API endpoint to query
        required: True
      data:
        description:
            - The data to be put in the query string for the request
        type: dict
    extends_documentation_fragment: awx.awx.auth
"""

EXAMPLES = """
    - name: Create inventory in organization with certain description
      tower_inventory:
        name: new inventory
        organization: "{{ query('awx.awx.tower_api', 'organizations', data={'description': 'foo'})[0] }}"
"""

RETURN = """
_raw:
  description:
    - return data from the API
  type: list
  elements: integer
"""

from ..module_utils.tower_api import TowerModule
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs_orig):
        kwargs = kwargs_orig.copy()

        obj_ids = []

        for endpoint_raw in terms:
            endpoint = endpoint_raw.lower()
            data = kwargs.pop('data', {})

            module = TowerModule(argument_spec={}, mock_params=kwargs)

            response = module.get_endpoint(endpoint, data=data)

            resp_json = response['json']
            if 'id' in resp_json:
                obj_ids.append(resp_json['id'])
            elif 'results' in resp_json:
                obj_ids.extend([obj['id'] for obj in resp_json['results']])

        return obj_ids
