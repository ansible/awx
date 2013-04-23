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

import logging
import os
import select
import subprocess
import time
import traceback
from celery import task
from django.conf import settings
from lib.main.models import *

__all__ = ['run_job']

logger = logging.getLogger('lib.tasks')

class Timeout(object):

    def __init__(self, duration=None):
        # If initializing from another instance, create a new timeout from the
        # remaining time on the other instance.
        if isinstance(duration, Timeout):
            duration = duration.remaining
        self.reset(duration)

    def __repr__(self):
        if self._duration is None:
            return 'Timeout(None)'
        else:
            return 'Timeout(%f)' % self._duration

    def __hash__(self):
        return self._duration

    def __nonzero__(self):
        return self.block

    def reset(self, duration=False):
        if duration is not False:
            self._duration = float(max(0, duration)) if duration is not None else None
        self._begin = time.time()

    def expire(self):
        self._begin = time.time() - max(0, self._duration or 0.0)

    @property
    def duration(self):
        return self._duration

    @property
    def elapsed(self):
        return float(max(0, time.time() - self._begin))

    @property
    def remaining(self):
        if self._duration is None:
            return None
        else:
            return float(max(0, self._duration + self._begin - time.time()))

    @property
    def block(self):
        return bool(self.remaining or self.remaining is None)


@task(name='run_job')
def run_job(job_pk, **kwargs):
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

        creds = job.credential
        username = creds.ssh_username
        #sudo_username = job.credential.sudo_username
        


        cwd = job.project.local_path
        
        cmdline = ['ansible-playbook', '-i', inventory_script]
        if job.job_type == 'check':
            cmdline.append('--check')
        if job.use_sudo:
            cmdline.append('--sudo')
        if job.forks:  # FIXME: Max limit?
            cmdline.append('--forks=%d' % job.forks)
        if job.limit:
            cmdline.append('--limit=%s' % job.limit)
        if job.verbosity:
            cmdline.append('-%s' % ('v' * min(3, job.verbosity)))
        if job.extra_vars:
            # FIXME: escaping!
            extra_vars = ' '.join(['%s=%s' % (str(k), str(v)) for k,v in
                                   job.extra_vars.items()])
            cmdline.append('-e', extra_vars)
        cmdline.append(job.playbook) # relative path to project.local_path

        proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=cwd, env=env)
        # stdout, stderr = proc.communicate()
        proc_canceled = False
        while proc.returncode is None:
            new_stdout, new_stderr = '', ''
            timeout = Timeout(1.0)
            while timeout:
                # FIXME: Probably want to use poll (when on Linux), needs to be tested.
                if hasattr(select, 'poll') and False: 
                    poll = select.poll()
                    poll.register(proc.stdout.fileno(), select.POLLIN or select.POLLPRI)
                    poll.register(proc.stderr.fileno(), select.POLLIN or select.POLLPRI)
                    fd_events = poll.poll(1.0)
                    if not fd_events:
                        break
                    for fd, evt in fd_events:
                        if fd == proc.stdout.fileno() and evt > 0:
                            new_stdout += proc.stdout.read(1)
                        elif fd == proc.stderr.fileno() and evt > 0:
                            new_stderr += proc.stderr.read(1)
                else:
                    stdout_byte, stderr_byte = '', ''
                    fdlist = [proc.stdout.fileno(), proc.stderr.fileno()]
                    rwx = select.select(fdlist, [], [], timeout.remaining)
                    if proc.stdout.fileno() in rwx[0]:
                        stdout_byte = proc.stdout.read(1)
                        new_stdout += stdout_byte
                    if proc.stderr.fileno() in rwx[0]:
                        stderr_byte = proc.stderr.read(1)
                        new_stderr += stderr_byte
                    if not stdout_byte and not stderr_byte:
                        break
            job = Job.objects.get(pk=job_pk)
            update_fields = []
            if new_stdout:
                stdout += new_stdout
                job.result_stdout = stdout
                update_fields.append('result_stdout')
            if new_stderr:
                stderr += new_stderr
                job.result_stderr = stderr
                update_fields.append('result_stderr')
            if update_fields:
                job.save(update_fields=update_fields)
            proc.poll()
            if job.cancel_flag and not proc_canceled:
                proc.terminate()
                proc_canceled = True
        stdout += proc.stdout.read()
        stderr += proc.stderr.read()
        if proc_canceled:
            status = 'canceled'
        elif proc.returncode == 0:
            status = 'successful'
        else:
            status = 'failed'
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
