# -*- coding: utf-8 -*-

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict, namedtuple
import errno
import functools
import importlib
import json
import logging
import os
import shutil
import stat
import tempfile
import time
import traceback
from distutils.dir_util import copy_tree
from distutils.version import LooseVersion as Version
import yaml
import fcntl
try:
    import psutil
except Exception:
    psutil = None
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

# Runner
import ansible_runner

# AWX
from awx import __version__ as awx_application_version
from awx.main.constants import CLOUD_PROVIDERS, PRIVILEGE_ESCALATION_METHODS, STANDARD_INVENTORY_UPDATE_ENV
from awx.main.access import access_registry
from awx.main.models import (
    Schedule, TowerScheduleState, Instance, InstanceGroup,
    UnifiedJob, Notification,
    Inventory, InventorySource, SmartInventoryMembership,
    Job, AdHocCommand, ProjectUpdate, InventoryUpdate, SystemJob,
    JobEvent, ProjectUpdateEvent, InventoryUpdateEvent, AdHocCommandEvent, SystemJobEvent,
    build_safe_env
)
from awx.main.constants import ACTIVE_STATES
from awx.main.exceptions import AwxTaskError
from awx.main.queue import CallbackQueueDispatcher
from awx.main.isolated import manager as isolated_manager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename, reaper
from awx.main.utils import (get_ssh_version, update_scm_url,
                            get_licenser,
                            ignore_inventory_computed_fields,
                            ignore_inventory_group_removal, extract_ansible_vars, schedule_task_manager,
                            get_awx_version)
from awx.main.utils.common import _get_ansible_version, get_custom_venv_choices
from awx.main.utils.safe_yaml import safe_dump, sanitize_jinja
from awx.main.utils.reload import stop_local_services
from awx.main.utils.pglock import advisory_lock
from awx.main.consumers import emit_channel_notification
from awx.main import analytics
from awx.conf import settings_registry
from awx.conf.license import get_license

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


class InvalidVirtualenvError(Exception):

    def __init__(self, message):
        self.message = message


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


@task(queue='tower_broadcast_all', exchange_type='fanout')
def profile_sql(threshold=1, minutes=1):
    if threshold == 0:
        cache.delete('awx-profile-sql-threshold')
        logger.error('SQL PROFILING DISABLED')
    else:
        cache.set(
            'awx-profile-sql-threshold',
            threshold,
            timeout=minutes * 60
        )
        logger.error('SQL QUERIES >={}s ENABLED FOR {} MINUTE(S)'.format(threshold, minutes))


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
        isolated_manager.IsolatedManager().health_check(isolated_instance_qs)


