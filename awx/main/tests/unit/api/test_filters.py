# -*- coding: utf-8 -*-

import pytest

from rest_framework.exceptions import PermissionDenied, ParseError
from awx.api.filters import FieldLookupBackend, OrderByBackend, get_field_from_path
from awx.main.models import (AdHocCommand, ActivityStream,
                             CustomInventoryScript, Credential, Job,
                             JobTemplate, SystemJob, UnifiedJob, User,
                             WorkflowJob, WorkflowJobTemplate,
                             WorkflowJobOptions, InventorySource,
                             JobEvent)
from awx.main.models.oauth import OAuth2Application
from awx.main.models.jobs import JobOptions

# Django
from django.db.models.fields import FieldDoesNotExist


def test_related():
    field_lookup = FieldLookupBackend()
    lookup = '__'.join(['inventory', 'organization', 'pk'])
    field, new_lookup = field_lookup.get_field_from_lookup(InventorySource, lookup)
    print(field)
    print(new_lookup)


def test_invalid_filter_key():
    field_lookup = FieldLookupBackend()
    # FieldDoesNotExist is caught and converted to ParseError by filter_queryset
    with pytest.raises(FieldDoesNotExist) as excinfo:
        field_lookup.value_to_python(JobEvent, 'event_data.task_action', 'foo')
    assert 'has no field named' in str(excinfo)


def test_invalid_field_hop():
    with pytest.raises(ParseError) as excinfo:
        get_field_from_path(Credential, 'organization__description__user')
    assert 'No related model for' in str(excinfo)


def test_invalid_order_by_key():
    field_order_by = OrderByBackend()
    with pytest.raises(ParseError) as excinfo:
        [f for f in field_order_by._validate_ordering_fields(JobEvent, ('event_data.task_action',))]
    assert 'has no field named' in str(excinfo)


@pytest.mark.parametrize(u"empty_value", [u'', ''])
def test_empty_in(empty_value):
    field_lookup = FieldLookupBackend()
    with pytest.raises(ValueError) as excinfo:
        field_lookup.value_to_python(JobTemplate, 'project__name__in', empty_value)
    assert 'empty value for __in' in str(excinfo.value)


@pytest.mark.parametrize(u"valid_value", [u'foo', u'foo,'])
def test_valid_in(valid_value):
    field_lookup = FieldLookupBackend()
    value, new_lookup, _ = field_lookup.value_to_python(JobTemplate, 'project__name__in', valid_value)
    assert 'foo' in value


def test_invalid_field():
    invalid_field = u"ヽヾ"
    field_lookup = FieldLookupBackend()
    with pytest.raises(ValueError) as excinfo:
        field_lookup.value_to_python(WorkflowJobTemplate, invalid_field, 'foo')
    assert 'is not an allowed field name. Must be ascii encodable.' in str(excinfo.value)


@pytest.mark.parametrize('lookup_suffix', ['', 'contains', 'startswith', 'in'])
@pytest.mark.parametrize('password_field', Credential.PASSWORD_FIELDS)
def test_filter_on_password_field(password_field, lookup_suffix):
    field_lookup = FieldLookupBackend()
    lookup = '__'.join(filter(None, [password_field, lookup_suffix]))
    with pytest.raises(PermissionDenied) as excinfo:
        field, new_lookup = field_lookup.get_field_from_lookup(Credential, lookup)
    assert 'not allowed' in str(excinfo.value)


@pytest.mark.parametrize('model, query', [
    (User, 'password__icontains'),
    (User, 'settings__value__icontains'),
    (User, 'main_oauth2accesstoken__token__gt'),
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
    (CustomInventoryScript, 'script__icontains'),
    (ActivityStream, 'o_auth2_application__client_secret__gt'),
    (OAuth2Application, 'grant__code__gt')
])
def test_filter_sensitive_fields_and_relations(model, query):
    field_lookup = FieldLookupBackend()
    with pytest.raises(PermissionDenied) as excinfo:
        field, new_lookup = field_lookup.get_field_from_lookup(model, query)
    assert 'not allowed' in str(excinfo.value)


def test_looping_filters_prohibited():
    field_lookup = FieldLookupBackend()
    with pytest.raises(ParseError) as loop_exc:
        field_lookup.get_field_from_lookup(Job, 'job_events__job__job_events')
    assert 'job_events' in str(loop_exc.value)
