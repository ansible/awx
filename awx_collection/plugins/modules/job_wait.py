#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: job_wait
author: "Wayne Witzel III (@wwitzel3)"
short_description: Wait for Automation Platform Controller job to finish.
description:
    - Wait for Automation Platform Controller job to finish and report success or failure. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_id:
      description:
        - ID of the job to monitor.
      required: True
      type: int
    interval:
      description:
        - The interval in sections, to request an update from the controller.
        - For backwards compatibility if unset this will be set to the average of min and max intervals
      required: False
      default: 2
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish.
      type: int
    job_type:
      description:
        - Job type to wait for
      choices: ['project_updates', 'jobs', 'inventory_updates', 'workflow_jobs']
      default: 'jobs'
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Launch a job
  job_launch:
    job_template: "My Job Template"
  register: job

- name: Wait for job max 120s
  job_wait:
    job_id: "{{ job.id }}"
    timeout: 120
'''

RETURN = '''
id:
    description: job id that is being waited on
    returned: success
    type: int
    sample: 99
elapsed:
    description: total time in seconds the job took to run
    returned: success
    type: float
    sample: 10.879
started:
    description: timestamp of when the job started running
    returned: success
    type: str
    sample: "2017-03-01T17:03:53.200234Z"
finished:
    description: timestamp of when the job finished running
    returned: success
    type: str
    sample: "2017-03-01T17:04:04.078782Z"
status:
    description: current status of job
    returned: success
    type: str
    sample: successful
'''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        job_id=dict(type='int', required=True),
        job_type=dict(choices=['project_updates', 'jobs', 'inventory_updates', 'workflow_jobs'], default='jobs'),
        timeout=dict(type='int'),
        interval=dict(type='float', default=2),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    job_id = module.params.get('job_id')
    job_type = module.params.get('job_type')
    timeout = module.params.get('timeout')
    interval = module.params.get('interval')

    # Attempt to look up job based on the provided id
    job = module.get_one(
        job_type,
        **{
            'data': {
                'id': job_id,
            }
        }
    )

    if job is None:
        module.fail_json(msg='Unable to wait on ' + job_type.rstrip("s") + ' {0}; that ID does not exist.'.format(job_id))

    # Invoke wait function
    module.wait_on_url(url=job['url'], object_name=job_id, object_type='legacy_job_wait', timeout=timeout, interval=interval)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
