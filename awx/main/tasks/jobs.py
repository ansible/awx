# Python
from collections import OrderedDict
from distutils.dir_util import copy_tree
import errno
import functools
import fcntl
import json
import logging
import os
from pathlib import Path
import shutil
import stat
import yaml
import tempfile
import traceback
import time
import urllib.parse as urlparse
from uuid import uuid4


# Django
from django.conf import settings
from django.db import transaction


# Runner
import ansible_runner

# GitPython
import git
from gitdb.exc import BadName as BadGitName


# AWX
from awx.main.constants import ACTIVE_STATES
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename
from awx.main.constants import (
    PRIVILEGE_ESCALATION_METHODS,
    STANDARD_INVENTORY_UPDATE_ENV,
    JOB_FOLDER_PREFIX,
    MAX_ISOLATED_PATH_COLON_DELIMITER,
)
from awx.main.models import (
    Instance,
    Inventory,
    InventorySource,
    Job,
    AdHocCommand,
    ProjectUpdate,
    InventoryUpdate,
    SystemJob,
    JobEvent,
    ProjectUpdateEvent,
    InventoryUpdateEvent,
    AdHocCommandEvent,
    SystemJobEvent,
    build_safe_env,
)
from awx.main.tasks.callback import (
    RunnerCallback,
    RunnerCallbackForAdHocCommand,
    RunnerCallbackForInventoryUpdate,
    RunnerCallbackForProjectUpdate,
    RunnerCallbackForSystemJob,
)
from awx.main.tasks.receptor import AWXReceptorJob
from awx.main.exceptions import AwxTaskError, PostRunError, ReceptorNodeNotFound
from awx.main.utils.ansible import read_ansible_config
from awx.main.utils.execution_environments import CONTAINER_ROOT, to_container_path
from awx.main.utils.safe_yaml import safe_dump, sanitize_jinja
from awx.main.utils.common import (
    update_scm_url,
    extract_ansible_vars,
    get_awx_version,
    create_partition,
)
from awx.conf.license import get_license
from awx.main.utils.handlers import SpecialInventoryHandler
from awx.main.tasks.system import handle_success_and_failure_notifications, update_smart_memberships_for_inventory, update_inventory_computed_fields
from awx.main.utils.update_model import update_model
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger('awx.main.tasks.jobs')


