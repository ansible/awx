#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
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
module: tower_workflow_approval
author: "Sean Sullivan (@sean-m-sullivan)"
short_description: Approve an approval node in a workflow job.
description:
    - Approve an approval node in a workflow job. See
      U(https://www.ansible.com/tower) for an overview.
options:
    workflow_job_id:
      description:
        - ID of the workflow job to monitor for approval.
      required: True
      type: int
    name:
      description:
        - Name of the Approval node to approve or deny.
      required: True
      type: str
    action:
      description:
        - Type of action to take.
      choices: ["approve", "deny"]
      default: "manual"
      type: str
    interval:
      description:
        - The interval in sections, to request an update from Tower.
      required: False
      default: 1
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a workflow job to to reach approval node.
      default: 10
      type: int
extends_documentation_fragment: awx.awx.auth
"""


EXAMPLES = """
- name: Launch a workflow with a timeout of 10 seconds
  tower_workflow_launch:
    workflow_template: "Test Workflow"
    wait: False
  register: workflow

- name: Wait for approval node to activate and approve 
  tower_workflow_approval:
    workflow_job_id: "{{ workflow.id }}"
    name: Approve Me
    interval: 10
    timeout: 20
    action: deny
"""

RETURN = """

"""


from ..module_utils.tower_api import TowerAPIModule
import urllib.parse
import time


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        workflow_job_id=dict(type="int", required=True),
        name=dict(required=True),
        action=dict(choices=["approve", "deny"], default="approve"),
        timeout=dict(type="int", default=10),
        interval=dict(type="float", default=1),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    workflow_job_id = module.params.get("workflow_job_id")
    name = module.params.get("name")
    action = module.params.get("action")
    timeout = module.params.get("timeout")
    interval = module.params.get("interval")

    # Attempt to look up workflow job based on the provided id
    approval_job = module.wait_on_workflow_node_url(
        url="workflow_jobs/{0}/workflow_nodes/".format(workflow_job_id),
        object_name=name,
        object_type="Workflow Approval",
        timeout=timeout,
        interval=interval,
        **{
            "data": {
                "job__name": name,
            }
        }
    )
    response = module.post_endpoint("{0}{1}".format(approval_job["related"]["job"], action))
    if response["status_code"] == 204:
        module.json_output["changed"] = True

    # Attempt to look up jobs based on the status
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
