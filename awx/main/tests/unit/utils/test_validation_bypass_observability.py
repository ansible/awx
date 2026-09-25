import logging
from pathlib import Path

import pytest

import awx.api.serializers  # noqa: F401 — register CleanTextMixin models

from ansible_base.lib.utils.bulk_validation_audit import audit_bulk_model_instances

from awx.main.models import Host, Inventory, Job, Organization, WorkflowJob, WorkflowJobNode
from awx.main.utils.db import bulk_update_sorted_by_id
from awx.main.utils.validation_bypass_observability import (
    audit_workflow_job_nodes_for_bulk_create,
    configure_validation_bypass_observability,
)

LOGGER = 'ansible_base.lib.utils.validation_signals'


@pytest.mark.django_db
def test_configure_validation_bypass_observability_wires_dab(mocker):
    mocker.patch('awx.main.utils.validation_bypass_observability.register_validation_signals')
    allow = mocker.patch('awx.main.utils.validation_bypass_observability.extend_caller_allowlist_prefixes')
    deny = mocker.patch('awx.main.utils.validation_bypass_observability.extend_internal_caller_prefixes')

    configure_validation_bypass_observability()

    allow.assert_called_once()
    prefixes = allow.call_args[0][0]
    assert 'awx.api.serializers' in prefixes
    assert 'awx.main.scheduler' in prefixes
    assert 'awx.main.utils' not in prefixes
    deny.assert_called_once()
    internal = deny.call_args[0][0]
    assert 'awx.main.models' in internal
    assert 'awx.main.utils.validation_bypass_observability' in internal
    assert 'awx.main.utils.db' in internal


@pytest.mark.django_db
def test_audit_bulk_model_instances_skips_host_description_when_serializer_already_logged(caplog):
    from ansible_base.lib.utils.validation_signals import (
        get_validation_context_token,
        register_serializer_validation_rejection,
        reset_validation_context,
    )

    org = Organization.objects.create(name='org-bulk-host-dedupe')
    inv = Inventory.objects.create(name='inv-bulk-host-dedupe', organization=org)
    host = Host(name='host-bulk-dedupe', description='<script>x</script>', inventory=inv)
    register_serializer_validation_rejection('main.Host', 'description')
    token = get_validation_context_token()
    try:
        with caplog.at_level(logging.WARNING, logger=LOGGER):
            audit_bulk_model_instances([host], operation='bulk_create')
    finally:
        reset_validation_context(token)
    assert 'ORM bypass' not in caplog.text


@pytest.mark.django_db
def test_audit_bulk_model_instances_logs_host_description_on_bulk_create(caplog):
    org = Organization.objects.create(name='org-bulk-host-audit')
    inv = Inventory.objects.create(name='inv-bulk-host-audit', organization=org)
    host = Host(name='host-bulk', description='<script>x</script>', inventory=inv)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_bulk_model_instances([host], operation='bulk_create')
    assert 'ORM bypass (bulk_create)' in caplog.text
    assert 'description' in caplog.text
    assert 'main.Host' in caplog.text


@pytest.mark.django_db
def test_audit_workflow_job_nodes_skips_when_serializer_already_logged(caplog):
    from ansible_base.lib.utils.validation_signals import register_serializer_validation_rejection

    wfj = WorkflowJob.objects.create(name='wf-audit-limit-dedupe')
    node = WorkflowJobNode(workflow_job=wfj, identifier='wf-node-1')
    node.limit = '<script>x</script>'
    register_serializer_validation_rejection('main.WorkflowJobNode', 'limit')
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_workflow_job_nodes_for_bulk_create([node])
    assert 'ORM bypass' not in caplog.text


@pytest.mark.django_db
def test_audit_workflow_job_nodes_logs_limit_pseudo_field(caplog):
    wfj = WorkflowJob.objects.create(name='wf-audit-limit')
    node = WorkflowJobNode(workflow_job=wfj, identifier='wf-node-1')
    node.limit = '<script>x</script>'
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_workflow_job_nodes_for_bulk_create([node])
    assert 'ORM bypass (bulk_create)' in caplog.text
    assert 'limit' in caplog.text
    assert 'WorkflowJobNode' in caplog.text