@task()
def awx_periodic_scheduler():
    with advisory_lock('awx_periodic_scheduler_lock', wait=False) as acquired:
        if acquired is False:
            logger.debug("Not running periodic scheduler, another task holds lock")
            return
        logger.debug("Starting periodic scheduler")

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

    def get_ansible_version(self, instance):
        if not hasattr(self, '_ansible_version'):
            self._ansible_version = _get_ansible_version(
                ansible_path=self.get_path_to_ansible(instance, executable='ansible'))
        return self._ansible_version

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

    def build_private_data(self, instance, private_data_dir):
        '''
        Return SSH private key data (only if stored in DB as ssh_key_data).
        Return structure is a dict of the form:
        '''

    def build_private_data_dir(self, instance):
        '''
        Create a temporary directory for job-related files.
        '''
        path = tempfile.mkdtemp(prefix='awx_%s_' % instance.pk, dir=settings.AWX_PROOT_BASE_PATH)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        if settings.AWX_CLEANUP_PATHS:
            self.cleanup_paths.append(path)
        # Ansible Runner requires that this directory exists.
        # Specifically, when using process isolation
        os.mkdir(os.path.join(path, 'project'))
        return path

    def build_private_data_files(self, instance, private_data_dir):
        '''
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
        '''
        private_data = self.build_private_data(instance, private_data_dir)
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
                # OpenSSH formatted keys must have a trailing newline to be
                # accepted by ssh-add.
                if 'OPENSSH PRIVATE KEY' in data and not data.endswith('\n'):
                    data += '\n'
                # For credentials used with ssh-add, write to a named pipe which
                # will be read then closed, instead of leaving the SSH key on disk.
                if credential and credential.kind in ('ssh', 'scm') and not ssh_too_old:
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
                    handle, path = tempfile.mkstemp(dir=private_data_dir)
                    f = os.fdopen(handle, 'w')
                    f.write(data)
                    f.close()
                    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
                private_data_files['credentials'][credential] = path
            for credential, data in private_data.get('certificates', {}).items():
                name = 'credential_%d-cert.pub' % credential.pk
                path = os.path.join(private_data_dir, name)
                with open(path, 'w') as f:
                    f.write(data)
                    f.close()
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        return private_data_files

    def build_passwords(self, instance, runtime_passwords):
        '''
        Build a dictionary of passwords for responding to prompts.
        '''
        return {
            'yes': 'yes',
            'no': 'no',
            '': '',
        }

    def build_extra_vars_file(self, instance, private_data_dir, passwords):
        '''
        Build ansible yaml file filled with extra vars to be passed via -e@file.yml
        '''

    def build_params_process_isolation(self, instance, private_data_dir, cwd):
        '''
        Build ansible runner .run() parameters for process isolation.
        '''
        process_isolation_params = dict()
        if self.should_use_proot(instance):
            process_isolation_params = {
                'process_isolation': True,
                'process_isolation_path': settings.AWX_PROOT_BASE_PATH,
                'process_isolation_show_paths': self.proot_show_paths + [private_data_dir, cwd] + settings.AWX_PROOT_SHOW_PATHS,
                'process_isolation_hide_paths': [
                    settings.AWX_PROOT_BASE_PATH,
                    '/etc/tower',
                    '/etc/ssh',
                    '/var/lib/awx',
                    '/var/log',
                    settings.PROJECTS_ROOT,
                    settings.JOBOUTPUT_ROOT,
                ] + getattr(settings, 'AWX_PROOT_HIDE_PATHS', None) or [],
                'process_isolation_ro_paths': [settings.ANSIBLE_VENV_PATH, settings.AWX_VENV_PATH],
            }
            if getattr(instance, 'ansible_virtualenv_path', settings.ANSIBLE_VENV_PATH) != settings.ANSIBLE_VENV_PATH:
                process_isolation_params['process_isolation_ro_paths'].append(instance.ansible_virtualenv_path)
        return process_isolation_params

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

    def add_ansible_venv(self, venv_path, env, isolated=False):
        env['VIRTUAL_ENV'] = venv_path
        env['PATH'] = os.path.join(venv_path, "bin") + ":" + env['PATH']
        venv_libdir = os.path.join(venv_path, "lib")

        if not isolated and (
            not os.path.exists(venv_libdir) or
            os.path.join(venv_path, '') not in get_custom_venv_choices()
        ):
            raise InvalidVirtualenvError(_(
                'Invalid virtual environment selected: {}'.format(venv_path)
            ))

        isolated_manager.set_pythonpath(venv_libdir, env)

    def add_awx_venv(self, env):
        env['VIRTUAL_ENV'] = settings.AWX_VENV_PATH
        env['PATH'] = os.path.join(settings.AWX_VENV_PATH, "bin") + ":" + env['PATH']

    def build_env(self, instance, private_data_dir, isolated, private_data_files=None):
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
        if self.should_use_proot(instance):
            env['PROOT_TMP_DIR'] = settings.AWX_PROOT_BASE_PATH
        env['AWX_PRIVATE_DATA_DIR'] = private_data_dir
        return env

    def should_use_proot(self, instance):
        '''
        Return whether this task should use proot.
        '''
        return False

    def build_inventory(self, instance, private_data_dir):
        script_params = dict(hostvars=True)
        if hasattr(instance, 'job_slice_number'):
            script_params['slice_number'] = instance.job_slice_number
            script_params['slice_count'] = instance.job_slice_count
        script_data = instance.inventory.get_script_data(**script_params)
        json_data = json.dumps(script_data)
        handle, path = tempfile.mkstemp(dir=private_data_dir)
        f = os.fdopen(handle, 'w')
        f.write('#! /usr/bin/env python\n# -*- coding: utf-8 -*-\nprint(%r)\n' % json_data)
        f.close()
        os.chmod(path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR)
        return path

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

    def build_cwd(self, instance, private_data_dir):
        raise NotImplementedError

    def build_output_replacements(self, instance, passwords={}):
        return []

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
        '''
        Return a dictionary where keys are strings or regular expressions for
        prompts, and values are password lookup keys (keys that are returned
        from build_passwords).
        '''
        return OrderedDict()

    def create_expect_passwords_data_struct(self, password_prompts, passwords):
        expect_passwords = {}
        for k, v in password_prompts.items():
            expect_passwords[k] = passwords.get(v, '') or ''
        return expect_passwords

    def pre_run_hook(self, instance):
        '''
        Hook for any steps to run before the job/task starts
        '''

    def post_run_hook(self, instance, status):
        '''
        Hook for any steps to run before job/task is marked as complete.
        '''

    def final_run_hook(self, instance, status, private_data_dir, fact_modification_times, isolated_manager_instance=None):
        '''
        Hook for any steps to run after job/task is marked as complete.
        '''

    def event_handler(self, event_data):
        #
        # ⚠️  D-D-D-DANGER ZONE ⚠️
        # This method is called once for *every event* emitted by Ansible
        # Runner as a playbook runs.  That means that changes to the code in
        # this method are _very_ likely to introduce performance regressions.
        #
        # Even if this function is made on average .05s slower, it can have
        # devastating performance implications for playbooks that emit
        # tens or hundreds of thousands of events.
        #
        # Proceed with caution!
        #
        '''
        Ansible runner puts a parent_uuid on each event, no matter what the type.
        AWX only saves the parent_uuid if the event is for a Job.
        '''
        if event_data.get(self.event_data_key, None):
            if self.event_data_key != 'job_id':
                event_data.pop('parent_uuid', None)
        should_write_event = False
        event_data.setdefault(self.event_data_key, self.instance.id)
        self.dispatcher.dispatch(event_data)
        self.event_ct += 1

        '''
        Handle artifacts
        '''
        if event_data.get('event_data', {}).get('artifact_data', {}):
            self.instance.artifacts = event_data['event_data']['artifact_data']
            self.instance.save(update_fields=['artifacts'])

        return should_write_event

    def cancel_callback(self):
        '''
        Ansible runner callback to tell the job when/if it is canceled
        '''
        self.instance = self.update_model(self.instance.pk)
        if self.instance.cancel_flag or self.instance.status == 'canceled':
            cancel_wait = (now() - self.instance.modified).seconds if self.instance.modified else 0
            if cancel_wait > 5:
                logger.warn('Request to cancel {} took {} seconds to complete.'.format(self.instance.log_format, cancel_wait))
            return True
        return False

    def finished_callback(self, runner_obj):
        '''
        Ansible runner callback triggered on finished run
        '''
        event_data = {
            'event': 'EOF',
            'final_counter': self.event_ct,
        }
        event_data.setdefault(self.event_data_key, self.instance.id)
        self.dispatcher.dispatch(event_data)

    def status_handler(self, status_data, runner_config):
        '''
        Ansible runner callback triggered on status transition
        '''
        if status_data['status'] == 'starting':
            job_env = dict(runner_config.env)
            '''
            Take the safe environment variables and overwrite 
            '''
            for k, v in self.safe_env.items():
                if k in job_env:
                    job_env[k] = v
            self.instance = self.update_model(self.instance.pk, job_args=json.dumps(runner_config.command),
                                              job_cwd=runner_config.cwd, job_env=job_env)

    def check_handler(self, config):
        '''
        IsolatedManager callback triggered by the repeated checks of the isolated node
        '''
        job_env = build_safe_env(config['env'])
        for k, v in self.safe_cred_env.items():
            if k in job_env:
                job_env[k] = v
        self.instance = self.update_model(self.instance.pk,
                                          job_args=json.dumps(config['command']),
                                          job_cwd=config['cwd'],
                                          job_env=job_env)


    @with_path_cleanup
    def run(self, pk, **kwargs):
        '''
        Run the job/task and capture its output.
        '''
        # self.instance because of the update_model pattern and when it's used in callback handlers
        self.instance = self.update_model(pk, status='running',
                                          start_args='')  # blank field to remove encrypted passwords

        self.instance.websocket_emit_status("running")
        status, rc = 'error', None
        output_replacements = []
        extra_update_fields = {}
        fact_modification_times = {}
        self.event_ct = 0

        '''
        Needs to be an object property because status_handler uses it in a callback context
        '''
        self.safe_env = {}
        self.safe_cred_env = {}
        private_data_dir = None
        isolated_manager_instance = None

        try:
            isolated = self.instance.is_isolated()
            self.pre_run_hook(self.instance)
            if self.instance.cancel_flag:
                self.instance = self.update_model(self.instance.pk, status='canceled')
            if self.instance.status != 'running':
                # Stop the task chain and prevent starting the job if it has
                # already been canceled.
                self.instance = self.update_model(pk)
                status = self.instance.status
                raise RuntimeError('not starting %s task' % self.instance.status)

            if not os.path.exists(settings.AWX_PROOT_BASE_PATH):
                raise RuntimeError('AWX_PROOT_BASE_PATH=%s does not exist' % settings.AWX_PROOT_BASE_PATH)

            # store a record of the venv used at runtime
            if hasattr(self.instance, 'custom_virtualenv'):
                self.update_model(pk, custom_virtualenv=getattr(self.instance, 'ansible_virtualenv_path', settings.ANSIBLE_VENV_PATH))
            private_data_dir = self.build_private_data_dir(self.instance)

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
            self.build_extra_vars_file(self.instance, private_data_dir, passwords)
            args = self.build_args(self.instance, private_data_dir, passwords)
            # TODO: output_replacements hurts my head right now
            #output_replacements = self.build_output_replacements(self.instance, **kwargs)
            output_replacements = []
            cwd = self.build_cwd(self.instance, private_data_dir)
            process_isolation_params = self.build_params_process_isolation(self.instance,
                                                                           private_data_dir,
                                                                           cwd)
            env = self.build_env(self.instance, private_data_dir, isolated,
                                 private_data_files=private_data_files)
            self.safe_env = build_safe_env(env)

            credentials = self.build_credentials_list(self.instance)

            for credential in credentials:
                if credential:
                    credential.credential_type.inject_credential(
                        credential, env, self.safe_cred_env, args, private_data_dir
                    )

            self.safe_env.update(self.safe_cred_env)

            self.write_args_file(private_data_dir, args)

            password_prompts = self.get_password_prompts(passwords)
            expect_passwords = self.create_expect_passwords_data_struct(password_prompts, passwords)

            self.instance = self.update_model(self.instance.pk, output_replacements=output_replacements)

            params = {
                'ident': self.instance.id,
                'private_data_dir': private_data_dir,
                'project_dir': cwd,
                'playbook': self.build_playbook_path_relative_to_cwd(self.instance, private_data_dir),
                'inventory': self.build_inventory(self.instance, private_data_dir),
                'passwords': expect_passwords,
                'envvars': env,
                'event_handler': self.event_handler,
                'cancel_callback': self.cancel_callback,
                'finished_callback': self.finished_callback,
                'status_handler': self.status_handler,
                'settings': {
                    'job_timeout': self.get_instance_timeout(self.instance),
                    'pexpect_timeout': getattr(settings, 'PEXPECT_TIMEOUT', 5),
                    'suppress_ansible_output': True,
                    **process_isolation_params,
                },
            }

            if isinstance(self.instance, AdHocCommand):
                params['module'] = self.build_module_name(self.instance)
                params['module_args'] = self.build_module_args(self.instance)

            if getattr(self.instance, 'use_fact_cache', False):
                # Enable Ansible fact cache.
                params['fact_cache_type'] = 'jsonfile'
            else:
                # Disable Ansible fact cache.
                params['fact_cache_type'] = ''

            '''
            Delete parameters if the values are None or empty array
            '''
            for v in ['passwords', 'playbook', 'inventory']:
                if not params[v]:
                    del params[v]

            if self.instance.is_isolated() is True:
                module_args = None
                if 'module_args' in params:
                    # if it's adhoc, copy the module args
                    module_args = ansible_runner.utils.args2cmdline(
                        params.get('module_args'),
                    )
                else:
                    # otherwise, it's a playbook, so copy the project dir
                    copy_tree(cwd, os.path.join(private_data_dir, 'project'))
                shutil.move(
                    params.pop('inventory'),
                    os.path.join(private_data_dir, 'inventory')
                )
                ansible_runner.utils.dump_artifacts(params)
                isolated_manager_instance = isolated_manager.IsolatedManager(
                    cancelled_callback=lambda: self.update_model(self.instance.pk).cancel_flag,
                    check_callback=self.check_handler,
                )
                status, rc = isolated_manager_instance.run(self.instance,
                                                           private_data_dir,
                                                           params.get('playbook'),
                                                           params.get('module'),
                                                           module_args,
                                                           event_data_key=self.event_data_key,
                                                           ident=str(self.instance.pk))
                self.event_ct = len(isolated_manager_instance.handled_events)
            else:
                self.dispatcher = CallbackQueueDispatcher()
                res = ansible_runner.interface.run(**params)
                status = res.status
                rc = res.rc

            if status == 'timeout':
                self.instance.job_explanation = "Job terminated due to timeout"
                status = 'failed'
                extra_update_fields['job_explanation'] = self.instance.job_explanation

        except InvalidVirtualenvError as e:
            extra_update_fields['job_explanation'] = e.message
            logger.error('{} {}'.format(self.instance.log_format, e.message))
        except Exception:
            # this could catch programming or file system errors
            extra_update_fields['result_traceback'] = traceback.format_exc()
            logger.exception('%s Exception occurred while running task', self.instance.log_format)
        finally:
            logger.info('%s finished running, producing %s events.', self.instance.log_format, self.event_ct)

        try:
            self.post_run_hook(self.instance, status)
        except Exception:
            logger.exception('{} Post run hook errored.'.format(self.instance.log_format))

        self.instance = self.update_model(pk)
        self.instance = self.update_model(pk, status=status,
                                          output_replacements=output_replacements,
                                          emitted_events=self.event_ct,
                                          **extra_update_fields)

        try:
            self.final_run_hook(self.instance, status, private_data_dir, fact_modification_times, isolated_manager_instance=isolated_manager_instance)
        except Exception:
            logger.exception('{} Final run hook errored.'.format(self.instance.log_format))

        self.instance.websocket_emit_status(status)
        if status != 'successful':
            if status == 'canceled':
                raise AwxTaskError.TaskCancel(self.instance, rc)
            else:
                raise AwxTaskError.TaskError(self.instance, rc)


