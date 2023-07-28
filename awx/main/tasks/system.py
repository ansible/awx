# Python
from collections import namedtuple
import functools
import importlib
import json
import logging
import os
from io import StringIO
from contextlib import redirect_stdout
import shutil
import time
from distutils.version import LooseVersion as Version
from datetime import datetime

# Django
from django.conf import settings
from django.db import transaction, DatabaseError, IntegrityError
from django.db.models.fields.related import ForeignKey
from django.utils.timezone import now, timedelta
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

# Django-CRUM
from crum import impersonate


# Runner
import ansible_runner.cleanup

# dateutil
from dateutil.parser import parse as parse_date

# AWX
from awx import __version__ as awx_application_version
from awx.main.access import access_registry
from awx.main.models import (
    Schedule,
    TowerScheduleState,
    Instance,
    InstanceGroup,
    UnifiedJob,
    Notification,
    Inventory,
    SmartInventoryMembership,
    Job,
    HostMetric,
)
from awx.main.constants import ACTIVE_STATES
from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename, reaper
from awx.main.utils.common import (
    get_type_for_model,
    ignore_inventory_computed_fields,
    ignore_inventory_group_removal,
    ScheduleWorkflowManager,
    ScheduleTaskManager,
)

from awx.main.utils.reload import stop_local_services
from awx.main.utils.pglock import advisory_lock
from awx.main.tasks.receptor import get_receptor_ctl, worker_info, worker_cleanup, administrative_workunit_reaper, write_receptor_config
from awx.main.consumers import emit_channel_notification
from awx.main import analytics
from awx.conf import settings_registry
from awx.main.analytics.subsystem_metrics import Metrics

from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger('awx.main.tasks.system')

OPENSSH_KEY_ERROR = u'''\
It looks like you're trying to use a private key in OpenSSH format, which \
isn't supported by the installed version of OpenSSH on this instance. \
Try upgrading OpenSSH or providing your private key in an different format. \
'''


def dispatch_startup():
    startup_logger = logging.getLogger('awx.main.tasks')

    # TODO: Enable this on VM installs
    if settings.IS_K8S:
        write_receptor_config()

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
    reaper.startup_reaping()
    reaper.reap_waiting(grace_period=0)
    m = Metrics()
    m.reset_values()


def inform_cluster_of_shutdown():
    try:
        this_inst = Instance.objects.get(hostname=settings.CLUSTER_HOST_ID)
        this_inst.mark_offline(update_last_seen=True, errors=_('Instance received normal shutdown signal'))
        try:
            reaper.reap_waiting(this_inst, grace_period=0)
        except Exception:
            logger.exception('failed to reap waiting jobs for {}'.format(this_inst.hostname))
        logger.warning('Normal shutdown signal for instance {}, removed self from capacity pool.'.format(this_inst.hostname))
    except Exception:
        logger.exception('Encountered problem with normal shutdown signal.')


