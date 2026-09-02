# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""Inject DAB CleanTextMixin frontend patterns into JSON sub-key schemas.

Top-level CharField OPTIONS metadata is handled by DAB's CleanTextMetadata
(AAP-85987). JSON sub-keys (credential inputs, notification config, credential
input source metadata) are domain-owned schemas, so pattern injection lives
here rather than in DAB.

Depends on django-ansible-base PR #1119 (AAP-85987) for
``build_tier2_frontend_pattern``. Until that lands on DAB devel, injection is
a no-op so Controller can still import and run.
"""

import copy

from ansible_base.lib.utils.settings import get_setting

try:
    from ansible_base.lib.metadata import build_tier2_frontend_pattern
except ImportError:  # pragma: no cover - DAB without AAP-85987
    build_tier2_frontend_pattern = None

# Keep in sync with ansible_base.lib.metadata.inject_clean_text_patterns (Tier 2).
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
    """Inject patterns into a credential-type ``fields`` or ``metadata`` list in place."""
    if not isinstance(fields, list):
        return
    for field in fields:
        inject_free_text_pattern(field)


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
