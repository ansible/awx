# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""Inject DAB CleanTextMixin frontend patterns into API OPTIONS metadata.

Controller defines its own ``DEFAULT_METADATA_CLASS`` (``awx.api.metadata.Metadata``)
rather than using DAB's ``CleanTextMetadata``, so top-level CharField OPTIONS
metadata is not handled automatically by DAB -- ``inject_top_level_clean_text_patterns``
below is called directly from ``awx.api.metadata.Metadata.get_field_info`` to cover it.
JSON sub-keys (credential inputs, notification config, credential input source
metadata) are domain-owned schemas that DAB has no visibility into at all, so
pattern injection for those lives here unconditionally.

Depends on django-ansible-base PR #1119 (AAP-85987) for
``build_tier2_frontend_pattern`` and ``inject_clean_text_patterns``. Until that
lands on DAB devel, injection is a no-op so Controller can still import and run.
"""

import copy

from ansible_base.lib.utils.settings import get_setting

try:
    from ansible_base.lib.metadata import build_tier2_frontend_pattern
except ImportError:  # pragma: no cover - DAB without AAP-85987
    build_tier2_frontend_pattern = None

try:
    from ansible_base.lib.metadata import inject_clean_text_patterns as _dab_inject_clean_text_patterns
except ImportError:  # pragma: no cover - DAB without AAP-85987
    _dab_inject_clean_text_patterns = None

try:
    from ansible_base.lib.metadata import TIER2_PATTERN_DESCRIPTION
except ImportError:  # pragma: no cover - DAB without AAP-85987
    TIER2_PATTERN_DESCRIPTION = "This field can't include HTML tags, script markup, unsafe URI schemes, shell or template syntax, or control characters."

_STRING_TYPES = frozenset({'string', 'str'})


def enhanced_input_validation_enabled():
    return bool(get_setting('ENHANCED_INPUT_VALIDATION_ENABLED', False))


def free_text_pattern_metadata():
    """Return Tier 2 (validate_free_text) pattern keys for API clients, or None."""
    if build_tier2_frontend_pattern is None:
        return None
    return {
        'pattern': build_tier2_frontend_pattern(),
        'pattern_description': TIER2_PATTERN_DESCRIPTION,
        'flags': 'i',
    }


def _is_string_schema(field_schema, field_type=None):
    if field_type is None:
        field_type = field_schema.get('type', 'string')
    return field_type in _STRING_TYPES


def inject_free_text_pattern(field_schema, *, secret=False, field_type=None):
    """Mutate a schema dict in place if it is a non-secret string field.

    No-op when the install-time toggle is off or DAB pattern helpers are missing.
    """
    if not isinstance(field_schema, dict):
        return field_schema
    if not enhanced_input_validation_enabled():
        return field_schema
    if secret or field_schema.get('secret') is True:
        return field_schema
    if not _is_string_schema(field_schema, field_type=field_type):
        return field_schema

    metadata = free_text_pattern_metadata()
    if metadata is None:
        return field_schema
    field_schema.update(metadata)
    return field_schema


def inject_patterns_into_field_list(fields):
    """Inject patterns into a credential-type ``fields`` or ``metadata`` list in place.

    Each field is shallow-copied before mutation so shared/module-level schema
    dicts (e.g. ``ManagedCredentialType.registry`` entries) are never modified.
    """
    if not enhanced_input_validation_enabled():
        return
    if not isinstance(fields, list):
        return
    for i, field in enumerate(fields):
        fields[i] = inject_free_text_pattern(copy.copy(field))


def inject_patterns_into_init_parameters(init_parameters):
    """Return a copy of notification ``init_parameters`` with patterns injected.

    Copies first so class-level backend dicts are never mutated.
    Password-typed keys are treated as secrets and skipped.
    """
    params = copy.deepcopy(init_parameters) if isinstance(init_parameters, dict) else {}
    if not enhanced_input_validation_enabled():
        return params
    for field_schema in params.values():
        if not isinstance(field_schema, dict):
            continue
        inject_free_text_pattern(field_schema, secret=field_schema.get('type') == 'password')
    return params


def inject_top_level_clean_text_patterns(field, field_info):
    """Advertise DAB CleanTextMixin Tier 1/Tier 2 patterns on a top-level serializer field.

    Delegates entirely to DAB's ``inject_clean_text_patterns``, which no-ops unless
    ``ENHANCED_INPUT_VALIDATION_ENABLED`` is on and the field's serializer mixes in
    ``CleanTextMixin``. No-op when the DAB helper is missing.
    """
    if _dab_inject_clean_text_patterns is None:
        return field_info
    return _dab_inject_clean_text_patterns(field, field_info)
