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
module: tower_job_wait
author: "Wayne Witzel III (@wwitzel3)"
short_description: Wait for Ansible Tower job to finish.
description:
    - Wait for Ansible Tower job to finish and report success or failure. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_id:
      description:
        - ID of the job to monitor.
      required: True
      type: int
    interval:
      description:
        - The interval in sections, to request an update from Tower.
        - For backwards compatability if unset this will be set to the average of min and max intervals
      required: False
      default: 1
      type: float
    min_interval:
      description:
        - Minimum interval in seconds, to request an update from Tower.
        - deprecated, use interval instead
      type: float
    max_interval:
      description:
        - Maximum interval in seconds, to request an update from Tower.
        - deprecated, use interval instead
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish.
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Launch a job
  tower_job_launch:
    job_template: "My Job Template"
    register: job

- name: Wait for job max 120s
  tower_job_wait:
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


from ..module_utils.tower_api import TowerAPIModule
import time


def check_job(module, job_url):
    response = module.get_endpoint(job_url)
    if response['status_code'] != 200:
        module.fail_json(msg="Unable to read job from Tower {0}: {1}".format(response['status_code'], module.extract_errors_from_response(response)))

    # Since we were successful, extract the fields we want to return
    for k in ('id', 'status', 'elapsed', 'started', 'finished'):
        module.json_output[k] = response['json'].get(k)

    # And finally return the payload
    return response['json']


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        job_id=dict(type='int', required=True),
        timeout=dict(type='int'),
        min_interval=dict(type='float'),
        max_interval=dict(type='float'),
        interval=dict(type='float', default=1),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    job_id = module.params.get('job_id')
    timeout = module.params.get('timeout')
    min_interval = module.params.get('min_interval')
    max_interval = module.params.get('max_interval')
    interval = module.params.get('interval')

    if min_interval is not None or max_interval is not None:
        # We can't tell if we got the default or if someone actually set this to 1.
        # For now if we find 1 and had a min or max then we will do the average logic.
        if interval == 1:
            if not min_interval:
                min_interval = 1
            if not max_interval:
                max_interval = 30
            interval = abs((min_interval + max_interval) / 2)
        module.deprecate(
            msg="Min and max interval have been deprecated, please use interval instead; interval will be set to {0}".format(interval),
            version="ansible.tower:4.0.0"
        )

    # Attempt to look up job based on the provided id
    job = module.get_one('jobs', **{
        'data': {
            'id': job_id,
        }
    })

    if job is None:
        module.fail_json(msg='Unable to wait on job {0}; that ID does not exist in Tower.'.format(job_id))

    job_url = job['url']

    # Grab our start time to compare against for the timeout
    start = time.time()

    # Get the initial job status from Tower, this will exit if there are any issues with the HTTP call
    result = check_job(module, job_url)

    # Loop while the job is not yet completed
    while not result['finished']:
        # If we are past our time out fail with a message
        if timeout and timeout < time.time() - start:
            module.json_output['msg'] = "Monitoring aborted due to timeout"
            module.fail_json(**module.json_output)

        # Put the process to sleep for our interval
        time.sleep(interval)

        # Check the job again
        result = check_job(module, job_url)

    # If the job has failed, we want to raise an Exception for that so we get a non-zero response.
    if result['failed']:
        module.json_output['msg'] = 'Job with id {0} failed'.format(job_id)
        module.fail_json(**module.json_output)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