@task(queue=get_task_queuename)
def apply_cluster_membership_policies():
    from awx.main.signals import disable_activity_stream

    started_waiting = time.time()
    with advisory_lock('cluster_policy_lock', wait=True):
        lock_time = time.time() - started_waiting
        if lock_time > 1.0:
            to_log = logger.info
        else:
            to_log = logger.debug
        to_log('Waited {} seconds to obtain lock name: cluster_policy_lock'.format(lock_time))
        started_compute = time.time()
        # Hop nodes should never get assigned to an InstanceGroup.
        all_instances = list(Instance.objects.exclude(node_type='hop').order_by('id'))
        all_groups = list(InstanceGroup.objects.prefetch_related('instances'))

        total_instances = len(all_instances)
        actual_groups = []
        actual_instances = []
        Group = namedtuple('Group', ['obj', 'instances', 'prior_instances'])
        Node = namedtuple('Instance', ['obj', 'groups'])

        # Process policy instance list first, these will represent manually managed memberships
        instance_hostnames_map = {inst.hostname: inst for inst in all_instances}
        for ig in all_groups:
            group_actual = Group(obj=ig, instances=[], prior_instances=[instance.pk for instance in ig.instances.all()])  # obtained in prefetch
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

            actual_groups.append(group_actual)

        # Process Instance minimum policies next, since it represents a concrete lower bound to the
        # number of instances to make available to instance groups
        actual_instances = [Node(obj=i, groups=[]) for i in all_instances if i.managed_by_policy]
        logger.debug("Total instances: {}, available for policy: {}".format(total_instances, len(actual_instances)))
        for g in sorted(actual_groups, key=lambda x: len(x.instances)):
            exclude_type = 'execution' if g.obj.name == settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME else 'control'
            policy_min_added = []
            for i in sorted(actual_instances, key=lambda x: len(x.groups)):
                if i.obj.node_type == exclude_type:
                    continue  # never place execution instances in controlplane group or control instances in other groups
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
            exclude_type = 'execution' if g.obj.name == settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME else 'control'
            candidate_pool_ct = sum(1 for i in actual_instances if i.obj.node_type != exclude_type)
            if not candidate_pool_ct:
                continue
            policy_per_added = []
            for i in sorted(actual_instances, key=lambda x: len(x.groups)):
                if i.obj.node_type == exclude_type:
                    continue
                if i.obj.id in g.instances:
                    # If the instance is already _in_ the group, it was
                    # applied earlier via a minimum policy or policy list
                    continue
                if 100 * float(len(g.instances)) / candidate_pool_ct >= g.obj.policy_instance_percentage:
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

        # On a differential basis, apply instances to groups
        with transaction.atomic():
            with disable_activity_stream():
                for g in actual_groups:
                    if g.obj.is_container_group:
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


@task(queue='tower_settings_change')
def clear_setting_cache(setting_keys):
    # log that cache is being cleared
    logger.info(f"clear_setting_cache of keys {setting_keys}")
    orig_len = len(setting_keys)
    for i in range(orig_len):
        for dependent_key in settings_registry.get_dependent_settings(setting_keys[i]):
            setting_keys.append(dependent_key)
    cache_keys = set(setting_keys)
    logger.debug('cache delete_many(%r)', cache_keys)
    cache.delete_many(cache_keys)


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
        cache.set('awx-profile-sql-threshold', threshold, timeout=minutes * 60)
        logger.error('SQL QUERIES >={}s ENABLED FOR {} MINUTE(S)'.format(threshold, minutes))


@task(queue=get_task_queuename)
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
            if job_id is not None:
                job_actual.log_lifecycle("notifications_sent")
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


