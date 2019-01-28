# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict, namedtuple
import configparser
import errno
import fnmatch
import functools
import importlib
import json
import logging
import os
import re
import shutil
import stat
import tempfile
import time
import traceback
from distutils.version import LooseVersion as Version
import yaml
import fcntl
try:
    import psutil
except Exception:
    psutil = None
from io import StringIO
import urllib.parse as urlparse

# Django
from django.conf import settings
from django.db import transaction, DatabaseError, IntegrityError
from django.db.models.fields.related import ForeignKey
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
from awx.main.constants import CLOUD_PROVIDERS, PRIVILEGE_ESCALATION_METHODS, STANDARD_INVENTORY_UPDATE_ENV
from awx.main.access import access_registry
from awx.main import analytics
from awx.main.models import * # noqa
from awx.main.constants import ACTIVE_STATES
from awx.main.exceptions import AwxTaskError
from awx.main.queue import CallbackQueueDispatcher
from awx.main.expect import run, isolated_manager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename, reaper
from awx.main.utils import (get_ansible_version, get_ssh_version, update_scm_url,
                            check_proot_installed, build_proot_temp_dir, get_licenser,
                            wrap_args_with_proot, OutputEventFilter, OutputVerboseFilter, ignore_inventory_computed_fields,
                            ignore_inventory_group_removal, extract_ansible_vars, schedule_task_manager)
from awx.main.utils.safe_yaml import safe_dump, sanitize_jinja
from awx.main.utils.reload import stop_local_services
from awx.main.utils.pglock import advisory_lock
from awx.main.consumers import emit_channel_notification
from awx.conf import settings_registry

from rest_framework.exceptions import PermissionDenied


__all__ = ['RunJob', 'RunSystemJob', 'RunProjectUpdate', 'RunInventoryUpdate',
           'RunAdHocCommand', 'handle_work_error', 'handle_work_success', 'apply_cluster_membership_policies',
           'update_inventory_computed_fields', 'update_host_smart_inventory_memberships',
           'send_notifications', 'run_administrative_checks', 'purge_old_stdout_files']

HIDDEN_PASSWORD = '**********'

OPENSSH_KEY_ERROR = u'''\
It looks like you're trying to use a private key in OpenSSH format, which \
isn't supported by the installed version of OpenSSH on this instance. \
Try upgrading OpenSSH or providing your private key in an different format. \
'''

logger = logging.getLogger('awx.main.tasks')


def dispatch_startup():
    startup_logger = logging.getLogger('awx.main.tasks')
    startup_logger.info("Syncing Schedules")
    for sch in Schedule.objects.all():
        try:
            sch.update_computed_fields()
            from awx.main.signals import disable_activity_stream
            with disable_activity_stream():
                sch.save()
        except Exception:
            logger.exception("Failed to rebuild schedule {}.".format(sch))

    #
    # When the dispatcher starts, if the instance cannot be found in the database,
    # automatically register it.  This is mostly useful for openshift-based
    # deployments where:
    #
    # 2 Instances come online
    # Instance B encounters a network blip, Instance A notices, and
    # deprovisions it
    # Instance B's connectivity is restored, the dispatcher starts, and it
    # re-registers itself
    #
    # In traditional container-less deployments, instances don't get
    # deprovisioned when they miss their heartbeat, so this code is mostly a
    # no-op.
    #
    apply_cluster_membership_policies()
    cluster_node_heartbeat()
    if Instance.objects.me().is_controller():
        awx_isolated_heartbeat()


def inform_cluster_of_shutdown():
    try:
        this_inst = Instance.objects.get(hostname=settings.CLUSTER_HOST_ID)
        this_inst.capacity = 0  # No thank you to new jobs while shut down
        this_inst.save(update_fields=['capacity', 'modified'])
        try:
            reaper.reap(this_inst)
        except Exception:
            logger.exception('failed to reap jobs for {}'.format(this_inst.hostname))
        logger.warning('Normal shutdown signal for instance {}, '
                       'removed self from capacity pool.'.format(this_inst.hostname))
    except Exception:
        logger.exception('Encountered problem with normal shutdown signal.')


@task()
def apply_cluster_membership_policies():
    started_waiting = time.time()
    with advisory_lock('cluster_policy_lock', wait=True):
        lock_time = time.time() - started_waiting
        if lock_time > 1.0:
            to_log = logger.info
        else:
            to_log = logger.debug
        to_log('Waited {} seconds to obtain lock name: cluster_policy_lock'.format(lock_time))
        started_compute = time.time()
        all_instances = list(Instance.objects.order_by('id'))
        all_groups = list(InstanceGroup.objects.prefetch_related('instances'))
        iso_hostnames = set([])
        for ig in all_groups:
            if ig.controller_id is not None:
                iso_hostnames.update(ig.policy_instance_list)

        considered_instances = [inst for inst in all_instances if inst.hostname not in iso_hostnames]
        total_instances = len(considered_instances)
        actual_groups = []
        actual_instances = []
        Group = namedtuple('Group', ['obj', 'instances', 'prior_instances'])
        Node = namedtuple('Instance', ['obj', 'groups'])

        # Process policy instance list first, these will represent manually managed memberships
        instance_hostnames_map = {inst.hostname: inst for inst in all_instances}
        for ig in all_groups:
            group_actual = Group(obj=ig, instances=[], prior_instances=[
                instance.pk for instance in ig.instances.all()  # obtained in prefetch
            ])
            for hostname in ig.policy_instance_list:
                if hostname not in instance_hostnames_map:
                    logger.info("Unknown instance {} in {} policy list".format(hostname, ig.name))
                    continue
                inst = instance_hostnames_map[hostname]
                group_actual.instances.append(inst.id)
                # NOTE: arguable behavior: policy-list-group is not added to
                # instance's group count for consideration in minimum-policy rules
            if group_actual.instances:
                logger.info("Policy List, adding Instances {} to Group {}".format(group_actual.instances, ig.name))

            if ig.controller_id is None:
                actual_groups.append(group_actual)
            else:
                # For isolated groups, _only_ apply the policy_instance_list
                # do not add to in-memory list, so minimum rules not applied
                logger.info('Committing instances to isolated group {}'.format(ig.name))
                ig.instances.set(group_actual.instances)

        # Process Instance minimum policies next, since it represents a concrete lower bound to the
        # number of instances to make available to instance groups
        actual_instances = [Node(obj=i, groups=[]) for i in considered_instances if i.managed_by_policy]
        logger.info("Total non-isolated instances:{} available for policy: {}".format(
            total_instances, len(actual_instances)))
        for g in sorted(actual_groups, key=lambda x: len(x.instances)):
            policy_min_added = []
            for i in sorted(actual_instances, key=lambda x: len(x.groups)):
                if len(g.instances) >= g.obj.policy_instance_minimum:
                    break
                if i.obj.id in g.instances:
                    # If the instance is already _in_ the group, it was
                    # applied earlier via the policy list
                    continue
                g.instances.append(i.obj.id)
                i.groups.append(g.obj.id)
                policy_min_added.append(i.obj.id)
            if policy_min_added:
                logger.info("Policy minimum, adding Instances {} to Group {}".format(policy_min_added, g.obj.name))

        # Finally, process instance policy percentages
        for g in sorted(actual_groups, key=lambda x: len(x.instances)):
            policy_per_added = []
            for i in sorted(actual_instances, key=lambda x: len(x.groups)):
                if i.obj.id in g.instances:
                    # If the instance is already _in_ the group, it was
                    # applied earlier via a minimum policy or policy list
                    continue
                if 100 * float(len(g.instances)) / len(actual_instances) >= g.obj.policy_instance_percentage:
                    break
                g.instances.append(i.obj.id)
                i.groups.append(g.obj.id)
                policy_per_added.append(i.obj.id)
            if policy_per_added:
                logger.info("Policy percentage, adding Instances {} to Group {}".format(policy_per_added, g.obj.name))

        # Determine if any changes need to be made
        needs_change = False
        for g in actual_groups:
            if set(g.instances) != set(g.prior_instances):
                needs_change = True
                break
        if not needs_change:
            logger.info('Cluster policy no-op finished in {} seconds'.format(time.time() - started_compute))
            return

        # On a differential basis, apply instances to non-isolated groups
        with transaction.atomic():
            for g in actual_groups:
                instances_to_add = set(g.instances) - set(g.prior_instances)
                instances_to_remove = set(g.prior_instances) - set(g.instances)
                if instances_to_add:
                    logger.info('Adding instances {} to group {}'.format(list(instances_to_add), g.obj.name))
                    g.obj.instances.add(*instances_to_add)
                if instances_to_remove:
                    logger.info('Removing instances {} from group {}'.format(list(instances_to_remove), g.obj.name))
                    g.obj.instances.remove(*instances_to_remove)
        logger.info('Cluster policy computation finished in {} seconds'.format(time.time() - started_compute))


