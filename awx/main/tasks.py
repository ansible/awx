# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import cStringIO
import datetime
import distutils.version
import json
import logging
import os
import re
import subprocess
import stat
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
from django.utils.timezone import now

# AWX
from awx.main.models import Job, ProjectUpdate
from awx.main.utils import get_ansible_version, decrypt_field, update_scm_url

__all__ = ['RunJob', 'RunProjectUpdate']

logger = logging.getLogger('awx.main.tasks')

# FIXME: Cleanly cancel task when celery worker is stopped.

class BaseTask(Task):
    
    name = None
    model = None

    def update_model(self, pk, **updates):
        '''
        Reload model from database and update the given fields.
        '''
        output_replacements = updates.pop('output_replacements', None) or []
        instance = self.model.objects.get(pk=pk)
        if updates:
            update_fields = []
            for field, value in updates.items():
                if field in ('result_stdout', 'result_traceback'):
                    for srch, repl in output_replacements:
                        value = value.replace(srch, repl)
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
            handle, path = tempfile.mkstemp()
            f = os.fdopen(handle, 'w')
            f.write(ssh_key_data)
            f.close()
            os.chmod(path, stat.S_IRUSR|stat.S_IWUSR)
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

    def build_safe_args(self, instance, **kwargs):
        return self.build_args(instance, **kwargs)

    def build_cwd(self, instance, **kwargs):
        raise NotImplementedError

    def build_output_replacements(self, instance, **kwargs):
        return []

    def get_idle_timeout(self):
        return None

    def get_password_prompts(self):
        '''
        Return a dictionary of prompt regular expressions and password lookup
        keys.
        '''
        return {
            r'Enter passphrase for .*:': 'ssh_key_unlock',
            r'Bad passphrase, try again for .*:': '',
        }

    def run_pexpect(self, instance, args, cwd, env, passwords,
                    output_replacements=None):
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
        idle_timeout = self.get_idle_timeout()
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
            updates = {'status': 'running',
                       'output_replacements': output_replacements}
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
            if idle_timeout and (time.time() - last_stdout_update) > idle_timeout:
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

    def post_run_hook(self, instance, **kwargs):
        '''
        Hook for actions to run after job/task has completed.
        '''
        # Cleanup instances that appear to be stuck.
        try:
            stuck_task_timeout = int(getattr(settings, 'STUCK_TASK_TIMEOUT', 300))
        except (TypeError, ValueError):
            stuck_task_timeout = 0
        if stuck_task_timeout <= 0:
            return
        # Never less than 30 seconds so we're not messing with active tasks.
        stuck_task_timeout = max(stuck_task_timeout, 30)
        cutoff = now() - datetime.timedelta(seconds=stuck_task_timeout)
        qs = self.model.objects.filter(status__in=('new', 'waiting', 'running'))
        qs = qs.filter(modified__lt=cutoff)
        for obj in qs:
            # If new, created but never started.  If waiting or running, the
            # modified timestamp should updated regularly, else the task is
            # probably stuck.
            # If pending, we could be started but celeryd is not running, or
            # we're waiting for an open slot in celeryd -- in either case we
            # shouldn't necessarily cancel the task.  Slim chance that somehow
            # the task was started, picked up by celery, but hit an error
            # before we could update the status.
            obj.status = 'canceled'
            obj.result_traceback += '\nCanceled stuck %s.' % unicode(self.model._meta.verbose_name)
            obj.save(update_fields=['status', 'result_traceback'])

    def run(self, pk, **kwargs):
        '''
        Run the job/task using ansible-playbook and capture its output.
        '''
        instance = self.update_model(pk)
        if not self.pre_run_check(instance, **kwargs):
            return
        instance = self.update_model(pk, status='running')
        status, stdout, tb = 'error', '', ''
        output_replacements = []
        try:
            kwargs['ssh_key_path'] = self.build_ssh_key_path(instance, **kwargs)
            kwargs['passwords'] = self.build_passwords(instance, **kwargs)
            args = self.build_args(instance, **kwargs)
            safe_args = self.build_safe_args(instance, **kwargs)
            output_replacements = self.build_output_replacements(instance, **kwargs)
            cwd = self.build_cwd(instance, **kwargs)
            env = self.build_env(instance, **kwargs)
            instance = self.update_model(pk, job_args=json.dumps(safe_args),
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
                                     result_traceback=tb,
                                     output_replacements=output_replacements)
        self.post_run_hook(instance, **kwargs)

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
        project_update = None
        while True:
            pk = job.pk
            if job.status in ('pending', 'waiting'):
                project = job.project
                pu_qs = project.project_updates.filter(status__in=('pending', 'running'))
                # Refresh the current project_update instance (if set).
                if project_update:
                    try:
                        project_update = project.project_updates.filter(pk=project_update.pk)[0]
                    except IndexError:
                        msg = 'Unable to check project update.'
                        job = self.update_model(pk, status='error',
                                                result_traceback=msg)
                        return False

                # If the job needs to update the project first (and there is no
                # specific project update defined).
                if not project_update and project.scm_update_on_launch:
                    job = self.update_model(pk, status='waiting')
                    try:
                        project_update = pu_qs[0]
                    except IndexError:
                        kw = dict([(k,v) for k,v in kwargs.items()
                                   if k.startswith('scm_')])
                        project_update = project.update(**kw)
                        if not project_update:
                            msg = 'Unable to update project before launch.'
                            job = self.update_model(pk, status='error',
                                                    result_traceback=msg)
                            return False
                    #print 'job %d waiting on project update %d' % (pk, project_update.pk)
                    time.sleep(2.0)
                # If project update has failed, abort the job.
                elif project_update and project_update.failed:
                    msg = 'Project update failed with status = %s.' % project_update.status
                    job = self.update_model(pk, status='error',
                                            result_traceback=msg)
                    return False
                # Check if blocked by any other active project updates.
                elif pu_qs.count():
                    #print 'job %d waiting on' % pk, pu_qs
                    job = self.update_model(pk, status='waiting')
                    time.sleep(4.0)
                # Otherwise continue running the job.
                else:
                    job = self.update_model(pk, status='pending')
                    return True
            elif job.cancel_flag:
                job = self.update_model(pk, status='canceled')
                return False
            else:
                return False

