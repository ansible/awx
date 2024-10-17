# -*- coding: utf-8 -*-

import pytest

# Django
from rest_framework.exceptions import PermissionDenied

from ansible_base.rest_filters.rest_framework.field_lookup_backend import FieldLookupBackend

from awx.main.models import (
    AdHocCommand,
    Job,
    JobTemplate,
    SystemJob,
    UnifiedJob,
    User,
    WorkflowJob,
    WorkflowJobTemplate,
    WorkflowJobOptions,
)
from awx.main.models.jobs import JobOptions


@pytest.mark.parametrize(
    'model, query',
    [
        (User, 'password__icontains'),
        (User, 'settings__value__icontains'),
        (UnifiedJob, 'job_args__icontains'),
        (UnifiedJob, 'job_env__icontains'),
        (UnifiedJob, 'start_args__icontains'),
        (AdHocCommand, 'extra_vars__icontains'),
        (JobOptions, 'extra_vars__icontains'),
        (SystemJob, 'extra_vars__icontains'),
        (WorkflowJobOptions, 'extra_vars__icontains'),
        (Job, 'survey_passwords__icontains'),
        (WorkflowJob, 'survey_passwords__icontains'),
        (JobTemplate, 'survey_spec__icontains'),
        (WorkflowJobTemplate, 'survey_spec__icontains'),
    ],
)
def test_filter_sensitive_fields_and_relations(model, query):
    field_lookup = FieldLookupBackend()
    with pytest.raises(PermissionDenied) as excinfo:
        field, new_lookup = field_lookup.get_field_from_lookup(model, query)
    assert 'not allowed' in str(excinfo.value)
