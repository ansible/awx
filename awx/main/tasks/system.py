# Python
import functools
import importlib
import itertools
import json
import logging
import os
import shutil
import time
from collections import namedtuple
from contextlib import redirect_stdout
from packaging.version import Version
from io import StringIO

# dispatcherd
from dispatcherd.factories import get_control_from_settings
from dispatcherd.publish import task

# Runner
import ansible_runner.cleanup
import psycopg
from ansible_base.lib.cache.tasks import clear_cache as dab_clear_cache
from ansible_base.lib.utils.db import advisory_lock

# django-ansible-base
from ansible_base.resource_registry.tasks.sync import SyncExecutor

# Django-CRUM
from crum import impersonate

# dateutil
from dateutil.parser import parse as parse_date

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.models import Q
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from rest_framework.exceptions import PermissionDenied

# AWX
from awx import __version__ as awx_application_version
from awx.conf import settings_registry
from awx.main import analytics
from awx.main.access import access_registry
from awx.main.analytics.subsystem_metrics import DispatcherMetrics
from awx.main.constants import ACTIVE_STATES, ERROR_STATES
from awx.main.consumers import emit_channel_notification
from awx.main.dispatch import get_task_queuename, reaper
from awx.main.models import (
    Instance,
    InstanceGroup,
    Inventory,
    Job,
    Notification,
    Schedule,
    SmartInventoryMembership,
    TowerScheduleState,
    UnifiedJob,
    WorkflowJob,
    convert_jsonfields,
)
from awx.main.models.credential import CredentialType
from awx.main.tasks.helpers import is_run_threshold_reached
from awx.main.tasks.host_indirect import save_indirect_host_entries
from awx.main.tasks.receptor import (
    _adoption_stall_budget_exhausted,
    administrative_workunit_reaper,
    get_adoption_unit_status,
    get_receptor_ctl,
    reattach_to_work_unit,
    worker_cleanup,
    worker_info,
    write_receptor_config,
)
from awx.main.tasks.signals import with_signal_handling
from awx.main.utils.common import ignore_inventory_computed_fields, ignore_inventory_group_removal
from awx.main.utils.failpoints import failpoint
from awx.main.utils.migration import is_database_synchronized
from awx.main.utils.reload import stop_local_services

logger = logging.getLogger('awx.main.tasks.system')

OPENSSH_KEY_ERROR = '''\
It looks like you're trying to use a private key in OpenSSH format, which \
isn't supported by the installed version of OpenSSH on this instance. \
Try upgrading OpenSSH or providing your private key in an different format. \
'''


def _sync_credential_types_to_db():
    """Ensure CredentialType DB rows match the installed plugins.

    The in-memory registry is populated lazily on first access via LazyLoadDict.
    This function only handles the DB sync step.
    """
    if is_database_synchronized():
        CredentialType.setup_tower_managed_defaults()


def _run_dispatch_startup_common():
    """
    Execute the common startup initialization steps.
    This includes updating schedules, syncing instance membership, and starting
    local reaping and resetting metrics.
    """
    startup_logger = logging.getLogger('awx.main.tasks')

    # TODO: Enable this on VM installs
    if settings.IS_K8S:
        try:
            write_receptor_config()
        except Exception:
            logger.exception("Failed to write receptor config, skipping.")

    try:
        _sync_credential_types_to_db()
    except Exception:
        logger.exception("Failed to sync credential types to DB, skipping.")

    try:
        convert_jsonfields()
    except Exception:
        logger.exception("Failed JSON field conversion, skipping.")

    startup_logger.debug("Syncing schedules")
    for sch in Schedule.objects.all():
        try:
            sch.update_computed_fields()
        except Exception:
            logger.exception("Failed to rebuild schedule %s.", sch)

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
    cluster_node_heartbeat(None)
    # Safety net: reap undispatched startup jobs even if cluster_node_heartbeat returned early
    # (receptor unavailable, rejoining cluster). _process_startup_jobs handles adoption; this
    # handles the reap-only case. reap_job() is idempotent — already-reaped jobs are skipped.
    _startup_reap_undispatched(settings.CLUSTER_HOST_ID)
    # Then mark any peer whose pod is gone, so the sweep below can see the jobs it left. Order
    # matters: the sweep decides what is orphaned from node_state, so the state has to be
    # written first or the jobs are invisible for another heartbeat.
    _startup_mark_departed_peers()
    # And sweep jobs left behind by a controller that is already gone. Separate from the reap
    # above: that one looks at jobs this node owns, this one at jobs nobody live owns.
    _startup_sweep_orphaned_jobs()
    m = DispatcherMetrics()
    m.reset_values()


def _dispatcherd_dispatch_startup():
    """
    New dispatcherd branch for startup: uses the control API to re-submit waiting jobs.
    """
    logger.debug("Dispatcherd enabled: dispatching waiting jobs via control channel")
    from awx.main.tasks.jobs import dispatch_waiting_jobs

    dispatch_waiting_jobs.apply_async(queue=get_task_queuename())


def dispatch_startup():
    """
    System initialization at startup.
    First, execute the common logic.
    Then, re-submit waiting jobs via the control API.
    """
    _run_dispatch_startup_common()
    _dispatcherd_dispatch_startup()


def inform_cluster_of_shutdown():
    """
    Clean system shutdown that marks the current instance offline.
    Relies on dispatcherd's built-in cleanup.
    """
    try:
        inst = Instance.objects.get(hostname=settings.CLUSTER_HOST_ID)
        inst.mark_offline(update_last_seen=True, errors=_('Instance received normal shutdown signal'))
    except Instance.DoesNotExist:
        logger.exception("Cluster host not found: %s", settings.CLUSTER_HOST_ID)
        return

    logger.debug("No extra reaping required for instance %s", inst.hostname)
    logger.warning("Normal shutdown processed for instance %s; instance removed from capacity pool.", inst.hostname)


@task(queue=get_task_queuename, timeout=3600 * 5)
def migrate_jsonfield(table, pkfield, columns):
    batchsize = 10000
    with advisory_lock(f'json_migration_{table}', wait=False) as acquired:
        if not acquired:
            return

        from django.db.migrations.executor import MigrationExecutor

        # If Django is currently running migrations, wait until it is done.
        while True:
            executor = MigrationExecutor(connection)
            if not executor.migration_plan(executor.loader.graph.leaf_nodes()):
                break
            time.sleep(120)

        logger.warning(f"Migrating json fields for {table}: {', '.join(columns)}")

        with connection.cursor() as cursor:
            for i in itertools.count(0, batchsize):
                # Are there even any rows in the table beyond this point?
                cursor.execute(f"select count(1) from {table} where {pkfield} >= %s limit 1;", (i,))
                if not cursor.fetchone()[0]:
                    break

                column_expr = ', '.join(f"{colname} = {colname}_old::jsonb" for colname in columns)
                # If any of the old columns have non-null values, the data needs to be cast and copied over.
                empty_expr = ' or '.join(f"{colname}_old is not null" for colname in columns)
                cursor.execute(  # Only clobber the new fields if there is non-null data in the old ones.
                    f"""
                    update {table}
                      set {column_expr}
                      where {pkfield} >= %s and {pkfield} < %s
                        and {empty_expr};
                    """,
                    (i, i + batchsize),
                )
                rows = cursor.rowcount
                logger.debug(f"Batch {i} to {i + batchsize} copied on {table}, {rows} rows affected.")

            column_expr = ', '.join(f"DROP COLUMN {column}_old" for column in columns)
            cursor.execute(f"ALTER TABLE {table} {column_expr};")

        logger.warning(f"Migration of {table} to jsonb is finished.")


