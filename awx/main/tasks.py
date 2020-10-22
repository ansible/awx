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
from pathlib import Path
from uuid import uuid4
import urllib.parse as urlparse
import shlex

# Django
from django.conf import settings
from django.db import transaction, DatabaseError, IntegrityError, ProgrammingError, connection
from django.db.models.fields.related import ForeignKey
from django.utils.timezone import now, timedelta
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, gettext_noop
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

# Kubernetes
from kubernetes.client.rest import ApiException

# Django-CRUM
from crum import impersonate

# GitPython
import git
from gitdb.exc import BadName as BadGitName

# Runner
import ansible_runner

# AWX
from awx import __version__ as awx_application_version
from awx.main.constants import PRIVILEGE_ESCALATION_METHODS, STANDARD_INVENTORY_UPDATE_ENV
from awx.main.access import access_registry
from awx.main.analytics import all_collectors, expensive_collectors
from awx.main.redact import UriCleaner
from awx.main.models import (
    Schedule, TowerScheduleState, Instance, InstanceGroup,
    UnifiedJob, Notification,
    Inventory, InventorySource, SmartInventoryMembership,
    Job, AdHocCommand, ProjectUpdate, InventoryUpdate, SystemJob,
    JobEvent, ProjectUpdateEvent, InventoryUpdateEvent, AdHocCommandEvent, SystemJobEvent,
    build_safe_env, enforce_bigint_pk_migration
)
from awx.main.constants import ACTIVE_STATES
from awx.main.exceptions import AwxTaskError
from awx.main.queue import CallbackQueueDispatcher
from awx.main.isolated import manager as isolated_manager
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_local_queuename, reaper
from awx.main.utils import (update_scm_url,
                            ignore_inventory_computed_fields,
                            ignore_inventory_group_removal, extract_ansible_vars, schedule_task_manager,
                            get_awx_version)
from awx.main.utils.ansible import read_ansible_config
from awx.main.utils.common import get_custom_venv_choices
from awx.main.utils.external_logging import reconfigure_rsyslog
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
           'send_notifications', 'purge_old_stdout_files']

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
    startup_logger.debug("Syncing Schedules")
    for sch in Schedule.objects.all():
        try:
            sch.update_computed_fields()
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

    # at process startup, detect the need to migrate old event records from int
    # to bigint; at *some point* in the future, once certain versions of AWX
    # and Tower fall out of use/support, we can probably just _assume_ that
    # everybody has moved to bigint, and remove this code entirely
    enforce_bigint_pk_migration()

    # Update Tower's rsyslog.conf file based on loggins settings in the db
    reconfigure_rsyslog()


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