@task(queue='tower_broadcast_all', exchange_type='fanout')
def handle_setting_changes(setting_keys):
    orig_len = len(setting_keys)
    for i in range(orig_len):
        for dependent_key in settings_registry.get_dependent_settings(setting_keys[i]):
            setting_keys.append(dependent_key)
    cache_keys = set(setting_keys)
    logger.debug('cache delete_many(%r)', cache_keys)
    cache.delete_many(cache_keys)


@task(queue='tower_broadcast_all', exchange_type='fanout')
def delete_project_files(project_path):
    # TODO: possibly implement some retry logic
    lock_file = project_path + '.lock'
    if os.path.exists(project_path):
        try:
            shutil.rmtree(project_path)
            logger.info('Success removing project files {}'.format(project_path))
        except Exception:
            logger.exception('Could not remove project directory {}'.format(project_path))
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            logger.debug('Success removing {}'.format(lock_file))
        except Exception:
            logger.exception('Could not remove lock file {}'.format(lock_file))


@task()
def send_notifications(notification_list, job_id=None):
    if not isinstance(notification_list, list):
        raise TypeError("notification_list should be of type list")
    if job_id is not None:
        job_actual = UnifiedJob.objects.get(id=job_id)

    notifications = Notification.objects.filter(id__in=notification_list)
    if job_id is not None:
        job_actual.notifications.add(*notifications)

    for notification in notifications:
        update_fields = ['status', 'notifications_sent']
        try:
            sent = notification.notification_template.send(notification.subject, notification.body)
            notification.status = "successful"
            notification.notifications_sent = sent
        except Exception as e:
            logger.error("Send Notification Failed {}".format(e))
            notification.status = "failed"
            notification.error = smart_str(e)
            update_fields.append('error')
        finally:
            try:
                notification.save(update_fields=update_fields)
            except Exception:
                logger.exception('Error saving notification {} result.'.format(notification.id))


@task()
def gather_analytics():
    if settings.PENDO_TRACKING_STATE == 'off':
        return
    try:
        tgz = analytics.gather()
        logger.debug('gathered analytics: {}'.format(tgz))
        analytics.ship(tgz)
    finally:
        if os.path.exists(tgz):
            os.remove(tgz)


@task()
def run_administrative_checks():
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


@task(queue=get_local_queuename)
def purge_old_stdout_files():
    nowtime = time.time()
    for f in os.listdir(settings.JOBOUTPUT_ROOT):
        if os.path.getctime(os.path.join(settings.JOBOUTPUT_ROOT,f)) < nowtime - settings.LOCAL_STDOUT_EXPIRE_TIME:
            os.unlink(os.path.join(settings.JOBOUTPUT_ROOT,f))
            logger.info("Removing {}".format(os.path.join(settings.JOBOUTPUT_ROOT,f)))


@task(queue=get_local_queuename)
def cluster_node_heartbeat():
    logger.debug("Cluster node heartbeat task.")
    nowtime = now()
    instance_list = list(Instance.objects.all_non_isolated())
    this_inst = None
    lost_instances = []

    (changed, instance) = Instance.objects.get_or_register()
    if changed:
        logger.info("Registered tower node '{}'".format(instance.hostname))

    for inst in list(instance_list):
        if inst.hostname == settings.CLUSTER_HOST_ID:
            this_inst = inst
            instance_list.remove(inst)
        elif inst.is_lost(ref_time=nowtime):
            lost_instances.append(inst)
            instance_list.remove(inst)
    if this_inst:
        startup_event = this_inst.is_lost(ref_time=nowtime)
        if this_inst.capacity == 0 and this_inst.enabled:
            logger.warning('Rejoining the cluster as instance {}.'.format(this_inst.hostname))
        if this_inst.enabled:
            this_inst.refresh_capacity()
        elif this_inst.capacity != 0 and not this_inst.enabled:
            this_inst.capacity = 0
            this_inst.save(update_fields=['capacity'])
        if startup_event:
            return
    else:
        raise RuntimeError("Cluster Host Not Found: {}".format(settings.CLUSTER_HOST_ID))
    # IFF any node has a greater version than we do, then we'll shutdown services
    for other_inst in instance_list:
        if other_inst.version == "":
            continue
        if Version(other_inst.version.split('-', 1)[0]) > Version(awx_application_version.split('-', 1)[0]) and not settings.DEBUG:
            logger.error("Host {} reports version {}, but this node {} is at {}, shutting down".format(
                other_inst.hostname,
                other_inst.version,
                this_inst.hostname,
                this_inst.version
            ))
            # Shutdown signal will set the capacity to zero to ensure no Jobs get added to this instance.
            # The heartbeat task will reset the capacity to the system capacity after upgrade.
            stop_local_services(communicate=False)
            raise RuntimeError("Shutting down.")
    for other_inst in lost_instances:
        try:
            reaper.reap(other_inst)
        except Exception:
            logger.exception('failed to reap jobs for {}'.format(other_inst.hostname))
        try:
            # Capacity could already be 0 because:
            #  * It's a new node and it never had a heartbeat
            #  * It was set to 0 by another tower node running this method
            #  * It was set to 0 by this node, but auto deprovisioning is off
            #
            # If auto deprovisining is on, don't bother setting the capacity to 0
            # since we will delete the node anyway.
            if other_inst.capacity != 0 and not settings.AWX_AUTO_DEPROVISION_INSTANCES:
                other_inst.capacity = 0
                other_inst.save(update_fields=['capacity'])
                logger.error("Host {} last checked in at {}, marked as lost.".format(
                    other_inst.hostname, other_inst.modified))
            elif settings.AWX_AUTO_DEPROVISION_INSTANCES:
                deprovision_hostname = other_inst.hostname
                other_inst.delete()
                logger.info("Host {} Automatically Deprovisioned.".format(deprovision_hostname))
        except DatabaseError as e:
            if 'did not affect any rows' in str(e):
                logger.debug('Another instance has marked {} as lost'.format(other_inst.hostname))
            else:
                logger.exception('Error marking {} as lost'.format(other_inst.hostname))


