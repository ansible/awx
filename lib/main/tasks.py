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

import cStringIO
import logging
import os
import select
import subprocess
import time
import traceback
from celery import Task
from django.conf import settings
import pexpect
from lib.main.models import *

__all__ = ['RunJob']

logger = logging.getLogger('lib.main.tasks')


class RunJob(Task):
    '''
    Celery task to run a job using ansible-playbook.
    '''

    name = 'run_job'

    def update_job(self, job_pk, **job_updates):
        '''
        Reload Job from database and update the given fields.
        '''
        job = Job.objects.get(pk=job_pk)
        if job_updates:
            for field, value in job_updates.items():
                setattr(job, field, value)
            job.save(update_fields=job_updates.keys())
        return job

    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_env(self, job, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        callback_script = self.get_path_to('management', 'commands',
                                           'acom_callback_event.py')
        env = dict(os.environ.items())
        # question: when running over CLI, generate a random ID or grab next, etc?
        # answer: TBD
        env['ACOM_JOB_ID'] = str(job.pk)
        env['ACOM_INVENTORY_ID'] = str(job.inventory.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ACOM_CALLBACK_EVENT_SCRIPT'] = callback_script
        if hasattr(settings, 'ANSIBLE_TRANSPORT'):
            env['ANSIBLE_TRANSPORT'] = getattr(settings, 'ANSIBLE_TRANSPORT')
        env['ANSIBLE_NOCOLOR'] = '1' # Prevent output of escape sequences.
        return env

    def build_args(self, job, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.credential
        use_ssh_agent = False
        if creds:
            username = creds.ssh_username
            sudo_username = creds.sudo_username
            # FIXME: Do something with creds.
        inventory_script = self.get_path_to('management', 'commands',
                                            'acom_inventory.py')
        args = ['ansible-playbook', '-i', inventory_script]
        if job.job_type == 'check':
            args.append('--check')
        if job.use_sudo:
            args.append('--sudo')
        if job.forks:  # FIXME: Max limit?
            args.append('--forks=%d' % job.forks)
        if job.limit:
            args.append('--limit=%s' % job.limit)
        if job.verbosity:
            args.append('-%s' % ('v' * min(3, job.verbosity)))
        if job.extra_vars:
            # FIXME: escaping!
            extra_vars = ' '.join(['%s=%s' % (str(k), str(v)) for k,v in
                                   job.extra_vars.items()])
            args.append('-e', extra_vars)
        args.append(job.playbook) # relative path to project.local_path
        if use_ssh_agent:
            key_path = 'myrsa' # FIXME
            cmd = '; '.join([subprocess.list2cmdline(['ssh-add', keypath]),
                             subprocess.list2cmdline(args)])
            return ['ssh-agent', 'sh', '-c', cmd]
        else:
            return args

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user and sudo.
        '''
        return {}

    def capture_subprocess_output(self, proc, timeout=1.0):
        '''
        Capture stdout/stderr from the given process until the timeout expires.
        '''
        stdout, stderr = '', ''
        until = time.time() + timeout
        remaining = max(0, until - time.time())
        while remaining > 0:
            # FIXME: Probably want to use poll (when on Linux), needs to be tested.
            if hasattr(select, 'poll') and False: 
                poll = select.poll()
                poll.register(proc.stdout.fileno(), select.POLLIN or select.POLLPRI)
                poll.register(proc.stderr.fileno(), select.POLLIN or select.POLLPRI)
                fd_events = poll.poll(remaining)
                if not fd_events:
                    break
                for fd, evt in fd_events:
                    if fd == proc.stdout.fileno() and evt > 0:
                        stdout += proc.stdout.read(1)
                    elif fd == proc.stderr.fileno() and evt > 0:
                        stderr += proc.stderr.read(1)
            else:
                stdout_byte, stderr_byte = '', ''
                fdlist = [proc.stdout.fileno(), proc.stderr.fileno()]
                rwx = select.select(fdlist, [], [], remaining)
                if proc.stdout.fileno() in rwx[0]:
                    stdout_byte = proc.stdout.read(1)
                    stdout += stdout_byte
                if proc.stderr.fileno() in rwx[0]:
                    stderr_byte = proc.stderr.read(1)
                    stderr += stderr_byte
                if not stdout_byte and not stderr_byte:
                    break
            remaining = max(0, until - time.time())
        return stdout, stderr

    def run_subprocess(self, job_pk, args, cwd, env, passwords):
        '''
        Run the job using subprocess to capture stdout/stderr.
        '''
        status, stdout, stderr = 'error', '', ''
        proc = subprocess.Popen(args, cwd=cwd, env=env,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc_canceled = False
        while proc.poll() is None:
            new_stdout, new_stderr = self.capture_subprocess_output(proc)
            job_updates = {}
            if new_stdout:
                stdout += new_stdout
                job_updates['result_stdout'] = stdout
            if new_stderr:
                stderr += new_stderr
                job_updates['result_stdout'] = stdout
            job = self.update_job(job_pk, **job_updates)
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
        return status, stdout, stderr

    def run_pexpect(self, job_pk, args, cwd, env, passwords):
        '''
        Run the job using pexpect to capture output and provide passwords when
        requested.
        '''
        status, stdout, stderr = 'error', '', ''
        logfile = cStringIO.StringIO()
        logfile_pos = logfile.tell()
        child = pexpect.spawn(args[0], args[1:], cwd=cwd, env=env)
        child.logfile_read = logfile
        job_canceled = False
        while child.isalive():
            expect_list = [
                r'Enter passphrase for .*:',
                r'Bad passphrase, try again for .*:',
                r'sudo password.*:',
                r'SSH password:',
                pexpect.TIMEOUT,
                pexpect.EOF,
            ]
            result_id = child.expect(expect_list, timeout=2)
            if result_id == 0:
                child.sendline(passwords.get('ssh_unlock_key', ''))
            elif result_id == 1:
                child.sendline('')
            elif result_id == 2:
                child.sendline(passwords.get('sudo_password', ''))
            elif result_id == 3:
                child.sendline(passwords.get('ssh_password', ''))
            job_updates = {}
            if logfile_pos != logfile.tell():
                job_updates['result_stdout'] = logfile.getvalue()
            job = self.update_job(job_pk, **job_updates)
            if job.cancel_flag:
                child.close(True)
                job_canceled = True
        if job_canceled:
            status = 'canceled'
        elif child.exitstatus == 0:
            status = 'successful'
        else:
            status = 'failed'
        stdout = logfile.getvalue()
        return status, stdout, stderr

    def run(self, job_pk, **kwargs):
        '''
        Run the job using ansible-playbook and capture its output.
        '''
        job = self.update_job(job_pk, status='running')
        try:
            status, stdout, stderr, tb = 'error', '', '', ''
            args = self.build_args(job, **kwargs)
            cwd = job.project.local_path
            env = self.build_env(job, **kwargs)
            passwords = self.build_passwords(job, **kwargs)
            #status, stdout, stderr = self.run_subprocess(job_pk, args, cwd,
            #                                             env, passwords)
            status, stdout, stderr = self.run_pexpect(job_pk, args, cwd, env,
                                                      passwords)
        except Exception:
            tb = traceback.format_exc()
        self.update_job(job_pk, status=status, result_stdout=stdout,
                        result_stderr=stderr, result_traceback=tb)