@task(queue=get_task_queuename, timeout=3600, on_duplicate='queue_one')
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
            # we don't want to allow execution nodes in the control plane
            exclude_type = 'execution' if ig.name == settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME else 'control'
            group_actual = Group(obj=ig, instances=[], prior_instances=[instance.pk for instance in ig.instances.all()])  # obtained in prefetch
            for hostname in ig.policy_instance_list:
                if hostname not in instance_hostnames_map:
                    logger.info("Unknown instance {} in {} policy list".format(hostname, ig.name))
                    continue
                inst = instance_hostnames_map[hostname]
                if inst.node_type == exclude_type:
                    logger.info("Instance {} is excluded in {} policy list".format(hostname, ig.name))
                    continue
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


def _resolve_setting_dependents(key):
    return settings_registry.get_dependent_settings(key)


def _post_setting_invalidation(invalidated_keys):
    if 'LOG_AGGREGATOR_LEVEL' in invalidated_keys:
        ctl = get_control_from_settings()
        ctl.queuename = get_task_queuename()
        ctl.control('set_log_level', data={'level': settings.LOG_AGGREGATOR_LEVEL})


@task(queue='tower_settings_change', timeout=600)
def clear_setting_cache(setting_keys):
    dab_clear_cache(setting_keys, _resolve_setting_dependents, _post_setting_invalidation)


@task(queue='tower_broadcast_all', timeout=600)
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


@task(queue=get_task_queuename, timeout=1800)
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


def events_processed_hook(unified_job):
    """This method is intended to be called for every unified job
    after the playbook_on_stats/EOF event is processed and final status is saved
    Either one of these events could happen before the other, or there may be no events"""
    unified_job.send_notification_templates('succeeded' if unified_job.status == 'successful' else 'failed')
    if isinstance(unified_job, Job):
        if not settings.INDIRECT_NODE_COUNTING_ENABLED:
            Job.objects.filter(id=unified_job.id, event_queries_processed=False).update(event_queries_processed=True)
            return
        if unified_job.event_queries_processed is True:
            # If this is called from callback receiver, it likely does not have updated model data
            # a refresh now is formally robust
            unified_job.refresh_from_db(fields=['event_queries_processed'])
        if unified_job.event_queries_processed is False:
            save_indirect_host_entries.delay(unified_job.id)


@task(queue=get_task_queuename, timeout=3600 * 5, on_duplicate='discard')
def gather_analytics():
    if is_run_threshold_reached(getattr(settings, 'AUTOMATION_ANALYTICS_LAST_GATHER', None), settings.AUTOMATION_ANALYTICS_GATHER_INTERVAL):
        analytics.gather()


@task(queue=get_task_queuename, timeout=600, on_duplicate='queue_one')
def purge_old_stdout_files():
    nowtime = time.time()
    for f in os.listdir(settings.JOBOUTPUT_ROOT):
        if os.path.getctime(os.path.join(settings.JOBOUTPUT_ROOT, f)) < nowtime - settings.LOCAL_STDOUT_EXPIRE_TIME:
            os.unlink(os.path.join(settings.JOBOUTPUT_ROOT, f))
            logger.debug("Removing {}".format(os.path.join(settings.JOBOUTPUT_ROOT, f)))


class CleanupImagesAndFiles:
    @classmethod
    def get_first_control_instance(cls) -> Instance | None:
        return (
            Instance.objects.filter(node_type__in=['hybrid', 'control'], node_state=Instance.States.READY, enabled=True, capacity__gt=0)
            .order_by('-hostname')
            .first()
        )

    @classmethod
    def get_execution_instances(cls) -> QuerySet[Instance]:
        return Instance.objects.filter(node_type='execution', node_state=Instance.States.READY, enabled=True, capacity__gt=0)

    @classmethod
    def run_local(cls, this_inst: Instance, **kwargs):
        if settings.IS_K8S:
            return
        runner_cleanup_kwargs = this_inst.get_cleanup_task_kwargs(**kwargs)
        if runner_cleanup_kwargs:
            stdout = ''
            with StringIO() as buffer:
                with redirect_stdout(buffer):
                    ansible_runner.cleanup.run_cleanup(runner_cleanup_kwargs)
                    stdout = buffer.getvalue()
            if '(changed: True)' in stdout:
                logger.info(f'Performed local cleanup with kwargs {kwargs}, output:\n{stdout}')

    @classmethod
    def run_remote(cls, this_inst: Instance, **kwargs):
        # if we are the first instance alphabetically, then run cleanup on execution nodes
        checker_instance = cls.get_first_control_instance()

        if checker_instance and this_inst.hostname == checker_instance.hostname:
            for inst in cls.get_execution_instances():
                runner_cleanup_kwargs = inst.get_cleanup_task_kwargs(**kwargs)
                if not runner_cleanup_kwargs:
                    continue
                try:
                    stdout = worker_cleanup(inst.hostname, runner_cleanup_kwargs)
                    if '(changed: True)' in stdout:
                        logger.info(f'Performed cleanup on execution node {inst.hostname} with output:\n{stdout}')
                except RuntimeError:
                    logger.exception(f'Error running cleanup on execution node {inst.hostname}')

    @classmethod
    def run(cls, **kwargs):
        if settings.IS_K8S:
            return
        this_inst = Instance.objects.me()
        cls.run_local(this_inst, **kwargs)
        cls.run_remote(this_inst, **kwargs)


@task(queue='tower_broadcast_all', timeout=3600)
def handle_removed_image(remove_images=None):
    """Special broadcast invocation of this method to handle case of deleted EE"""
    CleanupImagesAndFiles.run(remove_images=remove_images, file_pattern='')


@task(queue=get_task_queuename, timeout=3600, on_duplicate='queue_one')
def cleanup_images_and_files():
    CleanupImagesAndFiles.run(image_prune=True)


@task(queue=get_task_queuename, timeout=600, on_duplicate='queue_one')
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


def inspect_established_receptor_connections(mesh_status):
    '''
    Flips link state from ADDING to ESTABLISHED
    If the InstanceLink source and target match the entries
    in Known Connection Costs, flip to Established.
    '''
    from awx.main.models import InstanceLink

    all_links = InstanceLink.objects.filter(link_state=InstanceLink.States.ADDING)
    if not all_links.exists():
        return
    active_receptor_conns = mesh_status['KnownConnectionCosts']
    update_links = []
    for link in all_links:
        if link.link_state != InstanceLink.States.REMOVING:
            if link.target.instance.hostname in active_receptor_conns.get(link.source.hostname, {}):
                if link.link_state is not InstanceLink.States.ESTABLISHED:
                    link.link_state = InstanceLink.States.ESTABLISHED
                    update_links.append(link)

    InstanceLink.objects.bulk_update(update_links, ['link_state'])


