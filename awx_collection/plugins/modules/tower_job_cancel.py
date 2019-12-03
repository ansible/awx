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
module: tower_job_cancel
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: Cancel an Ansible Tower Job.
description:
    - Cancel Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_id:
      description:
        - ID of the job to cancel
      required: True
      type: int
    fail_if_not_running:
      description:
        - Fail loudly if the I(job_id) does not reference a running job.
      default: False
      type: bool
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Cancel job
  tower_job_cancel:
    job_id: job.id
'''

RETURN = '''
id:
    description: job id requesting to cancel
    returned: success
    type: int
    sample: 94
status:
    description: status of the cancel request
    returned: success
    type: str
    sample: canceled
'''


from ..module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        job_id=dict(type='int', required=True),
        fail_if_not_running=dict(type='bool', default=False),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    job_id = module.params.get('job_id')
    json_output = {}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        job = tower_cli.get_resource('job')
        params = module.params.copy()

        try:
            result = job.cancel(job_id, **params)
            json_output['id'] = job_id
        except (exc.ConnectionError, exc.BadRequest, exc.TowerCLIError, exc.AuthError) as excinfo:
            module.fail_json(msg='Unable to cancel job_id/{0}: {1}'.format(job_id, excinfo), changed=False)

    json_output['changed'] = result['changed']
    json_output['status'] = result['status']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
