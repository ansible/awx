#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2021, Ranmsés <ranmses@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: workflow_job_list
author: "Ranmsés (@ranmses)"
short_description: List Automation Platform Controller workflow jobs.
description:
    - List Automation Platform Controller workflow jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    status:
      description:
        - Only list workflow jobs with this status.
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
        - Query used to further filter the list of workflow jobs. C({"foo":"bar"}) will be passed at C(?foo=bar)
      type: dict
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: List failed workflow jobs created on 2021-07-21 or after
  workflow_job_list:
    status: failed
    query: {"created__gt": "2021-07-21"}
    controller_config_file: "~/tower_cli.cfg"
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
    description: a list of workflow job objects represented as dictionaries
    returned: success
    type: list
    sample: [{"allow_simultaneous": true, "canceled_on": null, "created": "2021-07-21T16:17:02.460654Z",
              "description": "Failed Test Workflow", "elapsed": 482.879, "extra_vars": {}, "failed": true,
              "finished": "2021-07-21T16:25:05.900832Z", "id": 144032, "inventory": 1, "is_sliced_job": false,
              "job_explanation": "No error handling paths found, marking workflow as failed", "job_template": null,
              "launch_type": "relaunch", "limit": null, "modified": "2021-07-21T16:17:03.028857Z", "name": "Test Workflow Template", ...}]
'''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        status=dict(choices=['pending', 'waiting', 'running', 'error', 'failed', 'canceled', 'successful']),
        page=dict(type='int'),
        all_pages=dict(type='bool', default=False),
        query=dict(type='dict'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ('page', 'all_pages'),
        ],
    )

    # Extract our parameters
    query = module.params.get('query')
    status = module.params.get('status')
    page = module.params.get('page')
    all_pages = module.params.get('all_pages')

    workflow_job_search_data = {'type': 'workflow_job'}
    if page:
        workflow_job_search_data['page'] = page
    if status:
        workflow_job_search_data['status'] = status
    if query:
        workflow_job_search_data.update(query)
    if all_pages:
        workflow_job_list = module.get_all_endpoint('workflow_jobs', **{'data': workflow_job_search_data})
    else:
        workflow_job_list = module.get_endpoint('workflow_jobs', **{'data': workflow_job_search_data})

    # Attempt to look up workflow jobs based on the status
    module.exit_json(**workflow_job_list['json'])


if __name__ == '__main__':
    main()
