# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import ConfigParser
import cStringIO
from distutils.version import StrictVersion as Version
import json
import logging
import os
import pipes
import re
import stat
import tempfile
import time
import traceback
import urlparse
import uuid

import dateutil.parser

# Pexpect
import pexpect

# ZMQ
import zmq

# Celery
from celery import Task, task
from djcelery.models import PeriodicTask

# Django
from django.conf import settings
from django.db import transaction, DatabaseError
from django.utils.datastructures import SortedDict
from django.utils.timezone import now

# AWX
from awx.main.models import * # Job, JobEvent, ProjectUpdate, InventoryUpdate, Schedule, UnifiedJobTemplate
from awx.main.utils import get_ansible_version, decrypt_field, update_scm_url, ignore_inventory_computed_fields

__all__ = ['RunJob', 'RunProjectUpdate', 'RunInventoryUpdate', 'handle_work_error', 'update_inventory_computed_fields']

HIDDEN_PASSWORD = '**********'

logger = logging.getLogger('awx.main.tasks')

# FIXME: Cleanly cancel task when celery worker is stopped.

@task(bind=True)
def tower_periodic_scheduler(self):
    def get_last_run():
        if not os.path.exists(settings.SCHEDULE_METADATA_LOCATION):
            return None
        fd = open(settings.SCHEDULE_METADATA_LOCATION)
        try:
            last_run = dateutil.parser.parse(fd.read())
            return last_run
        except Exception, e:
            return None
    def write_last_run(last_run):
        fd = open(settings.SCHEDULE_METADATA_LOCATION, 'w')
        fd.write(last_run.isoformat())
        fd.close()

    run_now = now()
    last_run = get_last_run()
    if not last_run:
        logger.debug("First run time")
        write_last_run(run_now)
        return
    logger.debug("Last run was: %s", last_run)
    write_last_run(run_now)
    old_schedules = Schedule.objects.enabled().before(last_run)
    for schedule in old_schedules:
        schedule.save()
    schedules = Schedule.objects.enabled().between(last_run, run_now)
    for schedule in schedules:
        template = schedule.unified_job_template
        schedule.save() # To update next_run timestamp.
        new_unified_job = template.create_unified_job(launch_type='scheduled', schedule=schedule)
        can_start = new_unified_job.signal_start()
        if not can_start:
            new_unified_job.status = 'failed'
            new_unified_job.job_explanation = "Scheduled job could not start because it was not in the right state or required manual credentials"
            new_unified_job.save(update_fields=['job_status', 'job_explanation'])
            new_unified_job.socketio_emit_status("failed")

@task()
def notify_task_runner(metadata_dict):
    signal_context = zmq.Context()
    signal_socket = signal_context.socket(zmq.PUSH)
    signal_socket.connect(settings.TASK_COMMAND_PORT)
    signal_socket.send_json(metadata_dict)

@task(bind=True)
def handle_work_error(self, task_id, subtasks=None):
    print('Executing error task id %s, subtasks: %s' % (str(self.request.id), str(subtasks)))
    first_task = None
    first_task_type = ''
    first_task_name = ''
    if subtasks is not None:
        for each_task in subtasks:
            instance_name = ''
            if each_task['type'] == 'project_update':
                instance = ProjectUpdate.objects.get(id=each_task['id'])
                instance_name = instance.project.name
            elif each_task['type'] == 'inventory_update':
                instance = InventoryUpdate.objects.get(id=each_task['id'])
                instance_name = instance.inventory_source.inventory.name
            elif each_task['type'] == 'job':
                instance = Job.objects.get(id=each_task['id'])
                instance_name = instance.job_template.name
            else:
                # Unknown task type
                break
            if first_task is None:
                first_task = instance
                first_task_type = each_task['type']
                first_task_name = instance_name
            if instance.celery_task_id != task_id:
                instance.status = 'failed'
                instance.failed = True
                instance.job_explanation = "Previous Task Failed: %s for %s with celery task id: %s" % \
                    (first_task_type, first_task_name, task_id)
                instance.save()
                instance.socketio_emit_status("failed")