def inspect_execution_and_hop_nodes(instance_list, mesh_status):
    with advisory_lock('inspect_execution_and_hop_nodes_lock', wait=False) as acquired:
        if not acquired:
            logger.debug("Not running inspect_execution_and_hop_nodes, another instance holds lock")
            return
        if mesh_status is None:
            logger.debug("Not running inspect_execution_and_hop_nodes, mesh status unavailable")
            return
        start = time.monotonic()
        node_lookup = {inst.hostname: inst for inst in instance_list}

        inspect_established_receptor_connections(mesh_status)

        nowtime = now()
        workers = mesh_status.get('Advertisements') or []
        updated_count = 0

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
            updated_count += 1

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
            elif (instance.capacity == 0 or (instance.cpu == 0 and instance.memory == 0)) and instance.enabled:
                # nodes with proven connection but need remediation run health checks are reduced frequency
                if not instance.last_health_check or (nowtime - instance.last_health_check).total_seconds() >= settings.EXECUTION_NODE_REMEDIATION_CHECKS:
                    # Periodically re-run the health check of errored nodes, in case someone fixed it
                    # TODO: perhaps decrease the frequency of these checks
                    logger.debug(f'Restarting health check for execution node {hostname} with known errors.')
                    execution_node_health_check.apply_async([hostname])

        elapsed = time.monotonic() - start
        if elapsed > 2.0:
            logger.warning(f"inspect_execution_and_hop_nodes completed in {elapsed:.1f}s, updated {updated_count} node(s)")
        else:
            logger.debug(f"inspect_execution_and_hop_nodes completed in {elapsed:.3f}s, updated {updated_count} node(s)")


@task(queue=get_task_queuename, bind=True)
def cluster_node_heartbeat(binder):
    """
    Dispatcherd implementation.
    Uses Control API to get running tasks.
    """

    # Run common instance management logic — ctl is the same receptor connection used for
    # mesh status; we reuse it for the job processing loop to avoid a second socket open.
    failpoint('heartbeat.start', periodic=binder is not None)
    this_inst, instance_list, lost_instances, _ctl = _heartbeat_instance_management()
    if this_inst is None:
        return  # Early return case from instance management

    # Check versions
    _heartbeat_check_versions(this_inst, instance_list)

    # Handle lost instances
    _heartbeat_handle_lost_instances(lost_instances, this_inst)

    if binder is None:
        # Startup: one loop over all running jobs on this instance.
        # Dispatched jobs are handed to adopt_job_async; undispatched jobs are reaped.
        _process_startup_jobs(this_inst)
        logger.debug("Heartbeat finished in startup.")
        return

    # Periodic heartbeat: get running tasks from dispatcherd, then process orphaned jobs.
    active_task_ids = _get_active_task_ids_from_dispatcherd(binder)
    if active_task_ids is None:
        logger.warning("No active task IDs retrieved from dispatcherd, skipping reaper")
        return  # Failed to get task IDs, don't attempt reaping

    # One loop over all orphaned running jobs — adopt dispatched, reap undispatched.
    ref_time = now()
    logger.debug(f"Running job processing loop with {len(active_task_ids)} excluded UUIDs")
    _process_running_jobs(this_inst, active_task_ids, ref_time)

    # Reconcile behind the owner-driven paths above: pick up jobs whose controller is gone
    # from the Instance table entirely, which neither _process_running_jobs (it only looks at
    # jobs this node owns) nor the lost-instance path (it keys on the row it just deleted)
    # can see. Runs on every node, so adoption load is no longer winner-takes-all.
    _sweep_orphaned_jobs(this_inst)

    # If waiting jobs are hanging out, resubmit them
    if UnifiedJob.objects.filter(controller_node=settings.CLUSTER_HOST_ID, status='waiting').exists():
        from awx.main.tasks.jobs import dispatch_waiting_jobs

        dispatch_waiting_jobs.apply_async(queue=get_task_queuename())


def _get_active_task_ids_from_dispatcherd(binder):
    """
    Retrieve active task IDs from the dispatcherd control API.

    Returns:
        list: List of active task UUIDs
        None: If there was an error retrieving the data
    """
    active_task_ids = []
    try:
        logger.debug("Querying dispatcherd API for running tasks")
        data = binder.control('running')

        # Extract UUIDs from the running data
        # Process running data: first item is a dict with node_id and task entries
        data.pop('node_id', None)

        # Extract task UUIDs from data structure
        for task_key, task_value in data.items():
            if isinstance(task_value, dict) and 'uuid' in task_value:
                active_task_ids.append(task_value['uuid'])
                logger.debug(f"Found active task with UUID: {task_value['uuid']}")
            elif isinstance(task_key, str):
                # Handle case where UUID might be the key
                active_task_ids.append(task_key)
                logger.debug(f"Found active task with key: {task_key}")

        logger.debug(f"Retrieved {len(active_task_ids)} active task IDs from dispatcherd")
        return active_task_ids
    except Exception:
        logger.exception("Failed to get running tasks from dispatcherd")
        return None


def _mesh_all_ready_nodes_visible(mesh_status):
    """Return False if the receptor mesh is still re-establishing after a controller restart.

    Uses KnownConnectionCosts as the stability signal: receptor's routing protocol
    populates this table as connections establish via gossip. An empty table means no
    routing has propagated yet (Window A — typically the first ~10s after restart).

    In Kubernetes (IS_K8S=True), controller pods are stateless and independent with no
    peer connections expected. Empty routing is the normal steady state, not instability.

    No DB state is consulted. KnownConnectionCosts is maintained entirely by the receptor
    Go process, making it a reliable mesh-state signal free of stale DB records.

    Fails open (returns True) when mesh_status is None so existing error paths are
    not bypassed.
    """
    if mesh_status is None:
        return True  # fail open: status unavailable, let normal peer-judgment proceed
    if settings.IS_K8S:
        return True  # K8s pods are stateless; no mesh consensus required
    if not (mesh_status.get('KnownConnectionCosts') or {}):
        logger.info('Mesh stability gate: routing table empty, deferring peer-judgment (receptor re-establishing)')
        return False
    return True


def _heartbeat_instance_management():
    """Common logic for heartbeat instance management."""
    logger.debug("Cluster node heartbeat task.")
    nowtime = now()
    instance_list = list(Instance.objects.filter(node_state__in=(Instance.States.READY, Instance.States.UNAVAILABLE, Instance.States.INSTALLED)))
    this_inst = None
    lost_instances = []

    for inst in instance_list:
        if inst.hostname == settings.CLUSTER_HOST_ID:
            this_inst = inst
            break

    try:
        ctl = get_receptor_ctl()
    except FileNotFoundError:
        logger.error('Receptor not available, marking instance offline.')
        if this_inst:
            this_inst.local_health_check()
            this_inst.mark_offline(errors='Receptor not available')
        return None, None, None, None

    try:
        mesh_status = ctl.simple_command('status')
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning(f'Receptor status unavailable: {exc}')
        mesh_status = None

    inspect_execution_and_hop_nodes(instance_list, mesh_status)

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
            return None, None, None, None  # Early return case
        elif not last_last_seen:
            logger.warning(f'Instance does not have recorded last_seen, updating to {nowtime}')
        elif (nowtime - last_last_seen) > timedelta(seconds=settings.CLUSTER_NODE_HEARTBEAT_PERIOD + 2):
            logger.warning(f'Heartbeat skew - interval={(nowtime - last_last_seen).total_seconds():.4f}, expected={settings.CLUSTER_NODE_HEARTBEAT_PERIOD}')
    else:
        if settings.AWX_AUTO_DEPROVISION_INSTANCES:
            changed, this_inst = Instance.objects.register(ip_address=os.environ.get('MY_POD_IP'), node_type='control', node_uuid=settings.SYSTEM_UUID)
            if changed:
                logger.warning(f'Recreated instance record {this_inst.hostname} after unexpected removal')
            this_inst.local_health_check()
        else:
            logger.error("Cluster Host Not Found: {}".format(settings.CLUSTER_HOST_ID))
            return None, None, None, None

    if lost_instances and not _mesh_all_ready_nodes_visible(mesh_status):
        # Mesh gate blocks cleanup, but execution and hop nodes can still be reaped
        # (they don't depend on mesh consensus). Defer only control nodes.
        execution_hop_lost = [inst for inst in lost_instances if inst.node_type in ('execution', 'hop')]
        return this_inst, instance_list, execution_hop_lost, ctl

    return this_inst, instance_list, lost_instances, ctl