@task(queue=get_task_queuename)
def gather_analytics():
    from awx.conf.models import Setting

    if is_run_threshold_reached(Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_GATHER').first(), settings.AUTOMATION_ANALYTICS_GATHER_INTERVAL):
        analytics.gather()


@task(queue=get_task_queuename)
def purge_old_stdout_files():
    nowtime = time.time()
    for f in os.listdir(settings.JOBOUTPUT_ROOT):
        if os.path.getctime(os.path.join(settings.JOBOUTPUT_ROOT, f)) < nowtime - settings.LOCAL_STDOUT_EXPIRE_TIME:
            os.unlink(os.path.join(settings.JOBOUTPUT_ROOT, f))
            logger.debug("Removing {}".format(os.path.join(settings.JOBOUTPUT_ROOT, f)))


def _cleanup_images_and_files(**kwargs):
    if settings.IS_K8S:
        return
    this_inst = Instance.objects.me()
    runner_cleanup_kwargs = this_inst.get_cleanup_task_kwargs(**kwargs)
    if runner_cleanup_kwargs:
        stdout = ''
        with StringIO() as buffer:
            with redirect_stdout(buffer):
                ansible_runner.cleanup.run_cleanup(runner_cleanup_kwargs)
                stdout = buffer.getvalue()
        if '(changed: True)' in stdout:
            logger.info(f'Performed local cleanup with kwargs {kwargs}, output:\n{stdout}')

    # if we are the first instance alphabetically, then run cleanup on execution nodes
    checker_instance = (
        Instance.objects.filter(node_type__in=['hybrid', 'control'], node_state=Instance.States.READY, enabled=True, capacity__gt=0)
        .order_by('-hostname')
        .first()
    )
    if checker_instance and this_inst.hostname == checker_instance.hostname:
        for inst in Instance.objects.filter(node_type='execution', node_state=Instance.States.READY, enabled=True, capacity__gt=0):
            runner_cleanup_kwargs = inst.get_cleanup_task_kwargs(**kwargs)
            if not runner_cleanup_kwargs:
                continue
            try:
                stdout = worker_cleanup(inst.hostname, runner_cleanup_kwargs)
                if '(changed: True)' in stdout:
                    logger.info(f'Performed cleanup on execution node {inst.hostname} with output:\n{stdout}')
            except RuntimeError:
                logger.exception(f'Error running cleanup on execution node {inst.hostname}')


@task(queue='tower_broadcast_all')
def handle_removed_image(remove_images=None):
    """Special broadcast invocation of this method to handle case of deleted EE"""
    _cleanup_images_and_files(remove_images=remove_images, file_pattern='')


@task(queue=get_task_queuename)
def cleanup_images_and_files():
    _cleanup_images_and_files()


@task(queue=get_task_queuename)
def cleanup_host_metrics():
    """Run cleanup host metrics ~each month"""
    # TODO: move whole method to host_metrics in follow-up PR
    from awx.conf.models import Setting

    if is_run_threshold_reached(
        Setting.objects.filter(key='CLEANUP_HOST_METRICS_LAST_TS').first(), getattr(settings, 'CLEANUP_HOST_METRICS_INTERVAL', 30) * 86400
    ):
        months_ago = getattr(settings, 'CLEANUP_HOST_METRICS_SOFT_THRESHOLD', 12)
        logger.info("Executing cleanup_host_metrics")
        HostMetric.cleanup_task(months_ago)
        logger.info("Finished cleanup_host_metrics")


def is_run_threshold_reached(setting, threshold_seconds):
    from rest_framework.fields import DateTimeField

    last_time = DateTimeField().to_internal_value(setting.value) if setting and setting.value else DateTimeField().to_internal_value('1970-01-01')

    return (now() - last_time).total_seconds() > threshold_seconds


@task(queue=get_task_queuename)
def cluster_node_health_check(node):
    """
    Used for the health check endpoint, refreshes the status of the instance, but must be ran on target node
    """
    if node == '':
        logger.warning('Local health check incorrectly called with blank string')
        return
    elif node != settings.CLUSTER_HOST_ID:
        logger.warning(f'Local health check for {node} incorrectly sent to {settings.CLUSTER_HOST_ID}')
        return
    try:
        this_inst = Instance.objects.me()
    except Instance.DoesNotExist:
        logger.warning(f'Instance record for {node} missing, could not check capacity.')
        return
    this_inst.local_health_check()


@task(queue=get_task_queuename)
def execution_node_health_check(node):
    if node == '':
        logger.warning('Remote health check incorrectly called with blank string')
        return
    try:
        instance = Instance.objects.get(hostname=node)
    except Instance.DoesNotExist:
        logger.warning(f'Instance record for {node} missing, could not check capacity.')
        return

    if instance.node_type != 'execution':
        logger.warning(f'Execution node health check ran against {instance.node_type} node {instance.hostname}')
        return

    if instance.node_state not in (Instance.States.READY, Instance.States.UNAVAILABLE, Instance.States.INSTALLED):
        logger.warning(f"Execution node health check ran against node {instance.hostname} in state {instance.node_state}")
        return

    data = worker_info(node)

    prior_capacity = instance.capacity

    instance.save_health_data(
        version='ansible-runner-' + data.get('runner_version', '???'),
        cpu=data.get('cpu_count', 0),
        memory=data.get('mem_in_bytes', 0),
        uuid=data.get('uuid'),
        errors='\n'.join(data.get('errors', [])),
    )

    if data['errors']:
        formatted_error = "\n".join(data["errors"])
        if prior_capacity:
            logger.warning(f'Health check marking execution node {node} as lost, errors:\n{formatted_error}')
        else:
            logger.info(f'Failed to find capacity of new or lost execution node {node}, errors:\n{formatted_error}')
    else:
        logger.info('Set capacity of execution node {} to {}, worker info data:\n{}'.format(node, instance.capacity, json.dumps(data, indent=2)))

    return data


def inspect_execution_nodes(instance_list):
    with advisory_lock('inspect_execution_nodes_lock', wait=False):
        node_lookup = {inst.hostname: inst for inst in instance_list}

        ctl = get_receptor_ctl()
        mesh_status = ctl.simple_command('status')

        nowtime = now()
        workers = mesh_status['Advertisements']

        for ad in workers:
            hostname = ad['NodeID']

            if hostname in node_lookup:
                instance = node_lookup[hostname]
            else:
                logger.warning(f"Unrecognized node advertising on mesh: {hostname}")
                continue

            # Control-plane nodes are dealt with via local_health_check instead.
            if instance.node_type in (Instance.Types.CONTROL, Instance.Types.HYBRID):
                continue

            last_seen = parse_date(ad['Time'])
            if instance.last_seen and instance.last_seen >= last_seen:
                continue
            instance.last_seen = last_seen
            instance.save(update_fields=['last_seen'])

            # Only execution nodes should be dealt with by execution_node_health_check
            if instance.node_type == Instance.Types.HOP:
                if instance.node_state in (Instance.States.UNAVAILABLE, Instance.States.INSTALLED):
                    logger.warning(f'Hop node {hostname}, has rejoined the receptor mesh')
                    instance.save_health_data(errors='')
                continue

            if instance.node_state in (Instance.States.UNAVAILABLE, Instance.States.INSTALLED):
                # if the instance *was* lost, but has appeared again,
                # attempt to re-establish the initial capacity and version
                # check
                logger.warning(f'Execution node attempting to rejoin as instance {hostname}.')
                execution_node_health_check.apply_async([hostname])
            elif instance.capacity == 0 and instance.enabled:
                # nodes with proven connection but need remediation run health checks are reduced frequency
                if not instance.last_health_check or (nowtime - instance.last_health_check).total_seconds() >= settings.EXECUTION_NODE_REMEDIATION_CHECKS:
                    # Periodically re-run the health check of errored nodes, in case someone fixed it
                    # TODO: perhaps decrease the frequency of these checks
                    logger.debug(f'Restarting health check for execution node {hostname} with known errors.')
                    execution_node_health_check.apply_async([hostname])


@task(queue=get_task_queuename, bind_kwargs=['dispatch_time', 'worker_tasks'])
def cluster_node_heartbeat(dispatch_time=None, worker_tasks=None):
    logger.debug("Cluster node heartbeat task.")
    nowtime = now()
    instance_list = list(Instance.objects.filter(node_state__in=(Instance.States.READY, Instance.States.UNAVAILABLE, Instance.States.INSTALLED)))
    this_inst = None
    lost_instances = []

    for inst in instance_list:
        if inst.hostname == settings.CLUSTER_HOST_ID:
            this_inst = inst
            break

    inspect_execution_nodes(instance_list)

    for inst in list(instance_list):
        if inst == this_inst:
            continue
        if inst.is_lost(ref_time=nowtime):
            lost_instances.append(inst)
            instance_list.remove(inst)

    if this_inst:
        startup_event = this_inst.is_lost(ref_time=nowtime)
        last_last_seen = this_inst.last_seen
        this_inst.local_health_check()
        if startup_event and this_inst.capacity != 0:
            logger.warning(f'Rejoining the cluster as instance {this_inst.hostname}. Prior last_seen {last_last_seen}')
            return
        elif not last_last_seen:
            logger.warning(f'Instance does not have recorded last_seen, updating to {nowtime}')
        elif (nowtime - last_last_seen) > timedelta(seconds=settings.CLUSTER_NODE_HEARTBEAT_PERIOD + 2):
            logger.warning(f'Heartbeat skew - interval={(nowtime - last_last_seen).total_seconds():.4f}, expected={settings.CLUSTER_NODE_HEARTBEAT_PERIOD}')
    else:
        if settings.AWX_AUTO_DEPROVISION_INSTANCES:
            (changed, this_inst) = Instance.objects.register(ip_address=os.environ.get('MY_POD_IP'), node_type='control', node_uuid=settings.SYSTEM_UUID)
            if changed:
                logger.warning(f'Recreated instance record {this_inst.hostname} after unexpected removal')
            this_inst.local_health_check()
        else:
            raise RuntimeError("Cluster Host Not Found: {}".format(settings.CLUSTER_HOST_ID))
    # IFF any node has a greater version than we do, then we'll shutdown services
    for other_inst in instance_list:
        if other_inst.node_type in ('execution', 'hop'):
            continue
        if other_inst.version == "" or other_inst.version.startswith('ansible-runner'):
            continue
        if Version(other_inst.version.split('-', 1)[0]) > Version(awx_application_version.split('-', 1)[0]) and not settings.DEBUG:
            logger.error(
                "Host {} reports version {}, but this node {} is at {}, shutting down".format(
                    other_inst.hostname, other_inst.version, this_inst.hostname, this_inst.version
                )
            )
            # Shutdown signal will set the capacity to zero to ensure no Jobs get added to this instance.
            # The heartbeat task will reset the capacity to the system capacity after upgrade.
            stop_local_services(communicate=False)
            raise RuntimeError("Shutting down.")

    for other_inst in lost_instances:
        try:
            explanation = "Job reaped due to instance shutdown"
            reaper.reap(other_inst, job_explanation=explanation)
            reaper.reap_waiting(other_inst, grace_period=0, job_explanation=explanation)
        except Exception:
            logger.exception('failed to reap jobs for {}'.format(other_inst.hostname))
        try:
            if settings.AWX_AUTO_DEPROVISION_INSTANCES and other_inst.node_type == "control":
                deprovision_hostname = other_inst.hostname
                other_inst.delete()  # FIXME: what about associated inbound links?
                logger.info("Host {} Automatically Deprovisioned.".format(deprovision_hostname))
            elif other_inst.node_state == Instance.States.READY:
                other_inst.mark_offline(errors=_('Another cluster node has determined this instance to be unresponsive'))
                logger.error("Host {} last checked in at {}, marked as lost.".format(other_inst.hostname, other_inst.last_seen))

        except DatabaseError as e:
            if 'did not affect any rows' in str(e):
                logger.debug('Another instance has marked {} as lost'.format(other_inst.hostname))
            else:
                logger.exception('Error marking {} as lost'.format(other_inst.hostname))

    # Run local reaper
    if worker_tasks is not None:
        active_task_ids = []
        for task_list in worker_tasks.values():
            active_task_ids.extend(task_list)
        reaper.reap(instance=this_inst, excluded_uuids=active_task_ids, ref_time=datetime.fromisoformat(dispatch_time))
        if max(len(task_list) for task_list in worker_tasks.values()) <= 1:
            reaper.reap_waiting(instance=this_inst, excluded_uuids=active_task_ids, ref_time=datetime.fromisoformat(dispatch_time))


@task(queue=get_task_queuename)
def awx_receptor_workunit_reaper():
    """
    When an AWX job is launched via receptor, files such as status, stdin, and stdout are created
    in a specific receptor directory. This directory on disk is a random 8 character string, e.g. qLL2JFNT
    This is also called the work Unit ID in receptor, and is used in various receptor commands,
    e.g. "work results qLL2JFNT"
    After an AWX job executes, the receptor work unit directory is cleaned up by
    issuing the work release command. In some cases the release process might fail, or
    if AWX crashes during a job's execution, the work release command is never issued to begin with.
    As such, this periodic task will obtain a list of all receptor work units, and find which ones
    belong to AWX jobs that are in a completed state (status is canceled, error, or succeeded).
    This task will call "work release" on each of these work units to clean up the files on disk.

    Note that when we call "work release" on a work unit that actually represents remote work
    both the local and remote work units are cleaned up.

    Since we are cleaning up jobs that controller considers to be inactive, we take the added
    precaution of calling "work cancel" in case the work unit is still active.
    """
    if not settings.RECEPTOR_RELEASE_WORK:
        return
    logger.debug("Checking for unreleased receptor work units")
    receptor_ctl = get_receptor_ctl()
    receptor_work_list = receptor_ctl.simple_command("work list")

    unit_ids = [id for id in receptor_work_list]
    jobs_with_unreleased_receptor_units = UnifiedJob.objects.filter(work_unit_id__in=unit_ids).exclude(status__in=ACTIVE_STATES)
    for job in jobs_with_unreleased_receptor_units:
        logger.debug(f"{job.log_format} is not active, reaping receptor work unit {job.work_unit_id}")
        receptor_ctl.simple_command(f"work cancel {job.work_unit_id}")
        receptor_ctl.simple_command(f"work release {job.work_unit_id}")

    administrative_workunit_reaper(receptor_work_list)


@task(queue=get_task_queuename)
def awx_k8s_reaper():
    if not settings.RECEPTOR_RELEASE_WORK:
        return

    from awx.main.scheduler.kubernetes import PodManager  # prevent circular import

    for group in InstanceGroup.objects.filter(is_container_group=True).iterator():
        logger.debug("Checking for orphaned k8s pods for {}.".format(group))
        pods = PodManager.list_active_jobs(group)
        time_cutoff = now() - timedelta(seconds=settings.K8S_POD_REAPER_GRACE_PERIOD)
        for job in UnifiedJob.objects.filter(pk__in=pods.keys(), finished__lte=time_cutoff).exclude(status__in=ACTIVE_STATES):
            logger.debug('{} is no longer active, reaping orphaned k8s pod'.format(job.log_format))
            try:
                pm = PodManager(job)
                pm.kube_api.delete_namespaced_pod(name=pods[job.id], namespace=pm.namespace, _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT)
            except Exception:
                logger.exception("Failed to delete orphaned pod {} from {}".format(job.log_format, group))


@task(queue=get_task_queuename)
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
            schedule.update_computed_fields()  # To update next_run timestamp.
            if template.cache_timeout_blocked:
                logger.warning("Cache timeout is in the future, bypassing schedule for template %s" % str(template.id))
                continue
            try:
                job_kwargs = schedule.get_job_kwargs()
                new_unified_job = schedule.unified_job_template.create_unified_job(**job_kwargs)
                logger.debug('Spawned {} from schedule {}-{}.'.format(new_unified_job.log_format, schedule.name, schedule.pk))

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
                new_unified_job.job_explanation = gettext_noop(
                    "Scheduled job could not start because it \
                    was not in the right state or required manual credentials"
                )
                new_unified_job.save(update_fields=['status', 'job_explanation'])
                new_unified_job.websocket_emit_status("failed")
            emit_channel_notification('schedules-changed', dict(id=schedule.id, group_name="schedules"))
        state.save()


def schedule_manager_success_or_error(instance):
    if instance.unifiedjob_blocked_jobs.exists():
        ScheduleTaskManager().schedule()
    if instance.spawned_by_workflow:
        ScheduleWorkflowManager().schedule()


@task(queue=get_task_queuename)
def handle_work_success(task_actual):
    try:
        instance = UnifiedJob.get_instance_by_type(task_actual['type'], task_actual['id'])
    except ObjectDoesNotExist:
        logger.warning('Missing {} `{}` in success callback.'.format(task_actual['type'], task_actual['id']))
        return
    if not instance:
        return
    schedule_manager_success_or_error(instance)


@task(queue=get_task_queuename)
def handle_work_error(task_actual):
    try:
        instance = UnifiedJob.get_instance_by_type(task_actual['type'], task_actual['id'])
    except ObjectDoesNotExist:
        logger.warning('Missing {} `{}` in error callback.'.format(task_actual['type'], task_actual['id']))
        return
    if not instance:
        return

    subtasks = instance.get_jobs_fail_chain()  # reverse of dependent_jobs mostly
    logger.debug(f'Executing error task id {task_actual["id"]}, subtasks: {[subtask.id for subtask in subtasks]}')

    deps_of_deps = {}

    for subtask in subtasks:
        if subtask.celery_task_id != instance.celery_task_id and not subtask.cancel_flag and not subtask.status in ('successful', 'failed'):
            # If there are multiple in the dependency chain, A->B->C, and this was called for A, blame B for clarity
            blame_job = deps_of_deps.get(subtask.id, instance)
            subtask.status = 'failed'
            subtask.failed = True
            if not subtask.job_explanation:
                subtask.job_explanation = 'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % (
                    get_type_for_model(type(blame_job)),
                    blame_job.name,
                    blame_job.id,
                )
            subtask.save()
            subtask.websocket_emit_status("failed")

            for sub_subtask in subtask.get_jobs_fail_chain():
                deps_of_deps[sub_subtask.id] = subtask

    # We only send 1 job complete message since all the job completion message
    # handling does is trigger the scheduler. If we extend the functionality of
    # what the job complete message handler does then we may want to send a
    # completion event for each job here.
    schedule_manager_success_or_error(instance)


