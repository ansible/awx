# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
from celery import task
from lib.main.models import *

@task(name='run_launch_job')
def run_launch_job(launch_job_status_pk):
    launch_job_status = LaunchJobStatus.objects.get(pk=launch_job_status_pk)
    launch_job = launch_job_status.launch_job
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                              'plugins', 'callback'))
    inventory_script = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    'management', 'commands',
                                                    'acom_inventory.py'))
    env = dict(os.environ.items())
    env['ACOM_LAUNCH_JOB_STATUS_ID'] = str(launch_job_status.pk)
    env['ACOM_INVENTORY_ID'] = str(launch_job.inventory.pk)
    env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
    playbook = launch_job.project.default_playbook
    cmdline = ['ansible-playbook', '-i', inventory_script, '-v']
    if False: # local mode
        cmdline.extend(['-c', 'local'])
    cmdline.append(playbook)
    subprocess.check_call(cmdline, env=env)
    # FIXME: Capture stdout/stderr