def _heartbeat_check_versions(this_inst, instance_list):
    """Check versions across instances and determine if shutdown is needed."""
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


def _queue_job_adoption(job_id, source_controller):
    """Publish adopt_job_async for one job and record the resulting task id on it.

    Shared by all three adoption entry points so the published message is byte-identical
    between them: on_duplicate='discard' keys on (task, args, kwargs), and that is what lets
    dispatcherd drop a second submission made before the first message lands. Persisting the
    id matters because the job still carries the uuid of the dispatch task that died, which
    would make it look orphaned to every later heartbeat.
    """
    obj, _unused = adopt_job_async.apply_async(args=[job_id], kwargs={'source_controller': source_controller}, queue=get_task_queuename())
    UnifiedJob.objects.filter(pk=job_id).update(celery_task_id=obj['uuid'])


def _handle_lost_instance_job(j, other_inst):
    """Process a single job from a lost instance: adopt if possible, reap otherwise."""
    adoptable = j.work_unit_id and j.controller_node == other_inst.hostname and j.execution_node != other_inst.hostname
    if not adoptable:
        reaper.reap_job(j, 'failed', job_explanation='Job reaped due to instance shutdown')
        return

    # Take only what we can hold. This loop used to claim every job of the lost controller
    # unconditionally, which is how one pod ended up with all of them: a claim sets
    # controller_node to a live node, and the orphan sweep will not steal from a live node, so
    # nothing could redistribute them afterwards. Declining here leaves the job running and
    # still owned by the dead controller — the sweep's exact predicate — and the Instance row
    # is deleted moments later by our caller, so the peer picks it up on its next heartbeat.
    # Checked before the claim for that reason: claim first and the job is ours for good.
    if not _adoption_slot_available(headroom_needed=settings.AWX_CONTROL_NODE_TASK_IMPACT):
        logger.info(f'Cross-controller adoption deferred for job {j.id}: no control capacity here, leaving it for another controller to sweep')
        return

    failpoint('lost_instance.before_claim', job_id=j.id, lost=other_inst.hostname)
    claimed = UnifiedJob.objects.filter(pk=j.id, controller_node=other_inst.hostname, status='running').update(controller_node=settings.CLUSTER_HOST_ID)
    if not claimed:
        logger.info(f'Cross-controller adoption skipped for job {j.id}: already claimed by another controller')
        return

    try:
        _queue_job_adoption(j.id, settings.CLUSTER_HOST_ID)
        logger.info(f'Cross-controller adoption queued for job {j.id} (unit={j.work_unit_id}) from lost controller {other_inst.hostname}')
    except Exception:
        logger.exception(f'Failed to queue cross-controller adoption for job {j.id}, reaping instead')
        reaper.reap_job(j, 'failed', job_explanation='Job reaped due to instance shutdown')


def _reap_and_mark_lost_instance(other_inst):
    """Reap a lost instance's running jobs and mark it offline (or deprovision it)."""
    try:
        workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
        running_jobs = list(
            UnifiedJob.objects.filter(
                Q(execution_node=other_inst.hostname) | Q(controller_node=other_inst.hostname),
                status='running',
            ).exclude(polymorphic_ctype_id=workflow_ctype_id)
        )
        for j in running_jobs:
            _handle_lost_instance_job(j, other_inst)
        # Any jobs that were waiting to be processed by this node will be handed back to task manager
        UnifiedJob.objects.filter(status='waiting', controller_node=other_inst.hostname).update(status='pending', controller_node='', execution_node='')
    except Exception:
        logger.exception('failed to re-process jobs for lost instance {}'.format(other_inst.hostname))
    try:
        if settings.AWX_AUTO_DEPROVISION_INSTANCES and other_inst.node_type == "control":
            deprovision_hostname = other_inst.hostname
            other_inst.delete()  # FIXME: what about associated inbound links?
            logger.info("Host {} Automatically Deprovisioned.".format(deprovision_hostname))
        elif other_inst.node_state == Instance.States.READY:
            other_inst.mark_offline(errors=_('Another cluster node has determined this instance to be unresponsive'))
            logger.error("Host {} last checked in at {}, marked as lost.".format(other_inst.hostname, other_inst.last_seen))

    except DatabaseError as e:
        cause = e.__cause__
        if cause and hasattr(cause, 'sqlstate'):
            sqlstate = cause.sqlstate
            sqlstate_str = psycopg.errors.lookup(sqlstate)
            logger.debug('SQL Error state: {} - {}'.format(sqlstate, sqlstate_str))

            if sqlstate == psycopg.errors.NoData:
                logger.debug('Another instance has marked {} as lost'.format(other_inst.hostname))
            else:
                logger.exception("Error marking {} as lost.".format(other_inst.hostname))
        else:
            logger.exception('No SQL state available.  Error marking {} as lost'.format(other_inst.hostname))


def _heartbeat_handle_lost_instances(lost_instances, this_inst):
    """Handle lost instances by reaping their running jobs and marking them offline."""
    for other_inst in lost_instances:
        # Serialize offline handling against the task manager so we never reap jobs
        # mid-schedule; if the lock is held, retry this instance on the next heartbeat.
        with advisory_lock('task_manager_lock', wait=False) as acquired:
            if not acquired:
                logger.info(f'task_manager_lock held, deferring offline handling for {other_inst.hostname} to next heartbeat cycle')
                continue
            _reap_and_mark_lost_instance(other_inst)


def _startup_reap_undispatched(hostname):
    """Reap undispatched running jobs at startup using only the hostname — no receptor needed.

    Called unconditionally from _run_dispatch_startup_common so undispatched jobs are always
    reaped, even when cluster_node_heartbeat() returns early (receptor unavailable, rejoining
    cluster). reap_job() is idempotent: jobs already handled by _process_startup_jobs are
    skipped via the running-status check.
    """
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    jobs = list(
        UnifiedJob.objects.filter(
            status='running',
            controller_node=hostname,
        )
        .filter(Q(work_unit_id='') | Q(work_unit_id=None))
        .exclude(polymorphic_ctype_id=workflow_ctype_id)
    )
    job_ids = [j.id for j in jobs]
    for j in jobs:
        reaper.reap_job(
            j,
            'failed',
            job_explanation='Task was marked as running at system start up. The system must have not shut down properly, so it has been marked as failed.',
        )
    if job_ids:
        logger.error(f'Unified jobs {job_ids} were reaped on dispatch startup')


def _process_startup_jobs(this_inst):
    """On controller restart, process all running jobs owned by this instance in one loop.

    Dispatched jobs (work_unit_id set) are handed off to adopt_job_async, which streams
    events in real-time in a background task. Undispatched jobs are reaped immediately.
    """
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    jobs = list(UnifiedJob.objects.filter(status='running', controller_node=this_inst.hostname).exclude(polymorphic_ctype_id=workflow_ctype_id))
    if not jobs:
        return

    reaped_ids = []
    for j in jobs:
        try:
            if j.work_unit_id:
                # Queue adoption. Task will claim ownership atomically when it executes.
                _queue_job_adoption(j.id, this_inst.hostname)
            else:
                reaped_ids.append(j.id)
                reaper.reap_job(
                    j,
                    'failed',
                    job_explanation='Task was marked as running at system start up. The system must have not shut down properly, so it has been marked as failed.',
                )
        except Exception:
            logger.exception(f'Failed processing job {j.id} in startup job loop')
    if reaped_ids:
        logger.error(f'Unified jobs {reaped_ids} were reaped on dispatch startup')


