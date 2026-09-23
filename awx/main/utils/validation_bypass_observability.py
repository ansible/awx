"""Register django-ansible-base ORM bypass caller attribution for AWX."""

from collections.abc import Iterable

from django.db.models import Model

from ansible_base.lib.utils.bulk_validation_audit import (
    _log_bulk_violation,
    audit_bulk_model_instances,
)
from ansible_base.lib.utils.validation_signals import (
    _get_caller_info,
    _protected_models,
    _validate_field,
    extend_caller_allowlist_prefixes,
    extend_internal_caller_prefixes,
    register_validation_signals,
)

# Tier 2 prompt fields on LaunchTimeConfigBase models; not Django CharFields (AAP-78694).
_WORKFLOW_JOB_NODE_PROMPT_PSEUDO_FIELDS = frozenset({'scm_branch', 'limit', 'job_tags', 'skip_tags'})


def configure_validation_bypass_observability() -> None:
    """Call from AppConfig.ready() so ORM bypass logs show AWX entry points."""
    register_validation_signals()
    extend_caller_allowlist_prefixes(
        [
            "awx.api.views",
            "awx.api.serializers",
            "awx.main.tasks",
            "awx.main.management",
            "awx.main.utils",
        ]
    )
    extend_internal_caller_prefixes(
        [
            "awx.main.models",
            "awx.main.signals",
            "awx.main.dispatch",
        ]
    )


def audit_workflow_job_nodes_for_bulk_create(nodes: Iterable[Model]) -> None:
    """Log Tier 1/2 violations for WorkflowJobNode rows before ``bulk_create``.

    ``audit_bulk_model_instances`` only inspects model ``CharField`` / ``TextField``
    columns. Node prompt values (limit, job_tags, etc.) live in ``char_prompts`` via
    ``NullablePromptPseudoField`` and must be read with ``getattr`` after deferred
    attrs are applied on the in-memory instances.
    """
    audit_bulk_model_instances(nodes, operation='bulk_create')
    if not nodes:
        return
    sample = next(iter(nodes))
    protected = _protected_models.get(type(sample))
    if protected is None:
        return
    name_fields, excluded_fields = protected
    caller_info = _get_caller_info()
    resource_type = f"{sample._meta.app_label}.{sample._meta.object_name}"
    for instance in nodes:
        for field_name in _WORKFLOW_JOB_NODE_PROMPT_PSEUDO_FIELDS:
            if field_name in excluded_fields:
                continue
            value = getattr(instance, field_name, None)
            if value is None or not isinstance(value, str):
                continue
            violation = _validate_field(field_name, value, name_fields)
            if violation:
                tier, reason = violation
                _log_bulk_violation('bulk_create', field_name, resource_type, tier, caller_info, reason)
