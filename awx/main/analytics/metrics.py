import os
from datetime import datetime

from prometheus_client import (
    REGISTRY,
    PROCESS_COLLECTOR,
    PLATFORM_COLLECTOR,
    GC_COLLECTOR,
    Gauge,
    Info,
    generate_latest
)

from django.contrib.sessions.models import Session

# Temporary Imports
from django.db import connection
from django.db.models import Count
from django.conf import settings

from awx.conf.license import get_license
from awx.main.utils import (get_awx_version, get_ansible_version,
                            get_custom_venv_choices)
from awx.main import models
from awx.main.analytics.collectors import (
    counts, 
    instance_info,
    job_instance_counts
    )
from django.contrib.sessions.models import Session
from awx.main.analytics import register


REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(GC_COLLECTOR)


SYSTEM_INFO = Info('awx_system', 'AWX System Information')
ORG_COUNT = Gauge('awx_organizations_total', 'Number of organizations')
USER_COUNT = Gauge('awx_users_total', 'Number of users')
TEAM_COUNT = Gauge('awx_teams_total', 'Number of teams')
INV_COUNT = Gauge('awx_inventories_total', 'Number of inventories')
PROJ_COUNT = Gauge('awx_projects_total', 'Number of projects')
JT_COUNT = Gauge('awx_job_templates_total', 'Number of job templates')
WFJT_COUNT = Gauge('awx_workflow_job_templates_total', 'Number of workflow job templates')
HOST_COUNT = Gauge('awx_hosts_total', 'Number of hosts', ['type',])
SCHEDULE_COUNT = Gauge('awx_schedules_total', 'Number of schedules')
INV_SCRIPT_COUNT = Gauge('awx_inventory_scripts_total', 'Number of invetory scripts')
USER_SESSIONS = Gauge('awx_sessions_total', 'Number of sessions', ['type',])
CUSTOM_VENVS = Gauge('awx_custom_virtualenvs_total', 'Number of virtualenvs')
RUNNING_JOBS = Gauge('awx_running_jobs_total', 'Number of running jobs on the Tower system')

INSTANCE_CAPACITY = Gauge('awx_instance_capacity', 'Capacity of each node in a Tower system', ['type',])
INSTANCE_CPU = Gauge('awx_instance_cpu', 'CPU cores on each node in a Tower system', ['type',])
INSTANCE_MEMORY = Gauge('awx_instance_memory', 'RAM (Kb) on each node in a Tower system', ['type',])
INSTANCE_INFO = Info('awx_instance', 'Info about each node in a Tower system', ['type',])
INSTANCE_LAUNCH_TYPE = Gauge('awx_instance_launch_type_total', 'Type of Job launched', ['node', 'launch_type',])
INSTANCE_STATUS = Gauge('awx_instance_status_total', 'Status of Job launched', ['node', 'status',])


def metrics():
    license_info = get_license(show_key=False)
    SYSTEM_INFO.info({'system_uuid': settings.SYSTEM_UUID,
                      'tower_url_base': settings.TOWER_URL_BASE,
                      'tower_version': get_awx_version(),
                      'ansible_version': get_ansible_version(),
                      'license_type': license_info.get('license_type', 'UNLICENSED'),
                      'free_instances': str(license_info.get('free instances', 0)),
                      'license_expiry': str(license_info.get('time_remaining', 0)),
                      'pendo_tracking': settings.PENDO_TRACKING_STATE,
                      'external_logger_enabled': str(settings.LOG_AGGREGATOR_ENABLED),
                      'external_logger_type': getattr(settings, 'LOG_AGGREGATOR_TYPE', 'None')})

    current_counts = counts(datetime.now())

    ORG_COUNT.set(current_counts['organization'])
    USER_COUNT.set(current_counts['user'])
    TEAM_COUNT.set(current_counts['team'])
    INV_COUNT.set(current_counts['inventory'])
    PROJ_COUNT.set(current_counts['project'])
    JT_COUNT.set(current_counts['job_template'])
    WFJT_COUNT.set(current_counts['workflow_job_template'])

    HOST_COUNT.labels(type='all').set(current_counts['host'])
    HOST_COUNT.labels(type='active').set(current_counts['active_host_count'])

    SCHEDULE_COUNT.set(current_counts['schedule'])
    INV_SCRIPT_COUNT.set(current_counts['custom_inventory_script'])
    CUSTOM_VENVS.set(current_counts['custom_virtualenvs'])

    USER_SESSIONS.labels(type='all').set(current_counts['active_sessions'])
    USER_SESSIONS.labels(type='user').set(current_counts['active_user_sessions'])
    USER_SESSIONS.labels(type='anonymous').set(current_counts['active_anonymous_sessions'])

    RUNNING_JOBS.set(current_counts['running_jobs'])


    instance_data = instance_info(datetime.now())
    for uuid in instance_data:
        INSTANCE_CAPACITY.labels(type=uuid).set(instance_data[uuid]['capacity'])
        INSTANCE_CPU.labels(type=uuid).set(instance_data[uuid]['cpu'])
        INSTANCE_MEMORY.labels(type=uuid).set(instance_data[uuid]['memory'])
        INSTANCE_INFO.labels(type=uuid).info({'enabled': str(instance_data[uuid]['enabled']), 
                                             'last_isolated_check': getattr(instance_data[uuid], 'last_isolated_check', 'None'),
                                             'managed_by_policy': str(instance_data[uuid]['managed_by_policy']),
                                             'version': instance_data[uuid]['version']
                                            })

    instance_data = job_instance_counts(datetime.now())
    for node in instance_data:
        # skipping internal execution node (for system jobs) 
        # TODO: determine if we should exclude execution_node from instance count
        if node == '':
            continue
        types = instance_data[node].get('launch_type', {})
        for launch_type, value in types.items():
            INSTANCE_LAUNCH_TYPE.labels(node=node, launch_type=launch_type).set(value)
        statuses = instance_data[node].get('status', {})
        for status, value in types.items():
            INSTANCE_STATUS.labels(node=node, status=status).set(value)


    return generate_latest()


__all__ = ['metrics']