def _process_running_jobs(this_inst, active_task_ids, ref_time):
    """On each heartbeat, process running jobs that dispatcherd is no longer tracking.

    Jobs still in active_task_ids are legitimately running — leave them alone.
    For orphaned jobs (not in active_task_ids):
    - Dispatched and owned by this controller (work_unit_id set, controller_node=this_inst) → adopt_job_async (real-time streaming).
    - Owned by another live controller → defer (let the owner handle it).
    - Undispatched or owned by a lost controller → reap.
    """
    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    base_q = Q(status='running') & (Q(execution_node=this_inst.hostname) | Q(controller_node=this_inst.hostname))
    base_q &= ~Q(polymorphic_ctype_id=workflow_ctype_id)
    if active_task_ids:
        base_q &= ~Q(celery_task_id__in=active_task_ids)
    if ref_time:
        base_q &= Q(started__lte=ref_time)
    jobs = list(UnifiedJob.objects.filter(base_q))
    if not jobs:
        return

    for j in jobs:
        try:
            if j.work_unit_id and j.controller_node == this_inst.hostname:
                # Queue adoption. Task will claim ownership atomically when it executes.
                _queue_job_adoption(j.id, this_inst.hostname)
            elif (
                j.controller_node != this_inst.hostname
                and Instance.objects.filter(
                    hostname=j.controller_node,
                    node_state__in=(Instance.States.READY, Instance.States.INSTALLED),
                ).exists()
            ):
                # Another live controller owns this job; let it handle adoption or reaping
                pass
            else:
                reaper.reap_job(j, 'failed')
        except Exception:
            logger.exception(f'Failed processing job {j.id} in heartbeat job loop')


def _sweep_orphaned_jobs(this_inst):
    """Adopt running jobs whose controller is no longer a live instance.

    The lost-instance path is one-shot and winner-takes-all: the pod that wins
    `task_manager_lock` claims every job of the dead controller, publishes each adoption to
    its *own* queue (get_task_queuename() is this node's hostname), and then deletes the
    Instance row. The peer derives lost instances from that table, so after the delete it is
    not merely slow — it has nothing left to see. And `_process_running_jobs` only considers
    jobs a node already owns, so a job left behind by that single pass matches no path on any
    node and stays `running` forever (observed: job 2068378, orphaned 2026-10-02).

    This sweep keys on job state rather than on the Instance row, which is what makes it a
    reconciler instead of a second claimant. It needs no lock: the claim below is atomic, and
    a successful claim sets controller_node to a *live* instance, which removes the job from
    every other node's sweep. If that owner later dies it stops being live and the job becomes
    sweepable again — the same rule recovers from a failed adopter.

    Capacity is what distributes the work. Each claim is already counted in consumed_capacity,
    so _adoption_slot_available() sees it on the next iteration: this node takes what it can
    hold and leaves the rest owned by the dead controller, where the peer's own sweep will
    find them.
    """
    live_hostnames = Instance.objects.filter(
        node_state__in=(Instance.States.READY, Instance.States.INSTALLED),
    ).values_list('hostname', flat=True)

    workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
    orphans = (
        UnifiedJob.objects.filter(status='running')
        .exclude(work_unit_id='')
        .exclude(controller_node='')
        # An unset controller_node also satisfies "not a live instance", but there may be a
        # window during dispatch where it is unset while the job is already running, and
        # sweeping then would steal live work. The gap is hypothetical; the theft would not be.
        .exclude(controller_node__in=live_hostnames)
        .exclude(polymorphic_ctype_id=workflow_ctype_id)
        .order_by('started')  # longest-stranded first: they are closest to their deadline
        .values_list('pk', 'controller_node')[: settings.HADR_ORPHAN_SWEEP_MAX_PER_HEARTBEAT]
    )

    swept = 0
    for job_id, former_controller in list(orphans):
        try:
            if not _adoption_slot_available():
                logger.info(f'Orphan sweep stopping at {swept} adoptions: out of control capacity, peer or next heartbeat takes the rest')
                break
            failpoint('sweep.before_claim', job_id=job_id, former=former_controller)
            claimed = UnifiedJob.objects.filter(pk=job_id, controller_node=former_controller, status='running').update(controller_node=this_inst.hostname)
            if not claimed:
                # Another node swept it between the query and here, or it just finished.
                continue
            _queue_job_adoption(job_id, this_inst.hostname)
            swept += 1
            logger.warning(f'Orphan sweep adopting job {job_id}: controller {former_controller} is no longer a live instance')
        except Exception:
            # One unadoptable job must not strand every job behind it in the list.
            logger.exception(f'Orphan sweep failed to adopt job {job_id}')

    if swept:
        logger.info(f'Orphan sweep queued {swept} adoption(s) for jobs whose controller is gone')


def _current_namespace():
    return settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE


def _control_pod_is_gone(hostname):
    """Does the Kubernetes pod backing this control instance still exist?

    Returns True only on a definitive 404 for that exact pod name. Anything else — a timeout,
    a 5xx, an unreadable serviceaccount token, a VM install — returns None, meaning "cannot
    tell", and the caller must leave the instance alone.

    The asymmetry is deliberate. Marking a live controller unavailable lets a peer adopt jobs
    it is still streaming; the claim is atomic so that is not corruption, but both nodes would
    stream the same events into the same job. Failing to mark a dead one costs nothing but the
    is_lost() timeout, which is what happens today anyway. Only one of those two mistakes is
    worth avoiding at the price of the other.

    On OpenShift the Instance hostname is the pod name, which is what makes a lookup by name
    possible at all. A read per name is used rather than one list call because a 404 for a
    name we asked about is unambiguous, whereas an empty or mis-selected list is
    indistinguishable from "every peer is gone".
    """
    if not settings.IS_K8S:
        return None

    try:
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException
    except ImportError:
        logger.warning('No kubernetes client available; cannot tell whether departed peers still have pods')
        return None

    try:
        config.load_incluster_config()
        client.CoreV1Api().read_namespaced_pod(name=hostname, namespace=_current_namespace())
    except ApiException as exc:
        if exc.status == 404:
            return True
        logger.warning(f'Could not tell whether pod {hostname} still exists (HTTP {exc.status}); treating it as alive')
        return None
    except Exception:
        logger.warning(f'Could not tell whether pod {hostname} still exists; treating it as alive', exc_info=True)
        return None

    return False