@task(queue=get_local_queuename)
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
                logger.debug("Policy List, adding Instances {} to Group {}".format(group_actual.instances, ig.name))

            if ig.controller_id is None:
                actual_groups.append(group_actual)
            else:
                # For isolated groups, _only_ apply the policy_instance_list
                # do not add to in-memory list, so minimum rules not applied
                logger.debug('Committing instances to isolated group {}'.format(ig.name))
                ig.instances.set(group_actual.instances)

        # Process Instance minimum policies next, since it represents a concrete lower bound to the
        # number of instances to make available to instance groups
        actual_instances = [Node(obj=i, groups=[]) for i in considered_instances if i.managed_by_policy]
        logger.debug("Total non-isolated instances:{} available for policy: {}".format(
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
                logger.debug("Policy minimum, adding Instances {} to Group {}".format(policy_min_added, g.obj.name))

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
                logger.debug("Policy percentage, adding Instances {} to Group {}".format(policy_per_added, g.obj.name))

        # Determine if any changes need to be made
        needs_change = False
        for g in actual_groups:
            if set(g.instances) != set(g.prior_instances):
                needs_change = True
                break
        if not needs_change:
            logger.debug('Cluster policy no-op finished in {} seconds'.format(time.time() - started_compute))
            return

        # On a differential basis, apply instances to non-isolated groups
        with transaction.atomic():
            for g in actual_groups:
                if g.obj.is_containerized:
                    logger.debug('Skipping containerized group {} for policy calculation'.format(g.obj.name))
                    continue
                instances_to_add = set(g.instances) - set(g.prior_instances)
                instances_to_remove = set(g.prior_instances) - set(g.instances)
                if instances_to_add:
                    logger.debug('Adding instances {} to group {}'.format(list(instances_to_add), g.obj.name))
                    g.obj.instances.add(*instances_to_add)
                if instances_to_remove:
                    logger.debug('Removing instances {} from group {}'.format(list(instances_to_remove), g.obj.name))
                    g.obj.instances.remove(*instances_to_remove)
        logger.debug('Cluster policy computation finished in {} seconds'.format(time.time() - started_compute))


@task(queue='tower_broadcast_all')
def handle_setting_changes(setting_keys):
    orig_len = len(setting_keys)
    for i in range(orig_len):
        for dependent_key in settings_registry.get_dependent_settings(setting_keys[i]):
            setting_keys.append(dependent_key)
    cache_keys = set(setting_keys)
    logger.debug('cache delete_many(%r)', cache_keys)
    cache.delete_many(cache_keys)

    if any([
        setting.startswith('LOG_AGGREGATOR')
        for setting in setting_keys
    ]):
        reconfigure_rsyslog()


@task(queue='tower_broadcast_all')
def delete_project_files(project_path):
    # TODO: possibly implement some retry logic
    lock_file = project_path + '.lock'
    if os.path.exists(project_path):
        try:
            shutil.rmtree(project_path)
            logger.debug('Success removing project files {}'.format(project_path))
        except Exception:
            logger.exception('Could not remove project directory {}'.format(project_path))
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            logger.debug('Success removing {}'.format(lock_file))
        except Exception:
            logger.exception('Could not remove lock file {}'.format(lock_file))


@task(queue='tower_broadcast_all')
def profile_sql(threshold=1, minutes=1):
    if threshold <= 0:
        cache.delete('awx-profile-sql-threshold')
        logger.error('SQL PROFILING DISABLED')
    else:
        cache.set(
            'awx-profile-sql-threshold',
            threshold,
            timeout=minutes * 60
        )
        logger.error('SQL QUERIES >={}s ENABLED FOR {} MINUTE(S)'.format(threshold, minutes))


@task(queue=get_local_queuename)
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
            logger.exception("Send Notification Failed {}".format(e))
            notification.status = "failed"
            notification.error = smart_str(e)
            update_fields.append('error')
        finally:
            try:
                notification.save(update_fields=update_fields)
            except Exception:
                logger.exception('Error saving notification {} result.'.format(notification.id))


@task(queue=get_local_queuename)
def gather_analytics():
    def _gather_and_ship(subset, since, until):
        tgzfiles = []
        try:
            tgzfiles = analytics.gather(subset=subset, since=since, until=until)
            # empty analytics without raising an exception is not an error
            if not tgzfiles:
                return True
            logger.info('Gathered analytics from {} to {}: {}'.format(since, until, tgzfiles))
            for tgz in tgzfiles:
                analytics.ship(tgz)
        except Exception:
            logger.exception('Error gathering and sending analytics for {} to {}.'.format(since,until))
            return False
        finally:
            if tgzfiles:
                for tgz in tgzfiles:
                    if os.path.exists(tgz):
                        os.remove(tgz)
        return True

    from awx.conf.models import Setting
    from rest_framework.fields import DateTimeField
    if not settings.INSIGHTS_TRACKING_STATE:
        return
    if not (settings.AUTOMATION_ANALYTICS_URL and settings.REDHAT_USERNAME and settings.REDHAT_PASSWORD):
        logger.debug('Not gathering analytics, configuration is invalid')
        return
    last_gather = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_GATHER').first()
    if last_gather:
        last_time = DateTimeField().to_internal_value(last_gather.value)
    else:
        last_time = None
    gather_time = now()
    if not last_time or ((gather_time - last_time).total_seconds() > settings.AUTOMATION_ANALYTICS_GATHER_INTERVAL):
        with advisory_lock('gather_analytics_lock', wait=False) as acquired:
            if acquired is False:
                logger.debug('Not gathering analytics, another task holds lock')
                return
            subset = list(all_collectors().keys())
            incremental_collectors = []
            for collector in expensive_collectors():
                if collector in subset:
                    subset.remove(collector)
                    incremental_collectors.append(collector)

            # Cap gathering at 4 weeks of data if there has been no data gathering
            since = last_time or (gather_time - timedelta(weeks=4))

            if incremental_collectors:
                start = since
                until = None
                while start < gather_time:
                    until = start + timedelta(hours = 4)
                    if (until > gather_time):
                        until = gather_time
                    if not _gather_and_ship(incremental_collectors, since=start, until=until):
                        break
                    start = until
                    settings.AUTOMATION_ANALYTICS_LAST_GATHER = until
            if subset:
                _gather_and_ship(subset, since=since, until=gather_time)


@task(queue=get_local_queuename)
def purge_old_stdout_files():
    nowtime = time.time()
    for f in os.listdir(settings.JOBOUTPUT_ROOT):
        if os.path.getctime(os.path.join(settings.JOBOUTPUT_ROOT,f)) < nowtime - settings.LOCAL_STDOUT_EXPIRE_TIME:
            os.unlink(os.path.join(settings.JOBOUTPUT_ROOT,f))
            logger.debug("Removing {}".format(os.path.join(settings.JOBOUTPUT_ROOT,f)))


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
        this_inst.refresh_capacity()
        if startup_event:
            logger.warning('Rejoining the cluster as instance {}.'.format(this_inst.hostname))
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
def awx_k8s_reaper():
    from awx.main.scheduler.kubernetes import PodManager # prevent circular import
    for group in InstanceGroup.objects.filter(credential__isnull=False).iterator():
        if group.is_containerized:
            logger.debug("Checking for orphaned k8s pods for {}.".format(group))
            for job in UnifiedJob.objects.filter(
                pk__in=list(PodManager.list_active_jobs(group))
            ).exclude(status__in=ACTIVE_STATES):
                logger.debug('{} is no longer active, reaping orphaned k8s pod'.format(job.log_format))
                try:
                    PodManager(job).delete()
                except Exception:
                    logger.exception("Failed to delete orphaned pod {} from {}".format(
                        job.log_format, group
                    ))



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
        isolated_manager.IsolatedManager(CallbackQueueDispatcher.dispatch).health_check(isolated_instance_qs)


@task(queue=get_local_queuename)
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
            schedule.update_computed_fields()
        schedules = Schedule.objects.enabled().between(last_run, run_now)

        invalid_license = False
        try:
            access_registry[Job](None).check_license(quiet=True)
        except PermissionDenied as e:
            invalid_license = e

        for schedule in schedules:
            template = schedule.unified_job_template
            schedule.update_computed_fields() # To update next_run timestamp.
            if template.cache_timeout_blocked:
                logger.warn("Cache timeout is in the future, bypassing schedule for template %s" % str(template.id))
                continue
            try:
                job_kwargs = schedule.get_job_kwargs()
                new_unified_job = schedule.unified_job_template.create_unified_job(**job_kwargs)
                logger.debug('Spawned {} from schedule {}-{}.'.format(
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
                new_unified_job.job_explanation = gettext_noop("Scheduled job could not start because it \
                    was not in the right state or required manual credentials")
                new_unified_job.save(update_fields=['status', 'job_explanation'])
                new_unified_job.websocket_emit_status("failed")
            emit_channel_notification('schedules-changed', dict(id=schedule.id, group_name="schedules"))
        state.save()


@task(queue=get_local_queuename)
def handle_work_success(task_actual):
    try:
        instance = UnifiedJob.get_instance_by_type(task_actual['type'], task_actual['id'])
    except ObjectDoesNotExist:
        logger.warning('Missing {} `{}` in success callback.'.format(task_actual['type'], task_actual['id']))
        return
    if not instance:
        return

    schedule_task_manager()


@task(queue=get_local_queuename)
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

            if instance.celery_task_id != task_id and not instance.cancel_flag and not instance.status == 'successful':
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


@task(queue=get_local_queuename)
def handle_success_and_failure_notifications(job_id):
    uj = UnifiedJob.objects.get(pk=job_id)
    retries = 0
    while retries < 5:
        if uj.finished:
            uj.send_notification_templates('succeeded' if uj.status == 'successful' else 'failed')
            return
        else:
            # wait a few seconds to avoid a race where the
            # events are persisted _before_ the UJ.status
            # changes from running -> successful
            retries += 1
            time.sleep(1)
            uj = UnifiedJob.objects.get(pk=job_id)

    logger.warn(f"Failed to even try to send notifications for job '{uj}' due to job not being in finished state.")


@task(queue=get_local_queuename)
def update_inventory_computed_fields(inventory_id):
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
        i.update_computed_fields()
    except DatabaseError as e:
        if 'did not affect any rows' in str(e):
            logger.debug('Exiting duplicate update_inventory_computed_fields task.')
            return
        raise


def update_smart_memberships_for_inventory(smart_inventory):
    current = set(SmartInventoryMembership.objects.filter(inventory=smart_inventory).values_list('host_id', flat=True))
    new = set(smart_inventory.hosts.values_list('id', flat=True))
    additions = new - current
    removals = current - new
    if additions or removals:
        with transaction.atomic():
            if removals:
                SmartInventoryMembership.objects.filter(inventory=smart_inventory, host_id__in=removals).delete()
            if additions:
                add_for_inventory = [
                    SmartInventoryMembership(inventory_id=smart_inventory.id, host_id=host_id)
                    for host_id in additions
                ]
                SmartInventoryMembership.objects.bulk_create(add_for_inventory, ignore_conflicts=True)
        logger.debug('Smart host membership cached for {}, {} additions, {} removals, {} total count.'.format(
            smart_inventory.pk, len(additions), len(removals), len(new)
        ))
        return True  # changed
    return False


@task(queue=get_local_queuename)
def update_host_smart_inventory_memberships():
    smart_inventories = Inventory.objects.filter(kind='smart', host_filter__isnull=False, pending_deletion=False)
    changed_inventories = set([])
    for smart_inventory in smart_inventories:
        try:
            changed = update_smart_memberships_for_inventory(smart_inventory)
            if changed:
                changed_inventories.add(smart_inventory)
        except IntegrityError:
            logger.exception('Failed to update smart inventory memberships for {}'.format(smart_inventory.pk))
    # Update computed fields for changed inventories outside atomic action
    for smart_inventory in changed_inventories:
        smart_inventory.update_computed_fields()


@task(queue=get_local_queuename)
def migrate_legacy_event_data(tblname):
    if 'event' not in tblname:
        return
    with advisory_lock(f'bigint_migration_{tblname}', wait=False) as acquired:
        if acquired is False:
            return
        chunk = settings.JOB_EVENT_MIGRATION_CHUNK_SIZE

        def _remaining():
            try:
                cursor.execute(f'SELECT MAX(id) FROM _old_{tblname};')
                return cursor.fetchone()[0]
            except ProgrammingError:
                # the table is gone (migration is unnecessary)
                return None

        with connection.cursor() as cursor:
            total_rows = _remaining()
            while total_rows:
                with transaction.atomic():
                    cursor.execute(
                        f'INSERT INTO {tblname} SELECT * FROM _old_{tblname} ORDER BY id DESC LIMIT {chunk} RETURNING id;'
                    )
                    last_insert_pk = cursor.fetchone()
                    if last_insert_pk is None:
                        # this means that the SELECT from the old table was
                        # empty, and there was nothing to insert (so we're done)
                        break
                    last_insert_pk = last_insert_pk[0]
                    cursor.execute(
                        f'DELETE FROM _old_{tblname} WHERE id IN (SELECT id FROM _old_{tblname} ORDER BY id DESC LIMIT {chunk});'
                    )
                logger.warn(
                    f'migrated int -> bigint rows to {tblname} from _old_{tblname}; # ({last_insert_pk} rows remaining)'
                )

            if _remaining() is None:
                cursor.execute(f'DROP TABLE IF EXISTS _old_{tblname}')
                logger.warn(f'{tblname} primary key migration to bigint has finished')


@task(queue=get_local_queuename)
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
    proot_show_paths = []

    def __init__(self):
        self.cleanup_paths = []
        self.parent_workflow_job_id = None
        self.host_map = {}

    def update_model(self, pk, _attempt=0, **updates):
        """Reload the model instance from the database and update the
        given fields.
        """
        try:
            with transaction.atomic():
                # Retrieve the model instance.
                instance = self.model.objects.get(pk=pk)

                # Update the appropriate fields and save the model
                # instance, then return the new instance.
                if updates:
                    update_fields = ['modified']
                    for field, value in updates.items():
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
        runner_project_folder = os.path.join(path, 'project')
        if not os.path.exists(runner_project_folder):
            # Ansible Runner requires that this directory exists.
            # Specifically, when using process isolation
            os.mkdir(runner_project_folder)
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
                    handle, path = tempfile.mkstemp(dir=private_data_dir)
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
        '''
        Build a dictionary of passwords for responding to prompts.
        '''
        return {
            'yes': 'yes',
            'no': 'no',
            '': '',
        }

    def build_extra_vars_file(self, instance, private_data_dir):
        '''
        Build ansible yaml file filled with extra vars to be passed via -e@file.yml
        '''

    def build_params_process_isolation(self, instance, private_data_dir, cwd):
        '''
        Build ansible runner .run() parameters for process isolation.
        '''
        process_isolation_params = dict()
        if self.should_use_proot(instance):
            local_paths = [private_data_dir]
            if cwd != private_data_dir and Path(private_data_dir) not in Path(cwd).parents:
                local_paths.append(cwd)
            show_paths = self.proot_show_paths + local_paths + \
                settings.AWX_PROOT_SHOW_PATHS

            pi_path = settings.AWX_PROOT_BASE_PATH
            if not self.instance.is_isolated() and not self.instance.is_containerized:
                pi_path = tempfile.mkdtemp(
                    prefix='ansible_runner_pi_',
                    dir=settings.AWX_PROOT_BASE_PATH
                )
                os.chmod(pi_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                self.cleanup_paths.append(pi_path)

            process_isolation_params = {
                'process_isolation': True,
                'process_isolation_path': pi_path,
                'process_isolation_show_paths': show_paths,
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

    def build_params_resource_profiling(self, instance, private_data_dir):
        resource_profiling_params = {}
        if self.should_use_resource_profiling(instance):
            cpu_poll_interval = settings.AWX_RESOURCE_PROFILING_CPU_POLL_INTERVAL
            mem_poll_interval = settings.AWX_RESOURCE_PROFILING_MEMORY_POLL_INTERVAL
            pid_poll_interval = settings.AWX_RESOURCE_PROFILING_PID_POLL_INTERVAL

            results_dir = os.path.join(private_data_dir, 'artifacts/playbook_profiling')
            if not os.path.isdir(results_dir):
                os.makedirs(results_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

            logger.debug('Collected the following resource profiling intervals: cpu: {} mem: {} pid: {}'
                         .format(cpu_poll_interval, mem_poll_interval, pid_poll_interval))

            resource_profiling_params.update({'resource_profiling': True,
                                              'resource_profiling_base_cgroup': 'ansible-runner',
                                              'resource_profiling_cpu_poll_interval': cpu_poll_interval,
                                              'resource_profiling_memory_poll_interval': mem_poll_interval,
                                              'resource_profiling_pid_poll_interval': pid_poll_interval,
                                              'resource_profiling_results_dir': results_dir})

        return resource_profiling_params

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

    def should_use_resource_profiling(self, job):
        '''
        Return whether this task should use resource profiling
        '''
        return False

    def should_use_proot(self, instance):
        '''
        Return whether this task should use proot.
        '''
        return False

    def build_inventory(self, instance, private_data_dir):
        script_params = dict(hostvars=True, towervars=True)
        if hasattr(instance, 'job_slice_number'):
            script_params['slice_number'] = instance.job_slice_number
            script_params['slice_count'] = instance.job_slice_count
        script_data = instance.inventory.get_script_data(**script_params)
        # maintain a list of host_name --> host_id
        # so we can associate emitted events to Host objects
        self.host_map = {
            hostname: hv.pop('remote_tower_id', '')
            for hostname, hv in script_data.get('_meta', {}).get('hostvars', {}).items()
        }
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

    def pre_run_hook(self, instance, private_data_dir):
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
        job_profiling_dir = os.path.join(private_data_dir, 'artifacts/playbook_profiling')
        awx_profiling_dir = '/var/log/tower/playbook_profiling/'
        if not os.path.exists(awx_profiling_dir):
            os.mkdir(awx_profiling_dir)
        if os.path.isdir(job_profiling_dir):
            shutil.copytree(job_profiling_dir, os.path.join(awx_profiling_dir, str(instance.pk)))

        if instance.is_containerized:
            from awx.main.scheduler.kubernetes import PodManager # prevent circular import
            pm = PodManager(instance)
            logger.debug(f"Deleting pod {pm.pod_name}")
            pm.delete()


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
        if self.parent_workflow_job_id:
            event_data['workflow_job_id'] = self.parent_workflow_job_id
        if self.host_map:
            host = event_data.get('event_data', {}).get('host', '').strip()
            if host:
                event_data['host_name'] = host
                if host in self.host_map:
                    event_data['host_id'] = self.host_map[host]
            else:
                event_data['host_name'] = ''
                event_data['host_id'] = ''
            if event_data.get('event') == 'playbook_on_stats':
                event_data['host_map'] = self.host_map

        if isinstance(self, RunProjectUpdate):
            # it's common for Ansible's SCM modules to print
            # error messages on failure that contain the plaintext
            # basic auth credentials (username + password)
            # it's also common for the nested event data itself (['res']['...'])
            # to contain unredacted text on failure
            # this is a _little_ expensive to filter
            # with regex, but project updates don't have many events,
            # so it *should* have a negligible performance impact
            task = event_data.get('event_data', {}).get('task_action')
            try:
                if task in ('git', 'hg', 'svn'):
                    event_data_json = json.dumps(event_data)
                    event_data_json = UriCleaner.remove_sensitive(event_data_json)
                    event_data = json.loads(event_data_json)
            except json.JSONDecodeError:
                pass

        event_data.setdefault(self.event_data_key, self.instance.id)
        self.dispatcher.dispatch(event_data)
        self.event_ct += 1

        '''
        Handle artifacts
        '''
        if event_data.get('event_data', {}).get('artifact_data', {}):
            self.instance.artifacts = event_data['event_data']['artifact_data']
            self.instance.save(update_fields=['artifacts'])

        return False

    def cancel_callback(self):
        '''
        Ansible runner callback to tell the job when/if it is canceled
        '''
        unified_job_id = self.instance.pk
        self.instance = self.update_model(unified_job_id)
        if not self.instance:
            logger.error('unified job {} was deleted while running, canceling'.format(unified_job_id))
            return True
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
        self.instance = self.model.objects.get(pk=pk)
        containerized = self.instance.is_containerized
        pod_manager = None
        if containerized:
            # Here we are trying to launch a pod before transitioning the job into a running
            # state. For some scenarios (like waiting for resources to become available) we do this
            # rather than marking the job as error or failed. This is not always desirable. Cases
            # such as invalid authentication should surface as an error.
            pod_manager = self.deploy_container_group_pod(self.instance)
            if not pod_manager:
                return

        # self.instance because of the update_model pattern and when it's used in callback handlers
        self.instance = self.update_model(pk, status='running',
                                          start_args='')  # blank field to remove encrypted passwords

        self.instance.websocket_emit_status("running")
        status, rc = 'error', None
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

        # store a reference to the parent workflow job (if any) so we can include
        # it in event data JSON
        if self.instance.spawned_by_workflow:
            self.parent_workflow_job_id = self.instance.get_workflow_job().id

        try:
            isolated = self.instance.is_isolated()
            self.instance.send_notification_templates("running")
            private_data_dir = self.build_private_data_dir(self.instance)
            self.pre_run_hook(self.instance, private_data_dir)
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
            cwd = self.build_cwd(self.instance, private_data_dir)
            resource_profiling_params = self.build_params_resource_profiling(self.instance,
                                                                             private_data_dir)
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
                    'suppress_ansible_output': True,
                    **process_isolation_params,
                    **resource_profiling_params,
                },
            }

            if containerized:
                # We don't want HOME passed through to container groups.
                params['envvars'].pop('HOME')

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

            self.dispatcher = CallbackQueueDispatcher()
            if self.instance.is_isolated() or containerized:
                module_args = None
                if 'module_args' in params:
                    # if it's adhoc, copy the module args
                    module_args = ansible_runner.utils.args2cmdline(
                        params.get('module_args'),
                    )
                shutil.move(
                    params.pop('inventory'),
                    os.path.join(private_data_dir, 'inventory')
                )

                ansible_runner.utils.dump_artifacts(params)
                isolated_manager_instance = isolated_manager.IsolatedManager(
                    self.event_handler,
                    canceled_callback=lambda: self.update_model(self.instance.pk).cancel_flag,
                    check_callback=self.check_handler,
                    pod_manager=pod_manager
                )
                status, rc = isolated_manager_instance.run(self.instance,
                                                           private_data_dir,
                                                           params.get('playbook'),
                                                           params.get('module'),
                                                           module_args,
                                                           ident=str(self.instance.pk))
                self.finished_callback(None)
            else:
                res = ansible_runner.interface.run(**params)
                status = res.status
                rc = res.rc

            if status == 'timeout':
                self.instance.job_explanation = "Job terminated due to timeout"
                status = 'failed'
                extra_update_fields['job_explanation'] = self.instance.job_explanation
                # ensure failure notification sends even if playbook_on_stats event is not triggered
                handle_success_and_failure_notifications.apply_async([self.instance.job.id])

        except InvalidVirtualenvError as e:
            extra_update_fields['job_explanation'] = e.message
            logger.error('{} {}'.format(self.instance.log_format, e.message))
        except Exception:
            # this could catch programming or file system errors
            extra_update_fields['result_traceback'] = traceback.format_exc()
            logger.exception('%s Exception occurred while running task', self.instance.log_format)
        finally:
            logger.debug('%s finished running, producing %s events.', self.instance.log_format, self.event_ct)

        try:
            self.post_run_hook(self.instance, status)
        except Exception:
            logger.exception('{} Post run hook errored.'.format(self.instance.log_format))

        self.instance = self.update_model(pk)
        self.instance = self.update_model(pk, status=status,
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


    def deploy_container_group_pod(self, task):
        from awx.main.scheduler.kubernetes import PodManager # Avoid circular import
        pod_manager = PodManager(self.instance)
        try:
            log_name = task.log_format
            logger.debug(f"Launching pod for {log_name}.")
            pod_manager.deploy()
        except (ApiException, Exception) as exc:
            if isinstance(exc, ApiException) and exc.status == 403:
                try:
                    if 'exceeded quota' in json.loads(exc.body)['message']:
                        # If the k8s cluster does not have capacity, we move the
                        # job back into pending and wait until the next run of
                        # the task manager. This does not exactly play well with
                        # our current instance group precendence logic, since it
                        # will just sit here forever if kubernetes returns this
                        # error.
                        logger.warn(exc.body)
                        logger.warn(f"Could not launch pod for {log_name}. Exceeded quota.")
                        self.update_model(task.pk, status='pending')
                        return
                except Exception:
                    logger.exception(f"Unable to handle response from Kubernetes API for {log_name}.")

            logger.exception(f"Error when launching pod for {log_name}")
            self.update_model(task.pk, status='error', result_traceback=traceback.format_exc())
            return

        self.update_model(task.pk, execution_node=pod_manager.pod_name)
        return pod_manager





@task(queue=get_local_queuename)
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

    def build_env(self, job, private_data_dir, isolated=False, private_data_files=None):
        '''
        Build environment dictionary for ansible-playbook.
        '''
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
        if job.project:
            env['PROJECT_REVISION'] = job.project.scm_revision
        env['ANSIBLE_RETRY_FILES_ENABLED'] = "False"
        env['MAX_EVENT_RES'] = str(settings.MAX_EVENT_RES_DATA)
        if not isolated:
            if hasattr(settings, 'AWX_ANSIBLE_CALLBACK_PLUGINS') and settings.AWX_ANSIBLE_CALLBACK_PLUGINS:
                env['ANSIBLE_CALLBACK_PLUGINS'] = ':'.join(settings.AWX_ANSIBLE_CALLBACK_PLUGINS)
            env['AWX_HOST'] = settings.TOWER_URL_BASE

        # Create a directory for ControlPath sockets that is unique to each
        # job and visible inside the proot environment (when enabled).
        cp_dir = os.path.join(private_data_dir, 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0o700)
        env['ANSIBLE_SSH_CONTROL_PATH_DIR'] = cp_dir

        # Set environment variables for cloud credentials.
        cred_files = private_data_files.get('credentials', {})
        for cloud_cred in job.cloud_credentials:
            if cloud_cred and cloud_cred.credential_type.namespace == 'openstack':
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

        path_vars = (
            ('ANSIBLE_COLLECTIONS_PATHS', 'collections_paths', 'requirements_collections', '~/.ansible/collections:/usr/share/ansible/collections'),
            ('ANSIBLE_ROLES_PATH', 'roles_path', 'requirements_roles', '~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles'))

        config_values = read_ansible_config(job.project.get_project_path(), list(map(lambda x: x[1], path_vars)))

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
            paths = [os.path.join(private_data_dir, folder)] + paths
            env[env_key] = os.pathsep.join(paths)

        return env

    def build_args(self, job, private_data_dir, passwords):
        '''
        Build command line argument list for running ansible-playbook,
        optionally using ssh-agent for public/private key authentication.
        '''
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

    def build_cwd(self, job, private_data_dir):
        return os.path.join(private_data_dir, 'project')

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

    def should_use_resource_profiling(self, job):
        '''
        Return whether this task should use resource profiling
        '''
        return settings.AWX_RESOURCE_PROFILING_ENABLED

    def should_use_proot(self, job):
        '''
        Return whether this task should use proot.
        '''
        if job.is_containerized:
            return False
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def pre_run_hook(self, job, private_data_dir):
        if job.inventory is None:
            error = _('Job could not start because it does not have a valid inventory.')
            self.update_model(job.pk, status='failed', job_explanation=error)
            raise RuntimeError(error)
        elif job.project is None:
            error = _('Job could not start because it does not have a valid project.')
            self.update_model(job.pk, status='failed', job_explanation=error)
            raise RuntimeError(error)
        elif job.project.status in ('error', 'failed'):
            msg = _(
                'The project revision for this job template is unknown due to a failed update.'
            )
            job = self.update_model(job.pk, status='failed', job_explanation=msg)
            raise RuntimeError(msg)

        project_path = job.project.get_project_path(check_if_exists=False)
        job_revision = job.project.scm_revision
        sync_needs = []
        source_update_tag = 'update_{}'.format(job.project.scm_type)
        branch_override = bool(job.scm_branch and job.scm_branch != job.project.scm_branch)
        if not job.project.scm_type:
            pass # manual projects are not synced, user has responsibility for that
        elif not os.path.exists(project_path):
            logger.debug('Performing fresh clone of {} on this instance.'.format(job.project))
            sync_needs.append(source_update_tag)
        elif job.project.scm_type == 'git' and job.project.scm_revision and (not branch_override):
            git_repo = git.Repo(project_path)
            try:
                if job_revision == git_repo.head.commit.hexsha:
                    logger.debug('Skipping project sync for {} because commit is locally available'.format(job.log_format))
                else:
                    sync_needs.append(source_update_tag)
            except (ValueError, BadGitName):
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
            pu_en = job.execution_node
            if job.is_isolated() is True:
                pu_ig = pu_ig.controller
                pu_en = settings.CLUSTER_HOST_ID

            sync_metafields = dict(
                launch_type="sync",
                job_type='run',
                job_tags=','.join(sync_needs),
                status='running',
                instance_group = pu_ig,
                execution_node=pu_en,
                celery_task_id=job.celery_task_id
            )
            if branch_override:
                sync_metafields['scm_branch'] = job.scm_branch
            if 'update_' not in sync_metafields['job_tags']:
                sync_metafields['scm_revision'] = job_revision
            local_project_sync = job.project.create_project_update(_eager_fields=sync_metafields)
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
                    job = self.update_model(job.pk, status='failed',
                                            job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                                             ('project_update', local_project_sync.name, local_project_sync.id)))
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
        if isolated_manager_instance and not job.is_containerized:
            isolated_manager_instance.cleanup()

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
    event_data_key = 'project_update_id'

    @property
    def proot_show_paths(self):
        return [settings.PROJECTS_ROOT]

    def __init__(self, *args, job_private_data_dir=None, **kwargs):
        super(RunProjectUpdate, self).__init__(*args, **kwargs)
        self.playbook_new_revision = None
        self.original_branch = None
        self.job_private_data_dir = job_private_data_dir

    def event_handler(self, event_data):
        super(RunProjectUpdate, self).event_handler(event_data)
        returned_data = event_data.get('event_data', {})
        if returned_data.get('task_action', '') == 'set_fact':
            returned_facts = returned_data.get('res', {}).get('ansible_facts', {})
            if 'scm_version' in returned_facts:
                self.playbook_new_revision = returned_facts['scm_version']

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
        if settings.GALAXY_IGNORE_CERTS:
            env['ANSIBLE_GALAXY_IGNORE'] = True

        # build out env vars for Galaxy credentials (in order)
        galaxy_server_list = []
        if project_update.project.organization:
            for i, cred in enumerate(
                project_update.project.organization.galaxy_credentials.all()
            ):
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
        '''
        Helper method to build SCM url and extra vars with parameters needed
        for authentication.
        '''
        extra_vars = {}
        if project_update.credential:
            scm_username = project_update.credential.get_input('username', default='')
            scm_password = project_update.credential.get_input('password', default='')
        else:
            scm_username = ''
            scm_password = ''
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
            elif scm_type in ('insights', 'archive'):
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
            scm_branch = {'hg': 'tip'}.get(project_update.scm_type, 'HEAD')

        galaxy_creds_are_defined = (
            project_update.project.organization and
            project_update.project.organization.galaxy_credentials.exists()
        )
        if not galaxy_creds_are_defined and (
            settings.AWX_ROLES_ENABLED or settings.AWX_COLLECTIONS_ENABLED
        ):
            logger.debug(
                'Galaxy role/collection syncing is enabled, but no '
                f'credentials are configured for {project_update.project.organization}.'
            )

        extra_vars.update({
            'projects_root': settings.PROJECTS_ROOT.rstrip('/'),
            'local_path': os.path.basename(project_update.project.local_path),
            'project_path': project_update.get_project_path(check_if_exists=False),  # deprecated
            'insights_url': settings.INSIGHTS_URL_BASE,
            'awx_license_type': get_license().get('license_type', 'UNLICENSED'),
            'awx_version': get_awx_version(),
            'scm_url': scm_url,
            'scm_branch': scm_branch,
            'scm_clean': project_update.scm_clean,
            'roles_enabled': galaxy_creds_are_defined and settings.AWX_ROLES_ENABLED,
            'collections_enabled': galaxy_creds_are_defined and settings.AWX_COLLECTIONS_ENABLED,
        })
        # apply custom refspec from user for PR refs and the like
        if project_update.scm_refspec:
            extra_vars['scm_refspec'] = project_update.scm_refspec
        elif project_update.project.allow_override:
            # If branch is override-able, do extra fetch for all branches
            extra_vars['scm_refspec'] = 'refs/heads/*:refs/remotes/origin/*'
        self._write_extra_vars_file(private_data_dir, extra_vars)

    def build_cwd(self, project_update, private_data_dir):
        return os.path.join(private_data_dir, 'project')

    def build_playbook_path_relative_to_cwd(self, project_update, private_data_dir):
        return os.path.join('project_update.yml')

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
                    logger.debug('Skipping SCM inventory update for `{}` because '
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
            logger.info(
                '{} spent {} waiting to acquire lock for local source tree '
                'for path {}.'.format(instance.log_format, waiting_time, lock_path))

    def pre_run_hook(self, instance, private_data_dir):
        # re-create root project folder if a natural disaster has destroyed it
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        self.acquire_lock(instance)
        self.original_branch = None
        if instance.scm_type == 'git' and instance.branch_override:
            project_path = instance.project.get_project_path(check_if_exists=False)
            if os.path.exists(project_path):
                git_repo = git.Repo(project_path)
                if git_repo.head.is_detached:
                    self.original_branch = git_repo.head.commit
                else:
                    self.original_branch = git_repo.active_branch

        stage_path = os.path.join(instance.get_cache_path(), 'stage')
        if os.path.exists(stage_path):
            logger.warning('{0} unexpectedly existed before update'.format(stage_path))
            shutil.rmtree(stage_path)
        os.makedirs(stage_path)  # presence of empty cache indicates lack of roles or collections

        # the project update playbook is not in a git repo, but uses a vendoring directory
        # to be consistent with the ansible-runner model,
        # that is moved into the runner projecct folder here
        awx_playbooks = self.get_path_to('..', 'playbooks')
        copy_tree(awx_playbooks, os.path.join(private_data_dir, 'project'))

    @staticmethod
    def clear_project_cache(cache_dir, keep_value):
        if os.path.isdir(cache_dir):
            for entry in os.listdir(cache_dir):
                old_path = os.path.join(cache_dir, entry)
                if entry not in (keep_value, 'stage'):
                    # invalidate, then delete
                    new_path = os.path.join(cache_dir,'.~~delete~~' + entry)
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
                source_as_uri, destination_folder, branch=source_branch,
                depth=1, single_branch=True,  # shallow, do not copy full history
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
        # To avoid hangs, very important to release lock even if errors happen here
        try:
            if self.playbook_new_revision:
                instance.scm_revision = self.playbook_new_revision
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
        if instance.job_type == 'check' and status not in ('failed', 'canceled',):
            if self.playbook_new_revision:
                p.scm_revision = self.playbook_new_revision
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

    def should_use_proot(self, project_update):
        '''
        Return whether this task should use proot.
        '''
        return getattr(settings, 'AWX_PROOT_ENABLED', False)


@task(queue=get_local_queuename)
class RunInventoryUpdate(BaseTask):

    model = InventoryUpdate
    event_model = InventoryUpdateEvent
    event_data_key = 'inventory_update_id'

    @property
    def proot_show_paths(self):
        return [settings.AWX_ANSIBLE_COLLECTIONS_PATHS]

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
            injector = InventorySource.injectors[inventory_update.source]()

        if injector is not None:
            env = injector.build_env(inventory_update, env, private_data_dir, private_data_files)
            # All CLOUD_PROVIDERS sources implement as inventory plugin from collection
            env['ANSIBLE_INVENTORY_ENABLED'] = 'auto'

        if inventory_update.source in ['scm', 'custom']:
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
            paths = [os.path.join(private_data_dir, folder)] + paths
            env[env_key] = os.pathsep.join(paths)

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
        if inventory_update.enabled_var:
            args.extend(['--enabled-var', shlex.quote(inventory_update.enabled_var)])
            args.extend(['--enabled-value', shlex.quote(inventory_update.enabled_value)])
        else:
            if getattr(settings, '%s_ENABLED_VAR' % src.upper(), False):
                args.extend(['--enabled-var',
                            getattr(settings, '%s_ENABLED_VAR' % src.upper())])
            if getattr(settings, '%s_ENABLED_VALUE' % src.upper(), False):
                args.extend(['--enabled-value',
                            getattr(settings, '%s_ENABLED_VALUE' % src.upper())])
        if inventory_update.host_filter:
            args.extend(['--host-filter', shlex.quote(inventory_update.host_filter)])
        if getattr(settings, '%s_EXCLUDE_EMPTY_GROUPS' % src.upper()):
            args.append('--exclude-empty-groups')
        if getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper(), False):
            args.extend(['--instance-id-var',
                        "'{}'".format(getattr(settings, '%s_INSTANCE_ID_VAR' % src.upper())),])
        # Add arguments for the source inventory script
        args.append('--source')
        args.append(self.pseudo_build_inventory(inventory_update, private_data_dir))
        if src == 'custom':
            args.append("--custom")
        args.append('-v%d' % inventory_update.verbosity)
        if settings.DEBUG:
            args.append('--traceback')
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
            inventory_path = os.path.join(private_data_dir, injector.filename)
            with open(inventory_path, 'w') as f:
                f.write(content)
            os.chmod(inventory_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        elif src == 'scm':
            inventory_path = os.path.join(private_data_dir, 'project', inventory_update.source_path)
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
            return os.path.join(private_data_dir, 'project')
        return private_data_dir

    def build_playbook_path_relative_to_cwd(self, inventory_update, private_data_dir):
        return None

    def build_credentials_list(self, inventory_update):
        # All credentials not used by inventory source injector
        return inventory_update.get_extra_credentials()

    def pre_run_hook(self, inventory_update, private_data_dir):
        source_project = None
        if inventory_update.inventory_source:
            source_project = inventory_update.inventory_source.source_project
        if (inventory_update.source=='scm' and inventory_update.launch_type!='scm' and
                source_project and source_project.scm_type):  # never ever update manual projects

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
                    execution_node=inventory_update.execution_node,
                    instance_group = inventory_update.instance_group,
                    celery_task_id=inventory_update.celery_task_id))
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
                    inventory_update.pk, status='failed',
                    job_explanation=('Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' %
                                     ('project_update', local_project_sync.name, local_project_sync.id)))
                raise
        elif inventory_update.source == 'scm' and inventory_update.launch_type == 'scm' and source_project:
            # This follows update, not sync, so make copy here
            RunProjectUpdate.make_local_copy(source_project, private_data_dir)


@task(queue=get_local_queuename)
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
        env = super(RunAdHocCommand, self).build_env(ad_hoc_command, private_data_dir,
                                                     isolated=isolated,
                                                     private_data_files=private_data_files)
        self.add_ansible_venv(settings.ANSIBLE_VENV_PATH, env)
        # Set environment variables needed for inventory and ad hoc event
        # callbacks to work.
        env['AD_HOC_COMMAND_ID'] = str(ad_hoc_command.pk)
        env['INVENTORY_ID'] = str(ad_hoc_command.inventory.pk)
        env['INVENTORY_HOSTVARS'] = str(True)
        env['ANSIBLE_LOAD_CALLBACK_PLUGINS'] = '1'
        env['ANSIBLE_SFTP_BATCH_MODE'] = 'False'

        # Create a directory for ControlPath sockets that is unique to each
        # ad hoc command and visible inside the proot environment (when enabled).
        cp_dir = os.path.join(private_data_dir, 'cp')
        if not os.path.exists(cp_dir):
            os.mkdir(cp_dir, 0o700)
        env['ANSIBLE_SSH_CONTROL_PATH'] = cp_dir

        return env

    def build_args(self, ad_hoc_command, private_data_dir, passwords):
        '''
        Build command line argument list for running ansible, optionally using
        ssh-agent for public/private key authentication.
        '''
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
                raise ValueError(_(
                    "{} are prohibited from use in ad hoc commands."
                ).format(", ".join(removed_vars)))
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
        if ad_hoc_command.is_containerized:
            return False
        return getattr(settings, 'AWX_PROOT_ENABLED', False)

    def final_run_hook(self, adhoc_job, status, private_data_dir, fact_modification_times, isolated_manager_instance=None):
        super(RunAdHocCommand, self).final_run_hook(adhoc_job, status, private_data_dir, fact_modification_times)
        if isolated_manager_instance:
            isolated_manager_instance.cleanup()


@task(queue=get_local_queuename)
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
            if system_job.job_type in ('cleanup_jobs', 'cleanup_activitystream'):
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


@task(queue=get_local_queuename)
def deep_copy_model_obj(
    model_module, model_name, obj_pk, new_obj_pk,
    user_pk, uuid, permission_check_func=None
):
    sub_obj_list = cache.get(uuid)
    if sub_obj_list is None:
        logger.error('Deep copy {} from {} to {} failed unexpectedly.'.format(model_name, obj_pk, new_obj_pk))
        return

    logger.debug('Deep copy {} from {} to {}.'.format(model_name, obj_pk, new_obj_pk))
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
        update_inventory_computed_fields.delay(new_obj.id)
