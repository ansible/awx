import io
import json
import os
import os.path
import platform
import distro

from django.db import connection
from django.db.models import Count
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext_lazy as _

from awx.conf.license import get_license
from awx.main.utils import get_awx_version, camelcase_to_underscore, datetime_hook
from awx.main import models
from awx.main.analytics import register
from awx.main.scheduler.task_manager_models import TaskManagerInstances

"""
This module is used to define metrics collected by awx.main.analytics.gather()
Each function is decorated with a key name, and should return a data
structure that can be serialized to JSON

@register('something', '1.0')
def something(since):
    # the generated archive will contain a `something.json` w/ this JSON
    return {'some': 'json'}

All functions - when called - will be passed a datetime.datetime object,
`since`, which represents the last time analytics were gathered (some metrics
functions - like those that return metadata about playbook runs, may return
data _since_ the last report date - i.e., new data in the last 24 hours)
"""


def trivial_slicing(key, since, until, last_gather):
    if since is not None:
        return [(since, until)]

    from awx.conf.models import Setting

    horizon = until - timedelta(weeks=4)
    last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
    last_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}', object_hook=datetime_hook)
    last_entry = max(last_entries.get(key) or last_gather, horizon)
    return [(last_entry, until)]


def four_hour_slicing(key, since, until, last_gather):
    if since is not None:
        last_entry = since
    else:
        from awx.conf.models import Setting

        horizon = until - timedelta(weeks=4)
        last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
        last_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}', object_hook=datetime_hook)
        try:
            last_entry = max(last_entries.get(key) or last_gather, horizon)
        except TypeError:  # last_entries has a stale non-datetime entry for this collector
            last_entry = max(last_gather, horizon)

    start, end = last_entry, None
    while start < until:
        end = min(start + timedelta(hours=4), until)
        yield (start, end)
        start = end


def _identify_lower(key, since, until, last_gather):
    from awx.conf.models import Setting

    last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
    last_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}', object_hook=datetime_hook)
    horizon = until - timedelta(weeks=4)

    lower = since or last_gather
    if not since and last_entries.get(key):
        lower = horizon

    return lower, last_entries


@register('config', '1.4', description=_('General platform configuration.'))
def config(since, **kwargs):
    license_info = get_license()
    install_type = 'traditional'
    if os.environ.get('container') == 'oci':
        install_type = 'openshift'
    elif 'KUBERNETES_SERVICE_PORT' in os.environ:
        install_type = 'k8s'
    return {
        'platform': {
            'system': platform.system(),
            'dist': distro.linux_distribution(),
            'release': platform.release(),
            'type': install_type,
        },
        'install_uuid': settings.INSTALL_UUID,
        'instance_uuid': settings.SYSTEM_UUID,
        'tower_url_base': settings.TOWER_URL_BASE,
        'tower_version': get_awx_version(),
        'license_type': license_info.get('license_type', 'UNLICENSED'),
        'license_date': license_info.get('license_date'),
        'subscription_name': license_info.get('subscription_name'),
        'sku': license_info.get('sku'),
        'support_level': license_info.get('support_level'),
        'product_name': license_info.get('product_name'),
        'valid_key': license_info.get('valid_key'),
        'satellite': license_info.get('satellite'),
        'pool_id': license_info.get('pool_id'),
        'current_instances': license_info.get('current_instances'),
        'automated_instances': license_info.get('automated_instances'),
        'automated_since': license_info.get('automated_since'),
        'trial': license_info.get('trial'),
        'grace_period_remaining': license_info.get('grace_period_remaining'),
        'compliant': license_info.get('compliant'),
        'date_warning': license_info.get('date_warning'),
        'date_expired': license_info.get('date_expired'),
        'free_instances': license_info.get('free_instances', 0),
        'total_licensed_instances': license_info.get('instance_count', 0),
        'license_expiry': license_info.get('time_remaining', 0),
        'pendo_tracking': settings.PENDO_TRACKING_STATE,
        'authentication_backends': settings.AUTHENTICATION_BACKENDS,
        'logging_aggregators': settings.LOG_AGGREGATOR_LOGGERS,
        'external_logger_enabled': settings.LOG_AGGREGATOR_ENABLED,
        'external_logger_type': getattr(settings, 'LOG_AGGREGATOR_TYPE', None),
    }