@pytest.mark.django_db
def test_audit_workflow_job_nodes_no_op_for_empty_list(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_workflow_job_nodes_for_bulk_create([])
    assert 'ORM bypass' not in caplog.text


@pytest.mark.django_db
def test_audit_bulk_model_instances_logs_registered_text_field_on_bulk_update(caplog):
    job = Job.objects.create(job_explanation='<script>x</script>')
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_bulk_model_instances([job], operation='bulk_update', update_fields=['job_explanation'])
    assert 'ORM bypass (bulk_update)' in caplog.text
    assert 'job_explanation' in caplog.text


@pytest.mark.django_db
def test_audit_bulk_model_instances_skips_unregistered_workflow_job_on_bulk_update(caplog):
    wj = WorkflowJob.objects.create(name='wf-job', job_explanation='<script>x</script>')
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_bulk_model_instances([wj], operation='bulk_update', update_fields=['job_explanation'])
    assert 'ORM bypass (bulk_update)' not in caplog.text


@pytest.mark.django_db
def test_audit_bulk_model_instances_bulk_update_no_op_when_update_fields_empty(caplog):
    job = Job.objects.create(job_explanation='<script>x</script>')
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        audit_bulk_model_instances([job], operation='bulk_update', update_fields=[])
    assert 'ORM bypass (bulk_update)' not in caplog.text


@pytest.mark.django_db
def test_bulk_update_sorted_by_id_skips_audit_when_fields_are_not_text(caplog):
    org = Organization.objects.create(name='org-bulk-update-audit')
    inv = Inventory.objects.create(name='inv-bulk-update-audit', organization=org)
    host = Host.objects.create(name='host-1', description='<script>x</script>', inventory=inv)
    host.ansible_facts = {'k': 'v'}
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        bulk_update_sorted_by_id(Host, [host], fields=['ansible_facts'])
    assert 'ORM bypass (bulk_update)' not in caplog.text


@pytest.mark.django_db
def test_bulk_update_sorted_by_id_audits_text_fields_in_fields_list(caplog):
    org = Organization.objects.create(name='org-bulk-update-desc')
    inv = Inventory.objects.create(name='inv-bulk-update-desc', organization=org)
    host = Host.objects.create(name='host-desc', description='clean', inventory=inv)
    host.description = '<script>x</script>'
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        bulk_update_sorted_by_id(Host, [host], fields=['description'])
    assert 'ORM bypass (bulk_update)' in caplog.text
    assert 'description' in caplog.text


def test_task_manager_audits_before_job_explanation_bulk_update():
    """Regression: scheduler must not bulk_update job_explanation without audit."""
    task_manager_py = Path(__file__).resolve().parents[3] / 'scheduler' / 'task_manager.py'
    source = task_manager_py.read_text()
    audit_marker = "audit_bulk_model_instances(tasks_to_update_job_explanation, operation='bulk_update', update_fields=['job_explanation'])"
    bulk_marker = "UnifiedJob.objects.bulk_update(tasks_to_update_job_explanation, ['job_explanation'])"
    assert audit_marker in source
    assert bulk_marker in source
    assert source.index('audit_bulk_model_instances') < source.index(bulk_marker)


def test_db_bulk_update_sorted_by_id_audits_before_orm_bulk_update():
    """Regression: shared bulk_update helper must audit before Django bulk_update."""
    db_py = Path(__file__).resolve().parents[3] / 'utils' / 'db.py'
    source = db_py.read_text()
    assert "audit_bulk_model_instances(sorted_objects, operation='bulk_update', update_fields=fields)" in source
    assert source.index('audit_bulk_model_instances') < source.index('model.objects.bulk_update')