def with_path_cleanup(f):
    @functools.wraps(f)
    def _wrapped(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        finally:
            for p in self.cleanup_paths:
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    elif os.path.exists(p):
                        os.remove(p)
                except OSError:
                    logger.exception("Failed to remove tmp file: {}".format(p))
            self.cleanup_paths = []

    return _wrapped


class BaseTask(object):
    model = None
    event_model = None
    abstract = True
    callback_class = RunnerCallback

    def __init__(self):
        self.cleanup_paths = []
        self.runner_callback = self.callback_class(model=self.model)

    def update_model(self, pk, _attempt=0, **updates):
        return update_model(self.model, pk, _attempt=0, **updates)

    def get_path_to(self, *args):
        """
        Return absolute path relative to this file.
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_execution_environment_params(self, instance, private_data_dir):
        """
        Return params structure to be executed by the container runtime
        """
        if settings.IS_K8S:
            return {}

        image = instance.execution_environment.image
        params = {
            "container_image": image,
            "process_isolation": True,
            "process_isolation_executable": "podman",  # need to provide, runner enforces default via argparse
            "container_options": ['--user=root'],
        }

        if settings.DEFAULT_CONTAINER_RUN_OPTIONS:
            params['container_options'].extend(settings.DEFAULT_CONTAINER_RUN_OPTIONS)

        if instance.execution_environment.credential:
            cred = instance.execution_environment.credential
            if all([cred.has_input(field_name) for field_name in ('host', 'username', 'password')]):
                host = cred.get_input('host')
                username = cred.get_input('username')
                password = cred.get_input('password')
                verify_ssl = cred.get_input('verify_ssl')
                params['container_auth_data'] = {'host': host, 'username': username, 'password': password, 'verify_ssl': verify_ssl}
            else:
                raise RuntimeError('Please recheck that your host, username, and password fields are all filled.')

        pull = instance.execution_environment.pull
        if pull:
            params['container_options'].append(f'--pull={pull}')

        params['container_volume_mounts'] = []
        if settings.DEFAULT_CONTAINER_VOLUME_MOUNTS:
            for this_path in settings.DEFAULT_CONTAINER_VOLUME_MOUNTS:
                params['container_volume_mounts'].append(this_path)

        if settings.AWX_ISOLATION_SHOW_PATHS:
            for this_path in settings.AWX_ISOLATION_SHOW_PATHS:
                # Verify if a mount path and SELinux context has been passed
                # Using z allows the dir to be mounted by multiple containers
                # Uppercase Z restricts access (in weird ways) to 1 container at a time
                if this_path.count(':') == MAX_ISOLATED_PATH_COLON_DELIMITER:
                    src, dest, scontext = this_path.split(':')
                    params['container_volume_mounts'].append(f'{src}:{dest}:{scontext}')
                elif this_path.count(':') == MAX_ISOLATED_PATH_COLON_DELIMITER - 1:
                    src, dest = this_path.split(':')
                    params['container_volume_mounts'].append(f'{src}:{dest}:z')
                else:
                    params['container_volume_mounts'].append(f'{this_path}:{this_path}:z')
        return params

    def build_private_data(self, instance, private_data_dir):
        """
        Return SSH private key data (only if stored in DB as ssh_key_data).
        Return structure is a dict of the form:
        """

    def build_private_data_dir(self, instance):
        """
        Create a temporary directory for job-related files.
        """
        path = tempfile.mkdtemp(prefix=JOB_FOLDER_PREFIX % instance.pk, dir=settings.AWX_ISOLATION_BASE_PATH)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        if settings.AWX_CLEANUP_PATHS:
            self.cleanup_paths.append(path)
        # Ansible runner requires that project exists,
        # and we will write files in the other folders without pre-creating the folder
        for subfolder in ('project', 'inventory', 'env'):
            runner_subfolder = os.path.join(path, subfolder)
            if not os.path.exists(runner_subfolder):
                os.mkdir(runner_subfolder)
        return path

    def build_private_data_files(self, instance, private_data_dir):
        """
        Creates temporary files containing the private data.
        Returns a dictionary i.e.,

        {
            'credentials': {
                <awx.main.models.Credential>: '/path/to/decrypted/data',
                <awx.main.models.Credential>: '/path/to/decrypted/data',
                ...
            },
            'certificates': {
                <awx.main.models.Credential>: /path/to/signed/ssh/certificate,
                <awx.main.models.Credential>: /path/to/signed/ssh/certificate,
                ...
            }
        }
        """
        private_data = self.build_private_data(instance, private_data_dir)
        private_data_files = {'credentials': {}}
        if private_data is not None:
            for credential, data in private_data.get('credentials', {}).items():
                # OpenSSH formatted keys must have a trailing newline to be
                # accepted by ssh-add.
                if 'OPENSSH PRIVATE KEY' in data and not data.endswith('\n'):
                    data += '\n'
                # For credentials used with ssh-add, write to a named pipe which
                # will be read then closed, instead of leaving the SSH key on disk.
                if credential and credential.credential_type.namespace in ('ssh', 'scm'):
                    try:
                        os.mkdir(os.path.join(private_data_dir, 'env'))
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise
                    path = os.path.join(private_data_dir, 'env', 'ssh_key')
                    ansible_runner.utils.open_fifo_write(path, data.encode())
                    private_data_files['credentials']['ssh'] = path
                # Ansible network modules do not yet support ssh-agent.
                # Instead, ssh private key file is explicitly passed via an
                # env variable.
                else:
                    handle, path = tempfile.mkstemp(dir=os.path.join(private_data_dir, 'env'))
                    f = os.fdopen(handle, 'w')
                    f.write(data)
                    f.close()
                    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
                private_data_files['credentials'][credential] = path
            for credential, data in private_data.get('certificates', {}).items():
                artifact_dir = os.path.join(private_data_dir, 'artifacts', str(self.instance.id))
                if not os.path.exists(artifact_dir):
                    os.makedirs(artifact_dir, mode=0o700)
                path = os.path.join(artifact_dir, 'ssh_key_data-cert.pub')
                with open(path, 'w') as f:
                    f.write(data)
                    f.close()
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        return private_data_files

    def build_passwords(self, instance, runtime_passwords):
        """
        Build a dictionary of passwords for responding to prompts.
        """
        return {
            'yes': 'yes',
            'no': 'no',
            '': '',
        }

    def build_extra_vars_file(self, instance, private_data_dir):
        """
        Build ansible yaml file filled with extra vars to be passed via -e@file.yml
        """

    def _write_extra_vars_file(self, private_data_dir, vars, safe_dict={}):
        env_path = os.path.join(private_data_dir, 'env')
        try:
            os.mkdir(env_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        path = os.path.join(env_path, 'extravars')
        handle = os.open(path, os.O_RDWR | os.O_CREAT, stat.S_IREAD | stat.S_IWRITE)
        f = os.fdopen(handle, 'w')
        if settings.ALLOW_JINJA_IN_EXTRA_VARS == 'always':
            f.write(yaml.safe_dump(vars))
        else:
            f.write(safe_dump(vars, safe_dict))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def add_awx_venv(self, env):
        env['VIRTUAL_ENV'] = settings.AWX_VENV_PATH
        if 'PATH' in env:
            env['PATH'] = os.path.join(settings.AWX_VENV_PATH, "bin") + ":" + env['PATH']
        else:
            env['PATH'] = os.path.join(settings.AWX_VENV_PATH, "bin")

    def build_env(self, instance, private_data_dir, private_data_files=None):
        """
        Build environment dictionary for ansible-playbook.
        """
        env = {}
        # Add ANSIBLE_* settings to the subprocess environment.
        for attr in dir(settings):
            if attr == attr.upper() and attr.startswith('ANSIBLE_'):
                env[attr] = str(getattr(settings, attr))
        # Also set environment variables configured in AWX_TASK_ENV setting.
        for key, value in settings.AWX_TASK_ENV.items():
            env[key] = str(value)

        env['AWX_PRIVATE_DATA_DIR'] = private_data_dir

        if self.instance.execution_environment is None:
            raise RuntimeError('The project could not sync because there is no Execution Environment.')

        return env

    def build_inventory(self, instance, private_data_dir):
        script_params = dict(hostvars=True, towervars=True)
        if hasattr(instance, 'job_slice_number'):
            script_params['slice_number'] = instance.job_slice_number
            script_params['slice_count'] = instance.job_slice_count
        script_data = instance.inventory.get_script_data(**script_params)
        # maintain a list of host_name --> host_id
        # so we can associate emitted events to Host objects
        self.runner_callback.host_map = {hostname: hv.pop('remote_tower_id', '') for hostname, hv in script_data.get('_meta', {}).get('hostvars', {}).items()}
        json_data = json.dumps(script_data)
        path = os.path.join(private_data_dir, 'inventory')
        fn = os.path.join(path, 'hosts')
        with open(fn, 'w') as f:
            os.chmod(fn, stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR)
            f.write('#! /usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint(%r)\n' % json_data)
        return fn

    def build_args(self, instance, private_data_dir, passwords):
        raise NotImplementedError

    def write_args_file(self, private_data_dir, args):
        env_path = os.path.join(private_data_dir, 'env')
        try:
            os.mkdir(env_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        path = os.path.join(env_path, 'cmdline')
        handle = os.open(path, os.O_RDWR | os.O_CREAT, stat.S_IREAD | stat.S_IWRITE)
        f = os.fdopen(handle, 'w')
        f.write(ansible_runner.utils.args2cmdline(*args))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def build_credentials_list(self, instance):
        return []

    def get_instance_timeout(self, instance):
        global_timeout_setting_name = instance._global_timeout_setting()
        if global_timeout_setting_name:
            global_timeout = getattr(settings, global_timeout_setting_name, 0)
            local_timeout = getattr(instance, 'timeout', 0)
            job_timeout = global_timeout if local_timeout == 0 else local_timeout
            job_timeout = 0 if local_timeout < 0 else job_timeout
        else:
            job_timeout = 0
        return job_timeout

    def get_password_prompts(self, passwords={}):
        """
        Return a dictionary where keys are strings or regular expressions for
        prompts, and values are password lookup keys (keys that are returned
        from build_passwords).
        """
        return OrderedDict()

    def create_expect_passwords_data_struct(self, password_prompts, passwords):
        expect_passwords = {}
        for k, v in password_prompts.items():
            expect_passwords[k] = passwords.get(v, '') or ''
        return expect_passwords

    def pre_run_hook(self, instance, private_data_dir):
        """
        Hook for any steps to run before the job/task starts
        """
        instance.log_lifecycle("pre_run")

    def post_run_hook(self, instance, status):
        """
        Hook for any steps to run before job/task is marked as complete.
        """
        instance.log_lifecycle("post_run")

    def final_run_hook(self, instance, status, private_data_dir, fact_modification_times):
        """
        Hook for any steps to run after job/task is marked as complete.
        """
        instance.log_lifecycle("finalize_run")
        artifact_dir = os.path.join(private_data_dir, 'artifacts', str(self.instance.id))
        job_profiling_dir = os.path.join(artifact_dir, 'playbook_profiling')
        awx_profiling_dir = '/var/log/tower/playbook_profiling/'
        collections_info = os.path.join(artifact_dir, 'collections.json')
        ansible_version_file = os.path.join(artifact_dir, 'ansible_version.txt')

        if not os.path.exists(awx_profiling_dir):
            os.mkdir(awx_profiling_dir)
        if os.path.isdir(job_profiling_dir):
            shutil.copytree(job_profiling_dir, os.path.join(awx_profiling_dir, str(instance.pk)))
        if os.path.exists(collections_info):
            with open(collections_info) as ee_json_info:
                ee_collections_info = json.loads(ee_json_info.read())
                instance.installed_collections = ee_collections_info
                instance.save(update_fields=['installed_collections'])
        if os.path.exists(ansible_version_file):
            with open(ansible_version_file) as ee_ansible_info:
                ansible_version_info = ee_ansible_info.readline()
                instance.ansible_version = ansible_version_info
                instance.save(update_fields=['ansible_version'])

    @with_path_cleanup
    def run(self, pk, **kwargs):
        """
        Run the job/task and capture its output.
        """
        self.instance = self.model.objects.get(pk=pk)

        if self.instance.execution_environment_id is None:
            from awx.main.signals import disable_activity_stream

            with disable_activity_stream():
                self.instance = self.update_model(self.instance.pk, execution_environment=self.instance.resolve_execution_environment())

        # self.instance because of the update_model pattern and when it's used in callback handlers
        self.instance = self.update_model(pk, status='running', start_args='')  # blank field to remove encrypted passwords
        self.instance.websocket_emit_status("running")
        status, rc = 'error', None
        extra_update_fields = {}
        fact_modification_times = {}
        self.runner_callback.event_ct = 0

        '''
        Needs to be an object property because status_handler uses it in a callback context
        '''

        self.safe_cred_env = {}
        private_data_dir = None

        try:
            self.instance.send_notification_templates("running")
            private_data_dir = self.build_private_data_dir(self.instance)
            self.pre_run_hook(self.instance, private_data_dir)
            self.instance.log_lifecycle("preparing_playbook")
            if self.instance.cancel_flag:
                self.instance = self.update_model(self.instance.pk, status='canceled')
            if self.instance.status != 'running':
                # Stop the task chain and prevent starting the job if it has
                # already been canceled.
                self.instance = self.update_model(pk)
                status = self.instance.status
                raise RuntimeError('not starting %s task' % self.instance.status)

            if not os.path.exists(settings.AWX_ISOLATION_BASE_PATH):
                raise RuntimeError('AWX_ISOLATION_BASE_PATH=%s does not exist' % settings.AWX_ISOLATION_BASE_PATH)

            # Fetch "cached" fact data from prior runs and put on the disk
            # where ansible expects to find it
            if getattr(self.instance, 'use_fact_cache', False):
                self.instance.start_job_fact_cache(
                    os.path.join(private_data_dir, 'artifacts', str(self.instance.id), 'fact_cache'),
                    fact_modification_times,
                )

            # May have to serialize the value
            private_data_files = self.build_private_data_files(self.instance, private_data_dir)
            passwords = self.build_passwords(self.instance, kwargs)
            self.build_extra_vars_file(self.instance, private_data_dir)
            args = self.build_args(self.instance, private_data_dir, passwords)
            env = self.build_env(self.instance, private_data_dir, private_data_files=private_data_files)
            self.runner_callback.safe_env = build_safe_env(env)

            self.runner_callback.instance = self.instance

            # store a reference to the parent workflow job (if any) so we can include
            # it in event data JSON
            if self.instance.spawned_by_workflow:
                self.runner_callback.parent_workflow_job_id = self.instance.get_workflow_job().id

            self.runner_callback.job_created = str(self.instance.created)

            credentials = self.build_credentials_list(self.instance)

            for credential in credentials:
                if credential:
                    credential.credential_type.inject_credential(credential, env, self.safe_cred_env, args, private_data_dir)

            self.runner_callback.safe_env.update(self.safe_cred_env)

            self.write_args_file(private_data_dir, args)

            password_prompts = self.get_password_prompts(passwords)
            expect_passwords = self.create_expect_passwords_data_struct(password_prompts, passwords)

            params = {
                'ident': self.instance.id,
                'private_data_dir': private_data_dir,
                'playbook': self.build_playbook_path_relative_to_cwd(self.instance, private_data_dir),
                'inventory': self.build_inventory(self.instance, private_data_dir),
                'passwords': expect_passwords,
                'envvars': env,
                'settings': {
                    'job_timeout': self.get_instance_timeout(self.instance),
                    'suppress_ansible_output': True,
                    'suppress_output_file': True,
                },
            }

            idle_timeout = getattr(settings, 'DEFAULT_JOB_IDLE_TIMEOUT', 0)
            if idle_timeout > 0:
                params['settings']['idle_timeout'] = idle_timeout

            if isinstance(self.instance, AdHocCommand):
                params['module'] = self.build_module_name(self.instance)
                params['module_args'] = self.build_module_args(self.instance)

            if getattr(self.instance, 'use_fact_cache', False):
                # Enable Ansible fact cache.
                params['fact_cache_type'] = 'jsonfile'
            else:
                # Disable Ansible fact cache.
                params['fact_cache_type'] = ''

            if self.instance.is_container_group_task or settings.IS_K8S:
                params['envvars'].pop('HOME', None)

            '''
            Delete parameters if the values are None or empty array
            '''
            for v in ['passwords', 'playbook', 'inventory']:
                if not params[v]:
                    del params[v]

            self.instance.log_lifecycle("running_playbook")
            if isinstance(self.instance, SystemJob):
                res = ansible_runner.interface.run(
                    project_dir=settings.BASE_DIR,
                    event_handler=self.runner_callback.event_handler,
                    finished_callback=self.runner_callback.finished_callback,
                    status_handler=self.runner_callback.status_handler,
                    cancel_callback=self.runner_callback.cancel_callback,
                    **params,
                )
            else:
                receptor_job = AWXReceptorJob(self, params)
                res = receptor_job.run()
                self.unit_id = receptor_job.unit_id

                if not res:
                    return

            status = res.status
            rc = res.rc

            if status in ('timeout', 'error'):
                job_explanation = f"Job terminated due to {status}"
                self.instance.job_explanation = self.instance.job_explanation or job_explanation
                if status == 'timeout':
                    status = 'failed'

                extra_update_fields['job_explanation'] = self.instance.job_explanation
                # ensure failure notification sends even if playbook_on_stats event is not triggered
                handle_success_and_failure_notifications.apply_async([self.instance.id])

        except ReceptorNodeNotFound as exc:
            extra_update_fields['job_explanation'] = str(exc)
        except Exception:
            # this could catch programming or file system errors
            extra_update_fields['result_traceback'] = traceback.format_exc()
            logger.exception('%s Exception occurred while running task', self.instance.log_format)
        finally:
            logger.debug('%s finished running, producing %s events.', self.instance.log_format, self.runner_callback.event_ct)

        try:
            self.post_run_hook(self.instance, status)
        except PostRunError as exc:
            if status == 'successful':
                status = exc.status
                extra_update_fields['job_explanation'] = exc.args[0]
                if exc.tb:
                    extra_update_fields['result_traceback'] = exc.tb
        except Exception:
            logger.exception('{} Post run hook errored.'.format(self.instance.log_format))

        self.instance = self.update_model(pk)
        self.instance = self.update_model(pk, status=status, emitted_events=self.runner_callback.event_ct, **extra_update_fields)

        try:
            self.final_run_hook(self.instance, status, private_data_dir, fact_modification_times)
        except Exception:
            logger.exception('{} Final run hook errored.'.format(self.instance.log_format))

        self.instance.websocket_emit_status(status)
        if status != 'successful':
            if status == 'canceled':
                raise AwxTaskError.TaskCancel(self.instance, rc)
            else:
                raise AwxTaskError.TaskError(self.instance, rc)


@task(queue=get_local_queuename)
class RunJob(BaseTask):
    """
    Run a job using ansible-playbook.
    """

    model = Job
    event_model = JobEvent

    def build_private_data(self, job, private_data_dir):
        """
        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                ...
            },
            'certificates': {
                <awx.main.models.Credential>: <signed SSH certificate data>,
                <awx.main.models.Credential>: <signed SSH certificate data>,
                ...
            }
        }
        """
        private_data = {'credentials': {}}
        for credential in job.credentials.prefetch_related('input_sources__source_credential').all():
            # If we were sent SSH credentials, decrypt them and send them
            # back (they will be written to a temporary file).
            if credential.has_input('ssh_key_data'):
                private_data['credentials'][credential] = credential.get_input('ssh_key_data', default='')
            if credential.has_input('ssh_public_key_data'):
                private_data.setdefault('certificates', {})[credential] = credential.get_input('ssh_public_key_data', default='')

        return private_data

    def build_passwords(self, job, runtime_passwords):
        """
        Build a dictionary of passwords for SSH private key, SSH user, sudo/su
        and ansible-vault.
        """
        passwords = super(RunJob, self).build_passwords(job, runtime_passwords)
        cred = job.machine_credential
        if cred:
            for field in ('ssh_key_unlock', 'ssh_password', 'become_password', 'vault_password'):
                value = runtime_passwords.get(field, cred.get_input('password' if field == 'ssh_password' else field, default=''))
                if value not in ('', 'ASK'):
                    passwords[field] = value

        for cred in job.vault_credentials:
            field = 'vault_password'
            vault_id = cred.get_input('vault_id', default=None)
            if vault_id:
                field = 'vault_password.{}'.format(vault_id)
                if field in passwords:
                    raise RuntimeError('multiple vault credentials were specified with --vault-id {}@prompt'.format(vault_id))
            value = runtime_passwords.get(field, cred.get_input('vault_password', default=''))
            if value not in ('', 'ASK'):
                passwords[field] = value

        '''
        Only 1 value can be provided for a unique prompt string. Prefer ssh
        key unlock over network key unlock.
        '''
        if 'ssh_key_unlock' not in passwords:
            for cred in job.network_credentials:
                if cred.inputs.get('ssh_key_unlock'):
                    passwords['ssh_key_unlock'] = runtime_passwords.get('ssh_key_unlock', cred.get_input('ssh_key_unlock', default=''))
                    break

        return passwords

    def build_env(self, job, private_data_dir, private_data_files=None):
        """
        Build environment dictionary for ansible-playbook.
        """
        env = super(RunJob, self).build_env(job, private_data_dir, private_data_files=private_data_files)
        if private_data_files is None:
            private_data_files = {}
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['JOB_ID'] = str(job.pk)
        env['INVENTORY_ID'] = str(job.inventory.pk)
        if job.project:
            env['PROJECT_REVISION'] = job.project.scm_revision
        env['ANSIBLE_RETRY_FILES_ENABLED'] = "False"
        env['MAX_EVENT_RES'] = str(settings.MAX_EVENT_RES_DATA)
        if hasattr(settings, 'AWX_ANSIBLE_CALLBACK_PLUGINS') and settings.AWX_ANSIBLE_CALLBACK_PLUGINS:
            env['ANSIBLE_CALLBACK_PLUGINS'] = ':'.join(settings.AWX_ANSIBLE_CALLBACK_PLUGINS)
        env['AWX_HOST'] = settings.TOWER_URL_BASE

        # Create a directory for ControlPath sockets that is unique to each job
        cp_dir = os.path.join(private_data_dir, 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0o700)
        # FIXME: more elegant way to manage this path in container
        env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = '/runner/cp'

        # Set environment variables for cloud credentials.
        cred_files = private_data_files.get('credentials', {})
        for cloud_cred in job.cloud_credentials:
            if cloud_cred and cloud_cred.credential_type.namespace == 'openstack' and cred_files.get(cloud_cred, ''):
                env['OS_CLIENT_CONFIG_FILE'] = to_container_path(cred_files.get(cloud_cred, ''), private_data_dir)

        for network_cred in job.network_credentials:
            env['ANSIBLE_NET_USERNAME'] = network_cred.get_input('username', default='')
            env['ANSIBLE_NET_PASSWORD'] = network_cred.get_input('password', default='')

            ssh_keyfile = cred_files.get(network_cred, '')
            if ssh_keyfile:
                env['ANSIBLE_NET_SSH_KEYFILE'] = ssh_keyfile

            authorize = network_cred.get_input('authorize', default=False)
            env['ANSIBLE_NET_AUTHORIZE'] = str(int(authorize))
            if authorize:
                env['ANSIBLE_NET_AUTH_PASS'] = network_cred.get_input('authorize_password', default='')

        path_vars = (
            ('ANSIBLE_COLLECTIONS_PATHS', 'collections_paths', 'requirements_collections', '~/.ansible/collections:/usr/share/ansible/collections'),
            ('ANSIBLE_ROLES_PATH', 'roles_path', 'requirements_roles', '~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles'),
        )

        config_values = read_ansible_config(os.path.join(private_data_dir, 'project'), list(map(lambda x: x[1], path_vars)))

        for env_key, config_setting, folder, default in path_vars:
            paths = default.split(':')
            if env_key in env:
                for path in env[env_key].split(':'):
                    if path not in paths:
                        paths = [env[env_key]] + paths
            elif config_setting in config_values:
                for path in config_values[config_setting].split(':'):
                    if path not in paths:
                        paths = [config_values[config_setting]] + paths
            paths = [os.path.join(CONTAINER_ROOT, folder)] + paths
            env[env_key] = os.pathsep.join(paths)

        return env

    def build_args(self, job, private_data_dir, passwords):
        """
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        """
        creds = job.machine_credential

        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = creds.get_input('username', default='')
            become_method = creds.get_input('become_method', default='')
            become_username = creds.get_input('become_username', default='')
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible-playbook's default of using
        # the current user.
        ssh_username = ssh_username or 'root'
        args = []
        if job.job_type == 'check':
            args.append('--check')
        args.extend(['-u', sanitize_jinja(ssh_username)])
        if 'ssh_password' in passwords:
            args.append('--ask-pass')
        if job.become_enabled:
            args.append('--become')
        if job.diff_mode:
            args.append('--diff')
        if become_method:
            args.extend(['--become-method', sanitize_jinja(become_method)])
        if become_username:
            args.extend(['--become-user', sanitize_jinja(become_username)])
        if 'become_password' in passwords:
            args.append('--ask-become-pass')

        # Support prompting for multiple vault passwords
        for k, v in passwords.items():
            if k.startswith('vault_password'):
                if k == 'vault_password':
                    args.append('--ask-vault-pass')
                else:
                    # split only on the first dot in case the vault ID itself contains a dot
                    vault_id = k.split('.', 1)[1]
                    args.append('--vault-id')
                    args.append('{}@prompt'.format(vault_id))

        if job.forks:
            if settings.MAX_FORKS > 0 and job.forks > settings.MAX_FORKS:
                logger.warning(f'Maximum number of forks ({settings.MAX_FORKS}) exceeded.')
                args.append('--forks=%d' % settings.MAX_FORKS)
            else:
                args.append('--forks=%d' % job.forks)
        if job.force_handlers:
            args.append('--force-handlers')
        if job.limit:
            args.extend(['-l', job.limit])
        if job.verbosity:
            args.append('-%s' % ('v' * min(5, job.verbosity)))
        if job.job_tags:
            args.extend(['-t', job.job_tags])
        if job.skip_tags:
            args.append('--skip-tags=%s' % job.skip_tags)
        if job.start_at_task:
            args.append('--start-at-task=%s' % job.start_at_task)

        return args

    def build_playbook_path_relative_to_cwd(self, job, private_data_dir):
        return job.playbook

    def build_extra_vars_file(self, job, private_data_dir):
        # Define special extra_vars for AWX, combine with job.extra_vars.
        extra_vars = job.awx_meta_vars()

        if job.extra_vars_dict:
            extra_vars.update(json.loads(job.decrypted_extra_vars()))

        # By default, all extra vars disallow Jinja2 template usage for
        # security reasons; top level key-values defined in JT.extra_vars, however,
        # are allowed as "safe" (because they can only be set by users with
        # higher levels of privilege - those that have the ability create and
        # edit Job Templates)
        safe_dict = {}
        if job.job_template and settings.ALLOW_JINJA_IN_EXTRA_VARS == 'template':
            safe_dict = job.job_template.extra_vars_dict

        return self._write_extra_vars_file(private_data_dir, extra_vars, safe_dict)

    def build_credentials_list(self, job):
        return job.credentials.prefetch_related('input_sources__source_credential').all()

    def get_password_prompts(self, passwords={}):
        d = super(RunJob, self).get_password_prompts(passwords)
        d[r'Enter passphrase for .*:\s*?$'] = 'ssh_key_unlock'
        d[r'Bad passphrase, try again for .*:\s*?$'] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[r'%s password.*:\s*?$' % (method[0])] = 'become_password'
            d[r'%s password.*:\s*?$' % (method[0].upper())] = 'become_password'
        d[r'BECOME password.*:\s*?$'] = 'become_password'
        d[r'SSH password:\s*?$'] = 'ssh_password'
        d[r'Password:\s*?$'] = 'ssh_password'
        d[r'Vault password:\s*?$'] = 'vault_password'
        for k, v in passwords.items():
            if k.startswith('vault_password.'):
                # split only on the first dot in case the vault ID itself contains a dot
                vault_id = k.split('.', 1)[1]
                d[r'Vault password \({}\):\s*?$'.format(vault_id)] = k
        return d

    def pre_run_hook(self, job, private_data_dir):
        super(RunJob, self).pre_run_hook(job, private_data_dir)
        if job.inventory is None:
            error = _('Job could not start because it does not have a valid inventory.')
            self.update_model(job.pk, status='failed', job_explanation=error)
            raise RuntimeError(error)
        elif job.project is None:
            error = _('Job could not start because it does not have a valid project.')
            self.update_model(job.pk, status='failed', job_explanation=error)
            raise RuntimeError(error)
        elif job.execution_environment is None:
            error = _('Job could not start because no Execution Environment could be found.')
            self.update_model(job.pk, status='error', job_explanation=error)
            raise RuntimeError(error)
        elif job.project.status in ('error', 'failed'):
            msg = _('The project revision for this job template is unknown due to a failed update.')
            job = self.update_model(job.pk, status='failed', job_explanation=msg)
            raise RuntimeError(msg)

        project_path = job.project.get_project_path(check_if_exists=False)
        job_revision = job.project.scm_revision
        sync_needs = []
        source_update_tag = 'update_{}'.format(job.project.scm_type)
        branch_override = bool(job.scm_branch and job.scm_branch != job.project.scm_branch)
        if not job.project.scm_type:
            pass  # manual projects are not synced, user has responsibility for that
        elif not os.path.exists(project_path):
            logger.debug('Performing fresh clone of {} on this instance.'.format(job.project))
            sync_needs.append(source_update_tag)
        elif job.project.scm_type == 'git' and job.project.scm_revision and (not branch_override):
            try:
                git_repo = git.Repo(project_path)

                if job_revision == git_repo.head.commit.hexsha:
                    logger.debug('Skipping project sync for {} because commit is locally available'.format(job.log_format))
                else:
                    sync_needs.append(source_update_tag)
            except (ValueError, BadGitName, git.exc.InvalidGitRepositoryError):
                logger.debug('Needed commit for {} not in local source tree, will sync with remote'.format(job.log_format))
                sync_needs.append(source_update_tag)
        else:
            logger.debug('Project not available locally, {} will sync with remote'.format(job.log_format))
            sync_needs.append(source_update_tag)

        has_cache = os.path.exists(os.path.join(job.project.get_cache_path(), job.project.cache_id))
        # Galaxy requirements are not supported for manual projects
        if job.project.scm_type and ((not has_cache) or branch_override):
            sync_needs.extend(['install_roles', 'install_collections'])

        if sync_needs:
            pu_ig = job.instance_group
            pu_en = Instance.objects.me().hostname

            sync_metafields = dict(
                launch_type="sync",
                job_type='run',
                job_tags=','.join(sync_needs),
                status='running',
                instance_group=pu_ig,
                execution_node=pu_en,
                controller_node=pu_en,
                celery_task_id=job.celery_task_id,
            )
            if branch_override:
                sync_metafields['scm_branch'] = job.scm_branch
                sync_metafields['scm_clean'] = True  # to accomidate force pushes
            if 'update_' not in sync_metafields['job_tags']:
                sync_metafields['scm_revision'] = job_revision
            local_project_sync = job.project.create_project_update(_eager_fields=sync_metafields)
            local_project_sync.log_lifecycle("controller_node_chosen")
            local_project_sync.log_lifecycle("execution_node_chosen")
            create_partition(local_project_sync.event_class._meta.db_table, start=local_project_sync.created)
            # save the associated job before calling run() so that a
            # cancel() call on the job can cancel the project update
            job = self.update_model(job.pk, project_update=local_project_sync)

            project_update_task = local_project_sync._get_task_class()
            try:
                # the job private_data_dir is passed so sync can download roles and collections there
                sync_task = project_update_task(job_private_data_dir=private_data_dir)
                sync_task.run(local_project_sync.id)
                local_project_sync.refresh_from_db()
                job = self.update_model(job.pk, scm_revision=local_project_sync.scm_revision)
            except Exception:
                local_project_sync.refresh_from_db()
                if local_project_sync.status != 'canceled':
                    job = self.update_model(
                        job.pk,
                        status='failed',
                        job_explanation=(
                            'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}'
                            % ('project_update', local_project_sync.name, local_project_sync.id)
                        ),
                    )
                    raise
                job.refresh_from_db()
                if job.cancel_flag:
                    return
        else:
            # Case where a local sync is not needed, meaning that local tree is
            # up-to-date with project, job is running project current version
            if job_revision:
                job = self.update_model(job.pk, scm_revision=job_revision)
            # Project update does not copy the folder, so copy here
            RunProjectUpdate.make_local_copy(job.project, private_data_dir, scm_revision=job_revision)

        if job.inventory.kind == 'smart':
            # cache smart inventory memberships so that the host_filter query is not
            # ran inside of the event saving code
            update_smart_memberships_for_inventory(job.inventory)

    def final_run_hook(self, job, status, private_data_dir, fact_modification_times):
        super(RunJob, self).final_run_hook(job, status, private_data_dir, fact_modification_times)
        if not private_data_dir:
            # If there's no private data dir, that means we didn't get into the
            # actual `run()` call; this _usually_ means something failed in
            # the pre_run_hook method
            return
        if job.use_fact_cache:
            job.finish_job_fact_cache(
                os.path.join(private_data_dir, 'artifacts', str(job.id), 'fact_cache'),
                fact_modification_times,
            )

        try:
            inventory = job.inventory
        except Inventory.DoesNotExist:
            pass
        else:
            if inventory is not None:
                update_inventory_computed_fields.delay(inventory.id)


@task(queue=get_local_queuename)
class RunProjectUpdate(BaseTask):

    model = ProjectUpdate
    event_model = ProjectUpdateEvent
    callback_class = RunnerCallbackForProjectUpdate

    def __init__(self, *args, job_private_data_dir=None, **kwargs):
        super(RunProjectUpdate, self).__init__(*args, **kwargs)
        self.original_branch = None
        self.job_private_data_dir = job_private_data_dir

    def build_private_data(self, project_update, private_data_dir):
        """
        Return SSH private key data needed for this project update.

        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>
            }
        }
        """
        private_data = {'credentials': {}}
        if project_update.credential:
            credential = project_update.credential
            if credential.has_input('ssh_key_data'):
                private_data['credentials'][credential] = credential.get_input('ssh_key_data', default='')
        return private_data

    def build_passwords(self, project_update, runtime_passwords):
        """
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        """
        passwords = super(RunProjectUpdate, self).build_passwords(project_update, runtime_passwords)
        if project_update.credential:
            passwords['scm_key_unlock'] = project_update.credential.get_input('ssh_key_unlock', default='')
            passwords['scm_username'] = project_update.credential.get_input('username', default='')
            passwords['scm_password'] = project_update.credential.get_input('password', default='')
        return passwords

    def build_env(self, project_update, private_data_dir, private_data_files=None):
        """
        Build environment dictionary for ansible-playbook.
        """
        env = super(RunProjectUpdate, self).build_env(project_update, private_data_dir, private_data_files=private_data_files)
        env['ANSIBLE_RETRY_FILES_ENABLED'] = str(False)
        env['ANSIBLE_ASK_PASS'] = str(False)
        env['ANSIBLE_BECOME_ASK_PASS'] = str(False)
        env['DISPLAY'] = ''  # Prevent stupid password popup when running tests.
        # give ansible a hint about the intended tmpdir to work around issues
        # like https://github.com/ansible/ansible/issues/30064
        env['TMP'] = settings.AWX_ISOLATION_BASE_PATH
        env['PROJECT_UPDATE_ID'] = str(project_update.pk)
        if settings.GALAXY_IGNORE_CERTS:
            env['ANSIBLE_GALAXY_IGNORE'] = True

        # build out env vars for Galaxy credentials (in order)
        galaxy_server_list = []
        if project_update.project.organization:
            for i, cred in enumerate(project_update.project.organization.galaxy_credentials.all()):
                env[f'ANSIBLE_GALAXY_SERVER_SERVER{i}_URL'] = cred.get_input('url')
                auth_url = cred.get_input('auth_url', default=None)
                token = cred.get_input('token', default=None)
                if token:
                    env[f'ANSIBLE_GALAXY_SERVER_SERVER{i}_TOKEN'] = token
                if auth_url:
                    env[f'ANSIBLE_GALAXY_SERVER_SERVER{i}_AUTH_URL'] = auth_url
                galaxy_server_list.append(f'server{i}')

        if galaxy_server_list:
            env['ANSIBLE_GALAXY_SERVER_LIST'] = ','.join(galaxy_server_list)

        return env

    def _build_scm_url_extra_vars(self, project_update):
        """
        Helper method to build SCM url and extra vars with parameters needed
        for authentication.
        """
        extra_vars = {}
        if project_update.credential:
            scm_username = project_update.credential.get_input('username', default='')
            scm_password = project_update.credential.get_input('password', default='')
        else:
            scm_username = ''
            scm_password = ''
        scm_type = project_update.scm_type
        scm_url = update_scm_url(scm_type, project_update.scm_url, check_special_cases=False)
        scm_url_parts = urlparse.urlsplit(scm_url)
        # Prefer the username/password in the URL, if provided.
        scm_username = scm_url_parts.username or scm_username
        scm_password = scm_url_parts.password or scm_password
        if scm_username:
            if scm_type == 'svn':
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = scm_password
                scm_password = False
                if scm_url_parts.scheme != 'svn+ssh':
                    scm_username = False
            elif scm_url_parts.scheme.endswith('ssh'):
                scm_password = False
            elif scm_type in ('insights', 'archive'):
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = scm_password
            scm_url = update_scm_url(scm_type, scm_url, scm_username, scm_password, scp_format=True)
        else:
            scm_url = update_scm_url(scm_type, scm_url, scp_format=True)

        # Pass the extra accept_hostkey parameter to the git module.
        if scm_type == 'git' and scm_url_parts.scheme.endswith('ssh'):
            extra_vars['scm_accept_hostkey'] = 'true'

        return scm_url, extra_vars

    def build_inventory(self, instance, private_data_dir):
        return 'localhost,'

    def build_args(self, project_update, private_data_dir, passwords):
        """
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        """
        args = []
        if getattr(settings, 'PROJECT_UPDATE_VVV', False):
            args.append('-vvv')
        if project_update.job_tags:
            args.extend(['-t', project_update.job_tags])
        return args

    def build_extra_vars_file(self, project_update, private_data_dir):
        extra_vars = {}
        scm_url, extra_vars_new = self._build_scm_url_extra_vars(project_update)
        extra_vars.update(extra_vars_new)

        scm_branch = project_update.scm_branch
        if project_update.job_type == 'run' and (not project_update.branch_override):
            if project_update.project.scm_revision:
                scm_branch = project_update.project.scm_revision
            elif not scm_branch:
                raise RuntimeError('Could not determine a revision to run from project.')
        elif not scm_branch:
            scm_branch = 'HEAD'

        galaxy_creds_are_defined = project_update.project.organization and project_update.project.organization.galaxy_credentials.exists()
        if not galaxy_creds_are_defined and (settings.AWX_ROLES_ENABLED or settings.AWX_COLLECTIONS_ENABLED):
            logger.warning('Galaxy role/collection syncing is enabled, but no ' f'credentials are configured for {project_update.project.organization}.')

        extra_vars.update(
            {
                'projects_root': settings.PROJECTS_ROOT.rstrip('/'),
                'local_path': os.path.basename(project_update.project.local_path),
                'project_path': project_update.get_project_path(check_if_exists=False),  # deprecated
                'insights_url': settings.INSIGHTS_URL_BASE,
                'awx_license_type': get_license().get('license_type', 'UNLICENSED'),
                'awx_version': get_awx_version(),
                'scm_url': scm_url,
                'scm_branch': scm_branch,
                'scm_clean': project_update.scm_clean,
                'scm_track_submodules': project_update.scm_track_submodules,
                'roles_enabled': galaxy_creds_are_defined and settings.AWX_ROLES_ENABLED,
                'collections_enabled': galaxy_creds_are_defined and settings.AWX_COLLECTIONS_ENABLED,
            }
        )
        # apply custom refspec from user for PR refs and the like
        if project_update.scm_refspec:
            extra_vars['scm_refspec'] = project_update.scm_refspec
        elif project_update.project.allow_override:
            # If branch is override-able, do extra fetch for all branches
            extra_vars['scm_refspec'] = 'refs/heads/*:refs/remotes/origin/*'

        if project_update.scm_type == 'archive':
            # for raw archive, prevent error moving files between volumes
            extra_vars['ansible_remote_tmp'] = os.path.join(project_update.get_project_path(check_if_exists=False), '.ansible_awx', 'tmp')

        self._write_extra_vars_file(private_data_dir, extra_vars)

    def build_playbook_path_relative_to_cwd(self, project_update, private_data_dir):
        return os.path.join('project_update.yml')

    def get_password_prompts(self, passwords={}):
        d = super(RunProjectUpdate, self).get_password_prompts(passwords)
        d[r'Username for.*:\s*?$'] = 'scm_username'
        d[r'Password for.*:\s*?$'] = 'scm_password'
        d[r'Password:\s*?$'] = 'scm_password'
        d[r'\S+?@\S+?\'s\s+?password:\s*?$'] = 'scm_password'
        d[r'Enter passphrase for .*:\s*?$'] = 'scm_key_unlock'
        d[r'Bad passphrase, try again for .*:\s*?$'] = ''
        # FIXME: Configure whether we should auto accept host keys?
        d[r'^Are you sure you want to continue connecting \(yes/no\)\?\s*?$'] = 'yes'
        return d

    def _update_dependent_inventories(self, project_update, dependent_inventory_sources):
        scm_revision = project_update.project.scm_revision
        inv_update_class = InventoryUpdate._get_task_class()
        for inv_src in dependent_inventory_sources:
            if not inv_src.update_on_project_update:
                continue
            if inv_src.scm_last_revision == scm_revision:
                logger.debug('Skipping SCM inventory update for `{}` because ' 'project has not changed.'.format(inv_src.name))
                continue
            logger.debug('Local dependent inventory update for `{}`.'.format(inv_src.name))
            with transaction.atomic():
                if InventoryUpdate.objects.filter(inventory_source=inv_src, status__in=ACTIVE_STATES).exists():
                    logger.debug('Skipping SCM inventory update for `{}` because ' 'another update is already active.'.format(inv_src.name))
                    continue

                if settings.IS_K8S:
                    instance_group = InventoryUpdate(inventory_source=inv_src).preferred_instance_groups[0]
                else:
                    instance_group = project_update.instance_group

                local_inv_update = inv_src.create_inventory_update(
                    _eager_fields=dict(
                        launch_type='scm',
                        status='running',
                        instance_group=instance_group,
                        execution_node=project_update.execution_node,
                        controller_node=project_update.execution_node,
                        source_project_update=project_update,
                        celery_task_id=project_update.celery_task_id,
                    )
                )
                local_inv_update.log_lifecycle("controller_node_chosen")
                local_inv_update.log_lifecycle("execution_node_chosen")
            try:
                create_partition(local_inv_update.event_class._meta.db_table, start=local_inv_update.created)
                inv_update_class().run(local_inv_update.id)
            except Exception:
                logger.exception('{} Unhandled exception updating dependent SCM inventory sources.'.format(project_update.log_format))

            try:
                project_update.refresh_from_db()
            except ProjectUpdate.DoesNotExist:
                logger.warning('Project update deleted during updates of dependent SCM inventory sources.')
                break
            try:
                local_inv_update.refresh_from_db()
            except InventoryUpdate.DoesNotExist:
                logger.warning('%s Dependent inventory update deleted during execution.', project_update.log_format)
                continue
            if project_update.cancel_flag:
                logger.info('Project update {} was canceled while updating dependent inventories.'.format(project_update.log_format))
                break
            if local_inv_update.cancel_flag:
                logger.info('Continuing to process project dependencies after {} was canceled'.format(local_inv_update.log_format))
            if local_inv_update.status == 'successful':
                inv_src.scm_last_revision = scm_revision
                inv_src.save(update_fields=['scm_last_revision'])

    def release_lock(self, instance):
        try:
            fcntl.lockf(self.lock_fd, fcntl.LOCK_UN)
        except IOError as e:
            logger.error("I/O error({0}) while trying to release lock file [{1}]: {2}".format(e.errno, instance.get_lock_file(), e.strerror))
            os.close(self.lock_fd)
            raise

        os.close(self.lock_fd)
        self.lock_fd = None

    '''
    Note: We don't support blocking=False
    '''

    def acquire_lock(self, instance, blocking=True):
        lock_path = instance.get_lock_file()
        if lock_path is None:
            # If from migration or someone blanked local_path for any other reason, recoverable by save
            instance.save()
            lock_path = instance.get_lock_file()
            if lock_path is None:
                raise RuntimeError(u'Invalid lock file path')

        try:
            self.lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
        except OSError as e:
            logger.error("I/O error({0}) while trying to open lock file [{1}]: {2}".format(e.errno, lock_path, e.strerror))
            raise

        start_time = time.time()
        while True:
            try:
                instance.refresh_from_db(fields=['cancel_flag'])
                if instance.cancel_flag:
                    logger.debug("ProjectUpdate({0}) was canceled".format(instance.pk))
                    return
                fcntl.lockf(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError as e:
                if e.errno not in (errno.EAGAIN, errno.EACCES):
                    os.close(self.lock_fd)
                    logger.error("I/O error({0}) while trying to aquire lock on file [{1}]: {2}".format(e.errno, lock_path, e.strerror))
                    raise
                else:
                    time.sleep(1.0)
        waiting_time = time.time() - start_time

        if waiting_time > 1.0:
            logger.info('{} spent {} waiting to acquire lock for local source tree ' 'for path {}.'.format(instance.log_format, waiting_time, lock_path))

    def pre_run_hook(self, instance, private_data_dir):
        super(RunProjectUpdate, self).pre_run_hook(instance, private_data_dir)
        # re-create root project folder if a natural disaster has destroyed it
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        project_path = instance.project.get_project_path(check_if_exists=False)

        self.acquire_lock(instance)

        self.original_branch = None
        if instance.scm_type == 'git' and instance.branch_override:
            if os.path.exists(project_path):
                git_repo = git.Repo(project_path)
                if git_repo.head.is_detached:
                    self.original_branch = git_repo.head.commit
                else:
                    self.original_branch = git_repo.active_branch

        if not os.path.exists(project_path):
            os.makedirs(project_path)  # used as container mount

        stage_path = os.path.join(instance.get_cache_path(), 'stage')
        if os.path.exists(stage_path):
            logger.warning('{0} unexpectedly existed before update'.format(stage_path))
            shutil.rmtree(stage_path)
        os.makedirs(stage_path)  # presence of empty cache indicates lack of roles or collections

        # the project update playbook is not in a git repo, but uses a vendoring directory
        # to be consistent with the ansible-runner model,
        # that is moved into the runner project folder here
        awx_playbooks = self.get_path_to('../../', 'playbooks')
        copy_tree(awx_playbooks, os.path.join(private_data_dir, 'project'))

    @staticmethod
    def clear_project_cache(cache_dir, keep_value):
        if os.path.isdir(cache_dir):
            for entry in os.listdir(cache_dir):
                old_path = os.path.join(cache_dir, entry)
                if entry not in (keep_value, 'stage'):
                    # invalidate, then delete
                    new_path = os.path.join(cache_dir, '.~~delete~~' + entry)
                    try:
                        os.rename(old_path, new_path)
                        shutil.rmtree(new_path)
                    except OSError:
                        logger.warning(f"Could not remove cache directory {old_path}")

    @staticmethod
    def make_local_copy(p, job_private_data_dir, scm_revision=None):
        """Copy project content (roles and collections) to a job private_data_dir

        :param object p: Either a project or a project update
        :param str job_private_data_dir: The root of the target ansible-runner folder
        :param str scm_revision: For branch_override cases, the git revision to copy
        """
        project_path = p.get_project_path(check_if_exists=False)
        destination_folder = os.path.join(job_private_data_dir, 'project')
        if not scm_revision:
            scm_revision = p.scm_revision

        if p.scm_type == 'git':
            git_repo = git.Repo(project_path)
            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
            tmp_branch_name = 'awx_internal/{}'.format(uuid4())
            # always clone based on specific job revision
            if not p.scm_revision:
                raise RuntimeError('Unexpectedly could not determine a revision to run from project.')
            source_branch = git_repo.create_head(tmp_branch_name, p.scm_revision)
            # git clone must take file:// syntax for source repo or else options like depth will be ignored
            source_as_uri = Path(project_path).as_uri()
            git.Repo.clone_from(
                source_as_uri,
                destination_folder,
                branch=source_branch,
                depth=1,
                single_branch=True,  # shallow, do not copy full history
            )
            # submodules copied in loop because shallow copies from local HEADs are ideal
            # and no git clone submodule options are compatible with minimum requirements
            for submodule in git_repo.submodules:
                subrepo_path = os.path.abspath(os.path.join(project_path, submodule.path))
                subrepo_destination_folder = os.path.abspath(os.path.join(destination_folder, submodule.path))
                subrepo_uri = Path(subrepo_path).as_uri()
                git.Repo.clone_from(subrepo_uri, subrepo_destination_folder, depth=1, single_branch=True)
            # force option is necessary because remote refs are not counted, although no information is lost
            git_repo.delete_head(tmp_branch_name, force=True)
        else:
            copy_tree(project_path, destination_folder, preserve_symlinks=1)

        # copy over the roles and collection cache to job folder
        cache_path = os.path.join(p.get_cache_path(), p.cache_id)
        subfolders = []
        if settings.AWX_COLLECTIONS_ENABLED:
            subfolders.append('requirements_collections')
        if settings.AWX_ROLES_ENABLED:
            subfolders.append('requirements_roles')
        for subfolder in subfolders:
            cache_subpath = os.path.join(cache_path, subfolder)
            if os.path.exists(cache_subpath):
                dest_subpath = os.path.join(job_private_data_dir, subfolder)
                copy_tree(cache_subpath, dest_subpath, preserve_symlinks=1)
                logger.debug('{0} {1} prepared {2} from cache'.format(type(p).__name__, p.pk, dest_subpath))

    def post_run_hook(self, instance, status):
        super(RunProjectUpdate, self).post_run_hook(instance, status)
        # To avoid hangs, very important to release lock even if errors happen here
        try:
            if self.runner_callback.playbook_new_revision:
                instance.scm_revision = self.runner_callback.playbook_new_revision
                instance.save(update_fields=['scm_revision'])

            # Roles and collection folders copy to durable cache
            base_path = instance.get_cache_path()
            stage_path = os.path.join(base_path, 'stage')
            if status == 'successful' and 'install_' in instance.job_tags:
                # Clear other caches before saving this one, and if branch is overridden
                # do not clear cache for main branch, but do clear it for other branches
                self.clear_project_cache(base_path, keep_value=instance.project.cache_id)
                cache_path = os.path.join(base_path, instance.cache_id)
                if os.path.exists(stage_path):
                    if os.path.exists(cache_path):
                        logger.warning('Rewriting cache at {0}, performance may suffer'.format(cache_path))
                        shutil.rmtree(cache_path)
                    os.rename(stage_path, cache_path)
                    logger.debug('{0} wrote to cache at {1}'.format(instance.log_format, cache_path))
            elif os.path.exists(stage_path):
                shutil.rmtree(stage_path)  # cannot trust content update produced

            if self.job_private_data_dir:
                if status == 'successful':
                    # copy project folder before resetting to default branch
                    # because some git-tree-specific resources (like submodules) might matter
                    self.make_local_copy(instance, self.job_private_data_dir)
                if self.original_branch:
                    # for git project syncs, non-default branches can be problems
                    # restore to branch the repo was on before this run
                    try:
                        self.original_branch.checkout()
                    except Exception:
                        # this could have failed due to dirty tree, but difficult to predict all cases
                        logger.exception('Failed to restore project repo to prior state after {}'.format(instance.log_format))
        finally:
            self.release_lock(instance)
        p = instance.project
        if instance.job_type == 'check' and status not in (
            'failed',
            'canceled',
        ):
            if self.runner_callback.playbook_new_revision:
                p.scm_revision = self.runner_callback.playbook_new_revision
            else:
                if status == 'successful':
                    logger.error("{} Could not find scm revision in check".format(instance.log_format))
            p.playbook_files = p.playbooks
            p.inventory_files = p.inventories
            p.save(update_fields=['scm_revision', 'playbook_files', 'inventory_files'])

        # Update any inventories that depend on this project
        dependent_inventory_sources = p.scm_inventory_sources.filter(update_on_project_update=True)
        if len(dependent_inventory_sources) > 0:
            if status == 'successful' and instance.launch_type != 'sync':
                self._update_dependent_inventories(instance, dependent_inventory_sources)

    def build_execution_environment_params(self, instance, private_data_dir):
        if settings.IS_K8S:
            return {}

        params = super(RunProjectUpdate, self).build_execution_environment_params(instance, private_data_dir)
        project_path = instance.get_project_path(check_if_exists=False)
        cache_path = instance.get_cache_path()
        params.setdefault('container_volume_mounts', [])
        params['container_volume_mounts'].extend(
            [
                f"{project_path}:{project_path}:Z",
                f"{cache_path}:{cache_path}:Z",
            ]
        )
        return params


@task(queue=get_local_queuename)
class RunInventoryUpdate(BaseTask):

    model = InventoryUpdate
    event_model = InventoryUpdateEvent
    callback_class = RunnerCallbackForInventoryUpdate

    def build_private_data(self, inventory_update, private_data_dir):
        """
        Return private data needed for inventory update.

        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>
            }
        }

        If no private data is needed, return None.
        """
        if inventory_update.source in InventorySource.injectors:
            injector = InventorySource.injectors[inventory_update.source]()
            return injector.build_private_data(inventory_update, private_data_dir)

    def build_env(self, inventory_update, private_data_dir, private_data_files=None):
        """Build environment dictionary for ansible-inventory.

        Most environment variables related to credentials or configuration
        are accomplished by the inventory source injectors (in this method)
        or custom credential type injectors (in main run method).
        """
        env = super(RunInventoryUpdate, self).build_env(inventory_update, private_data_dir, private_data_files=private_data_files)

        if private_data_files is None:
            private_data_files = {}
        # Pass inventory source ID to inventory script.
        env['INVENTORY_SOURCE_ID'] = str(inventory_update.inventory_source_id)
        env['INVENTORY_UPDATE_ID'] = str(inventory_update.pk)
        env.update(STANDARD_INVENTORY_UPDATE_ENV)

        injector = None
        if inventory_update.source in InventorySource.injectors:
            injector = InventorySource.injectors[inventory_update.source]()

        if injector is not None:
            env = injector.build_env(inventory_update, env, private_data_dir, private_data_files)
            # All CLOUD_PROVIDERS sources implement as inventory plugin from collection
            env['ANSIBLE_INVENTORY_ENABLED'] = 'auto'

        if inventory_update.source == 'scm':
            for env_k in inventory_update.source_vars_dict:
                if str(env_k) not in env and str(env_k) not in settings.INV_ENV_VARIABLE_BLOCKED:
                    env[str(env_k)] = str(inventory_update.source_vars_dict[env_k])
        elif inventory_update.source == 'file':
            raise NotImplementedError('Cannot update file sources through the task system.')

        if inventory_update.source == 'scm' and inventory_update.source_project_update:
            env_key = 'ANSIBLE_COLLECTIONS_PATHS'
            config_setting = 'collections_paths'
            folder = 'requirements_collections'
            default = '~/.ansible/collections:/usr/share/ansible/collections'

            config_values = read_ansible_config(os.path.join(private_data_dir, 'project'), [config_setting])

            paths = default.split(':')
            if env_key in env:
                for path in env[env_key].split(':'):
                    if path not in paths:
                        paths = [env[env_key]] + paths
            elif config_setting in config_values:
                for path in config_values[config_setting].split(':'):
                    if path not in paths:
                        paths = [config_values[config_setting]] + paths
            paths = [os.path.join(CONTAINER_ROOT, folder)] + paths
            env[env_key] = os.pathsep.join(paths)
        if 'ANSIBLE_COLLECTIONS_PATHS' in env:
            paths = env['ANSIBLE_COLLECTIONS_PATHS'].split(':')
        else:
            paths = ['~/.ansible/collections', '/usr/share/ansible/collections']
        paths.append('/usr/share/automation-controller/collections')
        env['ANSIBLE_COLLECTIONS_PATHS'] = os.pathsep.join(paths)

        return env

    def write_args_file(self, private_data_dir, args):
        path = os.path.join(private_data_dir, 'args')
        handle = os.open(path, os.O_RDWR | os.O_CREAT, stat.S_IREAD | stat.S_IWRITE)
        f = os.fdopen(handle, 'w')
        f.write(' '.join(args))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def build_args(self, inventory_update, private_data_dir, passwords):
        """Build the command line argument list for running an inventory
        import.
        """
        # Get the inventory source and inventory.
        inventory_source = inventory_update.inventory_source
        inventory = inventory_source.inventory

        if inventory is None:
            raise RuntimeError('Inventory Source is not associated with an Inventory.')

        args = ['ansible-inventory', '--list', '--export']

        # Add arguments for the source inventory file/script/thing
        rel_path = self.pseudo_build_inventory(inventory_update, private_data_dir)
        container_location = os.path.join(CONTAINER_ROOT, rel_path)
        source_location = os.path.join(private_data_dir, rel_path)

        args.append('-i')
        args.append(container_location)

        args.append('--output')
        args.append(os.path.join(CONTAINER_ROOT, 'artifacts', str(inventory_update.id), 'output.json'))

        if os.path.isdir(source_location):
            playbook_dir = container_location
        else:
            playbook_dir = os.path.dirname(container_location)
        args.extend(['--playbook-dir', playbook_dir])

        if inventory_update.verbosity:
            args.append('-' + 'v' * min(5, inventory_update.verbosity * 2 + 1))

        return args

    def build_inventory(self, inventory_update, private_data_dir):
        return None  # what runner expects in order to not deal with inventory

    def pseudo_build_inventory(self, inventory_update, private_data_dir):
        """Inventory imports are ran through a management command
        we pass the inventory in args to that command, so this is not considered
        to be "Ansible" inventory (by runner) even though it is
        Eventually, we would like to cut out the management command,
        and thus use this as the real inventory
        """
        src = inventory_update.source

        injector = None
        if inventory_update.source in InventorySource.injectors:
            injector = InventorySource.injectors[src]()

        if injector is not None:
            content = injector.inventory_contents(inventory_update, private_data_dir)
            # must be a statically named file
            inventory_path = os.path.join(private_data_dir, 'inventory', injector.filename)
            with open(inventory_path, 'w') as f:
                f.write(content)
            os.chmod(inventory_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

            rel_path = os.path.join('inventory', injector.filename)
        elif src == 'scm':
            rel_path = os.path.join('project', inventory_update.source_path)

        return rel_path

    def build_playbook_path_relative_to_cwd(self, inventory_update, private_data_dir):
        return None

    def build_credentials_list(self, inventory_update):
        # All credentials not used by inventory source injector
        return inventory_update.get_extra_credentials()

    def pre_run_hook(self, inventory_update, private_data_dir):
        super(RunInventoryUpdate, self).pre_run_hook(inventory_update, private_data_dir)
        source_project = None
        if inventory_update.inventory_source:
            source_project = inventory_update.inventory_source.source_project
        if (
            inventory_update.source == 'scm' and inventory_update.launch_type != 'scm' and source_project and source_project.scm_type
        ):  # never ever update manual projects

            # Check if the content cache exists, so that we do not unnecessarily re-download roles
            sync_needs = ['update_{}'.format(source_project.scm_type)]
            has_cache = os.path.exists(os.path.join(source_project.get_cache_path(), source_project.cache_id))
            # Galaxy requirements are not supported for manual projects
            if not has_cache:
                sync_needs.extend(['install_roles', 'install_collections'])

            local_project_sync = source_project.create_project_update(
                _eager_fields=dict(
                    launch_type="sync",
                    job_type='run',
                    job_tags=','.join(sync_needs),
                    status='running',
                    execution_node=Instance.objects.me().hostname,
                    controller_node=Instance.objects.me().hostname,
                    instance_group=inventory_update.instance_group,
                    celery_task_id=inventory_update.celery_task_id,
                )
            )
            local_project_sync.log_lifecycle("controller_node_chosen")
            local_project_sync.log_lifecycle("execution_node_chosen")
            create_partition(local_project_sync.event_class._meta.db_table, start=local_project_sync.created)
            # associate the inventory update before calling run() so that a
            # cancel() call on the inventory update can cancel the project update
            local_project_sync.scm_inventory_updates.add(inventory_update)

            project_update_task = local_project_sync._get_task_class()
            try:
                sync_task = project_update_task(job_private_data_dir=private_data_dir)
                sync_task.run(local_project_sync.id)
                local_project_sync.refresh_from_db()
                inventory_update.inventory_source.scm_last_revision = local_project_sync.scm_revision
                inventory_update.inventory_source.save(update_fields=['scm_last_revision'])
            except Exception:
                inventory_update = self.update_model(
                    inventory_update.pk,
                    status='failed',
                    job_explanation=(
                        'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}'
                        % ('project_update', local_project_sync.name, local_project_sync.id)
                    ),
                )
                raise
        elif inventory_update.source == 'scm' and inventory_update.launch_type == 'scm' and source_project:
            # This follows update, not sync, so make copy here
            RunProjectUpdate.make_local_copy(source_project, private_data_dir)

    def post_run_hook(self, inventory_update, status):
        super(RunInventoryUpdate, self).post_run_hook(inventory_update, status)
        if status != 'successful':
            return  # nothing to save, step out of the way to allow error reporting

        inventory_update.refresh_from_db()
        private_data_dir = inventory_update.job_env['AWX_PRIVATE_DATA_DIR']
        expected_output = os.path.join(private_data_dir, 'artifacts', str(inventory_update.id), 'output.json')
        with open(expected_output) as f:
            data = json.load(f)

        # build inventory save options
        options = dict(
            overwrite=inventory_update.overwrite,
            overwrite_vars=inventory_update.overwrite_vars,
        )
        src = inventory_update.source

        if inventory_update.enabled_var:
            options['enabled_var'] = inventory_update.enabled_var
            options['enabled_value'] = inventory_update.enabled_value
        else:
            if getattr(settings, '%s_ENABLED_VAR' % src.upper(), False):
                options['enabled_var'] = getattr(settings, '%s_ENABLED_VAR' % src.upper())
            if getattr(settings, '%s_ENABLED_VALUE' % src.upper(), False):
                options['enabled_value'] = getattr(settings, '%s_ENABLED_VALUE' % src.upper())

        if inventory_update.host_filter:
            options['host_filter'] = inventory_update.host_filter

        if getattr(settings, '%s_EXCLUDE_EMPTY_GROUPS' % src.upper()):
            options['exclude_empty_groups'] = True
        if getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper(), False):
            options['instance_id_var'] = getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper())

        # Verbosity is applied to saving process, as well as ansible-inventory CLI option
        if inventory_update.verbosity:
            options['verbosity'] = inventory_update.verbosity

        handler = SpecialInventoryHandler(
            self.runner_callback.event_handler,
            self.runner_callback.cancel_callback,
            verbosity=inventory_update.verbosity,
            job_timeout=self.get_instance_timeout(self.instance),
            start_time=inventory_update.started,
            counter=self.runner_callback.event_ct,
            initial_line=self.runner_callback.end_line,
        )
        inv_logger = logging.getLogger('awx.main.commands.inventory_import')
        formatter = inv_logger.handlers[0].formatter
        formatter.job_start = inventory_update.started
        handler.formatter = formatter
        inv_logger.handlers[0] = handler

        from awx.main.management.commands.inventory_import import Command as InventoryImportCommand

        cmd = InventoryImportCommand()
        try:
            # save the inventory data to database.
            # canceling exceptions will be handled in the global post_run_hook
            cmd.perform_update(options, data, inventory_update)
        except PermissionDenied as exc:
            logger.exception('License error saving {} content'.format(inventory_update.log_format))
            raise PostRunError(str(exc), status='error')
        except PostRunError:
            logger.exception('Error saving {} content, rolling back changes'.format(inventory_update.log_format))
            raise
        except Exception:
            logger.exception('Exception saving {} content, rolling back changes.'.format(inventory_update.log_format))
            raise PostRunError('Error occured while saving inventory data, see traceback or server logs', status='error', tb=traceback.format_exc())


@task(queue=get_local_queuename)
class RunAdHocCommand(BaseTask):
    """
    Run an ad hoc command using ansible.
    """

    model = AdHocCommand
    event_model = AdHocCommandEvent
    callback_class = RunnerCallbackForAdHocCommand

    def build_private_data(self, ad_hoc_command, private_data_dir):
        """
        Return SSH private key data needed for this ad hoc command (only if
        stored in DB as ssh_key_data).

        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                ...
            },
            'certificates': {
                <awx.main.models.Credential>: <signed SSH certificate data>,
                <awx.main.models.Credential>: <signed SSH certificate data>,
                ...
            }
        }
        """
        # If we were sent SSH credentials, decrypt them and send them
        # back (they will be written to a temporary file).
        creds = ad_hoc_command.credential
        private_data = {'credentials': {}}
        if creds and creds.has_input('ssh_key_data'):
            private_data['credentials'][creds] = creds.get_input('ssh_key_data', default='')
        if creds and creds.has_input('ssh_public_key_data'):
            private_data.setdefault('certificates', {})[creds] = creds.get_input('ssh_public_key_data', default='')
        return private_data

    def build_passwords(self, ad_hoc_command, runtime_passwords):
        """
        Build a dictionary of passwords for SSH private key, SSH user and
        sudo/su.
        """
        passwords = super(RunAdHocCommand, self).build_passwords(ad_hoc_command, runtime_passwords)
        cred = ad_hoc_command.credential
        if cred:
            for field in ('ssh_key_unlock', 'ssh_password', 'become_password'):
                value = runtime_passwords.get(field, cred.get_input('password' if field == 'ssh_password' else field, default=''))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, ad_hoc_command, private_data_dir, private_data_files=None):
        """
        Build environment dictionary for ansible.
        """
        env = super(RunAdHocCommand, self).build_env(ad_hoc_command, private_data_dir, private_data_files=private_data_files)
        # Set environment variables needed for inventory and ad hoc event
        # callbacks to work.
        env['AD_HOC_COMMAND_ID'] = str(ad_hoc_command.pk)
        env['INVENTORY_ID'] = str(ad_hoc_command.inventory.pk)
        env['INVENTORY_HOSTVARS'] = str(True)
        env['ANSIBLE_LOAD_CALLBACK_PLUGINS'] = '1'
        env['ANSIBLE_SFTP_BATCH_MODE'] = 'False'

        return env

    def build_args(self, ad_hoc_command, private_data_dir, passwords):
        """
        Build command line argument list for running ansible, optionally using
        ssh-agent for public/private key authentication.
        """
        creds = ad_hoc_command.credential
        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = creds.get_input('username', default='')
            become_method = creds.get_input('become_method', default='')
            become_username = creds.get_input('become_username', default='')
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible's default of using the
        # current user.
        ssh_username = ssh_username or 'root'
        args = []
        if ad_hoc_command.job_type == 'check':
            args.append('--check')
        args.extend(['-u', sanitize_jinja(ssh_username)])
        if 'ssh_password' in passwords:
            args.append('--ask-pass')
        # We only specify sudo/su user and password if explicitly given by the
        # credential.  Credential should never specify both sudo and su.
        if ad_hoc_command.become_enabled:
            args.append('--become')
        if become_method:
            args.extend(['--become-method', sanitize_jinja(become_method)])
        if become_username:
            args.extend(['--become-user', sanitize_jinja(become_username)])
        if 'become_password' in passwords:
            args.append('--ask-become-pass')

        if ad_hoc_command.forks:  # FIXME: Max limit?
            args.append('--forks=%d' % ad_hoc_command.forks)
        if ad_hoc_command.diff_mode:
            args.append('--diff')
        if ad_hoc_command.verbosity:
            args.append('-%s' % ('v' * min(5, ad_hoc_command.verbosity)))

        extra_vars = ad_hoc_command.awx_meta_vars()

        if ad_hoc_command.extra_vars_dict:
            redacted_extra_vars, removed_vars = extract_ansible_vars(ad_hoc_command.extra_vars_dict)
            if removed_vars:
                raise ValueError(_("{} are prohibited from use in ad hoc commands.").format(", ".join(removed_vars)))
            extra_vars.update(ad_hoc_command.extra_vars_dict)

        if ad_hoc_command.limit:
            args.append(ad_hoc_command.limit)
        else:
            args.append('all')

        return args

    def build_extra_vars_file(self, ad_hoc_command, private_data_dir):
        extra_vars = ad_hoc_command.awx_meta_vars()

        if ad_hoc_command.extra_vars_dict:
            redacted_extra_vars, removed_vars = extract_ansible_vars(ad_hoc_command.extra_vars_dict)
            if removed_vars:
                raise ValueError(_("{} are prohibited from use in ad hoc commands.").format(", ".join(removed_vars)))
            extra_vars.update(ad_hoc_command.extra_vars_dict)
        self._write_extra_vars_file(private_data_dir, extra_vars)

    def build_module_name(self, ad_hoc_command):
        return ad_hoc_command.module_name

    def build_module_args(self, ad_hoc_command):
        module_args = ad_hoc_command.module_args
        if settings.ALLOW_JINJA_IN_EXTRA_VARS != 'always':
            module_args = sanitize_jinja(module_args)
        return module_args

    def build_playbook_path_relative_to_cwd(self, job, private_data_dir):
        return None

    def get_password_prompts(self, passwords={}):
        d = super(RunAdHocCommand, self).get_password_prompts()
        d[r'Enter passphrase for .*:\s*?$'] = 'ssh_key_unlock'
        d[r'Bad passphrase, try again for .*:\s*?$'] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[r'%s password.*:\s*?$' % (method[0])] = 'become_password'
            d[r'%s password.*:\s*?$' % (method[0].upper())] = 'become_password'
        d[r'BECOME password.*:\s*?$'] = 'become_password'
        d[r'SSH password:\s*?$'] = 'ssh_password'
        d[r'Password:\s*?$'] = 'ssh_password'
        return d


@task(queue=get_local_queuename)
class RunSystemJob(BaseTask):

    model = SystemJob
    event_model = SystemJobEvent
    callback_class = RunnerCallbackForSystemJob

    def build_execution_environment_params(self, system_job, private_data_dir):
        return {}

    def build_args(self, system_job, private_data_dir, passwords):
        args = ['awx-manage', system_job.job_type]
        try:
            # System Job extra_vars can be blank, must be JSON if not blank
            if system_job.extra_vars == '':
                json_vars = {}
            else:
                json_vars = json.loads(system_job.extra_vars)
            if system_job.job_type in ('cleanup_jobs', 'cleanup_activitystream'):
                if 'days' in json_vars:
                    args.extend(['--days', str(json_vars.get('days', 60))])
                if 'dry_run' in json_vars and json_vars['dry_run']:
                    args.extend(['--dry-run'])
            if system_job.job_type == 'cleanup_jobs':
                args.extend(
                    ['--jobs', '--project-updates', '--inventory-updates', '--management-jobs', '--ad-hoc-commands', '--workflow-jobs', '--notifications']
                )
        except Exception:
            logger.exception("{} Failed to parse system job".format(system_job.log_format))
        return args

    def write_args_file(self, private_data_dir, args):
        path = os.path.join(private_data_dir, 'args')
        handle = os.open(path, os.O_RDWR | os.O_CREAT, stat.S_IREAD | stat.S_IWRITE)
        f = os.fdopen(handle, 'w')
        f.write(' '.join(args))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def build_env(self, instance, private_data_dir, private_data_files=None):
        base_env = super(RunSystemJob, self).build_env(instance, private_data_dir, private_data_files=private_data_files)
        # TODO: this is able to run by turning off isolation
        # the goal is to run it a container instead
        env = dict(os.environ.items())
        env.update(base_env)
        return env

    def build_playbook_path_relative_to_cwd(self, job, private_data_dir):
        return None

    def build_inventory(self, instance, private_data_dir):
        return None
