# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import traceback
from celery import task
from django.conf import settings
from lib.main.models import *

@task(name='run_launch_job')
def run_launch_job(launch_job_status_pk):
    launch_job_status = LaunchJobStatus.objects.get(pk=launch_job_status_pk)
    launch_job_status.status = 'running'
    launch_job_status.save()
    launch_job = launch_job_status.launch_job

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
        env['ACOM_LAUNCH_JOB_STATUS_ID'] = str(launch_job_status.pk)
        env['ACOM_INVENTORY_ID'] = str(launch_job.inventory.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ACOM_CALLBACK_EVENT_SCRIPT'] = callback_script
 
        if hasattr(settings, 'ANSIBLE_TRANSPORT'):
            env['ANSIBLE_TRANSPORT'] = getattr(settings, 'ANSIBLE_TRANSPORT')
 
        playbook = launch_job.project.default_playbook
        cmdline = ['ansible-playbook', '-i', inventory_script]
        if launch_job.job_type == 'check':
            cmdline.append('--check')
        cmdline.append(playbook)

        # FIXME: How to cancel/interrupt job? (not that important for now)
        proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate()
        status = 'successful' if proc.returncode == 0 else 'failed'
    except Exception:
        tb = traceback.format_exc()
 
    # Reload from database before updating/saving.
    launch_job_status = LaunchJobStatus.objects.get(pk=launch_job_status_pk)
    launch_job_status.status = status
    launch_job_status.result_stdout = stdout
    launch_job_status.result_stderr = stderr
    launch_job_status.result_traceback = tb
    launch_job_status.save()