@task(queue=get_local_queuename)
def awx_isolated_heartbeat():
    local_hostname = settings.CLUSTER_HOST_ID
    logger.debug("Controlling node checking for any isolated management tasks.")
    poll_interval = settings.AWX_ISOLATED_PERIODIC_CHECK
    # Get isolated instances not checked since poll interval - some buffer
    nowtime = now()
    accept_before = nowtime - timedelta(seconds=(poll_interval - 10))
    isolated_instance_qs = Instance.objects.filter(
        rampart_groups__controller__instances__hostname=local_hostname,
    )
    isolated_instance_qs = isolated_instance_qs.filter(
        last_isolated_check__lt=accept_before
    ) | isolated_instance_qs.filter(
        last_isolated_check=None
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
        isolated_manager.IsolatedManager.health_check(isolated_instance_qs, awx_application_version)


@task()
def awx_periodic_scheduler():
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

    invalid_license = False
    try:
        access_registry[Job](None).check_license()
    except PermissionDenied as e:
        invalid_license = e

    for schedule in schedules:
        template = schedule.unified_job_template
        schedule.save() # To update next_run timestamp.
        if template.cache_timeout_blocked:
            logger.warn("Cache timeout is in the future, bypassing schedule for template %s" % str(template.id))
            continue
        try:
            job_kwargs = schedule.get_job_kwargs()
            new_unified_job = schedule.unified_job_template.create_unified_job(**job_kwargs)
            logger.info('Spawned {} from schedule {}-{}.'.format(
                new_unified_job.log_format, schedule.name, schedule.pk))

            if invalid_license:
                new_unified_job.status = 'failed'
                new_unified_job.job_explanation = str(invalid_license)
                new_unified_job.save(update_fields=['status', 'job_explanation'])
                new_unified_job.websocket_emit_status("failed")
                raise invalid_license
            can_start = new_unified_job.signal_start()
        except Exception:
            logger.exception('Error spawning scheduled job.')
            continue
        if not can_start:
            new_unified_job.status = 'failed'
            new_unified_job.job_explanation = "Scheduled job could not start because it was not in the right state or required manual credentials"
            new_unified_job.save(update_fields=['status', 'job_explanation'])
            new_unified_job.websocket_emit_status("failed")
        emit_channel_notification('schedules-changed', dict(id=schedule.id, group_name="schedules"))
    state.save()


@task()
def handle_work_success(task_actual):
    try:
        instance = UnifiedJob.get_instance_by_type(task_actual['type'], task_actual['id'])
    except ObjectDoesNotExist:
        logger.warning('Missing {} `{}` in success callback.'.format(task_actual['type'], task_actual['id']))
        return
    if not instance:
        return

    schedule_task_manager()


@task()
def handle_work_error(task_id, *args, **kwargs):
    subtasks = kwargs.get('subtasks', None)
    logger.debug('Executing error task id %s, subtasks: %s' % (task_id, str(subtasks)))
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

    # We only send 1 job complete message since all the job completion message
    # handling does is trigger the scheduler. If we extend the functionality of
    # what the job complete message handler does then we may want to send a
    # completion event for each job here.
    if first_instance:
        schedule_task_manager()
        pass


@task()
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


@task()
def update_host_smart_inventory_memberships():
    try:
        with transaction.atomic():
            smart_inventories = Inventory.objects.filter(kind='smart', host_filter__isnull=False, pending_deletion=False)
            SmartInventoryMembership.objects.all().delete()
            memberships = []
            changed_inventories = set([])
            for smart_inventory in smart_inventories:
                add_for_inventory = [
                    SmartInventoryMembership(inventory_id=smart_inventory.id, host_id=host_id[0])
                    for host_id in smart_inventory.hosts.values_list('id')
                ]
                memberships.extend(add_for_inventory)
                if add_for_inventory:
                    changed_inventories.add(smart_inventory)
            SmartInventoryMembership.objects.bulk_create(memberships)
    except IntegrityError as e:
        logger.error("Update Host Smart Inventory Memberships failed due to an exception: {}".format(e))
        return
    # Update computed fields for changed inventories outside atomic action
    for smart_inventory in changed_inventories:
        smart_inventory.update_computed_fields(update_groups=False, update_hosts=False)


@task()
def delete_inventory(inventory_id, user_id, retries=5):
    # Delete inventory as user
    if user_id is None:
        user = None
    else:
        try:
            user = User.objects.get(id=user_id)
        except Exception:
            user = None
    with ignore_inventory_computed_fields(), ignore_inventory_group_removal(), impersonate(user):
        try:
            i = Inventory.objects.get(id=inventory_id)
            for host in i.hosts.iterator():
                host.job_events_as_primary_host.update(host=None)
            i.delete()
            emit_channel_notification(
                'inventories-status_changed',
                {'group_name': 'inventories', 'inventory_id': inventory_id, 'status': 'deleted'}
            )
            logger.debug('Deleted inventory {} as user {}.'.format(inventory_id, user_id))
        except Inventory.DoesNotExist:
            logger.exception("Delete Inventory failed due to missing inventory: " + str(inventory_id))
            return
        except DatabaseError:
            logger.exception('Database error deleting inventory {}, but will retry.'.format(inventory_id))
            if retries > 0:
                time.sleep(10)
                delete_inventory(inventory_id, user_id, retries=retries - 1)


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
                        if field in ('result_traceback'):
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

    def get_path_to_ansible(self, instance, executable='ansible-playbook', **kwargs):
        venv_path = getattr(instance, 'ansible_virtualenv_path', settings.ANSIBLE_VENV_PATH)
        venv_exe = os.path.join(venv_path, 'bin', executable)
        if os.path.exists(venv_exe):
            return venv_exe
        return shutil.which(executable)

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
            for credential, data in private_data.get('credentials', {}).items():
                # Bail out now if a private key was provided in OpenSSH format
                # and we're running an earlier version (<6.5).
                if 'OPENSSH PRIVATE KEY' in data and not openssh_keys_supported:
                    raise RuntimeError(OPENSSH_KEY_ERROR)
            for credential, data in private_data.get('credentials', {}).items():
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

    def build_extra_vars_file(self, vars, **kwargs):
        handle, path = tempfile.mkstemp(dir=kwargs.get('private_data_dir', None))
        f = os.fdopen(handle, 'w')
        if settings.ALLOW_JINJA_IN_EXTRA_VARS == 'always':
            f.write(yaml.safe_dump(vars))
        else:
            f.write(safe_dump(vars, kwargs.get('safe_dict', {}) or None))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def add_ansible_venv(self, venv_path, env, add_awx_lib=True, **kwargs):
        env['VIRTUAL_ENV'] = venv_path
        env['PATH'] = os.path.join(venv_path, "bin") + ":" + env['PATH']
        venv_libdir = os.path.join(venv_path, "lib")

        if not kwargs.get('isolated', False) and not os.path.exists(venv_libdir):
            raise RuntimeError(
                'a valid Python virtualenv does not exist at {}'.format(venv_path)
            )
        env.pop('PYTHONPATH', None)  # default to none if no python_ver matches
        for version in os.listdir(venv_libdir):
            if fnmatch.fnmatch(version, 'python[23].*'):
                if os.path.isdir(os.path.join(venv_libdir, version)):
                    env['PYTHONPATH'] = os.path.join(venv_libdir, version, "site-packages") + ":"
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
        env['AWX_PRIVATE_DATA_DIR'] = kwargs['private_data_dir']
        return env

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return False

    def build_inventory(self, instance, **kwargs):
        script_params = dict(hostvars=True)
        if hasattr(instance, 'job_slice_number'):
            script_params['slice_number'] = instance.job_slice_number
            script_params['slice_count'] = instance.job_slice_count
        script_data = instance.inventory.get_script_data(**script_params)
        json_data = json.dumps(script_data)
        handle, path = tempfile.mkstemp(dir=kwargs.get('private_data_dir', None))
        f = os.fdopen(handle, 'w')
        f.write('#! /usr/bin/env python\n# -*- coding: utf-8 -*-\nprint(%r)\n' % json_data)
        f.close()
        os.chmod(path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR)
        return path

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

    def get_password_prompts(self, **kwargs):
        '''
        Return a dictionary where keys are strings or regular expressions for
        prompts, and values are password lookup keys (keys that are returned
        from build_passwords).
        '''
        return OrderedDict()

    def get_stdout_handle(self, instance):
        '''
        Return an virtual file object for capturing stdout and/or events.
        '''
        dispatcher = CallbackQueueDispatcher()

        if isinstance(instance, (Job, AdHocCommand, ProjectUpdate)):
            def event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                if 'uuid' in event_data:
                    cache_event = cache.get('ev-{}'.format(event_data['uuid']), None)
                    if cache_event is not None:
                        event_data.update(json.loads(cache_event))
                dispatcher.dispatch(event_data)

            return OutputEventFilter(event_callback)
        else:
            def event_callback(event_data):
                event_data.setdefault(self.event_data_key, instance.id)
                dispatcher.dispatch(event_data)

            return OutputVerboseFilter(event_callback)

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
    def run(self, pk, **kwargs):
        '''
        Run the job/task and capture its output.
        '''
        instance = self.update_model(pk, status='running',
                                     start_args='')  # blank field to remove encrypted passwords

        instance.websocket_emit_status("running")
        status, rc, tb = 'error', None, ''
        output_replacements = []
        extra_update_fields = {}
        event_ct = 0
        stdout_handle = None

        try:
            kwargs['isolated'] = instance.is_isolated()
            self.pre_run_hook(instance, **kwargs)
            if instance.cancel_flag:
                instance = self.update_model(instance.pk, status='canceled')
            if instance.status != 'running':
                # Stop the task chain and prevent starting the job if it has
                # already been canceled.
                instance = self.update_model(pk)
                status = instance.status
                raise RuntimeError('not starting %s task' % instance.status)

            if not os.path.exists(settings.AWX_PROOT_BASE_PATH):
                raise RuntimeError('AWX_PROOT_BASE_PATH=%s does not exist' % settings.AWX_PROOT_BASE_PATH)

            # store a record of the venv used at runtime
            if hasattr(instance, 'custom_virtualenv'):
                self.update_model(pk, custom_virtualenv=getattr(instance, 'ansible_virtualenv_path', settings.ANSIBLE_VENV_PATH))

            # Fetch ansible version once here to support version-dependent features.
            kwargs['ansible_version'] = get_ansible_version()
            kwargs['private_data_dir'] = self.build_private_data_dir(instance, **kwargs)

            # Fetch "cached" fact data from prior runs and put on the disk
            # where ansible expects to find it
            if getattr(instance, 'use_fact_cache', False):
                instance.start_job_fact_cache(
                    os.path.join(kwargs['private_data_dir']),
                    kwargs.setdefault('fact_modification_times', {})
                )

            # May have to serialize the value
            kwargs['private_data_files'] = self.build_private_data_files(instance, **kwargs)
            kwargs['passwords'] = self.build_passwords(instance, **kwargs)
            kwargs['proot_show_paths'] = self.proot_show_paths
            if getattr(instance, 'ansible_virtualenv_path', settings.ANSIBLE_VENV_PATH) != settings.ANSIBLE_VENV_PATH:
                kwargs['proot_custom_virtualenv'] = instance.ansible_virtualenv_path
            args = self.build_args(instance, **kwargs)
            safe_args = self.build_safe_args(instance, **kwargs)
            output_replacements = self.build_output_replacements(instance, **kwargs)
            cwd = self.build_cwd(instance, **kwargs)
            env = self.build_env(instance, **kwargs)
            safe_env = build_safe_env(env)

            # handle custom injectors specified on the CredentialType
            credentials = []
            if isinstance(instance, Job):
                credentials = instance.credentials.all()
            elif isinstance(instance, InventoryUpdate):
                # TODO: allow multiple custom creds for inv updates
                credentials = [instance.get_cloud_credential()]
            elif isinstance(instance, Project):
                # once (or if) project updates
                # move from a .credential -> .credentials model, we can
                # lose this block
                credentials = [instance.credential]

            for credential in credentials:
                if credential:
                    credential.credential_type.inject_credential(
                        credential, env, safe_env, args, safe_args, kwargs['private_data_dir']
                    )

            if instance.is_isolated() is False:
                stdout_handle = self.get_stdout_handle(instance)
            else:
                stdout_handle = isolated_manager.IsolatedManager.get_stdout_handle(
                    instance, kwargs['private_data_dir'], event_data_key=self.event_data_key)
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
            if ssh_key_path and instance.is_isolated() is False:
                ssh_auth_sock = os.path.join(kwargs['private_data_dir'], 'ssh_auth.sock')
                args = run.wrap_args_with_ssh_agent(args, ssh_key_path, ssh_auth_sock)
                safe_args = run.wrap_args_with_ssh_agent(safe_args, ssh_key_path, ssh_auth_sock)
            instance = self.update_model(pk, job_args=json.dumps(safe_args),
                                         job_cwd=cwd, job_env=safe_env)

            expect_passwords = {}
            for k, v in self.get_password_prompts(**kwargs).items():
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
            if instance.is_isolated() is True:
                manager_instance = isolated_manager.IsolatedManager(
                    args, cwd, env, stdout_handle, ssh_key_path, **_kw
                )
                status, rc = manager_instance.run(instance,
                                                  kwargs['private_data_dir'],
                                                  kwargs.get('proot_temp_dir'))
            else:
                status, rc = run.run_pexpect(
                    args, cwd, env, stdout_handle, **_kw
                )

        except Exception:
            # run_pexpect does not throw exceptions for cancel or timeout
            # this could catch programming or file system errors
            tb = traceback.format_exc()
            logger.exception('%s Exception occurred while running task', instance.log_format)
        finally:
            try:
                if stdout_handle:
                    stdout_handle.flush()
                    stdout_handle.close()
                    event_ct = getattr(stdout_handle, '_counter', 0)
                logger.info('%s finished running, producing %s events.',
                            instance.log_format, event_ct)
            except Exception:
                logger.exception('Error flushing job stdout and saving event count.')

        try:
            self.post_run_hook(instance, status, **kwargs)
        except Exception:
            logger.exception('{} Post run hook errored.'.format(instance.log_format))
        instance = self.update_model(pk)
        if instance.cancel_flag:
            status = 'canceled'
            cancel_wait = (now() - instance.modified).seconds if instance.modified else 0
            if cancel_wait > 5:
                logger.warn('Request to cancel {} took {} seconds to complete.'.format(instance.log_format, cancel_wait))

        instance = self.update_model(pk, status=status, result_traceback=tb,
                                     output_replacements=output_replacements,
                                     emitted_events=event_ct,
                                     **extra_update_fields)
        try:
            self.final_run_hook(instance, status, **kwargs)
        except Exception:
            logger.exception('{} Final run hook errored.'.format(instance.log_format))
        instance.websocket_emit_status(status)
        if status != 'successful':
            if status == 'canceled':
                raise AwxTaskError.TaskCancel(instance, rc)
            else:
                raise AwxTaskError.TaskError(instance, rc)

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


@task()
class RunJob(BaseTask):
    '''
    Run a job using ansible-playbook.
    '''

    model = Job
    event_model = JobEvent
    event_data_key = 'job_id'

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
        for credential in job.credentials.all():
            # If we were sent SSH credentials, decrypt them and send them
            # back (they will be written to a temporary file).
            if credential.has_input('ssh_key_data'):
                private_data['credentials'][credential] = credential.get_input('ssh_key_data', default='')

            if credential.kind == 'openstack':
                openstack_auth = dict(auth_url=credential.get_input('host', default=''),
                                      username=credential.get_input('username', default=''),
                                      password=credential.get_input('password', default=''),
                                      project_name=credential.get_input('project', default=''))
                if credential.has_input('domain'):
                    openstack_auth['domain_name'] = credential.get_input('domain', default='')
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
        cred = job.get_deprecated_credential('ssh')
        if cred:
            for field in ('ssh_key_unlock', 'ssh_password', 'become_password'):
                value = kwargs.get(
                    field,
                    cred.get_input('password' if field == 'ssh_password' else field, default='')
                )
                if value not in ('', 'ASK'):
                    passwords[field] = value

        for cred in job.vault_credentials:
            field = 'vault_password'
            vault_id = cred.get_input('vault_id', default=None)
            if vault_id:
                field = 'vault_password.{}'.format(vault_id)
                if field in passwords:
                    raise RuntimeError(
                        'multiple vault credentials were specified with --vault-id {}@prompt'.format(
                            vault_id
                        )
                    )

            value = kwargs.get(field, None)
            if value is None:
                value = cred.get_input('vault_password', default='')

            if value not in ('', 'ASK'):
                passwords[field] = value

        '''
        Only 1 value can be provided for a unique prompt string. Prefer ssh
        key unlock over network key unlock.
        '''
        if 'ssh_key_unlock' not in passwords:
            for cred in job.network_credentials:
                if cred.has_input('ssh_key_unlock'):
                    passwords['ssh_key_unlock'] = kwargs.get(
                        'ssh_key_unlock',
                        cred.get_input('ssh_key_unlock', default='')
                    )
                    break

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
        env = self.add_ansible_venv(job.ansible_virtualenv_path, env, add_awx_lib=kwargs.get('isolated', False), **kwargs)
        # Set environment variables needed for inventory and job event
        # callbacks to work.
        env['JOB_ID'] = str(job.pk)
        env['INVENTORY_ID'] = str(job.inventory.pk)
        if job.use_fact_cache:
            library_path = env.get('ANSIBLE_LIBRARY')
            env['ANSIBLE_LIBRARY'] = ':'.join(
                filter(None, [
                    library_path,
                    self.get_path_to('..', 'plugins', 'library')
                ])
            )
            env['ANSIBLE_CACHE_PLUGIN'] = "jsonfile"
            env['ANSIBLE_CACHE_PLUGIN_CONNECTION'] = os.path.join(kwargs['private_data_dir'], 'facts')
        if job.project:
            env['PROJECT_REVISION'] = job.project.scm_revision
        env['ANSIBLE_RETRY_FILES_ENABLED'] = "False"
        env['MAX_EVENT_RES'] = str(settings.MAX_EVENT_RES_DATA)
        if not kwargs.get('isolated'):
            env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_path
            env['ANSIBLE_STDOUT_CALLBACK'] = 'awx_display'
            env['AWX_HOST'] = settings.TOWER_URL_BASE
        env['CACHE'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''

        # Create a directory for ControlPath sockets that is unique to each
        # job and visible inside the proot environment (when enabled).
        cp_dir = os.path.join(kwargs['private_data_dir'], 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0o700)
        env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = cp_dir

        # Set environment variables for cloud credentials.
        cred_files = kwargs.get('private_data_files', {}).get('credentials', {})
        for cloud_cred in job.cloud_credentials:
            if cloud_cred and cloud_cred.kind == 'openstack':
                env['OS_CLIENT_CONFIG_FILE'] = cred_files.get(cloud_cred, '')

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

        return env

    def build_args(self, job, **kwargs):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.get_deprecated_credential('ssh')

        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = kwargs.get('username', creds.get_input('username', default=''))
            become_method = kwargs.get('become_method', creds.get_input('become_method', default=''))
            become_username = kwargs.get('become_username', creds.get_input('become_username', default=''))
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible-playbook's default of using
        # the current user.
        ssh_username = ssh_username or 'root'
        args = [
            self.get_path_to_ansible(job, 'ansible-playbook', **kwargs),
            '-i',
            self.build_inventory(job, **kwargs)
        ]
        if job.job_type == 'check':
            args.append('--check')
        args.extend(['-u', sanitize_jinja(ssh_username)])
        if 'ssh_password' in kwargs.get('passwords', {}):
            args.append('--ask-pass')
        if job.become_enabled:
            args.append('--become')
        if job.diff_mode:
            args.append('--diff')
        if become_method:
            args.extend(['--become-method', sanitize_jinja(become_method)])
        if become_username:
            args.extend(['--become-user', sanitize_jinja(become_username)])
        if 'become_password' in kwargs.get('passwords', {}):
            args.append('--ask-become-pass')

        # Support prompting for multiple vault passwords
        for k, v in kwargs.get('passwords', {}).items():
            if k.startswith('vault_password'):
                if k == 'vault_password':
                    args.append('--ask-vault-pass')
                else:
                    vault_id = k.split('.')[1]
                    args.append('--vault-id')
                    args.append('{}@prompt'.format(vault_id))

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
        extra_vars = job.awx_meta_vars()

        if job.extra_vars_dict:
            if kwargs.get('display', False) and job.job_template:
                extra_vars.update(json.loads(job.display_extra_vars()))
            else:
                extra_vars.update(json.loads(job.decrypted_extra_vars()))

        # By default, all extra vars disallow Jinja2 template usage for
        # security reasons; top level key-values defined in JT.extra_vars, however,
        # are whitelisted as "safe" (because they can only be set by users with
        # higher levels of privilege - those that have the ability create and
        # edit Job Templates)
        safe_dict = {}
        if job.job_template and settings.ALLOW_JINJA_IN_EXTRA_VARS == 'template':
            safe_dict = job.job_template.extra_vars_dict
        extra_vars_path = self.build_extra_vars_file(
            vars=extra_vars,
            safe_dict=safe_dict,
            **kwargs
        )
        args.extend(['-e', '@%s' % (extra_vars_path)])

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

    def get_password_prompts(self, **kwargs):
        d = super(RunJob, self).get_password_prompts(**kwargs)
        d[re.compile(r'Enter passphrase for .*:\s*?$', re.M)] = 'ssh_key_unlock'
        d[re.compile(r'Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[re.compile(r'%s password.*:\s*?$' % (method[0]), re.M)] = 'become_password'
            d[re.compile(r'%s password.*:\s*?$' % (method[0].upper()), re.M)] = 'become_password'
        d[re.compile(r'BECOME password.*:\s*?$', re.M)] = 'become_password'
        d[re.compile(r'SSH password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Vault password:\s*?$', re.M)] = 'vault_password'
        for k, v in kwargs.get('passwords', {}).items():
            if k.startswith('vault_password.'):
                vault_id = k.split('.')[1]
                d[re.compile(r'Vault password \({}\):\s*?$'.format(vault_id), re.M)] = k
        return d

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def pre_run_hook(self, job, **kwargs):
        if job.inventory is None:
            error = _('Job could not start because it does not have a valid inventory.')
            self.update_model(job.pk, status='failed', job_explanation=error)
            raise RuntimeError(error)
        if job.project and job.project.scm_type:
            pu_ig = job.instance_group
            pu_en = job.execution_node
            if job.is_isolated() is True:
                pu_ig = pu_ig.controller
                pu_en = settings.CLUSTER_HOST_ID
            if job.project.status in ('error', 'failed'):
                msg = _(
                    'The project revision for this job template is unknown due to a failed update.'
                )
                job = self.update_model(job.pk, status='failed', job_explanation=msg)
                raise RuntimeError(msg)
            local_project_sync = job.project.create_project_update(
                _eager_fields=dict(
                    launch_type="sync",
                    job_type='run',
                    status='running',
                    instance_group = pu_ig,
                    execution_node=pu_en,
                    celery_task_id=job.celery_task_id))
            # save the associated job before calling run() so that a
            # cancel() call on the job can cancel the project update
            job = self.update_model(job.pk, project_update=local_project_sync)

            project_update_task = local_project_sync._get_task_class()
            try:
                project_update_task().run(local_project_sync.id)
                job = self.update_model(job.pk, scm_revision=job.project.scm_revision)
            except Exception:
                local_project_sync.refresh_from_db()
                if local_project_sync.status != 'canceled':
                    job = self.update_model(job.pk, status='failed',
                                            job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                                             ('project_update', local_project_sync.name, local_project_sync.id)))
                    raise

    def final_run_hook(self, job, status, **kwargs):
        super(RunJob, self).final_run_hook(job, status, **kwargs)
        if 'private_data_dir' not in kwargs:
            # If there's no private data dir, that means we didn't get into the
            # actual `run()` call; this _usually_ means something failed in
            # the pre_run_hook method
            return
        if job.use_fact_cache:
            job.finish_job_fact_cache(
                kwargs['private_data_dir'],
                kwargs['fact_modification_times']
            )

        # persist artifacts set via `set_stat` (if any)
        custom_stats_path = os.path.join(kwargs['private_data_dir'], 'artifacts', 'custom')
        if os.path.exists(custom_stats_path):
            with open(custom_stats_path, 'r') as f:
                custom_stat_data = None
                try:
                    custom_stat_data = json.load(f)
                except ValueError:
                    logger.warning('Could not parse custom `set_fact` data for job {}'.format(job.id))

                if custom_stat_data:
                    job.artifacts = custom_stat_data
                    job.save(update_fields=['artifacts'])

        try:
            inventory = job.inventory
        except Inventory.DoesNotExist:
            pass
        else:
            update_inventory_computed_fields.delay(inventory.id, True)


@task()
class RunProjectUpdate(BaseTask):

    model = ProjectUpdate
    event_model = ProjectUpdateEvent
    event_data_key = 'project_update_id'

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
            if credential.has_input('ssh_key_data'):
                private_data['credentials'][credential] = credential.get_input('ssh_key_data', default='')
        return private_data

    def build_passwords(self, project_update, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update,
                                                                  **kwargs)
        if project_update.credential:
            passwords['scm_key_unlock'] = project_update.credential.get_input('ssh_key_unlock', default='')
            passwords['scm_username'] = project_update.credential.get_input('username', default='')
            passwords['scm_password'] = project_update.credential.get_input('password', default='')
        return passwords

    def build_env(self, project_update, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = super(RunProjectUpdate, self).build_env(project_update, **kwargs)
        env = self.add_ansible_venv(settings.ANSIBLE_VENV_PATH, env)
        env['ANSIBLE_RETRY_FILES_ENABLED'] = str(False)
        env['ANSIBLE_ASK_PASS'] = str(False)
        env['ANSIBLE_BECOME_ASK_PASS'] = str(False)
        env['DISPLAY'] = '' # Prevent stupid password popup when running tests.
        # give ansible a hint about the intended tmpdir to work around issues
        # like https://github.com/ansible/ansible/issues/30064
        env['TMP'] = settings.AWX_PROOT_BASE_PATH
        env['CACHE'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''
        env['PROJECT_UPDATE_ID'] = str(project_update.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = self.get_path_to('..', 'plugins', 'callback')
        env['ANSIBLE_STDOUT_CALLBACK'] = 'awx_display'
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
        args = [
            self.get_path_to_ansible(project_update, 'ansible-playbook', **kwargs),
            '-i',
            self.build_inventory(project_update, **kwargs)
        ]
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
            'roles_enabled': getattr(settings, 'AWX_ROLES_ENABLED', True)
        })
        extra_vars_path = self.build_extra_vars_file(vars=extra_vars, **kwargs)
        args.extend(['-e', '@%s' % (extra_vars_path)])
        args.append('project_update.yml')
        return args

    def build_safe_args(self, project_update, **kwargs):
        pwdict = dict(kwargs.get('passwords', {}).items())
        for pw_name, pw_val in list(pwdict.items()):
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
        for pw_name, pw_val in list(pwdict.items()):
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

    def get_password_prompts(self, **kwargs):
        d = super(RunProjectUpdate, self).get_password_prompts(**kwargs)
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

    def _update_dependent_inventories(self, project_update, dependent_inventory_sources):
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
                    _eager_fields=dict(
                        launch_type='scm',
                        status='running',
                        instance_group=project_update.instance_group,
                        execution_node=project_update.execution_node,
                        source_project_update=project_update,
                        celery_task_id=project_update.celery_task_id))
            try:
                inv_update_class().run(local_inv_update.id)
            except Exception:
                logger.exception('{} Unhandled exception updating dependent SCM inventory sources.'.format(
                    project_update.log_format
                ))

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

        start_time = time.time()
        while True:
            try:
                instance.refresh_from_db(fields=['cancel_flag'])
                if instance.cancel_flag:
                    logger.info("ProjectUpdate({0}) was cancelled".format(instance.pk))
                    return
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
            logger.info(
                '{} spent {} waiting to acquire lock for local source tree '
                'for path {}.'.format(instance.log_format, waiting_time, lock_path))

    def pre_run_hook(self, instance, **kwargs):
        # re-create root project folder if a natural disaster has destroyed it
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        self.acquire_lock(instance)

    def post_run_hook(self, instance, status, **kwargs):
        self.release_lock(instance)
        p = instance.project
        if instance.job_type == 'check' and status not in ('failed', 'canceled',):
            fd = open(self.revision_path, 'r')
            lines = fd.readlines()
            if lines:
                p.scm_revision = lines[0].strip()
            else:
                logger.info("{} Could not find scm revision in check".format(instance.log_format))
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


@task()
class RunInventoryUpdate(BaseTask):

    model = InventoryUpdate
    event_model = InventoryUpdateEvent
    event_data_key = 'inventory_update_id'

    @property
    def proot_show_paths(self):
        return [self.get_path_to('..', 'plugins', 'inventory')]

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
        credential = inventory_update.get_cloud_credential()

        if inventory_update.source == 'openstack':
            openstack_auth = dict(auth_url=credential.get_input('host', default=''),
                                  username=credential.get_input('username', default=''),
                                  password=credential.get_input('password', default=''),
                                  project_name=credential.get_input('project', default=''))
            if credential.has_input('domain'):
                openstack_auth['domain_name'] = credential.get_input('domain', default='')

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

        cp = configparser.RawConfigParser()
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
            for k, v in ec2_opts.items():
                cp.set(section, k, str(v))
        # Allow custom options to vmware inventory script.
        elif inventory_update.source == 'vmware':

            section = 'vmware'
            cp.add_section(section)
            cp.set('vmware', 'cache_max_age', '0')
            cp.set('vmware', 'validate_certs', str(settings.VMWARE_VALIDATE_CERTS))
            cp.set('vmware', 'username', credential.get_input('username', default=''))
            cp.set('vmware', 'password', credential.get_input('password', default=''))
            cp.set('vmware', 'server', credential.get_input('host', default=''))

            vmware_opts = dict(inventory_update.source_vars_dict.items())
            if inventory_update.instance_filters:
                vmware_opts.setdefault('host_filters', inventory_update.instance_filters)
            if inventory_update.group_by:
                vmware_opts.setdefault('groupby_patterns', inventory_update.group_by)

            for k, v in vmware_opts.items():
                cp.set(section, k, str(v))

        elif inventory_update.source == 'satellite6':
            section = 'foreman'
            cp.add_section(section)

            group_patterns = '[]'
            group_prefix = 'foreman_'
            want_hostcollections = 'False'
            foreman_opts = dict(inventory_update.source_vars_dict.items())
            foreman_opts.setdefault('ssl_verify', 'False')
            for k, v in foreman_opts.items():
                if k == 'satellite6_group_patterns' and isinstance(v, str):
                    group_patterns = v
                elif k == 'satellite6_group_prefix' and isinstance(v, str):
                    group_prefix = v
                elif k == 'satellite6_want_hostcollections' and isinstance(v, bool):
                    want_hostcollections = v
                else:
                    cp.set(section, k, str(v))

            if credential:
                cp.set(section, 'url', credential.get_input('host', default=''))
                cp.set(section, 'user', credential.get_input('username', default=''))
                cp.set(section, 'password', credential.get_input('password', default=''))

            section = 'ansible'
            cp.add_section(section)
            cp.set(section, 'group_patterns', group_patterns)
            cp.set(section, 'want_facts', 'True')
            cp.set(section, 'want_hostcollections', str(want_hostcollections))
            cp.set(section, 'group_prefix', group_prefix)

            section = 'cache'
            cp.add_section(section)
            cp.set(section, 'path', '/tmp')
            cp.set(section, 'max_age', '0')

        elif inventory_update.source == 'cloudforms':
            section = 'cloudforms'
            cp.add_section(section)

            if credential:
                cp.set(section, 'url', credential.get_input('host', default=''))
                cp.set(section, 'username', credential.get_input('username', default=''))
                cp.set(section, 'password', credential.get_input('password', default=''))
                cp.set(section, 'ssl_verify', "false")

            cloudforms_opts = dict(inventory_update.source_vars_dict.items())
            for opt in ['version', 'purge_actions', 'clean_group_keys', 'nest_tags', 'suffix', 'prefer_ipv4']:
                if opt in cloudforms_opts:
                    cp.set(section, opt, str(cloudforms_opts[opt]))

            section = 'cache'
            cp.add_section(section)
            cp.set(section, 'max_age', "0")
            cache_path = tempfile.mkdtemp(
                prefix='cloudforms_cache',
                dir=kwargs.get('private_data_dir', None)
            )
            cp.set(section, 'path', cache_path)

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

            azure_rm_opts = dict(inventory_update.source_vars_dict.items())
            for k, v in azure_rm_opts.items():
                cp.set(section, k, str(v))

        # Return INI content.
        if cp.sections():
            f = StringIO()
            cp.write(f)
            private_data['credentials'][credential] = f.getvalue()
            return private_data

    def build_passwords(self, inventory_update, **kwargs):
        """Build a dictionary of authentication/credential information for
        an inventory source.

        This dictionary is used by `build_env`, below.
        """
        # Run the superclass implementation.
        passwords = super(RunInventoryUpdate, self).build_passwords(inventory_update, **kwargs)

        # Take key fields from the credential in use and add them to the
        # passwords dictionary.
        credential = inventory_update.get_cloud_credential()
        if credential:
            for subkey in ('username', 'host', 'project', 'client', 'tenant', 'subscription'):
                passwords['source_%s' % subkey] = credential.get_input(subkey, default='')
            for passkey in ('password', 'ssh_key_data', 'security_token', 'secret'):
                k = 'source_%s' % passkey
                passwords[k] = credential.get_input(passkey, default='')
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
        env.update(STANDARD_INVENTORY_UPDATE_ENV)
        plugin_name = inventory_update.get_inventory_plugin_name()
        if plugin_name is not None:
            env['ANSIBLE_INVENTORY_ENABLED'] = plugin_name

        # Set environment variables specific to each source.
        #
        # These are set here and then read in by the various Ansible inventory
        # modules, which will actually do the inventory sync.
        #
        # The inventory modules are vendored in AWX in the
        # `awx/plugins/inventory` directory; those files should be kept in
        # sync with those in Ansible core at all times.

        ini_mapping = {
            'ec2': 'EC2_INI_PATH',
            'vmware': 'VMWARE_INI_PATH',
            'azure_rm': 'AZURE_INI_PATH',
            'openstack': 'OS_CLIENT_CONFIG_FILE',
            'satellite6': 'FOREMAN_INI_PATH',
            'cloudforms': 'CLOUDFORMS_INI_PATH'
        }
        if inventory_update.source in ini_mapping:
            cred_data = kwargs.get('private_data_files', {}).get('credentials', '')
            env[ini_mapping[inventory_update.source]] = cred_data.get(
                inventory_update.get_cloud_credential(), ''
            )

        if inventory_update.source == 'gce':
            env['GCE_ZONE'] = inventory_update.source_regions if inventory_update.source_regions != 'all' else ''  # noqa

            # by default, the GCE inventory source caches results on disk for
            # 5 minutes; disable this behavior
            cp = configparser.ConfigParser()
            cp.add_section('cache')
            cp.set('cache', 'cache_max_age', '0')
            handle, path = tempfile.mkstemp(dir=kwargs.get('private_data_dir', None))
            cp.write(os.fdopen(handle, 'w'))
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            env['GCE_INI_PATH'] = path
        elif inventory_update.source in ['scm', 'custom']:
            for env_k in inventory_update.source_vars_dict:
                if str(env_k) not in env and str(env_k) not in settings.INV_ENV_VARIABLE_BLACKLIST:
                    env[str(env_k)] = str(inventory_update.source_vars_dict[env_k])
        elif inventory_update.source == 'tower':
            env['TOWER_INVENTORY'] = inventory_update.instance_filters
            env['TOWER_LICENSE_TYPE'] = get_licenser().validate()['license_type']
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

        if inventory is None:
            raise RuntimeError('Inventory Source is not associated with an Inventory.')

        # Piece together the initial command to run via. the shell.
        args = ['awx-manage', 'inventory_import']
        args.extend(['--inventory-id', str(inventory.pk)])

        # Add appropriate arguments for overwrite if the inventory_update
        # object calls for it.
        if inventory_update.overwrite:
            args.append('--overwrite')
        if inventory_update.overwrite_vars:
            args.append('--overwrite-vars')

        # Declare the virtualenv the management command should activate
        # as it calls ansible-inventory
        args.extend(['--venv', inventory_update.ansible_virtualenv_path])

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
            handle, path = tempfile.mkstemp(dir=kwargs['private_data_dir'])
            f = os.fdopen(handle, 'w')
            if inventory_update.source_script is None:
                raise RuntimeError('Inventory Script does not exist')
            f.write(inventory_update.source_script.script)
            f.close()
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            args.append(path)
            args.append("--custom")
        args.append('-v%d' % inventory_update.verbosity)
        if settings.DEBUG:
            args.append('--traceback')
        return args

    def build_cwd(self, inventory_update, **kwargs):
        if inventory_update.source == 'scm' and inventory_update.source_project_update:
            return inventory_update.source_project_update.get_project_path(check_if_exists=False)
        return self.get_path_to('..', 'plugins', 'inventory')

    def get_idle_timeout(self):
        return getattr(settings, 'INVENTORY_UPDATE_IDLE_TIMEOUT', None)

    def pre_run_hook(self, inventory_update, **kwargs):
        source_project = None
        if inventory_update.inventory_source:
            source_project = inventory_update.inventory_source.source_project
        if (inventory_update.source=='scm' and inventory_update.launch_type!='scm' and source_project):
            local_project_sync = source_project.create_project_update(
                _eager_fields=dict(
                    launch_type="sync",
                    job_type='run',
                    status='running',
                    execution_node=inventory_update.execution_node,
                    instance_group = inventory_update.instance_group,
                    celery_task_id=inventory_update.celery_task_id))
            # associate the inventory update before calling run() so that a
            # cancel() call on the inventory update can cancel the project update
            local_project_sync.scm_inventory_updates.add(inventory_update)

            project_update_task = local_project_sync._get_task_class()
            try:
                project_update_task().run(local_project_sync.id)
                inventory_update.inventory_source.scm_last_revision = local_project_sync.project.scm_revision
                inventory_update.inventory_source.save(update_fields=['scm_last_revision'])
            except Exception:
                inventory_update = self.update_model(
                    inventory_update.pk, status='failed',
                    job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                     ('project_update', local_project_sync.name, local_project_sync.id)))
                raise


@task()
class RunAdHocCommand(BaseTask):
    '''
    Run an ad hoc command using ansible.
    '''

    model = AdHocCommand
    event_model = AdHocCommandEvent
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
        if creds and creds.has_input('ssh_key_data'):
            private_data['credentials'][creds] = creds.get_input('ssh_key_data', default='')
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
                    value = kwargs.get(field, creds.get_input('password', default=''))
                else:
                    value = kwargs.get(field, creds.get_input(field, default=''))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, ad_hoc_command, **kwargs):
        '''
        Build environment dictionary for ansible.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        env = super(RunAdHocCommand, self).build_env(ad_hoc_command, **kwargs)
        env = self.add_ansible_venv(settings.ANSIBLE_VENV_PATH, env)
        # Set environment variables needed for inventory and ad hoc event
        # callbacks to work.
        env['AD_HOC_COMMAND_ID'] = str(ad_hoc_command.pk)
        env['INVENTORY_ID'] = str(ad_hoc_command.inventory.pk)
        env['INVENTORY_HOSTVARS'] = str(True)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ANSIBLE_LOAD_CALLBACK_PLUGINS'] = '1'
        env['ANSIBLE_STDOUT_CALLBACK'] = 'minimal'  # Hardcoded by Ansible for ad-hoc commands (either minimal or oneline).
        env['ANSIBLE_SFTP_BATCH_MODE'] = 'False'
        env['CACHE'] = settings.CACHES['default']['LOCATION'] if 'LOCATION' in settings.CACHES['default'] else ''

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
            ssh_username = kwargs.get('username', creds.get_input('username', default=''))
            become_method = kwargs.get('become_method', creds.get_input('become_method', default=''))
            become_username = kwargs.get('become_username', creds.get_input('become_username', default=''))
        else:
            become_method = None
            become_username = ""
        # Always specify the normal SSH user as root by default.  Since this
        # task is normally running in the background under a service account,
        # it doesn't make sense to rely on ansible's default of using the
        # current user.
        ssh_username = ssh_username or 'root'
        args = [
            self.get_path_to_ansible(ad_hoc_command, 'ansible', **kwargs),
            '-i',
            self.build_inventory(ad_hoc_command, **kwargs)
        ]
        if ad_hoc_command.job_type == 'check':
            args.append('--check')
        args.extend(['-u', sanitize_jinja(ssh_username)])
        if 'ssh_password' in kwargs.get('passwords', {}):
            args.append('--ask-pass')
        # We only specify sudo/su user and password if explicitly given by the
        # credential.  Credential should never specify both sudo and su.
        if ad_hoc_command.become_enabled:
            args.append('--become')
        if become_method:
            args.extend(['--become-method', sanitize_jinja(become_method)])
        if become_username:
            args.extend(['--become-user', sanitize_jinja(become_username)])
        if 'become_password' in kwargs.get('passwords', {}):
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
                raise ValueError(_(
                    "{} are prohibited from use in ad hoc commands."
                ).format(", ".join(removed_vars)))
            extra_vars.update(ad_hoc_command.extra_vars_dict)
        extra_vars_path = self.build_extra_vars_file(vars=extra_vars, **kwargs)
        args.extend(['-e', '@%s' % (extra_vars_path)])

        args.extend(['-m', ad_hoc_command.module_name])
        module_args = ad_hoc_command.module_args
        if settings.ALLOW_JINJA_IN_EXTRA_VARS != 'always':
            module_args = sanitize_jinja(module_args)
        args.extend(['-a', module_args])

        if ad_hoc_command.limit:
            args.append(ad_hoc_command.limit)
        else:
            args.append('all')

        return args

    def build_cwd(self, ad_hoc_command, **kwargs):
        return kwargs['private_data_dir']

    def get_idle_timeout(self):
        return getattr(settings, 'JOB_RUN_IDLE_TIMEOUT', None)

    def get_password_prompts(self, **kwargs):
        d = super(RunAdHocCommand, self).get_password_prompts(**kwargs)
        d[re.compile(r'Enter passphrase for .*:\s*?$', re.M)] = 'ssh_key_unlock'
        d[re.compile(r'Bad passphrase, try again for .*:\s*?$', re.M)] = ''
        for method in PRIVILEGE_ESCALATION_METHODS:
            d[re.compile(r'%s password.*:\s*?$' % (method[0]), re.M)] = 'become_password'
            d[re.compile(r'%s password.*:\s*?$' % (method[0].upper()), re.M)] = 'become_password'
        d[re.compile(r'BECOME password.*:\s*?$', re.M)] = 'become_password'
        d[re.compile(r'SSH password:\s*?$', re.M)] = 'ssh_password'
        d[re.compile(r'Password:\s*?$', re.M)] = 'ssh_password'
        return d

    def should_use_proot(self, instance, **kwargs):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)


@task()
class RunSystemJob(BaseTask):

    model = SystemJob
    event_model = SystemJobEvent
    event_data_key = 'system_job_id'

    def build_args(self, system_job, **kwargs):
        args = ['awx-manage', system_job.job_type]
        try:
            # System Job extra_vars can be blank, must be JSON if not blank
            if system_job.extra_vars == '':
                json_vars = {}
            else:
                json_vars = json.loads(system_job.extra_vars)
            if 'days' in json_vars:
                args.extend(['--days', str(json_vars.get('days', 60))])
            if 'dry_run' in json_vars and json_vars['dry_run']:
                args.extend(['--dry-run'])
            if system_job.job_type == 'cleanup_jobs':
                args.extend(['--jobs', '--project-updates', '--inventory-updates',
                             '--management-jobs', '--ad-hoc-commands', '--workflow-jobs',
                             '--notifications'])
        except Exception:
            logger.exception("{} Failed to parse system job".format(system_job.log_format))
        return args

    def build_env(self, instance, **kwargs):
        env = super(RunSystemJob, self).build_env(instance,
                                                  **kwargs)
        env = self.add_awx_venv(env)
        return env

    def build_cwd(self, instance, **kwargs):
        return settings.BASE_DIR


def _reconstruct_relationships(copy_mapping):
    for old_obj, new_obj in copy_mapping.items():
        model = type(old_obj)
        for field_name in getattr(model, 'FIELDS_TO_PRESERVE_AT_COPY', []):
            field = model._meta.get_field(field_name)
            if isinstance(field, ForeignKey):
                if getattr(new_obj, field_name, None):
                    continue
                related_obj = getattr(old_obj, field_name)
                related_obj = copy_mapping.get(related_obj, related_obj)
                setattr(new_obj, field_name, related_obj)
            elif field.many_to_many:
                for related_obj in getattr(old_obj, field_name).all():
                    logger.debug('Deep copy: Adding {} to {}({}).{} relationship'.format(
                        related_obj, new_obj, model, field_name
                    ))
                    getattr(new_obj, field_name).add(copy_mapping.get(related_obj, related_obj))
        new_obj.save()


@task()
def deep_copy_model_obj(
    model_module, model_name, obj_pk, new_obj_pk,
    user_pk, sub_obj_list, permission_check_func=None
):
    logger.info('Deep copy {} from {} to {}.'.format(model_name, obj_pk, new_obj_pk))
    from awx.api.generics import CopyAPIView
    from awx.main.signals import disable_activity_stream
    model = getattr(importlib.import_module(model_module), model_name, None)
    if model is None:
        return
    try:
        obj = model.objects.get(pk=obj_pk)
        new_obj = model.objects.get(pk=new_obj_pk)
        creater = User.objects.get(pk=user_pk)
    except ObjectDoesNotExist:
        logger.warning("Object or user no longer exists.")
        return
    with transaction.atomic(), ignore_inventory_computed_fields(), disable_activity_stream():
        copy_mapping = {}
        for sub_obj_setup in sub_obj_list:
            sub_model = getattr(importlib.import_module(sub_obj_setup[0]),
                                sub_obj_setup[1], None)
            if sub_model is None:
                continue
            try:
                sub_obj = sub_model.objects.get(pk=sub_obj_setup[2])
            except ObjectDoesNotExist:
                continue
            copy_mapping.update(CopyAPIView.copy_model_obj(
                obj, new_obj, sub_model, sub_obj, creater
            ))
        _reconstruct_relationships(copy_mapping)
        if permission_check_func:
            permission_check_func = getattr(getattr(
                importlib.import_module(permission_check_func[0]), permission_check_func[1]
            ), permission_check_func[2])
            permission_check_func(creater, copy_mapping.values())
    if isinstance(new_obj, Inventory):
        update_inventory_computed_fields.delay(new_obj.id, True)
