"""Register django-ansible-base ORM bypass observability for AWX.

Startup registers DAB ``post_save`` bypass signals and AWX caller prefixes.
Bulk ``bulk_create`` / ``bulk_update`` paths that skip ``post_save`` are audited at
call sites via DAB helpers; workflow job node prompt pseudo-fields are handled here.
"""

from collections.abc import Iterable

from django.db.models import Model

from ansible_base.lib.utils.bulk_validation_audit import audit_bulk_model_instances
from ansible_base.lib.utils.validation_signals import (
    _get_caller_info,
    _protected_models,
    _validate_field,
    extend_caller_allowlist_prefixes,
    extend_internal_caller_prefixes,
    log_orm_bypass_violation,
    register_validation_signals,
)

# Tier 2 prompt fields on LaunchTimeConfigBase models; not Django CharFields (AAP-78694).
_WORKFLOW_JOB_NODE_PROMPT_PSEUDO_FIELDS = frozenset({'scm_branch', 'limit', 'job_tags', 'skip_tags'})


def configure_validation_bypass_observability() -> None:
    """Call from AppConfig.ready() so ORM bypass logs show AWX entry points.

    DAB resolves ``[caller: …]`` by walking the stack outward and returning the
    first module on the caller allowlist (denylist is not applied in that phase).
    Allowlist only product surfaces (API, serializers, tasks, management, scheduler).
    List bulk-audit helpers under ``awx.main.utils`` on the internal denylist so
    logs attribute to the serializer, task, or scheduler frame that invoked them.
    """
    register_validation_signals()
    extend_caller_allowlist_prefixes(
        [
            "awx.api.views",
            "awx.api.serializers",
            "awx.main.tasks",
            "awx.main.management",
            "awx.main.scheduler",
        ]
    )
    extend_internal_caller_prefixes(
        [
            "awx.main.models",
            "awx.main.signals",
            "awx.main.dispatch",
            "awx.main.utils.validation_bypass_observability",
            "awx.main.utils.db",
        ]
    )


def audit_workflow_job_nodes_for_bulk_create(nodes: Iterable[Model]) -> None:
    """Log Tier 1/2 violations for WorkflowJobNode rows before ``bulk_create``.

    ``audit_bulk_model_instances`` only inspects model ``CharField`` / ``TextField``
    columns. Node prompt values (limit, job_tags, etc.) live in ``char_prompts`` via
    ``NullablePromptPseudoField`` and must be read with ``getattr`` after deferred
    attrs are applied on the in-memory instances.

    When called from a DRF ``create()`` after ``is_valid()``, the caller must run
    inside DAB ``serializer_mediated_persistence_context`` so duplicate
    ``Validation rejected`` / ``ORM bypass`` lines are not emitted (see DAB
    ``docs/lib/validation_bypass_observability.md``).
    """
    materialized = list(nodes)
    if not materialized:
        return
    audit_bulk_model_instances(materialized, operation='bulk_create')
    sample = materialized[0]
    protected = _protected_models.get(type(sample))
    if protected is None:
        return
    name_fields, excluded_fields = protected
    resource_type = f"{sample._meta.app_label}.{sample._meta.object_name}"
    caller_info = None
    for instance in materialized:
        for field_name in _WORKFLOW_JOB_NODE_PROMPT_PSEUDO_FIELDS:
            if field_name in excluded_fields:
                continue
            value = getattr(instance, field_name, None)
            if value is None or not isinstance(value, str):
                continue
            violation = _validate_field(field_name, value, name_fields)
            if violation:
                tier, reason = violation
                if caller_info is None:
                    caller_info = _get_caller_info()
                log_orm_bypass_violation('bulk_create', field_name, resource_type, tier, caller_info, reason)
