#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_job_list
author: "Wayne Witzel III (@wwitzel3)"
short_description: List Ansible Tower jobs.
description:
    - List Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    status:
      description:
        - Only list jobs with this status.
      choices: ['pending', 'waiting', 'running', 'error', 'failed', 'canceled', 'successful']
      type: str
    page:
      description:
        - Page number of the results to fetch.
      type: int
    all_pages:
      description:
        - Fetch all the pages and return a single result.
      type: bool
      default: 'no'
    query:
      description:
        - Query used to further filter the list of jobs. C({"foo":"bar"}) will be passed at C(?foo=bar)
      type: dict
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: List running jobs for the testing.yml playbook
  tower_job_list:
    status: running
    query: {"playbook": "testing.yml"}
    tower_config_file: "~/tower_cli.cfg"
  register: testing_jobs
'''

RETURN = '''
count:
    description: Total count of objects return
    returned: success
    type: int
    sample: 51
next:
    description: next page available for the listing
    returned: success
    type: int
    sample: 3
previous:
    description: previous page available for the listing
    returned: success
    type: int
    sample: 1
results:
    description: a list of job objects represented as dictionaries
    returned: success
    type: list
    sample: [{"allow_simultaneous": false, "artifacts": {}, "ask_credential_on_launch": false,
              "ask_inventory_on_launch": false, "ask_job_type_on_launch": false, "failed": false,
              "finished": "2017-02-22T15:09:05.633942Z", "force_handlers": false, "forks": 0, "id": 2,
              "inventory": 1, "job_explanation": "", "job_tags": "", "job_template": 5, "job_type": "run"}, ...]
'''


from ..module_utils.tower_api import TowerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        status=dict(choices=['pending', 'waiting', 'running', 'error', 'failed', 'canceled', 'successful']),
        page=dict(type='int'),
        all_pages=dict(type='bool', default=False),
        query=dict(type='dict'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ('page', 'all_pages'),
        ]
    )

    # Extract our parameters
    query = module.params.get('query')
    status = module.params.get('status')
    page = module.params.get('page')
    all_pages = module.params.get('all_pages')

    job_search_data = {}
    if page:
        job_search_data['page'] = page
    if status:
        job_search_data['status'] = status
    if query:
        job_search_data.update(query)
    if all_pages:
        job_list = module.get_all_endpoint('jobs', **{'data': job_search_data})
    else:
        job_list = module.get_endpoint('jobs', **{'data': job_search_data})

    # Attempt to look up jobs based on the status
    module.exit_json(**job_list['json'])


if __name__ == '__main__':
    main()
