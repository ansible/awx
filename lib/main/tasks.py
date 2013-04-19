# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import traceback
from celery import task
from django.conf import settings
from lib.main.models import *

__all__ = ['run_job']

@task(name='run_job')
def run_job(job_pk):
    job = Job.objects.get(pk=job_pk)
    job.status = 'running'
    job.save(update_fields=['status'])

    try:
        status, stdout, stderr, tb = 'error', '', '', ''
        plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 
                                                  'plugins', 'callback'))
        inventory_script = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        'management', 'commands',
                                                        'acom_inventory.py'))
        callback_script = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        'management', 'commands',
                                                        'acom_callback_event.py'))
        env = dict(os.environ.items())
        # question: when running over CLI, generate a random ID or grab next, etc?
        # answer: TBD
        env['ACOM_JOB_ID'] = str(job.pk)
        env['ACOM_INVENTORY_ID'] = str(job.inventory.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ACOM_CALLBACK_EVENT_SCRIPT'] = callback_script
 
        if hasattr(settings, 'ANSIBLE_TRANSPORT'):
            env['ANSIBLE_TRANSPORT'] = getattr(settings, 'ANSIBLE_TRANSPORT')

        cwd = job.project.local_path
        cmdline = ['ansible-playbook', '-i', inventory_script]
        if job.job_type == 'check':
            cmdline.append('--check')
        cmdline.append(job.playbook) # relative path to project.local_path

        # FIXME: How to cancel/interrupt job? (not that important for now)
        proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=cwd, env=env)
        stdout, stderr = proc.communicate()
        status = 'successful' if proc.returncode == 0 else 'failed'
    except Exception:
        tb = traceback.format_exc()
 
    # Reload from database before updating/saving.
    job = Job.objects.get(pk=job_pk)
    job.status = status
    job.result_stdout = stdout
    job.result_stderr = stderr
    job.result_traceback = tb
    job.save(update_fields=['status', 'result_stdout', 'result_stderr',
                            'result_traceback'])
