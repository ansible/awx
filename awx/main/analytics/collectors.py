import io
import os
import os.path
import platform

from django.db import connection
from django.db.models import Count
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from awx.conf.license import get_license
from awx.main.utils import (get_awx_version, get_ansible_version,
                            get_custom_venv_choices, camelcase_to_underscore)
from awx.main import models
from django.contrib.sessions.models import Session
from awx.main.analytics import register

'''
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
'''


@register('config', '1.2', description=_('General platform configuration.'))
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
            'dist': platform.dist(),
            'release': platform.release(),
            'type': install_type,
        },
        'install_uuid': settings.INSTALL_UUID,
        'instance_uuid': settings.SYSTEM_UUID,
        'tower_url_base': settings.TOWER_URL_BASE,
        'tower_version': get_awx_version(),
        'ansible_version': get_ansible_version(),
        'license_type': license_info.get('license_type', 'UNLICENSED'),
        'free_instances': license_info.get('free_instances', 0),
        'total_licensed_instances': license_info.get('instance_count', 0),
        'license_expiry': license_info.get('time_remaining', 0),
        'pendo_tracking': settings.PENDO_TRACKING_STATE,
        'authentication_backends': settings.AUTHENTICATION_BACKENDS,
        'logging_aggregators': settings.LOG_AGGREGATOR_LOGGERS,
        'external_logger_enabled': settings.LOG_AGGREGATOR_ENABLED,
        'external_logger_type': getattr(settings, 'LOG_AGGREGATOR_TYPE', None),
    }


@register('counts', '1.0', description=_('Counts of objects such as organizations, inventories, and projects'))
def counts(since, **kwargs):
    counts = {}
    for cls in (models.Organization, models.Team, models.User,
                models.Inventory, models.Credential, models.Project,
                models.JobTemplate, models.WorkflowJobTemplate, 
                models.Host, models.Schedule, models.CustomInventoryScript, 
                models.NotificationTemplate):
        counts[camelcase_to_underscore(cls.__name__)] = cls.objects.count()

    venvs = get_custom_venv_choices()
    counts['custom_virtualenvs'] = len([
        v for v in venvs
        if os.path.basename(v.rstrip('/')) != 'ansible'
    ])

    inv_counts = dict(models.Inventory.objects.order_by().values_list('kind').annotate(Count('kind')))
    inv_counts['normal'] = inv_counts.get('', 0)
    inv_counts.pop('', None)
    inv_counts['smart'] = inv_counts.get('smart', 0)
    counts['inventories'] = inv_counts
    
    counts['unified_job'] = models.UnifiedJob.objects.exclude(launch_type='sync').count() # excludes implicit project_updates
    counts['active_host_count'] = models.Host.objects.active_count()   
    active_sessions = Session.objects.filter(expire_date__gte=now()).count()
    active_user_sessions = models.UserSessionMembership.objects.select_related('session').filter(session__expire_date__gte=now()).count()
    active_anonymous_sessions = active_sessions - active_user_sessions
    counts['active_sessions'] = active_sessions
    counts['active_user_sessions'] = active_user_sessions
    counts['active_anonymous_sessions'] = active_anonymous_sessions
    counts['running_jobs'] = models.UnifiedJob.objects.exclude(launch_type='sync').filter(status__in=('running', 'waiting',)).count()
    counts['pending_jobs'] = models.UnifiedJob.objects.exclude(launch_type='sync').filter(status__in=('pending',)).count()
    return counts

    
@register('org_counts', '1.0', description=_('Counts of users and teams by organization'))
def org_counts(since, **kwargs):
    counts = {}
    for org in models.Organization.objects.annotate(num_users=Count('member_role__members', distinct=True), 
                                                    num_teams=Count('teams', distinct=True)).values('name', 'id', 'num_users', 'num_teams'):
        counts[org['id']] = {'name': org['name'],
                             'users': org['num_users'],
                             'teams': org['num_teams']
                             }
    return counts
    
    
@register('cred_type_counts', '1.0', description=_('Counts of credentials by credential type'))
def cred_type_counts(since, **kwargs):
    counts = {}
    for cred_type in models.CredentialType.objects.annotate(num_credentials=Count(
                                                            'credentials', distinct=True)).values('name', 'id', 'managed_by_tower', 'num_credentials'):  
        counts[cred_type['id']] = {'name': cred_type['name'],
                                   'credential_count': cred_type['num_credentials'],
                                   'managed_by_tower': cred_type['managed_by_tower']
                                   }
    return counts
    
    