@register('counts', '1.2', description=_('Counts of objects such as organizations, inventories, and projects'))
def counts(since, **kwargs):
    counts = {}
    for cls in (
        models.Organization,
        models.Team,
        models.User,
        models.Inventory,
        models.Credential,
        models.Project,
        models.JobTemplate,
        models.WorkflowJobTemplate,
        models.Host,
        models.Schedule,
        models.NotificationTemplate,
    ):
        counts[camelcase_to_underscore(cls.__name__)] = cls.objects.count()

    inv_counts = dict(models.Inventory.objects.order_by().values_list('kind').annotate(Count('kind')))
    inv_counts['normal'] = inv_counts.get('', 0)
    inv_counts.pop('', None)
    inv_counts['smart'] = inv_counts.get('smart', 0)
    counts['inventories'] = inv_counts

    counts['unified_job'] = models.UnifiedJob.objects.exclude(launch_type='sync').count()  # excludes implicit project_updates
    counts['active_host_count'] = models.Host.objects.active_count()
    active_sessions = Session.objects.filter(expire_date__gte=now()).count()
    active_user_sessions = models.UserSessionMembership.objects.select_related('session').filter(session__expire_date__gte=now()).count()
    active_anonymous_sessions = active_sessions - active_user_sessions
    counts['active_sessions'] = active_sessions
    counts['active_user_sessions'] = active_user_sessions
    counts['active_anonymous_sessions'] = active_anonymous_sessions
    counts['running_jobs'] = (
        models.UnifiedJob.objects.exclude(launch_type='sync')
        .filter(
            status__in=(
                'running',
                'waiting',
            )
        )
        .count()
    )
    counts['pending_jobs'] = models.UnifiedJob.objects.exclude(launch_type='sync').filter(status__in=('pending',)).count()
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute(f"select count(*) from pg_stat_activity where datname=\'{connection.settings_dict['NAME']}\'")
            counts['database_connections'] = cursor.fetchone()[0]
    else:
        # We should be using postgresql, but if we do that change that ever we should change the below value
        counts['database_connections'] = 1
    return counts


@register('org_counts', '1.0', description=_('Counts of users and teams by organization'))
def org_counts(since, **kwargs):
    counts = {}
    for org in models.Organization.objects.annotate(num_users=Count('member_role__members', distinct=True), num_teams=Count('teams', distinct=True)).values(
        'name', 'id', 'num_users', 'num_teams'
    ):
        counts[org['id']] = {'name': org['name'], 'users': org['num_users'], 'teams': org['num_teams']}
    return counts


@register('cred_type_counts', '1.0', description=_('Counts of credentials by credential type'))
def cred_type_counts(since, **kwargs):
    counts = {}
    for cred_type in models.CredentialType.objects.annotate(num_credentials=Count('credentials', distinct=True)).values(
        'name', 'id', 'managed', 'num_credentials'
    ):
        counts[cred_type['id']] = {
            'name': cred_type['name'],
            'credential_count': cred_type['num_credentials'],
            'managed': cred_type['managed'],
        }
    return counts


@register('inventory_counts', '1.2', description=_('Inventories, their inventory sources, and host counts'))
def inventory_counts(since, **kwargs):
    counts = {}
    for inv in (
        models.Inventory.objects.filter(kind='')
        .annotate(num_sources=Count('inventory_sources', distinct=True), num_hosts=Count('hosts', distinct=True))
        .only('id', 'name', 'kind')
    ):
        source_list = []
        for source in inv.inventory_sources.filter().annotate(num_hosts=Count('hosts', distinct=True)).values('name', 'source', 'num_hosts'):
            source_list.append(source)
        counts[inv.id] = {'name': inv.name, 'kind': inv.kind, 'hosts': inv.num_hosts, 'sources': inv.num_sources, 'source_list': source_list}

    for smart_inv in models.Inventory.objects.filter(kind='smart'):
        counts[smart_inv.id] = {'name': smart_inv.name, 'kind': smart_inv.kind, 'hosts': smart_inv.hosts.count(), 'sources': 0, 'source_list': []}
    return counts


