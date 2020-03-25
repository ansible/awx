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
version_added: "2.3"
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
    min_interval:
      description:
        - Minimum interval in seconds, to request an update from Tower.
      default: 1
      type: float
    max_interval:
      description:
        - Maximum interval in seconds, to request an update from Tower.
      default: 30
      type: float
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish.
      type: int
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
      version_added: "3.7"
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


from ..module_utils.tower_api import TowerModule
import time
import itertools


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
        min_interval=dict(type='float', default=1),
        max_interval=dict(type='float', default=30),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    job_id = module.params.get('job_id')
    timeout = module.params.get('timeout')
    min_interval = module.params.get('min_interval')
    max_interval = module.params.get('max_interval')

    # Attempt to look up job based on the provided id
    job = module.get_one('jobs', **{
        'data': {
            'id': job_id,
        }
    })

    if job is None:
        module.fail_json(msg='Unable to wait, on job {0} that ID does not exist in Tower.'.format(job_id))

    job_url = job['url']

    # This comes from tower_cli/models/base.py from the old tower-cli
    dots = itertools.cycle([0, 1, 2, 3])
    interval = min_interval
    start = time.time()

    # Poll the Ansible Tower instance for status, and print the status to the outfile (usually standard out).
    #
    # Note that this is one of the few places where we use `secho` even though we're in a function that might
    # theoretically be imported and run in Python.  This seems fine; outfile can be set to /dev/null and very
    # much the normal use for this method should be CLI monitoring.
    result = check_job(module, job_url)

    last_poll = time.time()
    timeout_check = 0
    while not result['finished']:
        # Sanity check: Have we officially timed out?
        # The timeout check is incremented below, so this is checking to see if we were timed out as of
        # the previous iteration. If we are timed out, abort.
        if timeout and timeout_check - start > timeout:
            module.json_output['msg'] = "Monitoring aborted due to timeout"
            module.fail_json(**module.json_output)

        # If the outfile is a TTY, print the current status.
        output = '\rCurrent status: %s%s' % (result['status'], '.' * next(dots))

        # Put the process to sleep briefly.
        time.sleep(0.2)

        # Sanity check: Have we reached our timeout?
        # If we're about to time out, then we need to ensure that we do one last check.
        #
        # Note that the actual timeout will be performed at the start of the **next** iteration,
        # so there's a chance for the job's completion to be noted first.
        timeout_check = time.time()
        if timeout and timeout_check - start > timeout:
            last_poll -= interval

        # If enough time has elapsed, ask the server for a new status.
        #
        # Note that this doesn't actually do a status check every single time; we want the "spinner" to
        # spin even if we're not actively doing a check.
        #
        # So, what happens is that we are "counting down" (actually up) to the next time that we intend
        # to do a check, and once that time hits, we do the status check as part of the normal cycle.
        if time.time() - last_poll > interval:
            result = check_job(module, job_url)
            last_poll = time.time()
            interval = min(interval * 1.5, max_interval)

    # If the job has failed, we want to raise an Exception for that so we get a non-zero response.
    if result['failed']:
        module.json_output['msg'] = 'Job with id {0} failed'.format(job_id)
        module.fail_json(**module.json_output)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