@register('inventory_counts', '1.2', description=_('Inventories, their inventory sources, and host counts'))
def inventory_counts(since, **kwargs):
    counts = {}
    for inv in models.Inventory.objects.filter(kind='').annotate(num_sources=Count('inventory_sources', distinct=True), 
                                                                 num_hosts=Count('hosts', distinct=True)).only('id', 'name', 'kind'):
        source_list = []
        for source in inv.inventory_sources.filter().annotate(num_hosts=Count('hosts', distinct=True)).values('name','source', 'num_hosts'):
            source_list.append(source)
        counts[inv.id] = {'name': inv.name,
                          'kind': inv.kind,
                          'hosts': inv.num_hosts,
                          'sources': inv.num_sources,
                          'source_list': source_list
                          }

    for smart_inv in models.Inventory.objects.filter(kind='smart'):
        counts[smart_inv.id] = {'name': smart_inv.name,
                                'kind': smart_inv.kind,
                                'hosts': smart_inv.hosts.count(),
                                'sources': 0,
                                'source_list': []
                                }
    return counts


@register('projects_by_scm_type', '1.0', description=_('Counts of projects by source control type'))
def projects_by_scm_type(since, **kwargs):
    counts = dict(
        (t[0] or 'manual', 0)
        for t in models.Project.SCM_TYPE_CHOICES
    )
    for result in models.Project.objects.values('scm_type').annotate(
        count=Count('scm_type')
    ).order_by('scm_type'):
        counts[result['scm_type'] or 'manual'] = result['count']
    return counts


def _get_isolated_datetime(last_check):
    if last_check:
        return last_check.isoformat()
    return last_check


@register('instance_info', '1.0', description=_('Cluster topology and capacity'))
def instance_info(since, include_hostnames=False, **kwargs):
    info = {}
    instances = models.Instance.objects.values_list('hostname').values(
        'uuid', 'version', 'capacity', 'cpu', 'memory', 'managed_by_policy', 'hostname', 'last_isolated_check', 'enabled')
    for instance in instances:
        consumed_capacity = sum(x.task_impact for x in models.UnifiedJob.objects.filter(execution_node=instance['hostname'],
                                status__in=('running', 'waiting')))
        instance_info = {
            'uuid': instance['uuid'],
            'version': instance['version'],
            'capacity': instance['capacity'],
            'cpu': instance['cpu'],
            'memory': instance['memory'],
            'managed_by_policy': instance['managed_by_policy'],
            'last_isolated_check': _get_isolated_datetime(instance['last_isolated_check']),
            'enabled': instance['enabled'],
            'consumed_capacity': consumed_capacity,
            'remaining_capacity': instance['capacity'] - consumed_capacity
        }
        if include_hostnames is True:
            instance_info['hostname'] = instance['hostname']
        info[instance['uuid']] = instance_info
    return info


def job_counts(since, **kwargs):
    counts = {}
    counts['total_jobs'] = models.UnifiedJob.objects.exclude(launch_type='sync').count()
    counts['status'] = dict(models.UnifiedJob.objects.exclude(launch_type='sync').values_list('status').annotate(Count('status')).order_by())
    counts['launch_type'] = dict(models.UnifiedJob.objects.exclude(launch_type='sync').values_list(
        'launch_type').annotate(Count('launch_type')).order_by())
    return counts
    
    
def job_instance_counts(since, **kwargs):
    counts = {}
    job_types = models.UnifiedJob.objects.exclude(launch_type='sync').values_list(
        'execution_node', 'launch_type').annotate(job_launch_type=Count('launch_type')).order_by()
    for job in job_types:
        counts.setdefault(job[0], {}).setdefault('launch_type', {})[job[1]] = job[2]
        
    job_statuses = models.UnifiedJob.objects.exclude(launch_type='sync').values_list(
        'execution_node', 'status').annotate(job_status=Count('status')).order_by()
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
            os.rename(self.files[0],self.files[0].replace('_split0',''))
        return self.files

    def write(self, s):
        if not self.header:
            self.header = s[0:s.index('\n')]
        self.counter += self.currentfile.write(s)
        if self.counter >= MAX_TABLE_SIZE:
            self.cycle_file()