@register('projects_by_scm_type', '1.0', description=_('Counts of projects by source control type'))
def projects_by_scm_type(since, **kwargs):
    counts = dict((t[0] or 'manual', 0) for t in models.Project.SCM_TYPE_CHOICES)
    for result in models.Project.objects.values('scm_type').annotate(count=Count('scm_type')).order_by('scm_type'):
        counts[result['scm_type'] or 'manual'] = result['count']
    return counts


@register('instance_info', '1.2', description=_('Cluster topology and capacity'))
def instance_info(since, include_hostnames=False, **kwargs):
    info = {}
    # Use same method that the TaskManager does to compute consumed capacity without querying all running jobs for each Instance
    active_tasks = models.UnifiedJob.objects.filter(status__in=['running', 'waiting']).only('task_impact', 'controller_node', 'execution_node')
    tm_instances = TaskManagerInstances(
        active_tasks, instance_fields=['uuid', 'version', 'capacity', 'cpu', 'memory', 'managed_by_policy', 'enabled', 'node_type']
    )
    for tm_instance in tm_instances.instances_by_hostname.values():
        instance = tm_instance.obj
        instance_info = {
            'uuid': instance.uuid,
            'version': instance.version,
            'capacity': instance.capacity,
            'cpu': instance.cpu,
            'memory': instance.memory,
            'managed_by_policy': instance.managed_by_policy,
            'enabled': instance.enabled,
            'consumed_capacity': tm_instance.consumed_capacity,
            'remaining_capacity': instance.capacity - tm_instance.consumed_capacity,
            'node_type': instance.node_type,
        }
        if include_hostnames is True:
            instance_info['hostname'] = instance.hostname
        info[instance.uuid] = instance_info
    return info


def job_counts(since, **kwargs):
    counts = {}
    counts['total_jobs'] = models.UnifiedJob.objects.exclude(launch_type='sync').count()
    counts['status'] = dict(models.UnifiedJob.objects.exclude(launch_type='sync').values_list('status').annotate(Count('status')).order_by())
    counts['launch_type'] = dict(models.UnifiedJob.objects.exclude(launch_type='sync').values_list('launch_type').annotate(Count('launch_type')).order_by())
    return counts


def job_instance_counts(since, **kwargs):
    counts = {}
    job_types = (
        models.UnifiedJob.objects.exclude(launch_type='sync')
        .values_list('execution_node', 'launch_type')
        .annotate(job_launch_type=Count('launch_type'))
        .order_by()
    )
    for job in job_types:
        counts.setdefault(job[0], {}).setdefault('launch_type', {})[job[1]] = job[2]

    job_statuses = models.UnifiedJob.objects.exclude(launch_type='sync').values_list('execution_node', 'status').annotate(job_status=Count('status')).order_by()
    for job in job_statuses:
        counts.setdefault(job[0], {}).setdefault('status', {})[job[1]] = job[2]
    return counts


@register('query_info', '1.0', description=_('Metadata about the analytics collected'))
def query_info(since, collection_type, until, **kwargs):
    query_info = {}
    query_info['last_run'] = str(since)
    query_info['current_time'] = str(until)
    query_info['collection_type'] = collection_type
    return query_info


'''
The event table can be *very* large, and we have a 100MB upload limit.

Split large table dumps at dump time into a series of files.
'''
MAX_TABLE_SIZE = 200 * 1048576


