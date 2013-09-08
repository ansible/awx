# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import cStringIO
import distutils.version
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import traceback
import urlparse

# Pexpect
import pexpect

# Celery
from celery import Task

# Django
from django.conf import settings

# AWX
from awx.main.models import Job, ProjectUpdate
from awx.main.utils import get_ansible_version, decrypt_field

__all__ = ['RunJob', 'RunProjectUpdate']

logger = logging.getLogger('awx.main.tasks')

# FIXME: Cleanly cancel task when celery worker is stopped.

class BaseTask(Task):
    
    name = None
    model = None
    idle_timeout = None

    def update_model(self, pk, **updates):
        '''
        Reload model from database and update the given fields.
        '''
        instance = self.model.objects.get(pk=pk)
        if updates:
            update_fields = []
            for field, value in updates.items():
                setattr(instance, field, value)
                update_fields.append(field)
                if field == 'status':
                    update_fields.append('failed')
            instance.save(update_fields=update_fields)
        return instance

    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_ssh_key_path(self, instance, **kwargs):
        '''
        Create a temporary file containing the SSH private key.
        '''
        ssh_key_data = ''
        if hasattr(instance, 'credential'):
            credential = instance.credential
            if hasattr(credential, 'ssh_key_data'):
                ssh_key_data = decrypt_field(credential, 'ssh_key_data')
        elif hasattr(instance, 'project'):
            project = instance.project
            if hasattr(project, 'scm_key_data'):
                ssh_key_data = decrypt_field(project, 'scm_key_data')
        if ssh_key_data:
            # FIXME: File permissions?
            handle, path = tempfile.mkstemp()
            f = os.fdopen(handle, 'w')
            f.write(ssh_key_data)
            f.close()
            return path
        else:
            return ''

    def build_passwords(self, instance, **kwargs):
        '''
        Build a dictionary of passwords for responding to prompts.
        '''
        return {
            'yes': 'yes',
            'no': 'no',
            '': '',
        }

    def build_env(self, instance, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = dict(os.environ.items())
        # Add ANSIBLE_* settings to the subprocess environment.
        for attr in dir(settings):
            if attr == attr.upper() and attr.startswith('ANSIBLE_'):
                env[attr] = str(getattr(settings, attr))
        # Also set environment variables configured in AWX_TASK_ENV setting.
        for key, value in settings.AWX_TASK_ENV.items():
            env[key] = str(value)
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['ANSIBLE_NOCOLOR'] = '1' # Prevent output of escape sequences.
        return env

    def build_args(self, instance, **kwargs):
        raise NotImplementedError

    def build_cwd(self, instance, **kwargs):
        raise NotImplementedError

    def get_password_prompts(self):
        '''
        Return a dictionary of prompt regular expressions and password lookup
        keys.
        '''
        return {
            r'Enter passphrase for .*:': 'ssh_key_unlock',
            r'Bad passphrase, try again for .*:': '',
        }

    def run_pexpect(self, instance, args, cwd, env, passwords):
        '''
        Run the given command using pexpect to capture output and provide
        passwords when requested.
        '''
        status, stdout = 'error', ''
        logfile = cStringIO.StringIO()
        logfile_pos = logfile.tell()
        child = pexpect.spawn(args[0], args[1:], cwd=cwd, env=env)
        child.logfile_read = logfile
        canceled = False
        last_stdout_update = time.time()
        expect_list = []
        expect_passwords = {}
        for n, item in enumerate(self.get_password_prompts().items()):
            expect_list.append(item[0])
            expect_passwords[n] = passwords.get(item[1], '') or ''
        expect_list.extend([pexpect.TIMEOUT, pexpect.EOF])
        while child.isalive():
            result_id = child.expect(expect_list, timeout=5)
            if result_id in expect_passwords:
                child.sendline(expect_passwords[result_id])
            updates = {'status': 'running'}
            if logfile_pos != logfile.tell():
                logfile_pos = logfile.tell()
                updates['result_stdout'] = logfile.getvalue()
                last_stdout_update = time.time()
            instance = self.update_model(instance.pk, **updates)
            if instance.cancel_flag:
                child.close(True)
                canceled = True
            # FIXME: Configurable idle timeout? Find a way to determine if task
            # is hung waiting at a prompt.
            if self.idle_timeout and (time.time() - last_stdout_update) > self.idle_timeout:
                child.close(True)
                canceled = True
        if canceled:
            status = 'canceled'
        elif child.exitstatus == 0:
            status = 'successful'
        else:
            status = 'failed'
        stdout = logfile.getvalue()
        return status, stdout

    def pre_run_check(self, instance, **kwargs):
        '''
        Hook for checking job/task before running.
        '''
        if instance.status != 'pending':
            return False
        return True

    def post_run_hook(self, instance):
        '''
        Hook for actions after job/task has completed.
        '''

    def run(self, pk, **kwargs):
        '''
        Run the job/task using ansible-playbook and capture its output.
        '''
        self.pk = pk
        self.kwargs = dict(kwargs.items())
        instance = self.update_model(pk)
        if not self.pre_run_check(instance, **kwargs):
            return
        instance = self.update_model(pk, status='running')
        status, stdout, tb = 'error', '', ''
        try:
            kwargs['ssh_key_path'] = self.build_ssh_key_path(instance, **kwargs)
            kwargs['passwords'] = self.build_passwords(instance, **kwargs)
            args = self.build_args(instance, **kwargs)
            cwd = self.build_cwd(instance, **kwargs)
            env = self.build_env(instance, **kwargs)
            instance = self.update_model(pk, job_args=json.dumps(args),
                                         job_cwd=cwd, job_env=env)
            status, stdout = self.run_pexpect(instance, args, cwd, env,
                                              kwargs['passwords'])
        except Exception:
            tb = traceback.format_exc()
        finally:
            if kwargs.get('ssh_key_path', ''):
                try:
                    os.remove(kwargs['ssh_key_path'])
                except IOError:
                    pass
        instance = self.update_model(pk, status=status, result_stdout=stdout,
                                     result_traceback=tb)
        self.post_run_hook(instance)

class RunJob(BaseTask):
    '''
    Celery task to run a job using ansible-playbook.
    '''

    name = 'run_job'
    model = Job

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user and sudo.
        '''
        passwords = super(RunJob, self).build_passwords(job, **kwargs)
        creds = job.credential
        if creds:
            for field in ('ssh_key_unlock', 'ssh_password', 'sudo_password'):
                value = kwargs.get(field, decrypt_field(creds, field))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, job, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        env = super(RunJob, self).build_env(job, **kwargs)
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['JOB_ID'] = str(job.pk)
        env['INVENTORY_ID'] = str(job.inventory.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['REST_API_URL'] = settings.INTERNAL_API_URL
        env['REST_API_TOKEN'] = job.task_auth_token or ''

        # When using Ansible >= 1.3, allow the inventory script to include host
        # variables inline via ['_meta']['hostvars'].
        try:
            Version = distutils.version.StrictVersion
            if Version( get_ansible_version()) >= Version('1.3'):
                env['INVENTORY_HOSTVARS'] = str(True)
        except ValueError:
            pass

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

    def build_cwd(self, job, **kwargs):
        cwd = job.project.get_project_path()
        if not cwd:
            root = settings.PROJECTS_ROOT
            raise RuntimeError('project local_path %s cannot be found in %s' %
                               (job.project.local_path, root))
        return cwd

    def get_password_prompts(self):
        d = super(RunJob, self).get_password_prompts()
        d.update({
            r'sudo password.*:': 'sudo_password',
            r'SSH password:': 'ssh_password',
            r'Password:': 'ssh_password',
        })
        return d

    def pre_run_check(self, job, **kwargs):
        '''
        Hook for checking job before running.
        '''
        if not super(RunJob, self).pre_run_check(job, **kwargs):
            return False
        # FIXME: Check if job is waiting on any projects that are being updated.
        return True

    def post_run_hook(self, job):
        '''
        Hook for actions after job has completed.
        '''
        # Start any project updates that were blocked waiting for the job.

class RunProjectUpdate(BaseTask):
    
    name = 'run_project_update'
    model = ProjectUpdate
    #idle_timeout = 30

    def build_passwords(self, project_update, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update,
                                                                  **kwargs)
        project = project_update.project
        value = decrypt_field(project, 'scm_key_unlock')
        if value not in ('', 'ASK'):
            passwords['ssh_key_unlock'] = value
        passwords['scm_username'] = project.scm_username
        passwords['scm_password'] = decrypt_field(project, 'scm_password')
        return passwords

    def build_env(self, project_update, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = super(RunProjectUpdate, self).build_env(project_update, **kwargs)
        env['ANSIBLE_ASK_SUDO_PASS'] = str(False)
        env['DISPLAY'] = '' # Prevent stupid password popup when running tests.
        return env

    def update_url_auth(self, url, username=None, password=None):
        parts = urlparse.urlsplit(url)
        netloc_username = username or parts.username or ''
        netloc_password = password or parts.password or ''
        if netloc_username:
            netloc = u':'.join(filter(None, [netloc_username, netloc_password]))
        else:
            netlock = u''
        netloc = u'@'.join(filter(None, [netloc, parts.hostname]))
        netloc = u':'.join(filter(None, [netloc, parts.port]))
        return urlparse.urlunsplit([parts.scheme, netloc, parts.path,
                                    parts.query, parts.fragment])

    def build_args(self, project_update, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        args = ['ansible-playbook', '-i', 'localhost,']
        # Since we specify -vvv and tasks use async polling, we should get some
        # output regularly...
        args.append('-%s' % ('v' * 3))
        extra_vars = {}
        project = project_update.project
        scm_url = project.scm_url
        if project.scm_username and project.scm_password not in ('ASK', ''):
            if project.scm_type == 'svn':
                extra_vars['scm_username'] = project.scm_username
                extra_vars['scm_password'] = decrypt_field(project, 'scm_password')
            else:
                scm_url = self.update_url_auth(scm_url, project.scm_username,
                                               decrypt_field(project, 'scm_password'))
        elif project.scm_username:
            if project.scm_type == 'svn':
                extra_vars['scm_username'] = project.scm_username
            else:  
                scm_url = self.update_url_auth(scm_url, project.scm_username)
        # FIXME: Need to hide password in saved job_args and result_stdout!
        scm_branch = project.scm_branch or {'hg': 'tip'}.get(project.scm_type, 'HEAD')
        scm_delete_on_update = project.scm_delete_on_update or project.scm_delete_on_next_update
        extra_vars.update({
            'project_path': project.get_project_path(check_if_exists=False),
            'scm_type': project.scm_type,
            'scm_url': scm_url,
            'scm_branch': scm_branch,
            'scm_clean': project.scm_clean,
            'scm_delete_on_update': scm_delete_on_update,
        })
        args.extend(['-e', json.dumps(extra_vars)])
        args.append('project_update.yml')

        ssh_key_path = kwargs.get('ssh_key_path', '')
        if ssh_key_path:
            subcmds = [('ssh-add', ssh_key_path), args]
            cmd = ' && '.join([subprocess.list2cmdline(x) for x in subcmds])
            args = ['ssh-agent', 'sh', '-c', cmd]
        return args

    def build_cwd(self, project_update, **kwargs):
        return self.get_path_to('..', 'playbooks')

    def get_password_prompts(self):
        d = super(RunProjectUpdate, self).get_password_prompts()
        d.update({
            # FIXME: Configure whether we should auto accept host keys?
            r'Are you sure you want to continue connecting \(yes/no\)\?': 'yes',
        })
        return d

    def pre_run_check(self, project_update, **kwargs):
        '''
        Hook for checking project update before running.
        '''
        if not super(RunProjectUpdate, self).pre_run_check(project_update, **kwargs):
            return False
        # FIXME: Check if project update is blocked by any jobs that are being run.
        project = project_update.project
        if project.jobs.filter(status__in=('pending', 'waiting', 'running')):
            pass
        return True

    def post_run_hook(self, project_update):
        '''
        Hook for actions after project_update has completed.
        '''
        # Start any jobs waiting on this update to finish.

