"""Register django-ansible-base ORM bypass caller attribution for AWX."""

from collections.abc import Iterable

from django.db.models import Model

from ansible_base.lib.utils.bulk_validation_audit import (
    _log_bulk_violation,
    audit_bulk_model_instances,
)
from ansible_base.lib.utils.validation_signals import (
    _get_caller_info,
    _get_text_fields,
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


def _audited_text_field_names(model: type[Model]) -> frozenset[str]:
    protected = _protected_models.get(model)
    if protected is None:
        return frozenset()
    _, excluded_fields = protected
    text_fields, _json_fields = _get_text_fields(model)
    return frozenset(field_name for field_name in text_fields if field_name not in excluded_fields)


def audit_bulk_update_instances(instances: Iterable[Model], fields: Iterable[str]) -> None:
    """Log Tier 1/2 violations for instances about to be bulk-updated (non-blocking).

    Only fields named in ``fields`` that are registered Char/Text columns are checked,
    so callers updating JSON or non-text columns (e.g. Host ``ansible_facts``) are not
    scanned for unrelated text on the in-memory instance.
    """
    update_fields = frozenset(fields)
    if not update_fields or not instances:
        return
    caller_info = _get_caller_info()
    for instance in instances:
        target_fields = update_fields & _audited_text_field_names(type(instance))
        if not target_fields:
            continue
        protected = _protected_models.get(type(instance))
        if protected is None:
            continue
        name_fields, excluded_fields = protected
        resource_type = f"{instance._meta.app_label}.{instance._meta.object_name}"
        for field_name in target_fields:
            if field_name in excluded_fields:
                continue
            value = getattr(instance, field_name, None)
            if value is None or not isinstance(value, str):
                continue
            violation = _validate_field(field_name, value, name_fields)
            if violation:
                tier, reason = violation
                _log_bulk_violation('bulk_update', field_name, resource_type, tier, caller_info, reason)