@task(queue=get_task_queuename)
def update_inventory_computed_fields(inventory_id):
    """
    Signal handler and wrapper around inventory.update_computed_fields to
    prevent unnecessary recursive calls.
    """
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
                add_for_inventory = [SmartInventoryMembership(inventory_id=smart_inventory.id, host_id=host_id) for host_id in additions]
                SmartInventoryMembership.objects.bulk_create(add_for_inventory, ignore_conflicts=True)
        logger.debug(
            'Smart host membership cached for {}, {} additions, {} removals, {} total count.'.format(
                smart_inventory.pk, len(additions), len(removals), len(new)
            )
        )
        return True  # changed
    return False


@task(queue=get_task_queuename)
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


@task(queue=get_task_queuename)
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
            Inventory.objects.get(id=inventory_id).delete()
            emit_channel_notification('inventories-status_changed', {'group_name': 'inventories', 'inventory_id': inventory_id, 'status': 'deleted'})
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
                    logger.debug('Deep copy: Adding {} to {}({}).{} relationship'.format(related_obj, new_obj, model, field_name))
                    getattr(new_obj, field_name).add(copy_mapping.get(related_obj, related_obj))
        new_obj.save()


@task(queue=get_task_queuename)
def deep_copy_model_obj(model_module, model_name, obj_pk, new_obj_pk, user_pk, permission_check_func=None):
    logger.debug('Deep copy {} from {} to {}.'.format(model_name, obj_pk, new_obj_pk))

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

    o2m_to_preserve = {}
    fields_to_preserve = set(getattr(model, 'FIELDS_TO_PRESERVE_AT_COPY', []))

    for field in model._meta.get_fields():
        if field.name in fields_to_preserve:
            if field.one_to_many:
                try:
                    field_val = getattr(obj, field.name)
                except AttributeError:
                    continue
                o2m_to_preserve[field.name] = field_val

    sub_obj_list = []
    for o2m in o2m_to_preserve:
        for sub_obj in o2m_to_preserve[o2m].all():
            sub_model = type(sub_obj)
            sub_obj_list.append((sub_model.__module__, sub_model.__name__, sub_obj.pk))

    from awx.api.generics import CopyAPIView
    from awx.main.signals import disable_activity_stream

    with transaction.atomic(), ignore_inventory_computed_fields(), disable_activity_stream():
        copy_mapping = {}
        for sub_obj_setup in sub_obj_list:
            sub_model = getattr(importlib.import_module(sub_obj_setup[0]), sub_obj_setup[1], None)
            if sub_model is None:
                continue
            try:
                sub_obj = sub_model.objects.get(pk=sub_obj_setup[2])
            except ObjectDoesNotExist:
                continue
            copy_mapping.update(CopyAPIView.copy_model_obj(obj, new_obj, sub_model, sub_obj, creater))
        _reconstruct_relationships(copy_mapping)
        if permission_check_func:
            permission_check_func = getattr(getattr(importlib.import_module(permission_check_func[0]), permission_check_func[1]), permission_check_func[2])
            permission_check_func(creater, copy_mapping.values())
    if isinstance(new_obj, Inventory):
        update_inventory_computed_fields.delay(new_obj.id)