class FileSplitter(io.StringIO):
    def __init__(self, filespec=None, *args, **kwargs):
        self.filespec = filespec
        self.files = []
        self.currentfile = None
        self.header = None
        self.counter = 0
        self.cycle_file()

    def cycle_file(self):
        if self.currentfile:
            self.currentfile.close()
        self.counter = 0
        fname = '{}_split{}'.format(self.filespec, len(self.files))
        self.currentfile = open(fname, 'w', encoding='utf-8')
        self.files.append(fname)
        if self.header:
            self.currentfile.write('{}\n'.format(self.header))

    def file_list(self):
        self.currentfile.close()
        # Check for an empty dump
        if len(self.header) + 1 == self.counter:
            os.remove(self.files[-1])
            self.files = self.files[:-1]
        # If we only have one file, remove the suffix
        if len(self.files) == 1:
            filename = self.files.pop()
            new_filename = filename.replace('_split0', '')
            os.rename(filename, new_filename)
            self.files.append(new_filename)
        return self.files

    def write(self, s):
        if not self.header:
            self.header = s[: s.index('\n')]
        self.counter += self.currentfile.write(s)
        if self.counter >= MAX_TABLE_SIZE:
            self.cycle_file()


def _copy_table(table, query, path):
    file_path = os.path.join(path, table + '_table.csv')
    file = FileSplitter(filespec=file_path)
    with connection.cursor() as cursor:
        cursor.copy_expert(query, file)
    return file.file_list()


def _events_table(since, full_path, until, tbl, where_column, project_job_created=False, **kwargs):
    def query(event_data):
        query = f'''COPY (SELECT {tbl}.id,
                          {tbl}.created,
                          {tbl}.modified,
                          {tbl + '.job_created' if project_job_created else 'NULL'} as job_created,
                          {tbl}.uuid,
                          {tbl}.parent_uuid,
                          {tbl}.event,
                          task_action,
                          resolved_action,
                          resolved_role,
                          -- '-' operator listed here:
                          -- https://www.postgresql.org/docs/12/functions-json.html
                          -- note that operator is only supported by jsonb objects
                          -- https://www.postgresql.org/docs/current/datatype-json.html
                          (CASE WHEN event = 'playbook_on_stats' THEN {event_data} - 'artifact_data' END) as playbook_on_stats,
                          {tbl}.failed,
                          {tbl}.changed,
                          {tbl}.playbook,
                          {tbl}.play,
                          {tbl}.task,
                          {tbl}.role,
                          {tbl}.job_id,
                          {tbl}.host_id,
                          {tbl}.host_name,
                          CAST(x.start AS TIMESTAMP WITH TIME ZONE) AS start,
                          CAST(x.end AS TIMESTAMP WITH TIME ZONE) AS end,
                          x.duration AS duration,
                          x.res->'warnings' AS warnings,
                          x.res->'deprecations' AS deprecations
                          FROM {tbl}, jsonb_to_record({event_data}) AS x("res" json, "duration" text, "task_action" text, "resolved_action" text, "resolved_role" text, "start" text, "end" text)
                          WHERE ({tbl}.{where_column} > '{since.isoformat()}' AND {tbl}.{where_column} <= '{until.isoformat()}')) TO STDOUT WITH CSV HEADER'''
        return query

    return _copy_table(table='events', query=query(fr"replace({tbl}.event_data, '\u', '\u005cu')::jsonb"), path=full_path)


@register('events_table', '1.5', format='csv', description=_('Automation task records'), expensive=four_hour_slicing)
def events_table_unpartitioned(since, full_path, until, **kwargs):
    return _events_table(since, full_path, until, '_unpartitioned_main_jobevent', 'created', **kwargs)


@register('events_table', '1.5', format='csv', description=_('Automation task records'), expensive=four_hour_slicing)
def events_table_partitioned_modified(since, full_path, until, **kwargs):
    return _events_table(since, full_path, until, 'main_jobevent', 'modified', project_job_created=True, **kwargs)


