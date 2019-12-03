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


from ..module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode
from ansible.module_utils.six import PY2
from ansible.module_utils.six.moves import cStringIO as StringIO
from codecs import getwriter


try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        job_id=dict(type='int', required=True),
        timeout=dict(type='int'),
        min_interval=dict(type='float', default=1),
        max_interval=dict(type='float', default=30),
    )

    module = TowerModule(
        argument_spec,
        supports_check_mode=True
    )

    json_output = {}
    fail_json = None

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        job = tower_cli.get_resource('job')
        params = module.params.copy()

        # tower-cli gets very noisy when monitoring.
        # We pass in our our outfile to suppress the out during our monitor call.
        if PY2:
            outfile = getwriter('utf-8')(StringIO())
        else:
            outfile = StringIO()
        params['outfile'] = outfile

        job_id = params.get('job_id')
        try:
            result = job.monitor(job_id, **params)
        except exc.Timeout:
            result = job.status(job_id)
            result['id'] = job_id
            json_output['msg'] = 'Timeout waiting for job to finish.'
            json_output['timeout'] = True
        except exc.NotFound as excinfo:
            fail_json = dict(msg='Unable to wait, no job_id {0} found: {1}'.format(job_id, excinfo), changed=False)
        except exc.JobFailure as excinfo:
            fail_json = dict(msg='Job with id={0} failed, error: {1}'.format(job_id, excinfo))
            fail_json['success'] = False
            result = job.get(job_id)
            for k in ('id', 'status', 'elapsed', 'started', 'finished'):
                fail_json[k] = result.get(k)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            fail_json = dict(msg='Unable to wait for job: {0}'.format(excinfo), changed=False)

    if fail_json is not None:
        module.fail_json(**fail_json)

    json_output['success'] = True
    for k in ('id', 'status', 'elapsed', 'started', 'finished'):
        json_output[k] = result.get(k)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
