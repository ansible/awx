import pytest

from prometheus_client.parser import text_string_to_metric_families
from awx.main import models
from awx.main.analytics.metrics import metrics

EXPECTED_VALUES = {
    'awx_system_info':1.0,
    'awx_organizations_total':1.0,
    'awx_users_total':1.0,
    'awx_teams_total':1.0,
    'awx_inventories_total':1.0,
    'awx_projects_total':1.0,
    'awx_job_templates_total':1.0,
    'awx_workflow_job_templates_total':1.0,
    'awx_hosts_total':1.0,
    'awx_hosts_total':1.0,
    'awx_schedules_total':1.0,
    'awx_inventory_scripts_total':1.0,
    'awx_sessions_total':0.0,
    'awx_sessions_total':0.0,
    'awx_sessions_total':0.0,
    'awx_custom_virtualenvs_total':0.0,
    'awx_running_jobs_total':0.0,
    'awx_instance_capacity':100.0,
    'awx_instance_cpu':0.0,
    'awx_instance_memory':0.0,
    'awx_instance_info':1.0,
}


@pytest.mark.django_db
def test_metrics_counts(organization_factory, job_template_factory, workflow_job_template_factory):
    objs = organization_factory('org', superusers=['admin'])
    jt = job_template_factory(
        'test', organization=objs.organization,
        inventory='test_inv', project='test_project',
        credential='test_cred'
    )
    workflow_job_template_factory('test')
    models.Team(organization=objs.organization).save()
    models.Host(inventory=jt.inventory).save()
    models.Schedule(
        rrule='DTSTART;TZID=America/New_York:20300504T150000',
        unified_job_template=jt.job_template
    ).save()
    models.CustomInventoryScript(organization=objs.organization).save()

    output = metrics()
    gauges = text_string_to_metric_families(output.decode('UTF-8'))

    for gauge in gauges:
        for sample in gauge.samples:
            # name, label, value, timestamp, exemplar
            name, _, value, _, _ = sample
            assert EXPECTED_VALUES[name] == value