@register('unified_jobs_table', '1.4', format='csv', description=_('Data on jobs run'), expensive=four_hour_slicing)
def unified_jobs_table(since, full_path, until, **kwargs):
    unified_job_query = '''COPY (SELECT main_unifiedjob.id,
                                 main_unifiedjob.polymorphic_ctype_id,
                                 django_content_type.model,
                                 main_unifiedjob.organization_id,
                                 main_organization.name as organization_name,
                                 main_executionenvironment.image as execution_environment_image,
                                 main_job.inventory_id,
                                 main_inventory.name as inventory_name,
                                 main_unifiedjob.created,
                                 main_unifiedjob.name,
                                 main_unifiedjob.unified_job_template_id,
                                 main_unifiedjob.launch_type,
                                 main_unifiedjob.schedule_id,
                                 main_unifiedjob.execution_node,
                                 main_unifiedjob.controller_node,
                                 main_unifiedjob.cancel_flag,
                                 main_unifiedjob.status,
                                 main_unifiedjob.failed,
                                 main_unifiedjob.started,
                                 main_unifiedjob.finished,
                                 main_unifiedjob.elapsed,
                                 main_unifiedjob.job_explanation,
                                 main_unifiedjob.instance_group_id,
                                 main_unifiedjob.installed_collections,
                                 main_unifiedjob.ansible_version,
                                 main_job.forks
                                 FROM main_unifiedjob
                                 JOIN django_content_type ON main_unifiedjob.polymorphic_ctype_id = django_content_type.id
                                 LEFT JOIN main_job ON main_unifiedjob.id = main_job.unifiedjob_ptr_id
                                 LEFT JOIN main_inventory ON main_job.inventory_id = main_inventory.id
                                 LEFT JOIN main_organization ON main_organization.id = main_unifiedjob.organization_id
                                 LEFT JOIN main_executionenvironment ON main_executionenvironment.id = main_unifiedjob.execution_environment_id
                                 WHERE ((main_unifiedjob.created > '{0}' AND main_unifiedjob.created <= '{1}')
                                       OR (main_unifiedjob.finished > '{0}' AND main_unifiedjob.finished <= '{1}'))
                                       AND main_unifiedjob.launch_type != 'sync'
                                 ORDER BY main_unifiedjob.id ASC) TO STDOUT WITH CSV HEADER
                        '''.format(
        since.isoformat(), until.isoformat()
    )
    return _copy_table(table='unified_jobs', query=unified_job_query, path=full_path)


@register('unified_job_template_table', '1.1', format='csv', description=_('Data on job templates'))
def unified_job_template_table(since, full_path, **kwargs):
    unified_job_template_query = '''COPY (SELECT main_unifiedjobtemplate.id,
                                 main_unifiedjobtemplate.polymorphic_ctype_id,
                                 django_content_type.model,
                                 main_executionenvironment.image as execution_environment_image,
                                 main_unifiedjobtemplate.created,
                                 main_unifiedjobtemplate.modified,
                                 main_unifiedjobtemplate.created_by_id,
                                 main_unifiedjobtemplate.modified_by_id,
                                 main_unifiedjobtemplate.name,
                                 main_unifiedjobtemplate.current_job_id,
                                 main_unifiedjobtemplate.last_job_id,
                                 main_unifiedjobtemplate.last_job_failed,
                                 main_unifiedjobtemplate.last_job_run,
                                 main_unifiedjobtemplate.next_job_run,
                                 main_unifiedjobtemplate.next_schedule_id,
                                 main_unifiedjobtemplate.status
                                 FROM main_unifiedjobtemplate
                                 LEFT JOIN main_executionenvironment ON main_executionenvironment.id = main_unifiedjobtemplate.execution_environment_id, django_content_type
                                 WHERE main_unifiedjobtemplate.polymorphic_ctype_id = django_content_type.id
                                 ORDER BY main_unifiedjobtemplate.id ASC) TO STDOUT WITH CSV HEADER'''
    return _copy_table(table='unified_job_template', query=unified_job_template_query, path=full_path)