class RunProjectUpdate(BaseTask):
    
    name = 'run_project_update'
    model = ProjectUpdate

    def build_passwords(self, project_update, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update,
                                                                  **kwargs)
        project = project_update.project
        value = kwargs.get('scm_key_unlock', decrypt_field(project, 'scm_key_unlock'))
        if value not in ('', 'ASK'):
            passwords['ssh_key_unlock'] = value
        passwords['scm_username'] = project.scm_username
        passwords['scm_password'] = kwargs.get('scm_password',
                                               decrypt_field(project, 'scm_password'))
        return passwords

    def build_env(self, project_update, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = super(RunProjectUpdate, self).build_env(project_update, **kwargs)
        env['ANSIBLE_ASK_PASS'] = str(False)
        env['ANSIBLE_ASK_SUDO_PASS'] = str(False)
        env['DISPLAY'] = '' # Prevent stupid password popup when running tests.
        return env

    def _build_scm_url_extra_vars(self, project_update, **kwargs):
        '''
        Helper method to build SCM url and extra vars with parameters needed
        for authentication.
        '''
        extra_vars = {}
        project = project_update.project
        scm_type = project.scm_type
        scm_url = update_scm_url(scm_type, project.scm_url)
        scm_url_parts = urlparse.urlsplit(scm_url)
        scm_username = kwargs.get('passwords', {}).get('scm_username', '')
        scm_username = scm_username or scm_url_parts.username or ''
        scm_password = kwargs.get('passwords', {}).get('scm_password', '')
        scm_password = scm_password or scm_url_parts.password or ''
        if scm_username and scm_password not in ('ASK', ''):
            if scm_type == 'svn':
                # FIXME: Need to somehow escape single/double quotes in username/password
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = scm_password
                scm_url = update_scm_url(scm_type, scm_url, False, False)
            elif scm_url_parts.scheme == 'ssh':
                scm_url = update_scm_url(scm_type, scm_url, scm_username, False)
            else:
                scm_url = update_scm_url(scm_type, scm_url, scm_username,
                                         scm_password)
        elif scm_username:
            if scm_type == 'svn':
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = ''
                scm_url = update_scm_url(scm_type, scm_url, False, False)
            else:  
                scm_url = update_scm_url(scm_type, scm_url, scm_username, False)
        return scm_url, extra_vars

    def build_args(self, project_update, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        args = ['ansible-playbook', '-i', 'localhost,']
        if getattr(settings, 'PROJECT_UPDATE_VVV', False):
            args.append('-vvv')
        else:
            args.append('-v')
        project = project_update.project
        scm_url, extra_vars = self._build_scm_url_extra_vars(project_update,
                                                             **kwargs)
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
        #print extra_vars
        args.extend(['-e', json.dumps(extra_vars)])
        args.append('project_update.yml')

        ssh_key_path = kwargs.get('ssh_key_path', '')
        if ssh_key_path:
            subcmds = [('ssh-add', ssh_key_path), args]
            cmd = ' && '.join([subprocess.list2cmdline(x) for x in subcmds])
            args = ['ssh-agent', 'sh', '-c', cmd]
        return args

    def build_safe_args(self, project_update, **kwargs):
        pwdict = dict(kwargs.get('passwords', {}).items())
        for pw_name, pw_val in pwdict.items():
            if pw_name in ('', 'yes', 'no', 'scm_username'):
                continue
            pwdict[pw_name] = '*'*len(pw_val)
        kwargs['passwords'] = pwdict
        return self.build_args(project_update, **kwargs)

    def build_cwd(self, project_update, **kwargs):
        return self.get_path_to('..', 'playbooks')

    def build_output_replacements(self, project_update, **kwargs):
        '''
        Return search/replace strings to prevent output URLs from showing
        sensitive passwords.
        '''
        output_replacements = []
        before_url = self._build_scm_url_extra_vars(project_update,
                                                    **kwargs)[0]
        scm_password = kwargs.get('passwords', {}).get('scm_password', '')
        pwdict = dict(kwargs.get('passwords', {}).items())
        for pw_name, pw_val in pwdict.items():
            if pw_name in ('', 'yes', 'no', 'scm_username'):
                continue
            pwdict[pw_name] = '*'*len(pw_val)
        kwargs['passwords'] = pwdict
        after_url = self._build_scm_url_extra_vars(project_update,
                                                   **kwargs)[0]
        if after_url != before_url:
            output_replacements.append((before_url, after_url))
        project = project_update.project
        if project.scm_type == 'svn' and project.scm_username and scm_password:
            d_before = {
                'username': project.scm_username,
                'password': scm_password,
            }
            d_after = {
                'username': project.scm_username,
                'password': '*'*len(scm_password),
            }
            pattern1 = "username=\"%(username)s\" password=\"%(password)s\""
            pattern2 = "--username '%(username)s' --password '%(password)s'"
            output_replacements.append((pattern1 % d_before, pattern1 % d_after))
            output_replacements.append((pattern2 % d_before, pattern2 % d_after))
        return output_replacements

    def get_password_prompts(self):
        d = super(RunProjectUpdate, self).get_password_prompts()
        d.update({
            re.compile(r'^Username for.*:\s*?$', re.M): 'scm_username',
            re.compile(r'^Password for.*:\s*?$', re.M): 'scm_password',
            re.compile(r'^Password:\s*?$', re.M): 'scm_password',
            re.compile(r'^\S+?@\S+?\'s\s+?password:\s*?$', re.M): 'scm_password',
            # FIXME: Configure whether we should auto accept host keys?
            re.compile(r'^Are you sure you want to continue connecting \(yes/no\)\?\s*?$', re.M): 'yes',
        })
        return d

    def get_idle_timeout(self):
        return getattr(settings, 'PROJECT_UPDATE_IDLE_TIMEOUT', None)

    def pre_run_check(self, project_update, **kwargs):
        '''
        Hook for checking project update before running.
        '''
        while True:
            pk = project_update.pk
            if project_update.status in ('pending', 'waiting'):
                # Check if project update is blocked by any jobs or other 
                # updates that are active.  Exclude job that is waiting for
                # this project update.
                project = project_update.project
                jobs_qs = project.jobs.filter(status__in=('pending', 'running'))
                pu_qs = project.project_updates.filter(status__in=('pending', 'running'))
                pu_qs = pu_qs.exclude(pk=project_update.pk)
                if jobs_qs.count() or pu_qs.count():
                    #print 'project update %d waiting on' % pk, jobs_qs, pu_qs
                    project_update = self.update_model(pk, status='waiting')
                    time.sleep(4.0)
                else:
                    project_update = self.update_model(pk, status='pending')
                    return True
            elif project_update.cancel_flag:
                project_update = self.update_model(pk, status='canceled')
                return False
            else:
                return False