def _startup_mark_departed_peers():
    """Mark control instances whose pod is gone, so their jobs become sweepable now.

    This is the writer of node_state for the case announce_shutdown structurally cannot cover:
    a node SIGKILLed before it could speak for itself — grace period exceeded, `--force
    --grace-period=0`, or a kubelet that stopped delivering signals at all. The replacement
    pod OpenShift schedules is a witness to that death, and until is_lost() times out 120 s
    later it is the only witness the cluster has.

    Only READY and INSTALLED rows are worth probing. An UNAVAILABLE one needs nothing from us,
    and a row already deleted by AWX_AUTO_DEPROVISION_INSTANCES is absent from the live set
    the sweep computes, so its jobs are sweepable without our help. INSTALLED earns its place
    separately: _reap_and_mark_lost_instance only marks offline when node_state is READY, so a
    node that died between registering and showing up on the mesh is marked by no other path.
    """
    try:
        peers = list(
            Instance.objects.filter(
                node_type='control',
                node_state__in=(Instance.States.READY, Instance.States.INSTALLED),
            ).exclude(hostname=settings.CLUSTER_HOST_ID)
        )
    except Exception:
        logger.exception('Could not list peer instances at startup; leaving them to lost-instance detection')
        return

    for peer in peers:
        if _control_pod_is_gone(peer.hostname) is not True:
            continue
        try:
            peer.mark_offline(errors=_('Pod no longer exists; detected by a peer at startup'))
        except Exception:
            # One unmarkable peer must not cost us the others.
            logger.exception(f'Failed to mark departed peer {peer.hostname} offline')
            continue
        logger.warning(f'Marked {peer.hostname} unavailable at startup: its pod no longer exists, so its jobs can be adopted now')


def _startup_sweep_orphaned_jobs():
    """Sweep orphaned jobs at startup, which the heartbeat's startup pass never reaches.

    `cluster_node_heartbeat(None)` returns at its `binder is None` branch, which sits above
    the `_sweep_orphaned_jobs()` call in the periodic path — and `_heartbeat_instance_management()`
    can return earlier still when this node is rejoining the cluster. So a booting pod has
    never once looked for jobs whose controller is already gone.

    That gap is widest when the whole control plane went down together. Each departing node
    marked itself unavailable on the way out (`announce_shutdown`), so its jobs are sweepable
    the moment anything looks — but its peers were leaving too, and the broadcast reached
    nobody. Until the first periodic heartbeat, up to CLUSTER_NODE_HEARTBEAT_PERIOD later,
    there is no one in the cluster whose job it is to look. This is the thing that looks.

    Publishing adoptions from here is safe: `dispatch_startup` runs as an OnStartProducer task
    inside the already-listening service, which is where `_process_startup_jobs` publishes its
    own adoptions from today. Calling it before `run_service()` would not be — the only broker
    is pg_notify, and a NOTIFY with no LISTEN is dropped, which would leave the job claimed by
    a live node with no task to run it and invisible to every later sweep.
    """
    try:
        _sweep_orphaned_jobs(Instance.objects.me())
    except RuntimeError:
        logger.warning('Skipping the startup orphan sweep: this node has no Instance row yet')
    except Exception:
        logger.exception('Startup orphan sweep failed; the next heartbeat will retry')


@task(queue='tower_broadcast_all')
def sweep_orphaned_jobs_now():
    """Run the orphan sweep off a broadcast instead of waiting for the next heartbeat.

    Published by announce_shutdown. Every control node subscribes to tower_broadcast_all, so
    the departing node's peers all sweep at once and share the work by capacity, exactly as
    they would on a heartbeat tick — only without the tick's 0-60 s of schedule jitter.
    """
    try:
        this_inst = Instance.objects.me()
    except RuntimeError:
        logger.warning('Sweep-now broadcast received, but this instance has no Instance row; skipping')
        return

    # The broadcast reaches every subscriber, the sender included. A node that has already
    # marked itself unavailable is on its way out: anything it claimed here would be
    # controlled by a node that is about to stop being live, so the jobs would simply need
    # sweeping again.
    if this_inst.node_state not in (Instance.States.READY, Instance.States.INSTALLED):
        logger.debug(f'Sweep-now broadcast received while {this_inst.node_state}; leaving the sweep to live nodes')
        return

    _sweep_orphaned_jobs(this_inst)


def announce_shutdown():
    """Tell the cluster this node is leaving, rather than letting it time out.

    A graceful shutdown used to be indistinguishable from a crash. Peers learned of a
    departed controller only once `is_lost()` fired, which costs
    CLUSTER_NODE_HEARTBEAT_PERIOD * CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE (120 s) plus up
    to one period of schedule jitter before anyone looks. Its jobs sat `running` and unowned
    for that whole window — the 90-180 s adoption lag measured on hadr-rosa-a.

    None of that wait is inherent. `_sweep_orphaned_jobs` does not gate on `is_lost()`; it
    gates on `node_state`. `is_lost()` is only how that state eventually gets written when
    nobody was around to write it. A node that is shutting down knows the answer already, so
    it writes the state itself and tells its peers to look — one UPDATE and one pg_notify.
    The `is_lost()` path is untouched and still covers the crash case, so this can make
    discovery faster but never slower.

    Call only after every job has detached from its work unit. Marking ourselves unavailable
    while still streaming would let a peer claim a job we have not let go of; the claim is
    atomic so it is not corruption, but both controllers would stream the same events.
    """
    try:
        this_inst = Instance.objects.me()
        this_inst.mark_offline(errors=_('Instance is shutting down'))
        logger.info(f'Announced shutdown of {this_inst.hostname}: marked unavailable so peers can adopt its jobs now')
    except RuntimeError:
        # Our row is already gone — the shape of job 2068378. There is nothing left to mark,
        # but the jobs we controlled are orphaned and no peer knows yet, so the broadcast
        # below is the only thing that can still reach them.
        logger.warning('No Instance row for this node at shutdown; broadcasting the sweep anyway')
    except Exception:
        # Still broadcast: peers that find nothing to do lose a query, whereas a peer that is
        # never told waits out the full is_lost() window.
        logger.exception('Failed to mark this instance offline at shutdown; broadcasting the sweep anyway')

    try:
        sweep_orphaned_jobs_now.apply_async(queue='tower_broadcast_all')
    except Exception:
        # This runs from a `finally` as the process exits. An exception escaping here would
        # replace whatever actually ended the process, which is the one thing an operator
        # needs from the logs. Degrading to the is_lost() timeout is the correct fallback.
        logger.exception('Failed to broadcast the shutdown sweep; peers will fall back to lost-instance detection')


def _adoption_slot_available(headroom_needed=0):
    """Is there room on this controller for one more adoption?

    An adoption is the one dispatcher task that occupies its worker for the whole remaining
    runtime of a job, because it streams that job's events. A controller inheriting a large
    instance's jobs would otherwise fill the pool with adoptions and starve the heartbeat,
    at which point the rest of the cluster declares *this* controller lost too and the
    cascade repeats. Jobs over the bound are simply not adopted this cycle: they stay running
    and claimed by us, so the next heartbeat re-queues them.

    Control capacity is that bound. It already prices exactly this cost — one
    AWX_CONTROL_NODE_TASK_IMPACT per running job we are the controller_node for — and an
    adopted job is controlled by us, so it is already in consumed_capacity. That makes the
    two adoption shapes fall out correctly without a second knob: re-adopting our own jobs
    after a restart is net zero, because those jobs counted against us before we died and
    still do, while inheriting a dead peer's jobs is genuinely new load and is throttled
    against the same number that bounds normally dispatched work. Operators tune it with the
    capacity_adjustment slider they already use.

    The claim (_claim_job_for_adoption) runs before this check, so the job being considered
    is itself counted; remaining_capacity == 0 means it is the one that exactly fills us.
    That is the default, headroom_needed=0.

    Callers that ask *before* claiming pass headroom_needed=AWX_CONTROL_NODE_TASK_IMPACT,
    because their job is not in consumed_capacity yet and a controller sitting at exactly
    capacity would otherwise take one job too many. _handle_lost_instance_job is the one such
    caller: it has to decline rather than claim, so that a job it cannot hold stays owned by
    the dead controller and remains visible to another node's orphan sweep.

    Fails open. A job nobody adopts has nothing left to finalize it, so an unreadable
    instance row is a worse reason to strand one than a full controller is.
    """
    try:
        me = Instance.objects.me()
    except Exception:
        logger.warning('Could not read the control capacity of this instance; proceeding with this adoption', exc_info=True)
        return True

    # Zero capacity means draining or not yet sized by the capacity job, not "no room" —
    # consumed_capacity is not meaningful against it, so do not let it block adoption.
    if not me.capacity:
        return True

    return me.remaining_capacity >= headroom_needed


