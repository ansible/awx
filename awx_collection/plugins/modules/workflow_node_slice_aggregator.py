#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2021, Sean Sullivan
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
---
module: workflow_node_slice_aggregator
author: "Sean Sullivan (@sean-m-sullivan)"
short_description: Aggregate variables from a sliced job template.
description:
    - Aggregate artifacts from a sliced job template.
    - This will combine dicts, subdicts, lists, and bools from a workflow of slices.
    - This is not a perfect merge, and is done at best effort.
    - This was designed so under each top level var, the inventory hostname is referenced as a subkey. 
    - This design was to prevent sub keys overwritting each other.
    - Extra Vars are also collected from the slices for reference.
    - This was meant to be used in the next node of a workflow after a sliced job template to replicate set_stats in a workflow.
    - Examples of vars in the examples. 
options:
    workflow_job_id:
      description:
        - ID of the workflow job to monitor for node.
      required: True
      type: int
    name:
      description:
        - Name of the workflow node that has sliced jobs to wait on.
      required: True
      type: str
    interval:
      description:
        - The interval in sections, to request an update from the controller.
      required: False
      default: 1
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a workflow job to to finish the nodes jobs.
      default: 10
      type: int
extends_documentation_fragment: awx.awx.auth
"""


EXAMPLES = """
- name: Launch a workflow with a timeout of 10 seconds
  workflow_launch:
    workflow_template: "Test Workflow"
    wait: False
  register: workflow

- name: Wait for a workflow node with slices to finish and get aggregate data
  workflow_node_slice_aggregator:
    workflow_job_id: "{{ tower_workflow_job_id }}"
    name: Sliced_Job
    timeout: 120
  register: node_lookup_results

- name: Set Stats
  set_stats:
    data:
      "{{node_lookup_results.artifacts}}"

"""

RETURN = """
aggregate_results:
  artifacts:
    combined_machine_vars:
      machine1:
        some_var: value
      machine2:
        some_var: value
    config_diff_succeeded: true
    host_groups:
      - machine1
      - machine2
  extra_vars: "{}"
  job_data:
    - job_data_from_contoller: data
"""


from ..module_utils.controller_api import ControllerAPIModule
from collections import defaultdict
from ansible.utils.vars import merge_hash
import time


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        workflow_job_id=dict(type="int", required=True),
        name=dict(required=True),
        timeout=dict(type="int", default=10),
        interval=dict(type="float", default=1),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    workflow_job_id = module.params.get("workflow_job_id")
    name = module.params.get("name")
    timeout = module.params.get("timeout")
    interval = module.params.get("interval")

    # Attempt to look up workflow job node based on the provided id
    node_url = "workflow_jobs/{0}/workflow_nodes/?job__name={1}".format(workflow_job_id, name)
    sliced_job_result = module.wait_on_workflow_node_url(
        url="workflow_jobs/{0}/workflow_nodes/".format(workflow_job_id),
        object_name=name,
        object_type="Workflow Node",
        timeout=timeout,
        interval=interval,
        **{
            "data": {
                "job__name": name,
            }
        }
    )
    artifacts = defaultdict(dict)
    job_data = []
    slices = module.get_endpoint(sliced_job_result['json']['related']['workflow_nodes'])['json']['results']
    for slice in slices:
        slice_job = module.get_endpoint(slice['related']['job'])['json']
        # Append job data so that users can sift through it.
        job_data.append(slice_job)
        # Since all slices share the same extra vars on launch, only need to copy them.
        module.json_output['extra_vars'] = slice_job['extra_vars']
        # Use Merge Hash to merge next slice with existing artifacts
        artifacts = merge_hash(artifacts,slice_job['artifacts'])

    module.json_output['artifacts'] = artifacts
    module.json_output['job_data'] = job_data
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
