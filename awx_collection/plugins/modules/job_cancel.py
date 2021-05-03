#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: job_cancel
author: "Wayne Witzel III (@wwitzel3)"
short_description: Cancel an Automation Platform Controller Job.
description:
    - Cancel Automation Platform Controller jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_id:
      description:
        - ID of the job to cancel
      required: True
      type: int
    fail_if_not_running:
      description:
        - Fail loudly if the I(job_id) can not be canceled
      default: False
      type: bool
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Cancel job
  job_cancel:
    job_id: job.id
'''

RETURN = '''
id:
    description: job id requesting to cancel
    returned: success
    type: int
    sample: 94
'''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        job_id=dict(type='int', required=True),
        fail_if_not_running=dict(type='bool', default=False),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    job_id = module.params.get('job_id')
    fail_if_not_running = module.params.get('fail_if_not_running')

    # Attempt to look up the job based on the provided name
    job = module.get_one(
        'jobs',
        **{
            'data': {
                'id': job_id,
            }
        }
    )

    if job is None:
        module.fail_json(msg="Unable to find job with id {0}".format(job_id))

    cancel_page = module.get_endpoint(job['related']['cancel'])
    if 'json' not in cancel_page or 'can_cancel' not in cancel_page['json']:
        module.fail_json(msg="Failed to cancel job, got unexpected response from the controller", **{'response': cancel_page})

    if not cancel_page['json']['can_cancel']:
        if fail_if_not_running:
            module.fail_json(msg="Job is not running")
        else:
            module.exit_json(**{'changed': False})

    results = module.post_endpoint(job['related']['cancel'], **{'data': {}})

    if results['status_code'] != 202:
        module.fail_json(msg="Failed to cancel job, see response for details", **{'response': results})

    module.exit_json(**{'changed': True})


if __name__ == '__main__':
    main()
