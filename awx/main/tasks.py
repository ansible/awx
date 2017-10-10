# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import codecs
from collections import OrderedDict
import ConfigParser
import cStringIO
import functools
import imp
import json
import logging
import os
import re
import shutil
import stat
import tempfile
import time
import traceback
import urlparse
import uuid
from distutils.version import LooseVersion as Version
import yaml
import fcntl
try:
    import psutil
except:
    psutil = None

# Celery
from celery import Task, task
from celery.signals import celeryd_init, worker_process_init, worker_shutdown

# Django
from django.conf import settings
from django.db import transaction, DatabaseError, IntegrityError
from django.utils.timezone import now, timedelta
from django.utils.encoding import smart_str
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

# Django-CRUM
from crum import impersonate

# AWX
from awx import __version__ as awx_application_version
from awx.main.constants import CLOUD_PROVIDERS, PRIVILEGE_ESCALATION_METHODS
from awx.main.models import * # noqa
from awx.main.models.unified_jobs import ACTIVE_STATES
from awx.main.exceptions import AwxTaskError, TaskCancel, TaskError
from awx.main.queue import CallbackQueueDispatcher
from awx.main.expect import run, isolated_manager
from awx.main.utils import (get_ansible_version, get_ssh_version, decrypt_field, update_scm_url,
                            check_proot_installed, build_proot_temp_dir, get_licenser,
                            wrap_args_with_proot, get_system_task_capacity, OutputEventFilter,
                            parse_yaml_or_json, ignore_inventory_computed_fields, ignore_inventory_group_removal,
                            get_type_for_model)
from awx.main.utils.reload import restart_local_services, stop_local_services
from awx.main.utils.handlers import configure_external_logger
from awx.main.consumers import emit_channel_notification
from awx.conf import settings_registry

__all__ = ['RunJob', 'RunSystemJob', 'RunProjectUpdate', 'RunInventoryUpdate',
           'RunAdHocCommand', 'handle_work_error', 'handle_work_success',
           'update_inventory_computed_fields', 'update_host_smart_inventory_memberships',
           'send_notifications', 'run_administrative_checks', 'purge_old_stdout_files']

HIDDEN_PASSWORD = '**********'

OPENSSH_KEY_ERROR = u'''\
It looks like you're trying to use a private key in OpenSSH format, which \
isn't supported by the installed version of OpenSSH on this instance. \
Try upgrading OpenSSH or providing your private key in an different format. \
'''

logger = logging.getLogger('awx.main.tasks')


class LogErrorsTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if isinstance(exc, AwxTaskError):
            # Error caused by user / tracked in job output
            logger.warning(str(exc))
        elif isinstance(self, BaseTask):
            logger.exception(
                '%s %s execution encountered exception.',
                get_type_for_model(self.model), args[0])
        else:
            logger.exception('Task {} encountered exception.'.format(self.name), exc_info=exc)
        super(LogErrorsTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@celeryd_init.connect
def celery_startup(conf=None, **kwargs):
    # Re-init all schedules
    # NOTE: Rework this during the Rampart work
    startup_logger = logging.getLogger('awx.main.tasks')
    startup_logger.info("Syncing Schedules")
    for sch in Schedule.objects.all():
        try:
            sch.update_computed_fields()
            from awx.main.signals import disable_activity_stream
            with disable_activity_stream():
                sch.save()
        except:
            logger.exception("Failed to rebuild schedule {}.".format(sch))


@worker_process_init.connect
def task_set_logger_pre_run(*args, **kwargs):
    try:
        cache.close()
        configure_external_logger(settings, is_startup=False)
    except:
        # General exception because LogErrorsTask not used with celery signals
        logger.exception('Encountered error on initial log configuration.')


@worker_shutdown.connect
def inform_cluster_of_shutdown(*args, **kwargs):
    try:
        this_inst = Instance.objects.get(hostname=settings.CLUSTER_HOST_ID)
        this_inst.capacity = 0  # No thank you to new jobs while shut down
        this_inst.save(update_fields=['capacity', 'modified'])
        logger.warning('Normal shutdown signal for instance {}, '
                       'removed self from capacity pool.'.format(this_inst.hostname))
    except:
        # General exception because LogErrorsTask not used with celery signals
        logger.exception('Encountered problem with normal shutdown signal.')


@task(queue='tower_broadcast_all', bind=True, base=LogErrorsTask)
def handle_setting_changes(self, setting_keys):
    orig_len = len(setting_keys)
    for i in range(orig_len):
        for dependent_key in settings_registry.get_dependent_settings(setting_keys[i]):
            setting_keys.append(dependent_key)
    logger.warn('Processing cache changes, task args: {0.args!r} kwargs: {0.kwargs!r}'.format(
        self.request))
    cache_keys = set(setting_keys)
    logger.debug('cache delete_many(%r)', cache_keys)
    cache.delete_many(cache_keys)
    for key in cache_keys:
        if key.startswith('LOG_AGGREGATOR_'):
            restart_local_services(['uwsgi', 'celery', 'beat', 'callback'])
            break


@task(queue='tower', base=LogErrorsTask)
def send_notifications(notification_list, job_id=None):
    if not isinstance(notification_list, list):
        raise TypeError("notification_list should be of type list")
    if job_id is not None:
        job_actual = UnifiedJob.objects.get(id=job_id)

    notifications = Notification.objects.filter(id__in=notification_list)
    if job_id is not None:
        job_actual.notifications.add(*notifications)

    for notification in notifications:
        try:
            sent = notification.notification_template.send(notification.subject, notification.body)
            notification.status = "successful"
            notification.notifications_sent = sent
        except Exception as e:
            logger.error("Send Notification Failed {}".format(e))
            notification.status = "failed"
            notification.error = smart_str(e)
        finally:
            notification.save()


@task(bind=True, queue='tower', base=LogErrorsTask)
def run_administrative_checks(self):
    logger.warn("Running administrative checks.")
    if not settings.TOWER_ADMIN_ALERTS:
        return
    validation_info = get_licenser().validate()
    if validation_info['license_type'] != 'open' and validation_info.get('instance_count', 0) < 1:
        return
    used_percentage = float(validation_info.get('current_instances', 0)) / float(validation_info.get('instance_count', 100))
    tower_admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    if (used_percentage * 100) > 90:
        send_mail("Ansible Tower host usage over 90%",
                  _("Ansible Tower host usage over 90%"),
                  tower_admin_emails,
                  fail_silently=True)
    if validation_info.get('date_warning', False):
        send_mail("Ansible Tower license will expire soon",
                  _("Ansible Tower license will expire soon"),
                  tower_admin_emails,
                  fail_silently=True)


@task(bind=True, queue='tower', base=LogErrorsTask)
def cleanup_authtokens(self):
    logger.warn("Cleaning up expired authtokens.")
    AuthToken.objects.filter(expires__lt=now()).delete()


@task(bind=True, base=LogErrorsTask)
def purge_old_stdout_files(self):
    nowtime = time.time()
    for f in os.listdir(settings.JOBOUTPUT_ROOT):
        if os.path.getctime(os.path.join(settings.JOBOUTPUT_ROOT,f)) < nowtime - settings.LOCAL_STDOUT_EXPIRE_TIME:
            os.unlink(os.path.join(settings.JOBOUTPUT_ROOT,f))
            logger.info("Removing {}".format(os.path.join(settings.JOBOUTPUT_ROOT,f)))


@task(bind=True, base=LogErrorsTask)
def cluster_node_heartbeat(self):
    logger.debug("Cluster node heartbeat task.")
    nowtime = now()
    instance_list = list(Instance.objects.filter(rampart_groups__controller__isnull=True).distinct())
    this_inst = None
    lost_instances = []
    for inst in list(instance_list):
        if inst.hostname == settings.CLUSTER_HOST_ID:
            this_inst = inst
            instance_list.remove(inst)
        elif inst.is_lost(ref_time=nowtime):
            lost_instances.append(inst)
            instance_list.remove(inst)
    if this_inst:
        startup_event = this_inst.is_lost(ref_time=nowtime)
        if this_inst.capacity == 0:
            logger.warning('Rejoining the cluster as instance {}.'.format(this_inst.hostname))
        this_inst.capacity = get_system_task_capacity()
        this_inst.version = awx_application_version
        this_inst.save(update_fields=['capacity', 'version', 'modified'])
        if startup_event:
            return
    else:
        raise RuntimeError("Cluster Host Not Found: {}".format(settings.CLUSTER_HOST_ID))
    # IFF any node has a greater version than we do, then we'll shutdown services
    for other_inst in instance_list:
        if other_inst.version == "":
            continue
        if Version(other_inst.version.split('-', 1)[0]) > Version(awx_application_version) and not settings.DEBUG:
            logger.error("Host {} reports version {}, but this node {} is at {}, shutting down".format(other_inst.hostname,
                                                                                                       other_inst.version,
                                                                                                       this_inst.hostname,
                                                                                                       this_inst.version))
            # Shutdown signal will set the capacity to zero to ensure no Jobs get added to this instance.
            # The heartbeat task will reset the capacity to the system capacity after upgrade.
            stop_local_services(['uwsgi', 'celery', 'beat', 'callback'], communicate=False)
            raise RuntimeError("Shutting down.")
    for other_inst in lost_instances:
        if other_inst.capacity == 0:
            continue
        try:
            other_inst.capacity = 0
            other_inst.save(update_fields=['capacity'])
            logger.error("Host {} last checked in at {}, marked as lost.".format(
                other_inst.hostname, other_inst.modified))
        except DatabaseError as e:
            if 'did not affect any rows' in str(e):
                logger.debug('Another instance has marked {} as lost'.format(other_inst.hostname))
            else:
                logger.exception('Error marking {} as lost'.format(other_inst.hostname))


@task(bind=True, base=LogErrorsTask)
def awx_isolated_heartbeat(self):
    local_hostname = settings.CLUSTER_HOST_ID
    logger.debug("Controlling node checking for any isolated management tasks.")
    poll_interval = settings.AWX_ISOLATED_PERIODIC_CHECK
    # Get isolated instances not checked since poll interval - some buffer
    nowtime = now()
    accept_before = nowtime - timedelta(seconds=(poll_interval - 10))
    isolated_instance_qs = Instance.objects.filter(
        rampart_groups__controller__instances__hostname=local_hostname,
        last_isolated_check__lt=accept_before
    )
    # Fast pass of isolated instances, claiming the nodes to update
    with transaction.atomic():
        for isolated_instance in isolated_instance_qs:
            isolated_instance.last_isolated_check = nowtime
            # Prevent modified time from being changed, as in normal heartbeat
            isolated_instance.save(update_fields=['last_isolated_check'])
    # Slow pass looping over isolated IGs and their isolated instances
    if len(isolated_instance_qs) > 0:
        logger.debug("Managing isolated instances {}.".format(','.join([inst.hostname for inst in isolated_instance_qs])))
        isolated_manager.IsolatedManager.health_check(isolated_instance_qs)


@task(bind=True, queue='tower', base=LogErrorsTask)
def awx_periodic_scheduler(self):
    run_now = now()
    state = TowerScheduleState.get_solo()
    last_run = state.schedule_last_run
    logger.debug("Last scheduler run was: %s", last_run)
    state.schedule_last_run = run_now
    state.save()

    old_schedules = Schedule.objects.enabled().before(last_run)
    for schedule in old_schedules:
        schedule.save()
    schedules = Schedule.objects.enabled().between(last_run, run_now)
    for schedule in schedules:
        template = schedule.unified_job_template
        schedule.save() # To update next_run timestamp.
        if template.cache_timeout_blocked:
            logger.warn("Cache timeout is in the future, bypassing schedule for template %s" % str(template.id))
            continue
        new_unified_job = template.create_unified_job(launch_type='scheduled', schedule=schedule)
        can_start = new_unified_job.signal_start(extra_vars=parse_yaml_or_json(schedule.extra_data))
        if not can_start:
            new_unified_job.status = 'failed'
            new_unified_job.job_explanation = "Scheduled job could not start because it was not in the right state or required manual credentials"
            new_unified_job.save(update_fields=['status', 'job_explanation'])
            new_unified_job.websocket_emit_status("failed")
        emit_channel_notification('schedules-changed', dict(id=schedule.id, group_name="schedules"))
    state.save()


def _send_notification_templates(instance, status_str):
    if status_str not in ['succeeded', 'failed']:
        raise ValueError(_("status_str must be either succeeded or failed"))
    try:
        notification_templates = instance.get_notification_templates()
    except:
        logger.warn("No notification template defined for emitting notification")
        notification_templates = None
    if notification_templates:
        if status_str == 'succeeded':
            notification_template_type = 'success'
        else:
            notification_template_type = 'error'
        all_notification_templates = set(notification_templates.get(notification_template_type, []) + notification_templates.get('any', []))
        if len(all_notification_templates):
            try:
                (notification_subject, notification_body) = getattr(instance, 'build_notification_%s_message' % status_str)()
            except AttributeError:
                raise NotImplementedError("build_notification_%s_message() does not exist" % status_str)
            send_notifications.delay([n.generate_notification(notification_subject, notification_body).id
                                      for n in all_notification_templates],
                                     job_id=instance.id)


@task(bind=True, queue='tower', base=LogErrorsTask)
def handle_work_success(self, result, task_actual):
    try:
        instance = UnifiedJob.get_instance_by_type(task_actual['type'], task_actual['id'])
    except ObjectDoesNotExist:
        logger.warning('Missing {} `{}` in success callback.'.format(task_actual['type'], task_actual['id']))
        return
    if not instance:
        return

    _send_notification_templates(instance, 'succeeded')

    from awx.main.scheduler.tasks import run_job_complete
    run_job_complete.delay(instance.id)


@task(bind=True, queue='tower', base=LogErrorsTask)
def handle_work_error(self, task_id, subtasks=None):
    logger.debug('Executing error task id %s, subtasks: %s' % (str(self.request.id), str(subtasks)))
    first_instance = None
    first_instance_type = ''
    if subtasks is not None:
        for each_task in subtasks:
            try:
                instance = UnifiedJob.get_instance_by_type(each_task['type'], each_task['id'])
                if not instance:
                    # Unknown task type
                    logger.warn("Unknown task type: {}".format(each_task['type']))
                    continue
            except ObjectDoesNotExist:
                logger.warning('Missing {} `{}` in error callback.'.format(each_task['type'], each_task['id']))
                continue

            if first_instance is None:
                first_instance = instance
                first_instance_type = each_task['type']

            if instance.celery_task_id != task_id and not instance.cancel_flag:
                instance.status = 'failed'
                instance.failed = True
                if not instance.job_explanation:
                    instance.job_explanation = 'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % \
                                               (first_instance_type, first_instance.name, first_instance.id)
                instance.save()
                instance.websocket_emit_status("failed")

        if first_instance:
            _send_notification_templates(first_instance, 'failed')

    # We only send 1 job complete message since all the job completion message
    # handling does is trigger the scheduler. If we extend the functionality of
    # what the job complete message handler does then we may want to send a
    # completion event for each job here.
    if first_instance:
        from awx.main.scheduler.tasks import run_job_complete
        run_job_complete.delay(first_instance.id)
        pass


@task(queue='tower', base=LogErrorsTask)
def update_inventory_computed_fields(inventory_id, should_update_hosts=True):
    '''
    Signal handler and wrapper around inventory.update_computed_fields to
    prevent unnecessary recursive calls.
    '''
    i = Inventory.objects.filter(id=inventory_id)
    if not i.exists():
        logger.error("Update Inventory Computed Fields failed due to missing inventory: " + str(inventory_id))
        return
    i = i[0]
    try:
        i.update_computed_fields(update_hosts=should_update_hosts)
    except DatabaseError as e:
        if 'did not affect any rows' in str(e):
            logger.debug('Exiting duplicate update_inventory_computed_fields task.')
            return
        raise


@task(queue='tower', base=LogErrorsTask)
def update_host_smart_inventory_memberships():
    try:
        with transaction.atomic():
            smart_inventories = Inventory.objects.filter(kind='smart', host_filter__isnull=False, pending_deletion=False)
            SmartInventoryMembership.objects.all().delete()
            memberships = []
            for smart_inventory in smart_inventories:
                memberships.extend([SmartInventoryMembership(inventory_id=smart_inventory.id, host_id=host_id[0])
                                    for host_id in smart_inventory.hosts.values_list('id')])
            SmartInventoryMembership.objects.bulk_create(memberships)
    except IntegrityError as e:
        logger.error("Update Host Smart Inventory Memberships failed due to an exception: " + str(e))
        return


@task(bind=True, queue='tower', base=LogErrorsTask, max_retries=5)
def delete_inventory(self, inventory_id, user_id):
    # Delete inventory as user
    if user_id is None:
        user = None
    else:
        try:
            user = User.objects.get(id=user_id)
        except:
            user = None
    with ignore_inventory_computed_fields(), ignore_inventory_group_removal(), impersonate(user):
        try:
            i = Inventory.objects.get(id=inventory_id)
            i.delete()
            emit_channel_notification(
                'inventories-status_changed',
                {'group_name': 'inventories', 'inventory_id': inventory_id, 'status': 'deleted'}
            )
            logger.debug('Deleted inventory %s as user %s.' % (inventory_id, user_id))
        except Inventory.DoesNotExist:
            logger.error("Delete Inventory failed due to missing inventory: " + str(inventory_id))
            return
        except DatabaseError:
            logger.warning('Database error deleting inventory {}, but will retry.'.format(inventory_id))
            self.retry(countdown=10)


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


class BaseTask(LogErrorsTask):
    name = None
    model = None
    abstract = True
    cleanup_paths = []
    proot_show_paths = []

    def update_model(self, pk, _attempt=0, **updates):
        """Reload the model instance from the database and update the
        given fields.
        """
        output_replacements = updates.pop('output_replacements', None) or []

        try:
            with transaction.atomic():
                # Retrieve the model instance.
                instance = self.model.objects.get(pk=pk)

                # Update the appropriate fields and save the model
                # instance, then return the new instance.
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
                return instance
        except DatabaseError as e:
            # Log out the error to the debug logger.
            logger.debug('Database error updating %s, retrying in 5 '
                         'seconds (retry #%d): %s',
                         self.model._meta.object_name, _attempt + 1, e)

            # Attempt to retry the update, assuming we haven't already
            # tried too many times.
            if _attempt < 5:
                time.sleep(5)
                return self.update_model(
                    pk,
                    _attempt=_attempt + 1,
                    output_replacements=output_replacements,
                    **updates
                )
            else:
                logger.error('Failed to update %s after %d retries.',
                             self.model._meta.object_name, _attempt)

    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_private_data(self, job, **kwargs):
        '''
        Return SSH private key data (only if stored in DB as ssh_key_data).
        Return structure is a dict of the form:
        '''

    def build_private_data_dir(self, instance, **kwargs):
        '''
        Create a temporary directory for job-related files.
        '''
        path = tempfile.mkdtemp(prefix='awx_%s_' % instance.pk, dir=settings.AWX_PROOT_BASE_PATH)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        self.cleanup_paths.append(path)
        return path

    def build_private_data_files(self, instance, **kwargs):
        '''
        Creates temporary files containing the private data.
        Returns a dictionary i.e.,

        {
            'credentials': {
                <awx.main.models.Credential>: '/path/to/decrypted/data',
                <awx.main.models.Credential>: '/path/to/decrypted/data',
                <awx.main.models.Credential>: '/path/to/decrypted/data',
            }
        }
        '''
        private_data = self.build_private_data(instance, **kwargs)
        private_data_files = {'credentials': {}}
        if private_data is not None:
            ssh_ver = get_ssh_version()
            ssh_too_old = True if ssh_ver == "unknown" else Version(ssh_ver) < Version("6.0")
            openssh_keys_supported = ssh_ver != "unknown" and Version(ssh_ver) >= Version("6.5")
            for credential, data in private_data.get('credentials', {}).iteritems():
                # Bail out now if a private key was provided in OpenSSH format
                # and we're running an earlier version (<6.5).
                if 'OPENSSH PRIVATE KEY' in data and not openssh_keys_supported:
                    raise RuntimeError(OPENSSH_KEY_ERROR)
            for credential, data in private_data.get('credentials', {}).iteritems():
                # OpenSSH formatted keys must have a trailing newline to be
                # accepted by ssh-add.
                if 'OPENSSH PRIVATE KEY' in data and not data.endswith('\n'):
                    data += '\n'
                # For credentials used with ssh-add, write to a named pipe which
                # will be read then closed, instead of leaving the SSH key on disk.
                if credential and credential.kind in ('ssh', 'scm') and not ssh_too_old:
                    name = 'credential_%d' % credential.pk
                    path = os.path.join(kwargs['private_data_dir'], name)
                    run.open_fifo_write(path, data)
                    private_data_files['credentials']['ssh'] = path
                # Ansible network modules do not yet support ssh-agent.
                # Instead, ssh private key file is explicitly passed via an
                # env variable.
                else:
                    handle, path = tempfile.mkstemp(dir=kwargs.get('private_data_dir', None))
                    f = os.fdopen(handle, 'w')
                    f.write(data)
                    f.close()
                    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
                private_data_files['credentials'][credential] = path
        return private_data_files

    def build_passwords(self, instance, **kwargs):
        '''
        Build a dictionary of passwords for responding to prompts.
        '''
        return {
            'yes': 'yes',
            'no': 'no',
            '': '',
        }

    def add_ansible_venv(self, env, add_awx_lib=True):
        env['VIRTUAL_ENV'] = settings.ANSIBLE_VENV_PATH
        env['PATH'] = os.path.join(settings.ANSIBLE_VENV_PATH, "bin") + ":" + env['PATH']
        venv_libdir = os.path.join(settings.ANSIBLE_VENV_PATH, "lib")
        env.pop('PYTHONPATH', None)  # default to none if no python_ver matches
        for python_ver in ["python2.7", "python2.6"]:
            if os.path.isdir(os.path.join(venv_libdir, python_ver)):
                env['PYTHONPATH'] = os.path.join(venv_libdir, python_ver, "site-packages") + ":"
                break
        # Add awx/lib to PYTHONPATH.
        if add_awx_lib:
            env['PYTHONPATH'] = env.get('PYTHONPATH', '') + self.get_path_to('..', 'lib') + ':'
        return env

    def add_awx_venv(self, env):
        env['VIRTUAL_ENV'] = settings.AWX_VENV_PATH
        env['PATH'] = os.path.join(settings.AWX_VENV_PATH, "bin") + ":" + env['PATH']
        return env

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
        # NOTE:
        # Derived class should call add_ansible_venv() or add_awx_venv()
        if self.should_use_proot(instance, **kwargs):
            env['PROOT_TMP_DIR'] = settings.AWX_PROOT_BASE_PATH
        return env

    def build_safe_env(self, env, **kwargs):
        '''
        Build environment dictionary, hiding potentially sensitive information
        such as passwords or keys.
        '''
        hidden_re = re.compile(r'API|TOKEN|KEY|SECRET|PASS', re.I)
        urlpass_re = re.compile(r'^.*?://[^:]+:(.*?)@.*?$')
        safe_env = dict(env)
        for k,v in safe_env.items():
            if k in ('REST_API_URL', 'AWS_ACCESS_KEY_ID'):
                continue
            elif k.startswith('ANSIBLE_') and not k.startswith('ANSIBLE_NET'):
                continue
            elif hidden_re.search(k):
                safe_env[k] = HIDDEN_PASSWORD
            elif type(v) == str and urlpass_re.match(v):
                safe_env[k] = urlpass_re.sub(HIDDEN_PASSWORD, v)
        return safe_env

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return False

    def build_inventory(self, instance, **kwargs):
        plugin = self.get_path_to('..', 'plugins', 'inventory', 'awxrest.py')
        if kwargs.get('isolated') is True:
            # For isolated jobs, we have to interact w/ the REST API from the
            # controlling node and ship the static JSON inventory to the
            # isolated host (because the isolated host itself can't reach the
            # REST API to fetch the inventory).
            path = os.path.join(kwargs['private_data_dir'], 'inventory')
            if os.path.exists(path):
                return path
            awxrest = imp.load_source('awxrest', plugin)
            with open(path, 'w') as f:
                buff = cStringIO.StringIO()
                awxrest.InventoryScript(**{
                    'base_url': settings.INTERNAL_API_URL,
                    'authtoken': instance.task_auth_token or '',
                    'inventory_id': str(instance.inventory.pk),
                    'list': True,
                    'hostvars': True,
                }).run(buff)
                json_data = buff.getvalue().strip()
                f.write("#! /usr/bin/env python\nprint '''%s'''\n" % json_data)
                os.chmod(path, stat.S_IRUSR | stat.S_IXUSR)
            return path
        else:
            return plugin

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

    def get_password_prompts(self):
        '''
        Return a dictionary where keys are strings or regular expressions for
        prompts, and values are password lookup keys (keys that are returned
        from build_passwords).
        '''
        return OrderedDict()

    def get_stdout_handle(self, instance):
        '''
        Return an open file object for capturing stdout.
        '''
        if not os.path.exists(settings.JOBOUTPUT_ROOT):
            os.makedirs(settings.JOBOUTPUT_ROOT)
        stdout_filename = os.path.join(settings.JOBOUTPUT_ROOT, "%d-%s.out" % (instance.pk, str(uuid.uuid1())))
        stdout_handle = codecs.open(stdout_filename, 'w', encoding='utf-8')
        assert stdout_handle.name == stdout_filename
        return stdout_handle

    def pre_run_hook(self, instance, **kwargs):
        '''
        Hook for any steps to run before the job/task starts
        '''

    def post_run_hook(self, instance, status, **kwargs):
        '''
        Hook for any steps to run before job/task is marked as complete.
        '''

    def final_run_hook(self, instance, status, **kwargs):
        '''
        Hook for any steps to run after job/task is marked as complete.
        '''

    @with_path_cleanup
    def run(self, pk, isolated_host=None, **kwargs):
        '''
        Run the job/task and capture its output.
        '''
        execution_node = settings.CLUSTER_HOST_ID
        if isolated_host is not None:
            execution_node = isolated_host
        instance = self.update_model(pk, status='running', execution_node=execution_node)

        instance.websocket_emit_status("running")
        status, rc, tb = 'error', None, ''
        output_replacements = []
        extra_update_fields = {}
        try:
            kwargs['isolated'] = isolated_host is not None
            self.pre_run_hook(instance, **kwargs)
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

            if not os.path.exists(settings.AWX_PROOT_BASE_PATH):
                raise RuntimeError('AWX_PROOT_BASE_PATH=%s does not exist' % settings.AWX_PROOT_BASE_PATH)
            # Fetch ansible version once here to support version-dependent features.
            kwargs['ansible_version'] = get_ansible_version()
            kwargs['private_data_dir'] = self.build_private_data_dir(instance, **kwargs)
            # May have to serialize the value
            kwargs['private_data_files'] = self.build_private_data_files(instance, **kwargs)
            kwargs['passwords'] = self.build_passwords(instance, **kwargs)
            kwargs['proot_show_paths'] = self.proot_show_paths
            args = self.build_args(instance, **kwargs)
            safe_args = self.build_safe_args(instance, **kwargs)
            output_replacements = self.build_output_replacements(instance, **kwargs)
            cwd = self.build_cwd(instance, **kwargs)
            env = self.build_env(instance, **kwargs)
            safe_env = self.build_safe_env(env, **kwargs)

            # handle custom injectors specified on the CredentialType
            if hasattr(instance, 'all_credentials'):
                credentials = instance.all_credentials
            elif hasattr(instance, 'credential'):
                credentials = [instance.credential]
            else:
                credentials = []
            for credential in credentials:
                if credential:
                    credential.credential_type.inject_credential(
                        credential, env, safe_env, args, safe_args, kwargs['private_data_dir']
                    )

            if isolated_host is None:
                stdout_handle = self.get_stdout_handle(instance)
            else:
                base_handle = super(self.__class__, self).get_stdout_handle(instance)
                stdout_handle = isolated_manager.IsolatedManager.wrap_stdout_handle(
                    instance, kwargs['private_data_dir'], base_handle,
                    event_data_key=self.event_data_key)
            if self.should_use_proot(instance, **kwargs):
                if not check_proot_installed():
                    raise RuntimeError('bubblewrap is not installed')
                kwargs['proot_temp_dir'] = build_proot_temp_dir()
                self.cleanup_paths.append(kwargs['proot_temp_dir'])
                args = wrap_args_with_proot(args, cwd, **kwargs)
                safe_args = wrap_args_with_proot(safe_args, cwd, **kwargs)
            # If there is an SSH key path defined, wrap args with ssh-agent.
            ssh_key_path = self.get_ssh_key_path(instance, **kwargs)
            # If we're executing on an isolated host, don't bother adding the
            # key to the agent in this environment
            if ssh_key_path and isolated_host is None:
                ssh_auth_sock = os.path.join(kwargs['private_data_dir'], 'ssh_auth.sock')
                args = run.wrap_args_with_ssh_agent(args, ssh_key_path, ssh_auth_sock)
                safe_args = run.wrap_args_with_ssh_agent(safe_args, ssh_key_path, ssh_auth_sock)
            instance = self.update_model(pk, job_args=json.dumps(safe_args),
                                         job_cwd=cwd, job_env=safe_env, result_stdout_file=stdout_handle.name)

            expect_passwords = {}
            for k, v in self.get_password_prompts().items():
                expect_passwords[k] = kwargs['passwords'].get(v, '') or ''
            _kw = dict(
                expect_passwords=expect_passwords,
                cancelled_callback=lambda: self.update_model(instance.pk).cancel_flag,
                job_timeout=self.get_instance_timeout(instance),
                idle_timeout=self.get_idle_timeout(),
                extra_update_fields=extra_update_fields,
                pexpect_timeout=getattr(settings, 'PEXPECT_TIMEOUT', 5),
                proot_cmd=getattr(settings, 'AWX_PROOT_CMD', 'bwrap'),
            )
            instance = self.update_model(instance.pk, output_replacements=output_replacements)
            if isolated_host:
                manager_instance = isolated_manager.IsolatedManager(
                    args, cwd, env, stdout_handle, ssh_key_path, **_kw
                )
                status, rc = manager_instance.run(instance, isolated_host,
                                                  kwargs['private_data_dir'],
                                                  kwargs.get('proot_temp_dir'))
            else:
                status, rc = run.run_pexpect(
                    args, cwd, env, stdout_handle, **_kw
                )

        except Exception:
            if status != 'canceled':
                tb = traceback.format_exc()
                if settings.DEBUG:
                    logger.exception('%s Exception occurred while running task', instance.log_format)
        finally:
            try:
                stdout_handle.flush()
                stdout_handle.close()
            except Exception:
                pass

        try:
            self.post_run_hook(instance, status, **kwargs)
        except Exception:
            logger.exception('{} Post run hook errored.'.format(instance.log_format))
        instance = self.update_model(pk)
        if instance.cancel_flag:
            status = 'canceled'

        instance = self.update_model(pk, status=status, result_traceback=tb,
                                     output_replacements=output_replacements,
                                     **extra_update_fields)
        try:
            self.final_run_hook(instance, status, **kwargs)
        except:
            logger.exception('%s Final run hook errored.', instance.log_format)
        instance.websocket_emit_status(status)
        if status != 'successful' and not hasattr(settings, 'CELERY_UNIT_TEST'):
            # Raising an exception will mark the job as 'failed' in celery
            # and will stop a task chain from continuing to execute
            if status == 'canceled':
                raise TaskCancel(instance, rc)
            else:
                raise TaskError(instance, rc)

    def get_ssh_key_path(self, instance, **kwargs):
        '''
        If using an SSH key, return the path for use by ssh-agent.
        '''
        private_data_files = kwargs.get('private_data_files', {})
        if 'ssh' in private_data_files.get('credentials', {}):
            return private_data_files['credentials']['ssh']
        '''
        Note: Don't inject network ssh key data into ssh-agent for network
        credentials because the ansible modules do not yet support it.
        We will want to add back in support when/if Ansible network modules
        support this.
        '''

        return ''


class RunJob(BaseTask):
    '''
    Celery task to run a job using ansible-playbook.
    '''

    name = 'awx.main.tasks.run_job'
    model = Job
    event_data_key= 'job_id'

    def build_private_data(self, job, **kwargs):
        '''
        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>
            }
        }
        '''
        private_data = {'credentials': {}}
        for credential in job.all_credentials:
            # If we were sent SSH credentials, decrypt them and send them
            # back (they will be written to a temporary file).
            if credential.ssh_key_data not in (None, ''):
                private_data['credentials'][credential] = decrypt_field(credential, 'ssh_key_data') or ''

            if credential.kind == 'openstack':
                openstack_auth = dict(auth_url=credential.host,
                                      username=credential.username,
                                      password=decrypt_field(credential, "password"),
                                      project_name=credential.project)
                if credential.domain not in (None, ''):
                    openstack_auth['domain_name'] = credential.domain
                openstack_data = {
                    'clouds': {
                        'devstack': {
                            'auth': openstack_auth,
                        },
                    },
                }
                private_data['credentials'][credential] = yaml.safe_dump(openstack_data, default_flow_style=False, allow_unicode=True)

        return private_data

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user, sudo/su
        and ansible-vault.
        '''
        passwords = super(RunJob, self).build_passwords(job, **kwargs)
        for cred, fields in {
            'credential': ('ssh_key_unlock', 'ssh_password', 'become_password'),
            'vault_credential': ('vault_password',)
        }.items():
            cred = getattr(job, cred, None)
            if cred:
                for field in fields:
                    if field == 'ssh_password':
                        value = kwargs.get(field, decrypt_field(cred, 'password'))
                    else:
                        value = kwargs.get(field, decrypt_field(cred, field))
                    if value not in ('', 'ASK'):
                        passwords[field] = value
        return passwords

    def build_env(self, job, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        plugin_dirs = [plugin_dir]
        if hasattr(settings, 'AWX_ANSIBLE_CALLBACK_PLUGINS') and \
                settings.AWX_ANSIBLE_CALLBACK_PLUGINS:
            plugin_dirs.extend(settings.AWX_ANSIBLE_CALLBACK_PLUGINS)
        plugin_path = ':'.join(plugin_dirs)
        env = super(RunJob, self).build_env(job, **kwargs)
        env = self.add_ansible_venv(env, add_awx_lib=kwargs.get('isolated', False))
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['JOB_ID'] = str(job.pk)
        env['INVENTORY_ID'] = str(job.inventory.pk)
        if job.use_fact_cache and not kwargs.get('isolated'):
            env['ANSIBLE_LIBRARY'] = self.get_path_to('..', 'plugins', 'library')
            env['ANSIBLE_CACHE_PLUGINS'] = self.get_path_to('..', 'plugins', 'fact_caching')
            env['ANSIBLE_CACHE_PLUGIN'] = "awx"
            env['ANSIBLE_CACHE_PLUGIN_TIMEOUT'] = str(settings.ANSIBLE_FACT_CACHE_TIMEOUT)
            env['ANSIBLE_CACHE_PLUGIN_CONNECTION'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''
        if job.project:
            env['PROJECT_REVISION'] = job.project.scm_revision
        env['ANSIBLE_RETRY_FILES_ENABLED'] = "False"
        env['MAX_EVENT_RES'] = str(settings.MAX_EVENT_RES_DATA)
        if not kwargs.get('isolated'):
            env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_path
            env['ANSIBLE_STDOUT_CALLBACK'] = 'awx_display'
            env['REST_API_URL'] = settings.INTERNAL_API_URL
            env['REST_API_TOKEN'] = job.task_auth_token or ''
            env['TOWER_HOST'] = settings.TOWER_URL_BASE
            env['AWX_HOST'] = settings.TOWER_URL_BASE
            env['CALLBACK_QUEUE'] = settings.CALLBACK_QUEUE
            env['CALLBACK_CONNECTION'] = settings.BROKER_URL
        env['CACHE'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''
        if getattr(settings, 'JOB_CALLBACK_DEBUG', False):
            env['JOB_CALLBACK_DEBUG'] = '2'
        elif settings.DEBUG:
            env['JOB_CALLBACK_DEBUG'] = '1'

        # Create a directory for ControlPath sockets that is unique to each
        # job and visible inside the proot environment (when enabled).
        cp_dir = os.path.join(kwargs['private_data_dir'], 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0700)
        env['ANSIBLE_SSH_CONTROL_PATH'] = os.path.join(cp_dir, '%%h%%p%%r')

        # Allow the inventory script to include host variables inline via ['_meta']['hostvars'].
        env['INVENTORY_HOSTVARS'] = str(True)

        # Set environment variables for cloud credentials.
        cred_files = kwargs.get('private_data_files', {}).get('credentials', {})
        for cloud_cred in job.cloud_credentials:
            if cloud_cred and cloud_cred.kind == 'aws':
                env['AWS_ACCESS_KEY_ID'] = cloud_cred.username
                env['AWS_SECRET_ACCESS_KEY'] = decrypt_field(cloud_cred, 'password')
                if len(cloud_cred.security_token) > 0:
                    env['AWS_SECURITY_TOKEN'] = decrypt_field(cloud_cred, 'security_token')
                # FIXME: Add EC2_URL, maybe EC2_REGION!
            elif cloud_cred and cloud_cred.kind == 'gce':
                env['GCE_EMAIL'] = cloud_cred.username
                env['GCE_PROJECT'] = cloud_cred.project
                env['GCE_PEM_FILE_PATH'] = cred_files.get(cloud_cred, '')
            elif cloud_cred and cloud_cred.kind == 'azure_rm':
                if len(cloud_cred.client) and len(cloud_cred.tenant):
                    env['AZURE_CLIENT_ID'] = cloud_cred.client
                    env['AZURE_SECRET'] = decrypt_field(cloud_cred, 'secret')
                    env['AZURE_TENANT'] = cloud_cred.tenant
                    env['AZURE_SUBSCRIPTION_ID'] = cloud_cred.subscription
                else:
                    env['AZURE_SUBSCRIPTION_ID'] = cloud_cred.subscription
                    env['AZURE_AD_USER'] = cloud_cred.username
                    env['AZURE_PASSWORD'] = decrypt_field(cloud_cred, 'password')
            elif cloud_cred and cloud_cred.kind == 'vmware':
                env['VMWARE_USER'] = cloud_cred.username
                env['VMWARE_PASSWORD'] = decrypt_field(cloud_cred, 'password')
                env['VMWARE_HOST'] = cloud_cred.host
                env['VMWARE_VALIDATE_CERTS'] = str(settings.VMWARE_VALIDATE_CERTS)
            elif cloud_cred and cloud_cred.kind == 'openstack':
                env['OS_CLIENT_CONFIG_FILE'] = cred_files.get(cloud_cred, '')

        for network_cred in job.network_credentials:
            env['ANSIBLE_NET_USERNAME'] = network_cred.username
            env['ANSIBLE_NET_PASSWORD'] = decrypt_field(network_cred, 'password')

            ssh_keyfile = cred_files.get(network_cred, '')
            if ssh_keyfile:
                env['ANSIBLE_NET_SSH_KEYFILE'] = ssh_keyfile

            authorize = network_cred.authorize
            env['ANSIBLE_NET_AUTHORIZE'] = unicode(int(authorize))
            if authorize:
                env['ANSIBLE_NET_AUTH_PASS'] = decrypt_field(network_cred, 'authorize_password')

        return env

    def build_args(self, job, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.credential
        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = kwargs.get('username', creds.username)
            become_method = kwargs.get('become_method', creds.become_method)
            become_username = kwargs.get('become_username', creds.become_username)
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible-playbook's default of using
        # the current user.
        ssh_username = ssh_username or 'root'
        args = ['ansible-playbook', '-i', self.build_inventory(job, **kwargs)]
        if job.job_type == 'check':
            args.append('--check')
        args.extend(['-u', ssh_username])
        if 'ssh_password' in kwargs.get('passwords', {}):
            args.append('--ask-pass')
        if job.become_enabled:
            args.append('--become')
        if job.diff_mode:
            args.append('--diff')
        if become_method:
            args.extend(['--become-method', become_method])
        if become_username:
            args.extend(['--become-user', become_username])
        if 'become_password' in kwargs.get('passwords', {}):
            args.append('--ask-become-pass')
        # Support prompting for a vault password.
        if 'vault_password' in kwargs.get('passwords', {}):
            args.append('--ask-vault-pass')

        if job.forks:  # FIXME: Max limit?
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

        # Define special extra_vars for AWX, combine with job.extra_vars.
        extra_vars = {
            'tower_job_id': job.pk,
            'tower_job_launch_type': job.launch_type,
            'awx_job_id': job.pk,
            'awx_job_launch_type': job.launch_type,
        }
        if job.project:
            extra_vars.update({
                'tower_project_revision': job.project.scm_revision,
                'awx_project_revision': job.project.scm_revision,
            })
        if job.job_template:
            extra_vars.update({
                'tower_job_template_id': job.job_template.pk,
                'tower_job_template_name': job.job_template.name,
                'awx_job_template_id': job.job_template.pk,
                'awx_job_template_name': job.job_template.name,
            })
        if job.created_by:
            extra_vars.update({
                'tower_user_id': job.created_by.pk,
                'tower_user_name': job.created_by.username,
                'awx_user_id': job.created_by.pk,
                'awx_user_name': job.created_by.username,
            })
        if job.extra_vars_dict:
            if kwargs.get('display', False) and job.job_template:
                extra_vars.update(json.loads(job.display_extra_vars()))
            else:
                extra_vars.update(job.extra_vars_dict)
        args.extend(['-e', json.dumps(extra_vars)])

        # Add path to playbook (relative to project.local_path).
        args.append(job.playbook)
        return args

    def build_safe_args(self, job, **kwargs):
        return self.build_args(job, display=True, **kwargs)

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
        d[re.compile(r'Enter passphrase for .*:\s*?$', re.M)] = 'ssh_key_unlock'
        d[re.compile(r'Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[re.compile(r'%s password.*:\s*?$' % (method[0]), re.M)] = 'become_password'
            d[re.compile(r'%s password.*:\s*?$' % (method[0].upper()), re.M)] = 'become_password'
        d[re.compile(r'SSH password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Vault password:\s*?$', re.M)] = 'vault_password'
        return d

    def get_stdout_handle(self, instance):
        '''
        Wrap stdout file object to capture events.
        '''
        stdout_handle = super(RunJob, self).get_stdout_handle(instance)

        if getattr(settings, 'USE_CALLBACK_QUEUE', False):
            dispatcher = CallbackQueueDispatcher()

            def job_event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                if 'uuid' in event_data:
                    cache_event = cache.get('ev-{}'.format(event_data['uuid']), None)
                    if cache_event is not None:
                        event_data.update(cache_event)
                dispatcher.dispatch(event_data)
        else:
            def job_event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                JobEvent.create_from_data(**event_data)

        return OutputEventFilter(stdout_handle, job_event_callback)

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def pre_run_hook(self, job, **kwargs):
        if job.project and job.project.scm_type:
            job_request_id = '' if self.request.id is None else self.request.id
            pu_ig = job.instance_group
            pu_en = job.execution_node
            if kwargs['isolated']:
                pu_ig = pu_ig.controller
                pu_en = settings.CLUSTER_HOST_ID
            local_project_sync = job.project.create_project_update(
                launch_type="sync",
                _eager_fields=dict(
                    job_type='run',
                    status='running',
                    instance_group = pu_ig,
                    execution_node=pu_en,
                    celery_task_id=job_request_id))
            # save the associated job before calling run() so that a
            # cancel() call on the job can cancel the project update
            job = self.update_model(job.pk, project_update=local_project_sync)

            project_update_task = local_project_sync._get_task_class()
            try:
                task_instance = project_update_task()
                task_instance.request.id = job_request_id
                task_instance.run(local_project_sync.id)
                job = self.update_model(job.pk, scm_revision=job.project.scm_revision)
            except Exception:
                job = self.update_model(job.pk, status='failed',
                                        job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                                         ('project_update', local_project_sync.name, local_project_sync.id)))
                raise

        if job.use_fact_cache and not kwargs.get('isolated'):
            job.start_job_fact_cache()


    def final_run_hook(self, job, status, **kwargs):
        super(RunJob, self).final_run_hook(job, status, **kwargs)
        if job.use_fact_cache and not kwargs.get('isolated'):
            job.finish_job_fact_cache()
        try:
            inventory = job.inventory
        except Inventory.DoesNotExist:
            pass
        else:
            update_inventory_computed_fields.delay(inventory.id, True)


class RunProjectUpdate(BaseTask):

    name = 'awx.main.tasks.run_project_update'
    model = ProjectUpdate

    @property
    def proot_show_paths(self):
        return [settings.PROJECTS_ROOT]

    def build_private_data(self, project_update, **kwargs):
        '''
        Return SSH private key data needed for this project update.

        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>
            }
        }
        '''
        handle, self.revision_path = tempfile.mkstemp(dir=settings.PROJECTS_ROOT)
        self.cleanup_paths.append(self.revision_path)
        private_data = {'credentials': {}}
        if project_update.credential:
            credential = project_update.credential
            if credential.ssh_key_data not in (None, ''):
                private_data['credentials'][credential] = decrypt_field(credential, 'ssh_key_data')
        return private_data

    def build_passwords(self, project_update, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update,
                                                                  **kwargs)
        if project_update.credential:
            passwords['scm_key_unlock'] = decrypt_field(project_update.credential, 'ssh_key_unlock')
            passwords['scm_username'] = project_update.credential.username
            passwords['scm_password'] = decrypt_field(project_update.credential, 'password')
        return passwords

    def build_env(self, project_update, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = super(RunProjectUpdate, self).build_env(project_update, **kwargs)
        env = self.add_ansible_venv(env)
        env['ANSIBLE_RETRY_FILES_ENABLED'] = str(False)
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
            elif scm_url_parts.scheme.endswith('ssh'):
                scm_password = False
            elif scm_type == 'insights':
                extra_vars['scm_username'] = scm_username
                extra_vars['scm_password'] = scm_password
            scm_url = update_scm_url(scm_type, scm_url, scm_username,
                                     scm_password, scp_format=True)
        else:
            scm_url = update_scm_url(scm_type, scm_url, scp_format=True)

        # Pass the extra accept_hostkey parameter to the git module.
        if scm_type == 'git' and scm_url_parts.scheme.endswith('ssh'):
            extra_vars['scm_accept_hostkey'] = 'true'

        return scm_url, extra_vars

    def build_inventory(self, instance, **kwargs):
        return 'localhost,'

    def build_args(self, project_update, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        args = ['ansible-playbook', '-i', self.build_inventory(project_update, **kwargs)]
        if getattr(settings, 'PROJECT_UPDATE_VVV', False):
            args.append('-vvv')
        else:
            args.append('-v')
        scm_url, extra_vars = self._build_scm_url_extra_vars(project_update,
                                                             **kwargs)
        if project_update.project.scm_revision and project_update.job_type == 'run':
            scm_branch = project_update.project.scm_revision
        else:
            scm_branch = project_update.scm_branch or {'hg': 'tip'}.get(project_update.scm_type, 'HEAD')
        extra_vars.update({
            'project_path': project_update.get_project_path(check_if_exists=False),
            'insights_url': settings.INSIGHTS_URL_BASE,
            'scm_type': project_update.scm_type,
            'scm_url': scm_url,
            'scm_branch': scm_branch,
            'scm_clean': project_update.scm_clean,
            'scm_delete_on_update': project_update.scm_delete_on_update if project_update.job_type == 'check' else False,
            'scm_full_checkout': True if project_update.job_type == 'run' else False,
            'scm_revision_output': self.revision_path,
            'scm_revision': project_update.project.scm_revision,
        })
        args.extend(['-e', json.dumps(extra_vars)])
        args.append('project_update.yml')
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
        d[re.compile(r'Username for.*:\s*?$', re.M)] = 'scm_username'
        d[re.compile(r'Password for.*:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'Password:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'\S+?@\S+?\'s\s+?password:\s*?$', re.M)] = 'scm_password'
        d[re.compile(r'Enter passphrase for .*:\s*?$', re.M)] = 'scm_key_unlock'
        d[re.compile(r'Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        # FIXME: Configure whether we should auto accept host keys?
        d[re.compile(r'^Are you sure you want to continue connecting \(yes/no\)\?\s*?$', re.M)] = 'yes'
        return d

    def get_idle_timeout(self):
        return getattr(settings, 'PROJECT_UPDATE_IDLE_TIMEOUT', None)

    def get_stdout_handle(self, instance):
        stdout_handle = super(RunProjectUpdate, self).get_stdout_handle(instance)
        pk = instance.pk

        def raw_callback(data):
            instance_actual = self.update_model(pk)
            result_stdout_text = instance_actual.result_stdout_text + data
            self.update_model(pk, result_stdout_text=result_stdout_text)
        return OutputEventFilter(stdout_handle, raw_callback=raw_callback)

    def _update_dependent_inventories(self, project_update, dependent_inventory_sources):
        project_request_id = '' if self.request.id is None else self.request.id
        scm_revision = project_update.project.scm_revision
        inv_update_class = InventoryUpdate._get_task_class()
        for inv_src in dependent_inventory_sources:
            if not inv_src.update_on_project_update:
                continue
            if inv_src.scm_last_revision == scm_revision:
                logger.debug('Skipping SCM inventory update for `{}` because '
                             'project has not changed.'.format(inv_src.name))
                continue
            logger.debug('Local dependent inventory update for `{}`.'.format(inv_src.name))
            with transaction.atomic():
                if InventoryUpdate.objects.filter(inventory_source=inv_src,
                                                  status__in=ACTIVE_STATES).exists():
                    logger.info('Skipping SCM inventory update for `{}` because '
                                'another update is already active.'.format(inv_src.name))
                    continue
                local_inv_update = inv_src.create_inventory_update(
                    launch_type='scm',
                    _eager_fields=dict(
                        status='running',
                        instance_group=project_update.instance_group,
                        execution_node=project_update.execution_node,
                        celery_task_id=str(project_request_id),
                        source_project_update=project_update))
            try:
                task_instance = inv_update_class()
                # Runs in the same Celery task as project update
                task_instance.request.id = project_request_id
                task_instance.run(local_inv_update.id)
            except Exception:
                logger.exception('%s Unhandled exception updating dependent SCM inventory sources.',
                                 project_update.log_format)

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
            if project_update.cancel_flag or local_inv_update.cancel_flag:
                if not project_update.cancel_flag:
                    self.update_model(project_update.pk, cancel_flag=True, job_explanation=_(
                        'Dependent inventory update {} was canceled.'.format(local_inv_update.name)))
                break  # Stop rest of updates if project or inventory update was canceled
            if local_inv_update.status == 'successful':
                inv_src.scm_last_revision = scm_revision
                inv_src.save(update_fields=['scm_last_revision'])

    def release_lock(self, instance):
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        except IOError as e:
            logger.error("I/O error({0}) while trying to open lock file [{1}]: {2}".format(e.errno, instance.get_lock_file(), e.strerror))
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
            raise RuntimeError(u'Invalid lock file path')

        try:
            self.lock_fd = os.open(lock_path, os.O_RDONLY | os.O_CREAT)
        except OSError as e:
            logger.error("I/O error({0}) while trying to open lock file [{1}]: {2}".format(e.errno, lock_path, e.strerror))
            raise

        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
        except IOError as e:
            os.close(self.lock_fd)
            logger.error("I/O error({0}) while trying to aquire lock on file [{1}]: {2}".format(e.errno, lock_path, e.strerror))
            raise

    def pre_run_hook(self, instance, **kwargs):
        # re-create root project folder if a natural disaster has destroyed it
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        if instance.launch_type == 'sync':
            self.acquire_lock(instance)

    def post_run_hook(self, instance, status, **kwargs):
        if instance.launch_type == 'sync':
            self.release_lock(instance)
        p = instance.project
        if instance.job_type == 'check' and status not in ('failed', 'canceled',):
            fd = open(self.revision_path, 'r')
            lines = fd.readlines()
            if lines:
                p.scm_revision = lines[0].strip()
            else:
                logger.info("%s Could not find scm revision in check", instance.log_format)
            p.playbook_files = p.playbooks
            p.inventory_files = p.inventories
            p.save()

        # Update any inventories that depend on this project
        dependent_inventory_sources = p.scm_inventory_sources.filter(update_on_project_update=True)
        if len(dependent_inventory_sources) > 0:
            if status == 'successful' and instance.launch_type != 'sync':
                self._update_dependent_inventories(instance, dependent_inventory_sources)

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)


class RunInventoryUpdate(BaseTask):

    name = 'awx.main.tasks.run_inventory_update'
    model = InventoryUpdate

    def build_private_data(self, inventory_update, **kwargs):
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
        private_data = {'credentials': {}}
        # If this is GCE, return the RSA key
        if inventory_update.source == 'gce':
            credential = inventory_update.credential
            private_data['credentials'][credential] = decrypt_field(credential, 'ssh_key_data')
            return private_data

        if inventory_update.source == 'openstack':
            credential = inventory_update.credential
            openstack_auth = dict(auth_url=credential.host,
                                  username=credential.username,
                                  password=decrypt_field(credential, "password"),
                                  project_name=credential.project)
            if credential.domain not in (None, ''):
                openstack_auth['domain_name'] = credential.domain
            private_state = inventory_update.source_vars_dict.get('private', True)
            # Retrieve cache path from inventory update vars if available,
            # otherwise create a temporary cache path only for this update.
            cache = inventory_update.source_vars_dict.get('cache', {})
            if not isinstance(cache, dict):
                cache = {}
            if not cache.get('path', ''):
                cache_path = tempfile.mkdtemp(prefix='openstack_cache', dir=kwargs.get('private_data_dir', None))
                cache['path'] = cache_path
            openstack_data = {
                'clouds': {
                    'devstack': {
                        'private': private_state,
                        'auth': openstack_auth,
                    },
                },
                'cache': cache,
            }
            ansible_variables = {
                'use_hostnames': True,
                'expand_hostvars': False,
                'fail_on_errors': True,
            }
            provided_count = 0
            for var_name in ansible_variables:
                if var_name in inventory_update.source_vars_dict:
                    ansible_variables[var_name] = inventory_update.source_vars_dict[var_name]
                    provided_count += 1
            if provided_count:
                openstack_data['ansible'] = ansible_variables
            private_data['credentials'][credential] = yaml.safe_dump(
                openstack_data, default_flow_style=False, allow_unicode=True
            )
            return private_data

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
            ec2_opts.setdefault('all_instances', 'True')
            ec2_opts.setdefault('all_rds_instances', 'False')
            ec2_opts.setdefault('include_rds_clusters', 'False')
            ec2_opts.setdefault('rds', 'False')
            ec2_opts.setdefault('nested_groups', 'True')
            ec2_opts.setdefault('elasticache', 'False')
            ec2_opts.setdefault('stack_filters', 'False')
            if inventory_update.instance_filters:
                ec2_opts.setdefault('instance_filters', inventory_update.instance_filters)
            group_by = [x.strip().lower() for x in inventory_update.group_by.split(',') if x.strip()]
            for choice in inventory_update.get_ec2_group_by_choices():
                value = bool((group_by and choice[0] in group_by) or (not group_by and choice[0] != 'instance_id'))
                ec2_opts.setdefault('group_by_%s' % choice[0], str(value))
            if 'cache_path' not in ec2_opts:
                cache_path = tempfile.mkdtemp(prefix='ec2_cache', dir=kwargs.get('private_data_dir', None))
                ec2_opts['cache_path'] = cache_path
            ec2_opts.setdefault('cache_max_age', '300')
            for k,v in ec2_opts.items():
                cp.set(section, k, unicode(v))
        # Allow custom options to vmware inventory script.
        elif inventory_update.source == 'vmware':
            credential = inventory_update.credential

            section = 'vmware'
            cp.add_section(section)
            cp.set('vmware', 'cache_max_age', 0)
            cp.set('vmware', 'validate_certs', str(settings.VMWARE_VALIDATE_CERTS))
            cp.set('vmware', 'username', credential.username)
            cp.set('vmware', 'password', decrypt_field(credential, 'password'))
            cp.set('vmware', 'server', credential.host)

            vmware_opts = dict(inventory_update.source_vars_dict.items())
            if inventory_update.instance_filters:
                vmware_opts.setdefault('host_filters', inventory_update.instance_filters)
            if inventory_update.group_by:
                vmware_opts.setdefault('groupby_patterns', inventory_update.group_by)

            for k,v in vmware_opts.items():
                cp.set(section, k, unicode(v))

        elif inventory_update.source == 'satellite6':
            section = 'foreman'
            cp.add_section(section)

            group_patterns = '[]'
            group_prefix = 'foreman_'
            foreman_opts = dict(inventory_update.source_vars_dict.items())
            foreman_opts.setdefault('ssl_verify', 'False')
            for k, v in foreman_opts.items():
                if k == 'satellite6_group_patterns' and isinstance(v, basestring):
                    group_patterns = v
                elif k == 'satellite6_group_prefix' and isinstance(v, basestring):
                    group_prefix = v
                else:
                    cp.set(section, k, unicode(v))

            credential = inventory_update.credential
            if credential:
                cp.set(section, 'url', credential.host)
                cp.set(section, 'user', credential.username)
                cp.set(section, 'password', decrypt_field(credential, 'password'))

            section = 'ansible'
            cp.add_section(section)
            cp.set(section, 'group_patterns', group_patterns)
            cp.set(section, 'want_facts', True)
            cp.set(section, 'group_prefix', group_prefix)

            section = 'cache'
            cp.add_section(section)
            cp.set(section, 'path', '/tmp')
            cp.set(section, 'max_age', '0')

        elif inventory_update.source == 'cloudforms':
            section = 'cloudforms'
            cp.add_section(section)

            credential = inventory_update.credential
            if credential:
                cp.set(section, 'url', credential.host)
                cp.set(section, 'username', credential.username)
                cp.set(section, 'password', decrypt_field(credential, 'password'))
                cp.set(section, 'ssl_verify', "false")

            cloudforms_opts = dict(inventory_update.source_vars_dict.items())
            for opt in ['version', 'purge_actions', 'clean_group_keys', 'nest_tags']:
                if opt in cloudforms_opts:
                    cp.set(section, opt, cloudforms_opts[opt])

            section = 'cache'
            cp.add_section(section)
            cp.set(section, 'max_age', "0")

        elif inventory_update.source == 'azure_rm':
            section = 'azure'
            cp.add_section(section)
            cp.set(section, 'include_powerstate', 'yes')
            cp.set(section, 'group_by_resource_group', 'yes')
            cp.set(section, 'group_by_location', 'yes')
            cp.set(section, 'group_by_tag', 'yes')
            if inventory_update.source_regions and 'all' not in inventory_update.source_regions:
                cp.set(
                    section, 'locations',
                    ','.join([x.strip() for x in inventory_update.source_regions.split(',')])
                )

        # Return INI content.
        if cp.sections():
            f = cStringIO.StringIO()
            cp.write(f)
            private_data['credentials'][inventory_update.credential] = f.getvalue()
            return private_data

    def build_passwords(self, inventory_update, **kwargs):
        """Build a dictionary of authentication/credential information for
        an inventory source.

        This dictionary is used by `build_env`, below.
        """
        # Run the superclass implementation.
        super_ = super(RunInventoryUpdate, self).build_passwords
        passwords = super_(inventory_update, **kwargs)

        # Take key fields from the credential in use and add them to the
        # passwords dictionary.
        credential = inventory_update.credential
        if credential:
            for subkey in ('username', 'host', 'project', 'client', 'tenant', 'subscription'):
                passwords['source_%s' % subkey] = getattr(credential, subkey)
            for passkey in ('password', 'ssh_key_data', 'security_token', 'secret'):
                k = 'source_%s' % passkey
                passwords[k] = decrypt_field(credential, passkey)
        return passwords

    def build_env(self, inventory_update, **kwargs):
        """Build environment dictionary for inventory import.

        This is the mechanism by which any data that needs to be passed
        to the inventory update script is set up. In particular, this is how
        inventory update is aware of its proper credentials.
        """
        env = super(RunInventoryUpdate, self).build_env(inventory_update,
                                                        **kwargs)
        env = self.add_awx_venv(env)
        # Pass inventory source ID to inventory script.
        env['INVENTORY_SOURCE_ID'] = str(inventory_update.inventory_source_id)
        env['INVENTORY_UPDATE_ID'] = str(inventory_update.pk)

        # Set environment variables specific to each source.
        #
        # These are set here and then read in by the various Ansible inventory
        # modules, which will actually do the inventory sync.
        #
        # The inventory modules are vendored in AWX in the
        # `awx/plugins/inventory` directory; those files should be kept in
        # sync with those in Ansible core at all times.
        passwords = kwargs.get('passwords', {})
        cred_data = kwargs.get('private_data_files', {}).get('credentials', '')
        cloud_credential = cred_data.get(inventory_update.credential, '')
        if inventory_update.source == 'ec2':
            if passwords.get('source_username', '') and passwords.get('source_password', ''):
                env['AWS_ACCESS_KEY_ID'] = passwords['source_username']
                env['AWS_SECRET_ACCESS_KEY'] = passwords['source_password']
                if len(passwords['source_security_token']) > 0:
                    env['AWS_SECURITY_TOKEN'] = passwords['source_security_token']
            env['EC2_INI_PATH'] = cloud_credential
        elif inventory_update.source == 'vmware':
            env['VMWARE_INI_PATH'] = cloud_credential
        elif inventory_update.source == 'azure_rm':
            if len(passwords.get('source_client', '')) and \
               len(passwords.get('source_tenant', '')):
                env['AZURE_CLIENT_ID'] = passwords.get('source_client', '')
                env['AZURE_SECRET'] = passwords.get('source_secret', '')
                env['AZURE_TENANT'] = passwords.get('source_tenant', '')
                env['AZURE_SUBSCRIPTION_ID'] = passwords.get('source_subscription', '')
            else:
                env['AZURE_SUBSCRIPTION_ID'] = passwords.get('source_subscription', '')
                env['AZURE_AD_USER'] = passwords.get('source_username', '')
                env['AZURE_PASSWORD'] = passwords.get('source_password', '')
            env['AZURE_INI_PATH'] = cloud_credential
        elif inventory_update.source == 'gce':
            env['GCE_EMAIL'] = passwords.get('source_username', '')
            env['GCE_PROJECT'] = passwords.get('source_project', '')
            env['GCE_PEM_FILE_PATH'] = cloud_credential
            env['GCE_ZONE'] = inventory_update.source_regions if inventory_update.source_regions != 'all' else ''
        elif inventory_update.source == 'openstack':
            env['OS_CLIENT_CONFIG_FILE'] = cloud_credential
        elif inventory_update.source == 'satellite6':
            env['FOREMAN_INI_PATH'] = cloud_credential
        elif inventory_update.source == 'cloudforms':
            env['CLOUDFORMS_INI_PATH'] = cloud_credential
        elif inventory_update.source in ['scm', 'custom']:
            for env_k in inventory_update.source_vars_dict:
                if str(env_k) not in env and str(env_k) not in settings.INV_ENV_VARIABLE_BLACKLIST:
                    env[str(env_k)] = unicode(inventory_update.source_vars_dict[env_k])
        elif inventory_update.source == 'file':
            raise NotImplementedError('Cannot update file sources through the task system.')
        # add private_data_files
        env['AWX_PRIVATE_DATA_DIR'] = kwargs.get('private_data_dir', '')
        return env

    def build_args(self, inventory_update, **kwargs):
        """Build the command line argument list for running an inventory
        import.
        """
        # Get the inventory source and inventory.
        inventory_source = inventory_update.inventory_source
        inventory = inventory_source.inventory

        # Piece together the initial command to run via. the shell.
        args = ['awx-manage', 'inventory_import']
        args.extend(['--inventory-id', str(inventory.pk)])

        # Add appropriate arguments for overwrite if the inventory_update
        # object calls for it.
        if inventory_update.overwrite:
            args.append('--overwrite')
        if inventory_update.overwrite_vars:
            args.append('--overwrite-vars')
        src = inventory_update.source

        # Add several options to the shell arguments based on the
        # inventory-source-specific setting in the AWX configuration.
        # These settings are "per-source"; it's entirely possible that
        # they will be different between cloud providers if an AWX user
        # actively uses more than one.
        if getattr(settings, '%s_ENABLED_VAR' % src.upper(), False):
            args.extend(['--enabled-var',
                        getattr(settings, '%s_ENABLED_VAR' % src.upper())])
        if getattr(settings, '%s_ENABLED_VALUE' % src.upper(), False):
            args.extend(['--enabled-value',
                        getattr(settings, '%s_ENABLED_VALUE' % src.upper())])
        if getattr(settings, '%s_GROUP_FILTER' % src.upper(), False):
            args.extend(['--group-filter',
                         getattr(settings, '%s_GROUP_FILTER' % src.upper())])
        if getattr(settings, '%s_HOST_FILTER' % src.upper(), False):
            args.extend(['--host-filter',
                         getattr(settings, '%s_HOST_FILTER' % src.upper())])
        if getattr(settings, '%s_EXCLUDE_EMPTY_GROUPS' % src.upper()):
            args.append('--exclude-empty-groups')
        if getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper(), False):
            args.extend(['--instance-id-var',
                        getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper()),])
        # Add arguments for the source inventory script
        args.append('--source')
        if src in CLOUD_PROVIDERS:
            # Get the path to the inventory plugin, and append it to our
            # arguments.
            plugin_path = self.get_path_to('..', 'plugins', 'inventory',
                                           '%s.py' % src)
            args.append(plugin_path)
        elif src == 'scm':
            args.append(inventory_update.get_actual_source_path())
        elif src == 'custom':
            runpath = tempfile.mkdtemp(prefix='awx_inventory_', dir=settings.AWX_PROOT_BASE_PATH)
            handle, path = tempfile.mkstemp(dir=runpath)
            f = os.fdopen(handle, 'w')
            if inventory_update.source_script is None:
                raise RuntimeError('Inventory Script does not exist')
            f.write(inventory_update.source_script.script.encode('utf-8'))
            f.close()
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            args.append(path)
            args.append("--custom")
            self.cleanup_paths.append(runpath)
        args.append('-v%d' % inventory_update.verbosity)
        if settings.DEBUG:
            args.append('--traceback')
        return args

    def get_stdout_handle(self, instance):
        stdout_handle = super(RunInventoryUpdate, self).get_stdout_handle(instance)
        pk = instance.pk

        def raw_callback(data):
            instance_actual = self.update_model(pk)
            result_stdout_text = instance_actual.result_stdout_text + data
            self.update_model(pk, result_stdout_text=result_stdout_text)
        return OutputEventFilter(stdout_handle, raw_callback=raw_callback)

    def build_cwd(self, inventory_update, **kwargs):
        return self.get_path_to('..', 'plugins', 'inventory')

    def get_idle_timeout(self):
        return getattr(settings, 'INVENTORY_UPDATE_IDLE_TIMEOUT', None)

    def pre_run_hook(self, inventory_update, **kwargs):
        source_project = None
        if inventory_update.inventory_source:
            source_project = inventory_update.inventory_source.source_project
        if (inventory_update.source=='scm' and inventory_update.launch_type=='manual' and source_project):
            request_id = '' if self.request.id is None else self.request.id
            local_project_sync = source_project.create_project_update(
                launch_type="sync",
                _eager_fields=dict(
                    job_type='run',
                    status='running',
                    execution_node=inventory_update.execution_node,
                    instance_group = inventory_update.instance_group,
                    celery_task_id=request_id))
            # associate the inventory update before calling run() so that a
            # cancel() call on the inventory update can cancel the project update
            local_project_sync.scm_inventory_updates.add(inventory_update)

            project_update_task = local_project_sync._get_task_class()
            try:
                task_instance = project_update_task()
                task_instance.request.id = request_id
                task_instance.run(local_project_sync.id)
                inventory_update.inventory_source.scm_last_revision = local_project_sync.project.scm_revision
                inventory_update.inventory_source.save(update_fields=['scm_last_revision'])
            except Exception:
                inventory_update = self.update_model(
                    inventory_update.pk, status='failed',
                    job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                     ('project_update', local_project_sync.name, local_project_sync.id)))
                raise


class RunAdHocCommand(BaseTask):
    '''
    Celery task to run an ad hoc command using ansible.
    '''

    name = 'awx.main.tasks.run_ad_hoc_command'
    model = AdHocCommand
    event_data_key = 'ad_hoc_command_id'

    def build_private_data(self, ad_hoc_command, **kwargs):
        '''
        Return SSH private key data needed for this ad hoc command (only if
        stored in DB as ssh_key_data).

        Returns a dict of the form
        {
            'credentials': {
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>,
                <awx.main.models.Credential>: <credential_decrypted_ssh_key_data>
            }
        }
        '''
        # If we were sent SSH credentials, decrypt them and send them
        # back (they will be written to a temporary file).
        creds = ad_hoc_command.credential
        private_data = {'credentials': {}}
        if creds and creds.ssh_key_data not in (None, ''):
            private_data['credentials'][creds] = decrypt_field(creds, 'ssh_key_data') or ''
        return private_data

    def build_passwords(self, ad_hoc_command, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user and
        sudo/su.
        '''
        passwords = super(RunAdHocCommand, self).build_passwords(ad_hoc_command, **kwargs)
        creds = ad_hoc_command.credential
        if creds:
            for field in ('ssh_key_unlock', 'ssh_password', 'become_password'):
                if field == 'ssh_password':
                    value = kwargs.get(field, decrypt_field(creds, 'password'))
                else:
                    value = kwargs.get(field, decrypt_field(creds, field))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, ad_hoc_command, **kwargs):
        '''
        Build environment dictionary for ansible.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        env = super(RunAdHocCommand, self).build_env(ad_hoc_command, **kwargs)
        env = self.add_ansible_venv(env)
        # Set environment variables needed for inventory and ad hoc event
        # callbacks to work.
        env['AD_HOC_COMMAND_ID'] = str(ad_hoc_command.pk)
        env['INVENTORY_ID'] = str(ad_hoc_command.inventory.pk)
        env['INVENTORY_HOSTVARS'] = str(True)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ANSIBLE_LOAD_CALLBACK_PLUGINS'] = '1'
        env['ANSIBLE_STDOUT_CALLBACK'] = 'minimal'  # Hardcoded by Ansible for ad-hoc commands (either minimal or oneline).
        env['REST_API_URL'] = settings.INTERNAL_API_URL
        env['REST_API_TOKEN'] = ad_hoc_command.task_auth_token or ''
        env['CALLBACK_QUEUE'] = settings.CALLBACK_QUEUE
        env['CALLBACK_CONNECTION'] = settings.BROKER_URL
        env['ANSIBLE_SFTP_BATCH_MODE'] = 'False'
        env['CACHE'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''
        if getattr(settings, 'JOB_CALLBACK_DEBUG', False):
            env['JOB_CALLBACK_DEBUG'] = '2'
        elif settings.DEBUG:
            env['JOB_CALLBACK_DEBUG'] = '1'

        # Specify empty SSH args (should disable ControlPersist entirely for
        # ad hoc commands).
        env.setdefault('ANSIBLE_SSH_ARGS', '')

        return env

    def build_args(self, ad_hoc_command, **kwargs):
        '''
        Build command line argument list for running ansible, optionally using
        ssh-agent for public/private key authentication.
        '''
        creds = ad_hoc_command.credential
        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = kwargs.get('username', creds.username)
            become_method = kwargs.get('become_method', creds.become_method)
            become_username = kwargs.get('become_username', creds.become_username)
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible's default of using the
        # current user.
        ssh_username = ssh_username or 'root'
        args = ['ansible', '-i', self.build_inventory(ad_hoc_command, **kwargs)]
        if ad_hoc_command.job_type == 'check':
            args.append('--check')
        args.extend(['-u', ssh_username])
        if 'ssh_password' in kwargs.get('passwords', {}):
            args.append('--ask-pass')
        # We only specify sudo/su user and password if explicitly given by the
        # credential.  Credential should never specify both sudo and su.
        if ad_hoc_command.become_enabled:
            args.append('--become')
        if become_method:
            args.extend(['--become-method', become_method])
        if become_username:
            args.extend(['--become-user', become_username])
        if 'become_password' in kwargs.get('passwords', {}):
            args.append('--ask-become-pass')

        if ad_hoc_command.forks:  # FIXME: Max limit?
            args.append('--forks=%d' % ad_hoc_command.forks)
        if ad_hoc_command.diff_mode:
            args.append('--diff')
        if ad_hoc_command.verbosity:
            args.append('-%s' % ('v' * min(5, ad_hoc_command.verbosity)))

        if ad_hoc_command.extra_vars_dict:
            args.extend(['-e', json.dumps(ad_hoc_command.extra_vars_dict)])

        args.extend(['-m', ad_hoc_command.module_name])
        args.extend(['-a', ad_hoc_command.module_args])

        if ad_hoc_command.limit:
            args.append(ad_hoc_command.limit)
        else:
            args.append('all')

        return args

    def build_cwd(self, ad_hoc_command, **kwargs):
        return kwargs['private_data_dir']

    def get_idle_timeout(self):
        return getattr(settings, 'JOB_RUN_IDLE_TIMEOUT', None)

    def get_password_prompts(self):
        d = super(RunAdHocCommand, self).get_password_prompts()
        d[re.compile(r'Enter passphrase for .*:\s*?$', re.M)] = 'ssh_key_unlock'
        d[re.compile(r'Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[re.compile(r'%s password.*:\s*?$' % (method[0]), re.M)] = 'become_password'
            d[re.compile(r'%s password.*:\s*?$' % (method[0].upper()), re.M)] = 'become_password'
        d[re.compile(r'SSH password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Password:\s*?$', re.M)] = 'ssh_password'
        return d

    def get_stdout_handle(self, instance):
        '''
        Wrap stdout file object to capture events.
        '''
        stdout_handle = super(RunAdHocCommand, self).get_stdout_handle(instance)

        if getattr(settings, 'USE_CALLBACK_QUEUE', False):
            dispatcher = CallbackQueueDispatcher()

            def ad_hoc_command_event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                if 'uuid' in event_data:
                    cache_event = cache.get('ev-{}'.format(event_data['uuid']), None)
                    if cache_event is not None:
                        event_data.update(cache_event)
                dispatcher.dispatch(event_data)
        else:
            def ad_hoc_command_event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                AdHocCommandEvent.create_from_data(**event_data)

        return OutputEventFilter(stdout_handle, ad_hoc_command_event_callback)

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)


class RunSystemJob(BaseTask):

    name = 'awx.main.tasks.run_system_job'
    model = SystemJob

    def build_args(self, system_job, **kwargs):
        args = ['awx-manage', system_job.job_type]
        try:
            json_vars = json.loads(system_job.extra_vars)
            if 'days' in json_vars and system_job.job_type != 'cleanup_facts':
                args.extend(['--days', str(json_vars.get('days', 60))])
            if 'dry_run' in json_vars and json_vars['dry_run'] and system_job.job_type != 'cleanup_facts':
                args.extend(['--dry-run'])
            if system_job.job_type == 'cleanup_jobs':
                args.extend(['--jobs', '--project-updates', '--inventory-updates',
                             '--management-jobs', '--ad-hoc-commands', '--workflow-jobs',
                             '--notifications'])
            if system_job.job_type == 'cleanup_facts':
                if 'older_than' in json_vars:
                    args.extend(['--older_than', str(json_vars['older_than'])])
                if 'granularity' in json_vars:
                    args.extend(['--granularity', str(json_vars['granularity'])])
        except Exception:
            logger.exception("%s Failed to parse system job", instance.log_format)
        return args

    def get_stdout_handle(self, instance):
        stdout_handle = super(RunSystemJob, self).get_stdout_handle(instance)
        pk = instance.pk

        def raw_callback(data):
            instance_actual = self.update_model(pk)
            result_stdout_text = instance_actual.result_stdout_text + data
            self.update_model(pk, result_stdout_text=result_stdout_text)
        return OutputEventFilter(stdout_handle, raw_callback=raw_callback)

    def build_env(self, instance, **kwargs):
        env = super(RunSystemJob, self).build_env(instance,
                                                  **kwargs)
        env = self.add_awx_venv(env)
        return env

    def build_cwd(self, instance, **kwargs):
        return settings.BASE_DIR