@task()
class RunJob(BaseTask):
    '''
    Run a job using ansible-playbook.
    '''

    model = Job
    event_model = JobEvent
    event_data_key = 'job_id'

    def build_private_data(self, job, private_data_dir):
        '''
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
        '''
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
        '''
        Build a dictionary of passwords for SSH private key, SSH user, sudo/su
        and ansible-vault.
        '''
        passwords = super(RunJob, self).build_passwords(job, runtime_passwords)
        cred = job.get_deprecated_credential('ssh')
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
                    raise RuntimeError(
                        'multiple vault credentials were specified with --vault-id {}@prompt'.format(
                            vault_id
                        )
                    )
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

    def add_ansible_venv(self, venv_path, env, isolated=False):
        super(RunJob, self).add_ansible_venv(venv_path, env, isolated=isolated)
        # Add awx/lib to PYTHONPATH.
        env['PYTHONPATH'] = env.get('PYTHONPATH', '') + self.get_path_to('..', 'lib') + ':'

    def build_env(self, job, private_data_dir, isolated=False, private_data_files=None):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        plugin_dirs = [plugin_dir]
        if hasattr(settings, 'AWX_ANSIBLE_CALLBACK_PLUGINS') and \
                settings.AWX_ANSIBLE_CALLBACK_PLUGINS:
            plugin_dirs.extend(settings.AWX_ANSIBLE_CALLBACK_PLUGINS)
        plugin_path = ':'.join(plugin_dirs)
        env = super(RunJob, self).build_env(job, private_data_dir,
                                            isolated=isolated,
                                            private_data_files=private_data_files)
        if private_data_files is None:
            private_data_files = {}
        self.add_ansible_venv(job.ansible_virtualenv_path, env, isolated=isolated)
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
        if job.project:
            env['PROJECT_REVISION'] = job.project.scm_revision
        env['ANSIBLE_RETRY_FILES_ENABLED'] = "False"
        env['MAX_EVENT_RES'] = str(settings.MAX_EVENT_RES_DATA)
        if not isolated:
            env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_path
            env['AWX_HOST'] = settings.TOWER_URL_BASE

        # Create a directory for ControlPath sockets that is unique to each
        # job and visible inside the proot environment (when enabled).
        cp_dir = os.path.join(private_data_dir, 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0o700)
        env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = cp_dir

        # Set environment variables for cloud credentials.
        cred_files = private_data_files.get('credentials', {})

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

    def build_args(self, job, private_data_dir, passwords):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        creds = job.get_deprecated_credential('ssh')

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

        return args

    def build_cwd(self, job, private_data_dir):
        cwd = job.project.get_project_path()
        if not cwd:
            root = settings.PROJECTS_ROOT
            raise RuntimeError('project local_path %s cannot be found in %s' %
                               (job.project.local_path, root))
        return cwd

    def build_playbook_path_relative_to_cwd(self, job, private_data_dir):
        return os.path.join(job.playbook)

    def build_extra_vars_file(self, job, private_data_dir, passwords):
        # Define special extra_vars for AWX, combine with job.extra_vars.
        extra_vars = job.awx_meta_vars()

        if job.extra_vars_dict:
            extra_vars.update(json.loads(job.decrypted_extra_vars()))

        # By default, all extra vars disallow Jinja2 template usage for
        # security reasons; top level key-values defined in JT.extra_vars, however,
        # are whitelisted as "safe" (because they can only be set by users with
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
                vault_id = k.split('.')[1]
                d[r'Vault password \({}\):\s*?$'.format(vault_id)] = k
        return d

    def should_use_proot(self, job):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def pre_run_hook(self, job):
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

    def final_run_hook(self, job, status, private_data_dir, fact_modification_times, isolated_manager_instance=None):
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
        if isolated_manager_instance:
            isolated_manager_instance.cleanup()
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

    def build_private_data(self, project_update, private_data_dir):
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
        if settings.AWX_CLEANUP_PATHS:
            self.cleanup_paths.append(self.revision_path)
        private_data = {'credentials': {}}
        if project_update.credential:
            credential = project_update.credential
            if credential.has_input('ssh_key_data'):
                private_data['credentials'][credential] = credential.get_input('ssh_key_data', default='')
        return private_data

    def build_passwords(self, project_update, runtime_passwords):
        '''
        Build a dictionary of passwords for SSH private key unlock and SCM
        username/password.
        '''
        passwords = super(RunProjectUpdate, self).build_passwords(project_update, runtime_passwords)
        if project_update.credential:
            passwords['scm_key_unlock'] = project_update.credential.get_input('ssh_key_unlock', default='')
            passwords['scm_username'] = project_update.credential.get_input('username', default='')
            passwords['scm_password'] = project_update.credential.get_input('password', default='')
        return passwords

    def build_env(self, project_update, private_data_dir, isolated=False, private_data_files=None):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = super(RunProjectUpdate, self).build_env(project_update, private_data_dir,
                                                      isolated=isolated,
                                                      private_data_files=private_data_files)
        self.add_ansible_venv(settings.ANSIBLE_VENV_PATH, env)
        env['ANSIBLE_RETRY_FILES_ENABLED'] = str(False)
        env['ANSIBLE_ASK_PASS'] = str(False)
        env['ANSIBLE_BECOME_ASK_PASS'] = str(False)
        env['DISPLAY'] = '' # Prevent stupid password popup when running tests.
        # give ansible a hint about the intended tmpdir to work around issues
        # like https://github.com/ansible/ansible/issues/30064
        env['TMP'] = settings.AWX_PROOT_BASE_PATH
        env['PROJECT_UPDATE_ID'] = str(project_update.pk)
        env['ANSIBLE_CALLBACK_PLUGINS'] = self.get_path_to('..', 'plugins', 'callback')
        return env

    def _build_scm_url_extra_vars(self, project_update, scm_username='', scm_password=''):
        '''
        Helper method to build SCM url and extra vars with parameters needed
        for authentication.
        '''
        extra_vars = {}
        scm_type = project_update.scm_type
        scm_url = update_scm_url(scm_type, project_update.scm_url,
                                 check_special_cases=False)
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

    def build_inventory(self, instance, private_data_dir):
        return 'localhost,'

    def build_args(self, project_update, private_data_dir, passwords):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
        args = []
        if getattr(settings, 'PROJECT_UPDATE_VVV', False):
            args.append('-vvv')
        else:
            args.append('-v')
        return args

    def build_extra_vars_file(self, project_update, private_data_dir, passwords):
        extra_vars = {}
        scm_url, extra_vars_new = self._build_scm_url_extra_vars(project_update,
                                                                 passwords.get('scm_username', ''),
                                                                 passwords.get('scm_password', ''))
        extra_vars.update(extra_vars_new)

        if project_update.project.scm_revision and project_update.job_type == 'run':
            scm_branch = project_update.project.scm_revision
        else:
            scm_branch = project_update.scm_branch or {'hg': 'tip'}.get(project_update.scm_type, 'HEAD')
        extra_vars.update({
            'project_path': project_update.get_project_path(check_if_exists=False),
            'insights_url': settings.INSIGHTS_URL_BASE,
            'awx_license_type': get_license(show_key=False).get('license_type', 'UNLICENSED'),
            'awx_version': get_awx_version(),
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
        self._write_extra_vars_file(private_data_dir, extra_vars)

    def build_cwd(self, project_update, private_data_dir):
        return self.get_path_to('..', 'playbooks')

    def build_playbook_path_relative_to_cwd(self, project_update, private_data_dir):
        self.build_cwd(project_update, private_data_dir)
        return os.path.join('project_update.yml')

    def build_output_replacements(self, project_update, passwords={}):
        '''
        Return search/replace strings to prevent output URLs from showing
        sensitive passwords.
        '''
        output_replacements = []
        before_url, before_passwords = self._build_scm_url_extra_vars(project_update, passwords)
        scm_username = before_passwords.get('scm_username', '')
        scm_password = before_passwords.get('scm_password', '')
        after_url = self._build_scm_url_extra_vars(project_update, passwords)[0]
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

    def get_password_prompts(self, passwords={}):
        d = super(RunProjectUpdate, self).get_password_prompts(passwords)
        d[r'Username for.*:\s*?$'] = 'scm_username'
        d[r'Password for.*:\s*?$'] = 'scm_password'
        d['Password:\s*?$'] = 'scm_password' # noqa
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

    def pre_run_hook(self, instance):
        # re-create root project folder if a natural disaster has destroyed it
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        self.acquire_lock(instance)

    def post_run_hook(self, instance, status):
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

    def should_use_proot(self, project_update):
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
            injector = InventorySource.injectors[inventory_update.source](self.get_ansible_version(inventory_update))
            return injector.build_private_data(inventory_update, private_data_dir)

    def build_passwords(self, inventory_update, runtime_passwords):
        """Build a dictionary of authentication/credential information for
        an inventory source.

        This dictionary is used by `build_env`, below.
        """
        # Run the superclass implementation.
        passwords = super(RunInventoryUpdate, self).build_passwords(inventory_update, runtime_passwords)

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

    def build_env(self, inventory_update, private_data_dir, isolated, private_data_files=None):
        """Build environment dictionary for inventory import.

        This used to be the mechanism by which any data that needs to be passed
        to the inventory update script is set up. In particular, this is how
        inventory update is aware of its proper credentials.

        Most environment injection is now accomplished by the credential
        injectors. The primary purpose this still serves is to
        still point to the inventory update INI or config file.
        """
        env = super(RunInventoryUpdate, self).build_env(inventory_update,
                                                        private_data_dir,
                                                        isolated,
                                                        private_data_files=private_data_files)
        if private_data_files is None:
            private_data_files = {}
        self.add_awx_venv(env)
        # Pass inventory source ID to inventory script.
        env['INVENTORY_SOURCE_ID'] = str(inventory_update.inventory_source_id)
        env['INVENTORY_UPDATE_ID'] = str(inventory_update.pk)
        env.update(STANDARD_INVENTORY_UPDATE_ENV)

        injector = None
        if inventory_update.source in InventorySource.injectors:
            injector = InventorySource.injectors[inventory_update.source](self.get_ansible_version(inventory_update))

        if injector is not None:
            env = injector.build_env(inventory_update, env, private_data_dir, private_data_files)
            # All CLOUD_PROVIDERS sources implement as either script or auto plugin
            if injector.should_use_plugin():
                env['ANSIBLE_INVENTORY_ENABLED'] = 'auto'
            else:
                env['ANSIBLE_INVENTORY_ENABLED'] = 'script'

        if inventory_update.source in ['scm', 'custom']:
            for env_k in inventory_update.source_vars_dict:
                if str(env_k) not in env and str(env_k) not in settings.INV_ENV_VARIABLE_BLACKLIST:
                    env[str(env_k)] = str(inventory_update.source_vars_dict[env_k])
        elif inventory_update.source == 'file':
            raise NotImplementedError('Cannot update file sources through the task system.')
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
        args.append(self.psuedo_build_inventory(inventory_update, private_data_dir))
        if src == 'custom':
            args.append("--custom")
        args.append('-v%d' % inventory_update.verbosity)
        if settings.DEBUG:
            args.append('--traceback')
        return args

    def build_inventory(self, inventory_update, private_data_dir):
        return None  # what runner expects in order to not deal with inventory

    def psuedo_build_inventory(self, inventory_update, private_data_dir):
        """Inventory imports are ran through a management command
        we pass the inventory in args to that command, so this is not considered
        to be "Ansible" inventory (by runner) even though it is
        Eventually, we would like to cut out the management command,
        and thus use this as the real inventory
        """
        src = inventory_update.source

        injector = None
        if inventory_update.source in InventorySource.injectors:
            injector = InventorySource.injectors[src](self.get_ansible_version(inventory_update))

        if injector is not None:
            if injector.should_use_plugin():
                content = injector.inventory_contents(inventory_update, private_data_dir)
                # must be a statically named file
                inventory_path = os.path.join(private_data_dir, injector.filename)
                with open(inventory_path, 'w') as f:
                    f.write(content)
                os.chmod(inventory_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            else:
                # Use the vendored script path
                inventory_path = self.get_path_to('..', 'plugins', 'inventory', injector.script_name)
        elif src == 'scm':
            inventory_path = inventory_update.get_actual_source_path()
        elif src == 'custom':
            handle, inventory_path = tempfile.mkstemp(dir=private_data_dir)
            f = os.fdopen(handle, 'w')
            if inventory_update.source_script is None:
                raise RuntimeError('Inventory Script does not exist')
            f.write(inventory_update.source_script.script)
            f.close()
            os.chmod(inventory_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        return inventory_path

    def build_cwd(self, inventory_update, private_data_dir):
        '''
        There are two cases where the inventory "source" is in a different
        location from the private data:
         - deprecated vendored inventory scripts in awx/plugins/inventory
         - SCM, where source needs to live in the project folder
        in these cases, the inventory does not exist in the standard tempdir
        '''
        src = inventory_update.source
        if src == 'scm' and inventory_update.source_project_update:
            return inventory_update.source_project_update.get_project_path(check_if_exists=False)
        if src in CLOUD_PROVIDERS:
            injector = None
            if src in InventorySource.injectors:
                injector = InventorySource.injectors[src](self.get_ansible_version(inventory_update))
            if (not injector) or (not injector.should_use_plugin()):
                return self.get_path_to('..', 'plugins', 'inventory')
        return private_data_dir

    def build_playbook_path_relative_to_cwd(self, inventory_update, private_data_dir):
        return None

    def build_credentials_list(self, inventory_update):
        # All credentials not used by inventory source injector
        return inventory_update.get_extra_credentials()

    def pre_run_hook(self, inventory_update):
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

    def build_private_data(self, ad_hoc_command, private_data_dir):
        '''
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
        '''
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
        '''
        Build a dictionary of passwords for SSH private key, SSH user and
        sudo/su.
        '''
        passwords = super(RunAdHocCommand, self).build_passwords(ad_hoc_command, runtime_passwords)
        cred = ad_hoc_command.credential
        if cred:
            for field in ('ssh_key_unlock', 'ssh_password', 'become_password'):
                value = runtime_passwords.get(field, cred.get_input('password' if field == 'ssh_password' else field, default=''))
                if value not in ('', 'ASK'):
                    passwords[field] = value
        return passwords

    def build_env(self, ad_hoc_command, private_data_dir, isolated=False, private_data_files=None):
        '''
        Build environment dictionary for ansible.
        '''
        plugin_dir = self.get_path_to('..', 'plugins', 'callback')
        env = super(RunAdHocCommand, self).build_env(ad_hoc_command, private_data_dir,
                                                     isolated=isolated,
                                                     private_data_files=private_data_files)
        self.add_ansible_venv(settings.ANSIBLE_VENV_PATH, env)
        # Set environment variables needed for inventory and ad hoc event
        # callbacks to work.
        env['AD_HOC_COMMAND_ID'] = str(ad_hoc_command.pk)
        env['INVENTORY_ID'] = str(ad_hoc_command.inventory.pk)
        env['INVENTORY_HOSTVARS'] = str(True)
        env['ANSIBLE_CALLBACK_PLUGINS'] = plugin_dir
        env['ANSIBLE_LOAD_CALLBACK_PLUGINS'] = '1'
        env['ANSIBLE_SFTP_BATCH_MODE'] = 'False'

        # Specify empty SSH args (should disable ControlPersist entirely for
        # ad hoc commands).
        env.setdefault('ANSIBLE_SSH_ARGS', '')

        return env

    def build_args(self, ad_hoc_command, private_data_dir, passwords):
        '''
        Build command line argument list for running ansible, optionally using
        ssh-agent for public/private key authentication.
        '''
        creds = ad_hoc_command.credential
        ssh_username, become_username, become_method = '', '', ''
        if creds:
            ssh_username = creds.username
            become_method = creds.become_method
            become_username = creds.become_username
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
                raise ValueError(_(
                    "{} are prohibited from use in ad hoc commands."
                ).format(", ".join(removed_vars)))
            extra_vars.update(ad_hoc_command.extra_vars_dict)

        if ad_hoc_command.limit:
            args.append(ad_hoc_command.limit)
        else:
            args.append('all')

        return args

    def build_extra_vars_file(self, ad_hoc_command, private_data_dir, passwords={}):
        extra_vars = ad_hoc_command.awx_meta_vars()

        if ad_hoc_command.extra_vars_dict:
            redacted_extra_vars, removed_vars = extract_ansible_vars(ad_hoc_command.extra_vars_dict)
            if removed_vars:
                raise ValueError(_(
                    "{} are prohibited from use in ad hoc commands."
                ).format(", ".join(removed_vars)))
            extra_vars.update(ad_hoc_command.extra_vars_dict)
        self._write_extra_vars_file(private_data_dir, extra_vars)

    def build_module_name(self, ad_hoc_command):
        return ad_hoc_command.module_name

    def build_module_args(self, ad_hoc_command):
        module_args = ad_hoc_command.module_args
        if settings.ALLOW_JINJA_IN_EXTRA_VARS != 'always':
            module_args = sanitize_jinja(module_args)
        return module_args

    def build_cwd(self, ad_hoc_command, private_data_dir):
        return private_data_dir

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

    def should_use_proot(self, ad_hoc_command):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def final_run_hook(self, adhoc_job, status, private_data_dir, fact_modification_times, isolated_manager_instance=None):
        super(RunAdHocCommand, self).final_run_hook(adhoc_job, status, private_data_dir, fact_modification_times)
        if isolated_manager_instance:
            isolated_manager_instance.cleanup()


@task()
class RunSystemJob(BaseTask):

    model = SystemJob
    event_model = SystemJobEvent
    event_data_key = 'system_job_id'

    def build_args(self, system_job, private_data_dir, passwords):
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

    def write_args_file(self, private_data_dir, args):
        path = os.path.join(private_data_dir, 'args')
        handle = os.open(path, os.O_RDWR | os.O_CREAT, stat.S_IREAD | stat.S_IWRITE)
        f = os.fdopen(handle, 'w')
        f.write(' '.join(args))
        f.close()
        os.chmod(path, stat.S_IRUSR)
        return path

    def build_env(self, instance, private_data_dir, isolated=False, private_data_files=None):
        env = super(RunSystemJob, self).build_env(instance, private_data_dir,
                                                  isolated=isolated,
                                                  private_data_files=private_data_files)
        self.add_awx_venv(env)
        return env

    def build_cwd(self, instance, private_data_dir):
        return settings.BASE_DIR

    def build_playbook_path_relative_to_cwd(self, job, private_data_dir):
        return None

    def build_inventory(self, instance, private_data_dir):
        return None


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
