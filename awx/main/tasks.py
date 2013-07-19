# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import cStringIO
import json
import logging
import os
import subprocess
import tempfile
import traceback

# Pexpect
import pexpect

# Celery
from celery import Task

# Django
from django.conf import settings

# AWX
from awx.main.models import Job

__all__ = ['RunJob']

logger = logging.getLogger('awx.main.tasks')

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
            update_fields = []
            for field, value in job_updates.items():
                setattr(job, field, value)
                update_fields.append(field)
                if field == 'status':
                    update_fields.append('failed')
            job.save(update_fields=update_fields)
        return job

    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_ssh_key_path(self, job, **kwargs):
        '''
        Create a temporary file containing the SSH private key.
        '''
        creds = job.credential
        if creds and creds.ssh_key_data:
            # FIXME: File permissions?
            handle, path = tempfile.mkstemp()
            f = os.fdopen(handle, 'w')
            f.write(creds.ssh_key_data)
            f.close()
            return path
        else:
            return ''

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user and sudo.
        '''
        passwords = {}
        creds = job.credential
        if creds:
            for field in ('ssh_key_unlock', 'ssh_password', 'sudo_password'):
                value = kwargs.get(field, getattr(creds, field))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, job, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        env = dict(os.environ.items())
        # question: when running over CLI, generate a random ID or grab next, etc?
        # answer: TBD
        # Add ANSIBLE_* settings to the subprocess environment.
        for attr in dir(settings):
            if attr == attr.upper() and attr.startswith('ANSIBLE_'):
                env[attr] = str(getattr(settings, attr))
        # Also set environment variables configured in AWX_TASK_ENV setting.
        for key, value in settings.AWX_TASK_ENV.items():
            env[key] = str(value)
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['JOB_ID'] = str(job.pk)
        env['INVENTORY_ID'] = str(job.inventory.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ANSIBLE_NOCOLOR'] = '1' # Prevent output of escape sequences.
        env['REST_API_URL'] = settings.INTERNAL_API_URL
        env['REST_API_TOKEN'] = job.task_auth_token or ''
        return env

    def build_args(self, job, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.credential
        ssh_username, sudo_username = '', ''
        if creds:
            ssh_username = kwargs.get('ssh_username', creds.ssh_username)
            sudo_username = kwargs.get('sudo_username', creds.sudo_username)
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible-playbook's default of using
        # the current user.
        ssh_username = ssh_username or 'root'
        inventory_script = self.get_path_to('..', 'scripts', 'inventory.py')
        args = ['ansible-playbook', '-i', inventory_script]
        if job.job_type == 'check':
            args.append('--check')
        args.extend(['-u', ssh_username])
        if 'ssh_password' in kwargs.get('passwords', {}):
            args.append('--ask-pass')
        # However, we should only specify sudo user if explicitly given by the
        # credentials, otherwise, the playbook will be forced to run using
        # sudo, which may not always be the desired behavior.
        if sudo_username:
            args.extend(['-U', sudo_username])
        if 'sudo_password' in kwargs.get('passwords', {}):
            args.append('--ask-sudo-pass')
        if job.forks:  # FIXME: Max limit?
            args.append('--forks=%d' % job.forks)
        if job.limit:
            args.extend(['-l', job.limit])
        if job.verbosity:
            args.append('-%s' % ('v' * min(3, job.verbosity)))
        if job.extra_vars:
            args.extend(['-e', job.extra_vars])
        if job.job_tags:
            args.extend(['-t', job.job_tags])
        args.append(job.playbook) # relative path to project.local_path
        ssh_key_path = kwargs.get('ssh_key_path', '')
        if ssh_key_path:
            cmd = ' '.join([subprocess.list2cmdline(['ssh-add', ssh_key_path]),
                            '&&', subprocess.list2cmdline(args)])
            args = ['ssh-agent', 'sh', '-c', cmd]
        return args

    def run_pexpect(self, job_pk, args, cwd, env, passwords):
        '''
        Run the job using pexpect to capture output and provide passwords when
        requested.
        '''
        status, stdout = 'error', ''
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
                r'Password:',
                pexpect.TIMEOUT,
                pexpect.EOF,
            ]
            result_id = child.expect(expect_list, timeout=2)
            if result_id == 0:
                child.sendline(passwords.get('ssh_key_unlock', ''))
            elif result_id == 1:
                child.sendline('')
            elif result_id == 2:
                child.sendline(passwords.get('sudo_password', ''))
            elif result_id in (3, 4):
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
        return status, stdout

    def run(self, job_pk, **kwargs):
        '''
        Run the job using ansible-playbook and capture its output.
        '''
        job = self.update_job(job_pk, status='running')
        status, stdout, tb = 'error', '', ''
        try:
            kwargs['ssh_key_path'] = self.build_ssh_key_path(job, **kwargs)
            kwargs['passwords'] = self.build_passwords(job, **kwargs)
            args = self.build_args(job, **kwargs)
            cwd = job.project.get_project_path()
            root = settings.PROJECTS_ROOT
            if not cwd:
                raise RuntimeError('project local_path %s cannot be found in %s' %
                                   (job.project.local_path, root))
            env = self.build_env(job, **kwargs)
            job = self.update_job(job_pk, job_args=json.dumps(args),
                                  job_cwd=cwd, job_env=env)
            status, stdout = self.run_pexpect(job_pk, args, cwd, env,
                                              kwargs['passwords'])
        except Exception:
            tb = traceback.format_exc()
        finally:
            if kwargs.get('ssh_key_path', ''):
                try:
                    os.remove(kwargs['ssh_key_path'])
                except IOError:
                    pass
        self.update_job(job_pk, status=status, result_stdout=stdout,
                        result_traceback=tb)