def _claim_job_for_adoption(job, job_id, source_controller):
    """Claim a job for adoption, handling various ownership scenarios.

    Returns True if the job is claimed (or already ours), False if we should skip.
    """
    if job.controller_node == settings.CLUSTER_HOST_ID:
        logger.debug(f'adopt_job_async: job {job_id} already transitioned to current controller at queue time')
        return True

    if job.controller_node == source_controller:
        updated_count = UnifiedJob.objects.filter(pk=job_id, controller_node=source_controller, status='running').update(
            controller_node=settings.CLUSTER_HOST_ID
        )
        if updated_count == 0:
            logger.info(f'Adoption skipped for job {job_id}: already claimed by another controller')
            return False
        return True

    logger.info(f'Adoption skipped for job {job_id}: belongs to different controller {job.controller_node}')
    return False


@task(queue=get_task_queuename, on_duplicate='discard')
@with_signal_handling
def adopt_job_async(job_id, source_controller=None):
    """Adopt a single orphaned job in a background task, streaming events in real-time.

    Called from _process_startup_jobs, _process_running_jobs, and _reap_and_mark_lost_instance
    via apply_async so the heartbeat returns immediately. on_duplicate='discard' ensures only
    one adoption runs per job across heartbeat cycles.

    Deliberately declared without a task timeout: it runs for as long as the job it is
    streaming, and a job's own timeout is what bounds that. It takes over signal handling for
    the same reason the job runner does — so a shutdown unwinds the stream in an orderly way
    instead of leaving the process-streamer thread blocked on a socket nobody will close.

    Exactly one controller may run the adoption, so ownership is claimed either at queue time
    (_reap_and_mark_lost_instance does it there, to keep the job visible to this controller
    even if the lost instance is deprovisioned before the task runs) or atomically here. That
    is why a job already moved to CLUSTER_HOST_ID is accepted alongside one still carrying
    source_controller.

    Args:
        job_id: UnifiedJob primary key
        source_controller: the controller_node value this job is expected to still carry.
            Every in-tree caller passes its own hostname (== settings.CLUSTER_HOST_ID),
            because _reap_and_mark_lost_instance claims ownership before publishing. It stays
            a parameter so a caller that has *not* pre-claimed can pass the lost controller's
            hostname and get the task-time atomic claim below instead. Defaults to this
            controller so a message published by a pre-AAP-89602 controller during a rolling
            upgrade (args=[job_id] only) still resolves, rather than failing with TypeError
            and stranding the job.
    """
    if source_controller is None:
        source_controller = settings.CLUSTER_HOST_ID

    job = UnifiedJob.objects.filter(id=job_id, status='running').first()
    if not job:
        logger.debug(f'adopt_job_async: job {job_id} is no longer running, skipping')
        return

    if not _claim_job_for_adoption(job, job_id, source_controller):
        return
    failpoint('adoption.after_claim', job_id=job_id)

    # Checked after the claim, not before: the claim is what keeps the job visible to this
    # controller's heartbeat, and without it a deferred job whose original controller is gone
    # would never be re-queued by anyone.
    if not _adoption_slot_available():
        # The deferral has to converge, and not only for this job's sake. The claim above is
        # what makes the job count against control capacity, and the job stays 'running'
        # while deferred, so a job parked here consumes a slot indefinitely and helps keep
        # the controller full — the same condition that parked it. Without a deadline the
        # backlog only ever grows (observed: 570 jobs, still climbing after 100+ minutes).
        # Failing the oldest releases capacity for the rest.
        if _adoption_stall_budget_exhausted(job):
            logger.error(f'Job {job_id} could not be adopted within HADR_JOB_ADOPTION_TIMEOUT while this controller was out of control capacity, failing')
            reaper.reap_job(job, 'failed', job_explanation='Job exceeded HADR_JOB_ADOPTION_TIMEOUT waiting for control capacity to adopt it')
            return
        logger.info(f'Adoption deferred for job {job_id}: this controller is out of control capacity, retrying next heartbeat')
        return

    # Single try/finally so the control socket is closed on every exit path, including
    # the timeout branch below, which returns early.
    receptor_ctl = get_receptor_ctl()
    try:
        # Only an *unreachable* unit times out. Reachability means the status query itself
        # succeeded, not that the state looks alive: an already-adopted unit's response carries
        # no StateName at all, and terminal units (Succeeded/Failed/Cancelled) still hold
        # results to harvest. Gating on the state value would reap both.
        # Pending/Running are reachable like any other answered query, so they are exempt too.
        # orphaned_since is only as fresh as the last persisted event, and a job that legitimately
        # runs for hours between events would look orphaned on that measure. Reaping it would
        # kill a healthy job; its real bound is the EE finishing, which the stream observes.
        try:
            # Local receptor first, remote adopt only if it does not know the unit.
            # Reused in reattach_to_work_unit so adoption never queries the unit twice.
            unit_status = get_adoption_unit_status(receptor_ctl, job)
            # Any successful response means the unit is reachable (Pending, Running, Succeeded, or Already Adopted)
            unit_reachable = True
        except Exception:
            unit_status = None
            unit_reachable = False

        # MAX(created) is only needed to decide the timeout, and JobEvent has no index on
        # created — it heap-fetches every event row for the job. Keep it inside the unreachable
        # branch: reachable jobs are re-queued by every heartbeat while reattach defers them,
        # so computing it up front would rescan the whole event table once a minute per job.
        if not unit_reachable:
            # A container-group job's work unit lived in the dying controller's own EE
            # sidecar, so "unreachable" here means "gone for good" — there is nothing for the
            # receptor path to adopt and waiting out the timeout would only fail the job.
            # Its pod survives in Kubernetes though, and that is recoverable. Deliberately
            # reached only after the receptor attempt fails: while the submitting controller
            # is still alive its unit answers, and reattaching to it keeps the full lifecycle
            # (live streaming, work cancel, release) instead of this recovery subset.
            if job.is_container_group_task:
                from awx.main.tasks.container_groups import adopt_container_group_job

                try:
                    adopt_container_group_job(job, receptor_ctl=receptor_ctl)
                except Exception:
                    logger.exception(f'adopt_job_async: container-group adoption failed for job {job.id}')
                return

            if _adoption_stall_budget_exhausted(job):
                logger.error(f'Job {job.id} (unit={job.work_unit_id}) orphaned for >{settings.HADR_JOB_ADOPTION_TIMEOUT}s, failing')
                # Best effort only: we only get here because the unit is unreachable, so the
                # cancel is expected to fail too. Not worth a traceback. The unit is not leaked —
                # awx_receptor_workunit_reaper releases units for any job outside ACTIVE_STATES,
                # and unlike an inline release it honors RECEPTOR_KEEP_WORK_ON_ERROR for
                # operators who keep failed work for debugging.
                try:
                    receptor_ctl.simple_command(f'work cancel {job.work_unit_id}')
                except Exception as exc:
                    logger.warning(f'Failed to cancel work unit {job.work_unit_id} while timing out job {job.id}: {exc}')
                reaper.reap_job(job, 'failed', job_explanation='Job exceeded HADR_JOB_ADOPTION_TIMEOUT during controller restart')
                return

        try:
            reattach_to_work_unit(job, receptor_ctl, unit_status=unit_status)
        except Exception:
            logger.exception(f'adopt_job_async: adoption failed for job {job.id} (unit={job.work_unit_id})')
    finally:
        try:
            receptor_ctl.close()
        except Exception:
            pass