@register('workflow_job_node_table', '1.0', format='csv', description=_('Data on workflow runs'), expensive=four_hour_slicing)
def workflow_job_node_table(since, full_path, until, **kwargs):
    workflow_job_node_query = '''COPY (SELECT main_workflowjobnode.id,
                                 main_workflowjobnode.created,
                                 main_workflowjobnode.modified,
                                 main_workflowjobnode.job_id,
                                 main_workflowjobnode.unified_job_template_id,
                                 main_workflowjobnode.workflow_job_id,
                                 main_workflowjobnode.inventory_id,
                                 success_nodes.nodes AS success_nodes,
                                 failure_nodes.nodes AS failure_nodes,
                                 always_nodes.nodes AS always_nodes,
                                 main_workflowjobnode.do_not_run,
                                 main_workflowjobnode.all_parents_must_converge
                                 FROM main_workflowjobnode
                                 LEFT JOIN (
                                     SELECT from_workflowjobnode_id, ARRAY_AGG(to_workflowjobnode_id) AS nodes
                                     FROM main_workflowjobnode_success_nodes
                                     GROUP BY from_workflowjobnode_id
                                 ) success_nodes ON main_workflowjobnode.id = success_nodes.from_workflowjobnode_id
                                 LEFT JOIN (
                                     SELECT from_workflowjobnode_id, ARRAY_AGG(to_workflowjobnode_id) AS nodes
                                     FROM main_workflowjobnode_failure_nodes
                                     GROUP BY from_workflowjobnode_id
                                 ) failure_nodes ON main_workflowjobnode.id = failure_nodes.from_workflowjobnode_id
                                 LEFT JOIN (
                                     SELECT from_workflowjobnode_id, ARRAY_AGG(to_workflowjobnode_id) AS nodes
                                     FROM main_workflowjobnode_always_nodes
                                     GROUP BY from_workflowjobnode_id
                                 ) always_nodes ON main_workflowjobnode.id = always_nodes.from_workflowjobnode_id
                                 WHERE (main_workflowjobnode.modified > '{}' AND main_workflowjobnode.modified <= '{}')
                                 ORDER BY main_workflowjobnode.id ASC) TO STDOUT WITH CSV HEADER
                              '''.format(
        since.isoformat(), until.isoformat()
    )
    return _copy_table(table='workflow_job_node', query=workflow_job_node_query, path=full_path)


@register('workflow_job_template_node_table', '1.0', format='csv', description=_('Data on workflows'))
def workflow_job_template_node_table(since, full_path, **kwargs):
    workflow_job_template_node_query = '''COPY (SELECT main_workflowjobtemplatenode.id,
                                 main_workflowjobtemplatenode.created,
                                 main_workflowjobtemplatenode.modified,
                                 main_workflowjobtemplatenode.unified_job_template_id,
                                 main_workflowjobtemplatenode.workflow_job_template_id,
                                 main_workflowjobtemplatenode.inventory_id,
                                 success_nodes.nodes AS success_nodes,
                                 failure_nodes.nodes AS failure_nodes,
                                 always_nodes.nodes AS always_nodes,
                                 main_workflowjobtemplatenode.all_parents_must_converge
                                 FROM main_workflowjobtemplatenode
                                 LEFT JOIN (
                                     SELECT from_workflowjobtemplatenode_id, ARRAY_AGG(to_workflowjobtemplatenode_id) AS nodes
                                     FROM main_workflowjobtemplatenode_success_nodes
                                     GROUP BY from_workflowjobtemplatenode_id
                                 ) success_nodes ON main_workflowjobtemplatenode.id = success_nodes.from_workflowjobtemplatenode_id
                                 LEFT JOIN (
                                     SELECT from_workflowjobtemplatenode_id, ARRAY_AGG(to_workflowjobtemplatenode_id) AS nodes
                                     FROM main_workflowjobtemplatenode_failure_nodes
                                     GROUP BY from_workflowjobtemplatenode_id
                                 ) failure_nodes ON main_workflowjobtemplatenode.id = failure_nodes.from_workflowjobtemplatenode_id
                                 LEFT JOIN (
                                     SELECT from_workflowjobtemplatenode_id, ARRAY_AGG(to_workflowjobtemplatenode_id) AS nodes
                                     FROM main_workflowjobtemplatenode_always_nodes
                                     GROUP BY from_workflowjobtemplatenode_id
                                 ) always_nodes ON main_workflowjobtemplatenode.id = always_nodes.from_workflowjobtemplatenode_id
                                 ORDER BY main_workflowjobtemplatenode.id ASC) TO STDOUT WITH CSV HEADER'''
    return _copy_table(table='workflow_job_template_node', query=workflow_job_template_node_query, path=full_path)