@task()
def update_inventory_computed_fields(inventory_id, should_update_hosts=True):
    '''
    Signal handler and wrapper around inventory.update_computed_fields to
    prevent unnecessary recursive calls.
    '''
    i = Inventory.objects.filter(id=inventory_id)
    if not i.exists():
        logger.error("Update Inventory Computed Fields failed due to missing inventory: " + str(inventory_id))
    i = i[0]
    i.update_computed_fields(update_hosts=should_update_hosts)

class BaseTask(Task):

    name = None
    model = None
    abstract = True

    @transaction.commit_on_success
    def update_model(self, pk, **updates):
        '''
        Reload model from database and update the given fields.
        '''
        output_replacements = updates.pop('output_replacements', None) or []
        # Commit outstanding transaction so that we fetch the latest object
        # from the database.
        transaction.commit()
        for retry_count in xrange(5):
            try:
                instance = self.model.objects.get(pk=pk)
                if updates:
                    update_fields = ['modified']
                    for field, value in updates.items():
                        if field in ('result_stdout', 'result_traceback'):
                            for srch, repl in output_replacements:
                                value = value.replace(srch, repl)
                        setattr(instance, field, value)
                        update_fields.append(field)
                        if field == 'status':
                            update_fields.append('failed')
                    instance.save(update_fields=update_fields)
                    transaction.commit()
                return instance
            except DatabaseError as e:
                transaction.rollback()
                logger.debug('Database error updating %s, retrying in 5 '
                             'seconds (retry #%d): %s',
                             self.model._meta.object_name, retry_count + 1, e)
                time.sleep(5)
        else:
            logger.error('Failed to update %s after %d retries.',
                         self.model._meta.object_name, retry_count)

    def signal_finished(self, pk):
        pass
        # notify_task_runner(dict(complete=pk))

    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_private_data(self, instance, **kwargs):
        '''
        Return any private data that needs to be written to a temporary file
        for this task.
        '''

    def build_private_data_file(self, instance, **kwargs):
        '''
        Create a temporary file containing the private data.
        '''
        private_data = self.build_private_data(instance, **kwargs)
        if private_data is not None:
            handle, path = tempfile.mkstemp()
            f = os.fdopen(handle, 'w')
            f.write(private_data)
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
        # Update PYTHONPATH to use local site-packages.
        python_paths = env.get('PYTHONPATH', '').split(os.pathsep)
        local_site_packages = self.get_path_to('..', 'lib', 'site-packages')
        if local_site_packages not in python_paths:
            python_paths.insert(0, local_site_packages)
        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        return env

    def build_safe_env(self, instance, **kwargs):
        '''
        Build environment dictionary, hiding potentially sensitive information
        such as passwords or keys.
        '''
        hidden_re = re.compile(r'API|TOKEN|KEY|SECRET|PASS', re.I)
        urlpass_re = re.compile(r'^.*?://.?:(.*?)@.*?$')
        env = self.build_env(instance, **kwargs)
        for k,v in env.items():
            if k in ('REST_API_URL', 'AWS_ACCESS_KEY', 'AWS_ACCESS_KEY_ID'):
                continue
            elif k.startswith('ANSIBLE_'):
                continue
            elif hidden_re.search(k):
                env[k] = HIDDEN_PASSWORD
            elif urlpass_re.match(v):
                env[k] = urlpass_re.sub(HIDDEN_PASSWORD, v)
        return env

    def args2cmdline(self, *args):
        return ' '.join([pipes.quote(a) for a in args])

    def wrap_args_with_ssh_agent(self, args, ssh_key_path):
        if ssh_key_path:
            cmd = ' && '.join([self.args2cmdline('ssh-add', ssh_key_path),
                               self.args2cmdline(*args)])
            args = ['ssh-agent', 'sh', '-c', cmd]
        return args

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
        Return a dictionary where keys are strings or regular expressions for
        prompts, and values are password lookup keys (keys that are returned
        from build_passwords).
        '''
        return SortedDict()

    def run_pexpect(self, instance, args, cwd, env, passwords, stdout_handle,
                    output_replacements=None):
        '''
        Run the given command using pexpect to capture output and provide
        passwords when requested.
        '''
        logfile = stdout_handle
        logfile_pos = logfile.tell()
        child = pexpect.spawnu(args[0], args[1:], cwd=cwd, env=env)
        child.logfile_read = logfile
        canceled = False
        last_stdout_update = time.time()
        idle_timeout = self.get_idle_timeout()
        expect_list = []
        expect_passwords = {}
        pexpect_timeout = getattr(settings, 'PEXPECT_TIMEOUT', 5)
        for n, item in enumerate(self.get_password_prompts().items()):
            expect_list.append(item[0])
            expect_passwords[n] = passwords.get(item[1], '') or ''
        expect_list.extend([pexpect.TIMEOUT, pexpect.EOF])
        instance = self.update_model(instance.pk, status='running',
                                     output_replacements=output_replacements)
        while child.isalive():
            result_id = child.expect(expect_list, timeout=pexpect_timeout)
            if result_id in expect_passwords:
                child.sendline(expect_passwords[result_id])
            if logfile_pos != logfile.tell():
                logfile_pos = logfile.tell()
                last_stdout_update = time.time()
            # Refresh model instance from the database (to check cancel flag).
            instance = self.update_model(instance.pk)
            if instance.cancel_flag:
                child.terminate(canceled)
                canceled = True
            if idle_timeout and (time.time() - last_stdout_update) > idle_timeout:
                child.close(True)
                canceled = True
        if canceled:
            return 'canceled'
        elif child.exitstatus == 0:
            return 'successful'
        else:
            return 'failed'

    def post_run_hook(self, instance, **kwargs):
        '''
        Hook for any steps to run after job/task is complete.
        '''

    def run(self, pk, **kwargs):
        '''
        Run the job/task and capture its output.
        '''
        instance = self.update_model(pk, status='running', celery_task_id=self.request.id)
        instance.socketio_emit_status("running")
        status, tb = 'error', ''
        output_replacements = []
        try:
            if instance.cancel_flag:
                instance = self.update_model(instance.pk, status='canceled')
            if instance.status != 'running':
                if hasattr(settings, 'CELERY_UNIT_TEST'):
                    return
                else:
                    # Stop the task chain and prevent starting the job if it has
                    # already been canceled.
                    instance = self.update_model(pk)
                    status = instance.status
                    raise RuntimeError('not starting %s task' % instance.status)
            # Fetch ansible version once here to support version-dependent features.
            kwargs['ansible_version'] = get_ansible_version()
            kwargs['private_data_file'] = self.build_private_data_file(instance, **kwargs)
            kwargs['passwords'] = self.build_passwords(instance, **kwargs)
            args = self.build_args(instance, **kwargs)
            safe_args = self.build_safe_args(instance, **kwargs)
            output_replacements = self.build_output_replacements(instance, **kwargs)
            cwd = self.build_cwd(instance, **kwargs)
            env = self.build_env(instance, **kwargs)
            safe_env = self.build_safe_env(instance, **kwargs)
            if not os.path.exists(settings.JOBOUTPUT_ROOT):
                os.makedirs(settings.JOBOUTPUT_ROOT)
            stdout_filename = os.path.join(settings.JOBOUTPUT_ROOT, str(uuid.uuid1()) + ".out")
            stdout_handle = open(stdout_filename, 'w')
            instance = self.update_model(pk, job_args=json.dumps(safe_args),
                                         job_cwd=cwd, job_env=safe_env, result_stdout_file=stdout_filename)
            status = self.run_pexpect(instance, args, cwd, env, kwargs['passwords'], stdout_handle)
        except Exception:
            if status != 'canceled':
                tb = traceback.format_exc()
        finally:
            if kwargs.get('private_data_file', ''):
                try:
                    os.remove(kwargs['private_data_file'])
                except OSError:
                    pass
                try:
                    stdout_handle.close()
                except Exception:
                    pass
        instance = self.update_model(pk, status=status, result_traceback=tb,
                                     output_replacements=output_replacements)
        self.post_run_hook(instance, **kwargs)
        instance.socketio_emit_status(status)
        if status != 'successful' and not hasattr(settings, 'CELERY_UNIT_TEST'):
            # Raising an exception will mark the job as 'failed' in celery
            # and will stop a task chain from continuing to execute
            if status == 'canceled':
                raise Exception("Task %s(pk:%s) was canceled" % (str(self.model.__class__), str(pk)))
            else:
                raise Exception("Task %s(pk:%s) encountered an error" % (str(self.model.__class__), str(pk)))
        if not hasattr(settings, 'CELERY_UNIT_TEST'):
            self.signal_finished(pk)


class RunJob(BaseTask):
    '''
    Celery task to run a job using ansible-playbook.
    '''

    name = 'awx.main.tasks.run_job'
    model = Job

    def build_private_data(self, job, **kwargs):
        '''
        Return SSH private key data needed for this job (only if stored in DB
        as ssh_key_data).
        '''
        credential = getattr(job, 'credential', None)
        if credential:
            return decrypt_field(credential, 'ssh_key_data') or None

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user, sudo
        and ansible-vault.
        '''
        passwords = super(RunJob, self).build_passwords(job, **kwargs)
        creds = job.credential
        if creds:
            for field in ('ssh_key_unlock', 'ssh_password', 'sudo_password', 'vault_password'):
                if field == 'ssh_password':
                    value = kwargs.get(field, decrypt_field(creds, 'password'))
                else:
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
        env['CALLBACK_CONSUMER_PORT'] = settings.CALLBACK_CONSUMER_PORT
        if getattr(settings, 'JOB_CALLBACK_DEBUG', False):
            env['JOB_CALLBACK_DEBUG'] = '2'
        elif settings.DEBUG:
            env['JOB_CALLBACK_DEBUG'] = '1'

        # When using Ansible >= 1.3, allow the inventory script to include host
        # variables inline via ['_meta']['hostvars'].
        try:
            if Version(kwargs['ansible_version']) >= Version('1.3'):
                env['INVENTORY_HOSTVARS'] = str(True)
        except ValueError:
            pass

        # Set environment variables for cloud credentials.
        cloud_cred = job.cloud_credential
        if cloud_cred and cloud_cred.kind == 'aws':
            env['AWS_ACCESS_KEY'] = cloud_cred.username
            env['AWS_SECRET_KEY'] = decrypt_field(cloud_cred, 'password')
            # FIXME: Add EC2_URL, maybe EC2_REGION!
        elif cloud_cred and cloud_cred.kind == 'rax':
            env['RAX_USERNAME'] = cloud_cred.username
            env['RAX_API_KEY'] = decrypt_field(cloud_cred, 'password')

        return env

    def build_args(self, job, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.credential
        ssh_username, sudo_username = '', ''
        if creds:
            ssh_username = kwargs.get('username', creds.username)
            sudo_username = kwargs.get('sudo_username', creds.sudo_username)
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible-playbook's default of using
        # the current user.
        ssh_username = ssh_username or 'root'
        inventory_script = self.get_path_to('..', 'plugins', 'inventory',
                                            'awxrest.py')
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

        # When using Ansible >= 1.5, support prompting for a vault password.
        try:
            if Version(kwargs['ansible_version']) >= Version('1.5'):
                if 'vault_password' in kwargs.get('passwords', {}):
                    args.append('--ask-vault-pass')
        except ValueError:
            pass

        # If private key isn't encrypted, pass the path on the command line.
        ssh_key_path = kwargs.get('private_data_file', '')
        use_ssh_agent = bool(creds and creds.has_encrypted_ssh_key_data)
        if ssh_key_path and not use_ssh_agent:
            args.append('--private-key=%s' % ssh_key_path)

        if job.forks:  # FIXME: Max limit?
            args.append('--forks=%d' % job.forks)
        if job.limit:
            args.extend(['-l', job.limit])
        if job.verbosity:
            args.append('-%s' % ('v' * min(3, job.verbosity)))
        if job.job_tags:
            args.extend(['-t', job.job_tags])

        # Define special extra_vars for Tower, combine with job.extra_vars.
        extra_vars = {
            'tower_job_id': job.pk,
            'tower_job_launch_type': job.launch_type,
        }
        if job.job_template and job.job_template.active:
            extra_vars.update({
                'tower_job_template_id': job.job_template.pk,
                'tower_job_template_name': job.job_template.name,
            })
        if job.created_by and job.created_by.is_active:
            extra_vars.update({
                'tower_user_id': job.created_by.pk,
                'tower_user_name': job.created_by.username,
            })
        if job.extra_vars_dict:
            extra_vars.update(job.extra_vars_dict)
        args.extend(['-e', json.dumps(extra_vars)])

        # Add path to playbook (relative to project.local_path).
        args.append(job.playbook)

        # If ssh unlock password is needed, run using ssh-agent.
        if ssh_key_path and use_ssh_agent:
            args = self.wrap_args_with_ssh_agent(args, ssh_key_path)

        return args

    def build_cwd(self, job, **kwargs):
        cwd = job.project.get_project_path()
        if not cwd:
            root = settings.PROJECTS_ROOT
            raise RuntimeError('project local_path %s cannot be found in %s' %
                               (job.project.local_path, root))
        return cwd

    def get_idle_timeout(self):
        return getattr(settings, 'JOB_RUN_IDLE_TIMEOUT', None)

    def get_password_prompts(self):
        d = super(RunJob, self).get_password_prompts()
        d[re.compile(r'^Enter passphrase for .*:\s*?$', re.M)] = 'ssh_key_unlock'
        d[re.compile(r'^Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        d[re.compile(r'^sudo password.*:\s*?$', re.M)] = 'sudo_password'
        d[re.compile(r'^SSH password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'^Password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'^Vault password:\s*?$', re.M)] = 'vault_password'
        return d

    def post_run_hook(self, job, **kwargs):
        '''
        Hook for actions to run after job/task has completed.
        '''
        super(RunJob, self).post_run_hook(job, **kwargs)
        try:
            inventory = job.inventory
        except Inventory.DoesNotExist:
            pass
        else:
            update_inventory_computed_fields.delay(inventory.id, True)
        # Update job event fields after job has completed (only when using REST
        # API callback).
        if not settings.CALLBACK_CONSUMER_PORT:
            for job_event in job.job_events.order_by('pk'):
                job_event.save(post_process=True)


class RunProjectUpdate(BaseTask):

    name = 'awx.main.tasks.run_project_update'
    model = ProjectUpdate

    def build_private_data(self, project_update, **kwargs):
        '''
        Return SSH private key data needed for this project update.
        '''
        if project_update.credential:
            return decrypt_field(project_update.credential, 'ssh_key_data') or None

    def build_passwords(self, project_update, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update,
                                                                  **kwargs)
        if project_update.credential:
            passwords['scm_key_unlock'] = decrypt_field(project_update.credential,
                                                        'ssh_key_unlock')
            passwords['scm_username'] = project_update.credential.username
            passwords['scm_password'] = decrypt_field(project_update.credential,
                                                     'password')
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
        scm_type = project_update.scm_type
        scm_url = update_scm_url(scm_type, project_update.scm_url,
                                 check_special_cases=False)
        scm_url_parts = urlparse.urlsplit(scm_url)
        scm_username = kwargs.get('passwords', {}).get('scm_username', '')
        scm_password = kwargs.get('passwords', {}).get('scm_password', '')
        # Prefer the username/password in the URL, if provided.
        scm_username = scm_url_parts.username or scm_username or ''
        scm_password = scm_url_parts.password or scm_password or ''
        if scm_username:
            if scm_type == 'svn':
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = scm_password
                scm_password = False
                if scm_url_parts.scheme != 'svn+ssh':
                    scm_username = False
            elif scm_url_parts.scheme == 'ssh':
                scm_password = False
            scm_url = update_scm_url(scm_type, scm_url, scm_username,
                                     scm_password)

        # When using Ansible >= 1.5, pass the extra accept_hostkey parameter to
        # the git module.
        if scm_type == 'git' and scm_url_parts.scheme == 'ssh':
            try:
                if Version(kwargs['ansible_version']) >= Version('1.5'):
                    extra_vars['scm_accept_hostkey'] = 'true'
            except ValueError:
                pass

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
        scm_url, extra_vars = self._build_scm_url_extra_vars(project_update,
                                                             **kwargs)
        scm_branch = project_update.scm_branch or {'hg': 'tip'}.get(project_update.scm_type, 'HEAD')
        extra_vars.update({
            'project_path': project_update.get_project_path(check_if_exists=False),
            'scm_type': project_update.scm_type,
            'scm_url': scm_url,
            'scm_branch': scm_branch,
            'scm_clean': project_update.scm_clean,
            'scm_delete_on_update': project_update.scm_delete_on_update,
        })
        args.extend(['-e', json.dumps(extra_vars)])
        args.append('project_update.yml')

        # If using an SSH key, run using ssh-agent.
        ssh_key_path = kwargs.get('private_data_file', '')
        if ssh_key_path:
            args = self.wrap_args_with_ssh_agent(args, ssh_key_path)

        return args

    def build_safe_args(self, project_update, **kwargs):
        pwdict = dict(kwargs.get('passwords', {}).items())
        for pw_name, pw_val in pwdict.items():
            if pw_name in ('', 'yes', 'no', 'scm_username'):
                continue
            pwdict[pw_name] = HIDDEN_PASSWORD
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
        scm_username = kwargs.get('passwords', {}).get('scm_username', '')
        scm_password = kwargs.get('passwords', {}).get('scm_password', '')
        pwdict = dict(kwargs.get('passwords', {}).items())
        for pw_name, pw_val in pwdict.items():
            if pw_name in ('', 'yes', 'no', 'scm_username'):
                continue
            pwdict[pw_name] = HIDDEN_PASSWORD
        kwargs['passwords'] = pwdict
        after_url = self._build_scm_url_extra_vars(project_update,
                                                   **kwargs)[0]
        if after_url != before_url:
            output_replacements.append((before_url, after_url))
        if project_update.scm_type == 'svn' and scm_username and scm_password:
            d_before = {
                'username': scm_username,
                'password': scm_password,
            }
            d_after = {
                'username': scm_username,
                'password': HIDDEN_PASSWORD,
            }
            pattern1 = "username=\"%(username)s\" password=\"%(password)s\""
            pattern2 = "--username '%(username)s' --password '%(password)s'"
            output_replacements.append((pattern1 % d_before, pattern1 % d_after))
            output_replacements.append((pattern2 % d_before, pattern2 % d_after))
        return output_replacements

    def get_password_prompts(self):
        d = super(RunProjectUpdate, self).get_password_prompts()
        d[re.compile(r'^Username for.*:\s*?$', re.M)] = 'scm_username'
        d[re.compile(r'^Password for.*:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'^Password:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'^\S+?@\S+?\'s\s+?password:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'^Enter passphrase for .*:\s*?$', re.M)] = 'scm_key_unlock'
        d[re.compile(r'^Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        # FIXME: Configure whether we should auto accept host keys?
        d[re.compile(r'^Are you sure you want to continue connecting \(yes/no\)\?\s*?$', re.M)] = 'yes'
        return d

    def get_idle_timeout(self):
        return getattr(settings, 'PROJECT_UPDATE_IDLE_TIMEOUT', None)


class RunInventoryUpdate(BaseTask):

    name = 'awx.main.tasks.run_inventory_update'
    model = InventoryUpdate

    def build_private_data(self, inventory_update, **kwargs):
        '''
        Return private data needed for inventory update.
        '''
        cp = ConfigParser.ConfigParser()
        # Build custom ec2.ini for ec2 inventory script to use.
        if inventory_update.source == 'ec2':
            section = 'ec2'
            cp.add_section(section)
            ec2_opts = dict(inventory_update.source_vars_dict.items())
            regions = inventory_update.source_regions or 'all'
            regions = ','.join([x.strip() for x in regions.split(',')])
            regions_blacklist = ','.join(settings.EC2_REGIONS_BLACKLIST)
            ec2_opts['regions'] = regions
            ec2_opts.setdefault('regions_exclude', regions_blacklist)
            ec2_opts.setdefault('destination_variable', 'public_dns_name')
            ec2_opts.setdefault('vpc_destination_variable', 'ip_address')
            ec2_opts.setdefault('route53', 'False')
            ec2_opts['cache_path'] = tempfile.mkdtemp(prefix='awx_ec2_')
            ec2_opts['cache_max_age'] = '300'
            for k,v in ec2_opts.items():
                cp.set(section, k, str(v))
        # Build pyrax creds INI for rax inventory script.
        elif inventory_update.source == 'rax':
            section = 'rackspace_cloud'
            cp.add_section(section)
            credential = inventory_update.credential
            if credential:
                cp.set(section, 'username', credential.username)
                cp.set(section, 'api_key', decrypt_field(credential,
                                                         'password'))
        # Return INI content.
        if cp.sections():
            f = cStringIO.StringIO()
            cp.write(f)
            return f.getvalue()

    def build_passwords(self, inventory_update, **kwargs):
        '''
        Build a dictionary of passwords inventory sources.
        '''
        passwords = super(RunInventoryUpdate, self).build_passwords(inventory_update,
                                                                    **kwargs)
        credential = inventory_update.credential
        if credential:
            passwords['source_username'] = credential.username
            passwords['source_password'] = decrypt_field(credential, 'password')
        return passwords

    def build_env(self, inventory_update, **kwargs):
        '''
        Build environment dictionary for inventory import.
        '''
        env = super(RunInventoryUpdate, self).build_env(inventory_update, **kwargs)
        # Pass inventory source ID to inventory script.
        env['INVENTORY_SOURCE_ID'] = str(inventory_update.inventory_source_id)
        # Set environment variables specific to each source.
        if inventory_update.source == 'ec2':
            env['AWS_ACCESS_KEY_ID'] = kwargs.get('passwords', {}).get('source_username', '')
            env['AWS_SECRET_ACCESS_KEY'] = kwargs.get('passwords', {}).get('source_password', '')
            env['EC2_INI_PATH'] = kwargs.get('private_data_file', '')
        elif inventory_update.source == 'rax':
            env['RAX_CREDS_FILE'] = kwargs.get('private_data_file', '')
            env['RAX_REGION'] = inventory_update.source_regions or 'all'
            # Set this environment variable so the vendored package won't
            # complain about not being able to determine its version number.
            env['PBR_VERSION'] = '0.5.21'
        elif inventory_update.source == 'file':
            # FIXME: Parse source_env to dict, update env.
            pass
        return env

    def build_args(self, inventory_update, **kwargs):
        '''
        Build command line argument list for running inventory import.
        '''
        inventory_source = inventory_update.inventory_source
        inventory = inventory_source.group.inventory
        args = ['awx-manage', 'inventory_import']
        args.extend(['--inventory-id', str(inventory.pk)])
        if inventory_update.overwrite:
            args.append('--overwrite')
        if inventory_update.overwrite_vars:
            args.append('--overwrite-vars')
        args.append('--source')
        if inventory_update.source == 'ec2':
            ec2_path = self.get_path_to('..', 'plugins', 'inventory', 'ec2.py')
            args.append(ec2_path)
            args.extend(['--enabled-var', settings.EC2_ENABLED_VAR])
            args.extend(['--enabled-value', settings.EC2_ENABLED_VALUE])
            args.extend(['--group-filter', settings.EC2_GROUP_FILTER])
            args.extend(['--host-filter', settings.EC2_HOST_FILTER])
            if settings.EC2_EXCLUDE_EMPTY_GROUPS:
                args.append('--exclude-empty-groups')
            if settings.EC2_INSTANCE_ID_VAR:
                args.extend(['--instance-id-var', settings.EC2_INSTANCE_ID_VAR])
        elif inventory_update.source == 'rax':
            rax_path = self.get_path_to('..', 'plugins', 'inventory', 'rax.py')
            args.append(rax_path)
            args.extend(['--enabled-var', settings.RAX_ENABLED_VAR])
            args.extend(['--enabled-value', settings.RAX_ENABLED_VALUE])
            args.extend(['--group-filter', settings.RAX_GROUP_FILTER])
            args.extend(['--host-filter', settings.RAX_HOST_FILTER])
            if settings.RAX_EXCLUDE_EMPTY_GROUPS:
                args.append('--exclude-empty-groups')
            if settings.RAX_INSTANCE_ID_VAR:
                args.extend(['--instance-id-var', settings.RAX_INSTANCE_ID_VAR])
        elif inventory_update.source == 'file':
            args.append(inventory_update.source_path)
        verbosity = getattr(settings, 'INVENTORY_UPDATE_VERBOSITY', 1)
        args.append('-v%d' % verbosity)
        if settings.DEBUG:
            args.append('--traceback')
        return args

    def build_cwd(self, inventory_update, **kwargs):
        return self.get_path_to('..', 'plugins', 'inventory')

    def get_idle_timeout(self):
        return getattr(settings, 'INVENTORY_UPDATE_IDLE_TIMEOUT', None)