@task(queue=get_task_queuename, timeout=1800, on_duplicate='queue_one')
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
    try:
        receptor_ctl = get_receptor_ctl()
    except FileNotFoundError:
        logger.info('Receptorctl sockfile not found for workunit reaper, doing nothing')
        return
    try:
        receptor_work_list = receptor_ctl.simple_command("work list")
    except ValueError as exc:
        logger.info(f'Error getting work list for workunit reaper, error: {str(exc)}')
        return

    unit_ids = [id for id in receptor_work_list]
    jobs_with_unreleased_receptor_units = UnifiedJob.objects.filter(work_unit_id__in=unit_ids).exclude(status__in=ACTIVE_STATES)
    if settings.RECEPTOR_KEEP_WORK_ON_ERROR:
        jobs_with_unreleased_receptor_units = jobs_with_unreleased_receptor_units.exclude(status__in=ERROR_STATES)
    for job in jobs_with_unreleased_receptor_units:
        logger.debug(f"{job.log_format} is not active, reaping receptor work unit {job.work_unit_id}")
        receptor_ctl.simple_command(f"work cancel {job.work_unit_id}")
        receptor_ctl.simple_command(f"work release {job.work_unit_id}")

    administrative_workunit_reaper(receptor_work_list)


@task(queue=get_task_queuename, timeout=1800, on_duplicate='queue_one')
def awx_k8s_reaper():
    if not settings.RECEPTOR_RELEASE_WORK:
        return

    from awx.main.scheduler.kubernetes import PodManager  # prevent circular import

    for group in InstanceGroup.objects.filter(is_container_group=True).iterator():
        logger.debug("Checking for orphaned k8s pods for {}.".format(group))
        pods = PodManager.list_active_jobs(group)
        time_cutoff = now() - timedelta(seconds=settings.K8S_POD_REAPER_GRACE_PERIOD)
        reap_job_candidates = UnifiedJob.objects.filter(pk__in=pods.keys(), finished__lte=time_cutoff).exclude(status__in=ACTIVE_STATES)
        if settings.RECEPTOR_KEEP_WORK_ON_ERROR:
            reap_job_candidates = reap_job_candidates.exclude(status__in=ERROR_STATES)
        for job in reap_job_candidates:
            logger.debug('{} is no longer active, reaping orphaned k8s pod'.format(job.log_format))
            try:
                pm = PodManager(job)
                pm.kube_api.delete_namespaced_pod(name=pods[job.id], namespace=pm.namespace, _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT)
            except Exception:
                logger.exception("Failed to delete orphaned pod {} from {}".format(job.log_format, group))


@task(queue=get_task_queuename, timeout=3600 * 5, on_duplicate='discard')
def awx_periodic_scheduler():
    lock_session_timeout_milliseconds = settings.TASK_MANAGER_LOCK_TIMEOUT * 1000
    with advisory_lock('awx_periodic_scheduler_lock', lock_session_timeout_milliseconds=lock_session_timeout_milliseconds, wait=False) as acquired:
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


@task(queue=get_task_queuename, timeout=3600)
def handle_failure_notifications(task_ids):
    """A task-ified version of the method that sends notifications."""
    found_task_ids = set()
    for instance in UnifiedJob.objects.filter(id__in=task_ids):
        found_task_ids.add(instance.id)
        try:
            instance.send_notification_templates('failed')
        except Exception:
            logger.exception(f'Error preparing notifications for task {instance.id}')
    deleted_tasks = set(task_ids) - found_task_ids
    if deleted_tasks:
        logger.warning(f'Could not send notifications for {deleted_tasks} because they were not found in the database')


@task(queue=get_task_queuename, timeout=3600 * 5)
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
        # https://github.com/django/django/blob/eff21d8e7a1cb297aedf1c702668b590a1b618f3/django/db/models/base.py#L1105
        # django raises DatabaseError("Forced update did not affect any rows.")

        # if sqlstate is set then there was a database error and otherwise will re-raise that error
        cause = e.__cause__
        if cause and hasattr(cause, 'sqlstate'):
            sqlstate = cause.sqlstate
            sqlstate_str = psycopg.errors.lookup(sqlstate)
            logger.error('SQL Error state: {} - {}'.format(sqlstate, sqlstate_str))
            raise

        # otherwise
        logger.debug('Exiting duplicate update_inventory_computed_fields task.')


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


@task(queue=get_task_queuename, timeout=3600, on_duplicate='queue_one')
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


def _batched_delete_inventory(inventory, batch_size=500):
    """Delete inventory hosts in batches to avoid high memory usage.

    With ansible facts, loading thousands of hosts at once can use a lot of memory. To avoid
    this, we delete them in batches (of 500).

    Safe to retry after a crash because inventory.pending_deletion
    is already set and each batch is its own transaction.
    """
    from awx.main.models.inventory import Host

    # first delete all hosts in batches
    total_deleted = 0
    while True:
        pks = list(Host.objects.filter(inventory_id=inventory.id).values_list('pk', flat=True)[:batch_size])
        if not pks:
            break
        with transaction.atomic():
            deleted_count, _ = Host.objects.filter(pk__in=pks).delete()
            total_deleted += deleted_count
        logger.debug('Batch-deleted %d hosts from inventory %d (%d total so far)', len(pks), inventory.id, total_deleted)

    # then delete the inventory itself
    inv_id = inventory.id
    inventory.delete()
    logger.info('Batched deletion of inventory %d complete (%d hosts removed)', inv_id, total_deleted)


@task(queue=get_task_queuename, timeout=3600 * 5)
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
            inv = Inventory.objects.get(id=inventory_id)
            _batched_delete_inventory(inv)
            emit_channel_notification('inventories-status_changed', {'group_name': 'inventories', 'inventory_id': inventory_id, 'status': 'deleted'})
            logger.debug('Deleted inventory {} as user {}.'.format(inventory_id, user_id))
        except Inventory.DoesNotExist:
            logger.warning("Delete Inventory failed due to missing inventory: " + str(inventory_id))
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


@task(queue=get_task_queuename, timeout=600)
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


@task(queue=get_task_queuename, timeout=3600, on_duplicate='discard')
def periodic_resource_sync():
    if not getattr(settings, 'RESOURCE_SERVER', None):
        logger.debug("Skipping periodic resource_sync, RESOURCE_SERVER not configured")
        return

    with advisory_lock('periodic_resource_sync', wait=False) as acquired:
        if acquired is False:
            logger.debug("Not running periodic_resource_sync, another task holds lock")
            return
        logger.debug("Running periodic resource sync")

        executor = SyncExecutor()
        executor.run()
        for key, item_list in executor.results.items():
            if not item_list or key == 'noop':
                continue
            # Log creations and conflicts
            if len(item_list) > 10 and settings.LOG_AGGREGATOR_LEVEL != 'DEBUG':
                logger.info(f'Periodic resource sync {key}, first 10 items:\n{item_list[:10]}')
            else:
                logger.info(f'Periodic resource sync {key}:\n{item_list}')