def _copy_table(table, query, path):
    file_path = os.path.join(path, table + '_table.csv')
    file = FileSplitter(filespec=file_path)
    with connection.cursor() as cursor:
        cursor.copy_expert(query, file)
    return file.file_list()


@register('events_table', '1.1', format='csv', description=_('Automation task records'), expensive=True)
def events_table(since, full_path, until, **kwargs):
    events_query = '''COPY (SELECT main_jobevent.id, 
                              main_jobevent.created,
                              main_jobevent.uuid,
                              main_jobevent.parent_uuid,
                              main_jobevent.event, 
                              main_jobevent.event_data::json->'task_action' AS task_action,
                              main_jobevent.failed, 
                              main_jobevent.changed, 
                              main_jobevent.playbook, 
                              main_jobevent.play,
                              main_jobevent.task,
                              main_jobevent.role, 
                              main_jobevent.job_id, 
                              main_jobevent.host_id, 
                              main_jobevent.host_name
                              , CAST(main_jobevent.event_data::json->>'start' AS TIMESTAMP WITH TIME ZONE) AS start,
                              CAST(main_jobevent.event_data::json->>'end' AS TIMESTAMP WITH TIME ZONE) AS end,
                              main_jobevent.event_data::json->'duration' AS duration,
                              main_jobevent.event_data::json->'res'->'warnings' AS warnings,
                              main_jobevent.event_data::json->'res'->'deprecations' AS deprecations
                              FROM main_jobevent 
                              WHERE (main_jobevent.created > '{}' AND main_jobevent.created <= '{}')
                              ORDER BY main_jobevent.id ASC) TO STDOUT WITH CSV HEADER
                   '''.format(since.isoformat(),until.isoformat())
    return _copy_table(table='events', query=events_query, path=full_path)


@register('unified_jobs_table', '1.1', format='csv', description=_('Data on jobs run'), expensive=True)
def unified_jobs_table(since, full_path, until, **kwargs):
    unified_job_query = '''COPY (SELECT main_unifiedjob.id,
                                 main_unifiedjob.polymorphic_ctype_id,
                                 django_content_type.model,
                                 main_unifiedjob.organization_id,
                                 main_organization.name as organization_name,
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
                                 main_unifiedjob.instance_group_id
                                 FROM main_unifiedjob
                                 JOIN django_content_type ON main_unifiedjob.polymorphic_ctype_id = django_content_type.id
                                 LEFT JOIN main_job ON main_unifiedjob.id = main_job.unifiedjob_ptr_id
                                 LEFT JOIN main_inventory ON main_job.inventory_id = main_inventory.id
                                 LEFT JOIN main_organization ON main_organization.id = main_unifiedjob.organization_id
                                 WHERE ((main_unifiedjob.created > '{0}' AND main_unifiedjob.created <= '{1}')
                                       OR (main_unifiedjob.finished > '{0}' AND main_unifiedjob.finished <= '{1}'))
                                       AND main_unifiedjob.launch_type != 'sync'
                                 ORDER BY main_unifiedjob.id ASC) TO STDOUT WITH CSV HEADER
                        '''.format(since.isoformat(),until.isoformat())
    return _copy_table(table='unified_jobs', query=unified_job_query, path=full_path)


@register('unified_job_template_table', '1.0', format='csv', description=_('Data on job templates'))
def unified_job_template_table(since, full_path, **kwargs):
    unified_job_template_query = '''COPY (SELECT main_unifiedjobtemplate.id, 
                                 main_unifiedjobtemplate.polymorphic_ctype_id,
                                 django_content_type.model,
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
                                 FROM main_unifiedjobtemplate, django_content_type
                                 WHERE main_unifiedjobtemplate.polymorphic_ctype_id = django_content_type.id
                                 ORDER BY main_unifiedjobtemplate.id ASC) TO STDOUT WITH CSV HEADER'''  
    return _copy_table(table='unified_job_template', query=unified_job_template_query, path=full_path)


@register('workflow_job_node_table', '1.0', format='csv', description=_('Data on workflow runs'), expensive=True)
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
                              '''.format(since.isoformat(),until.isoformat())
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
