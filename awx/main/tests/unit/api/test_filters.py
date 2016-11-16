import pytest

from rest_framework.exceptions import PermissionDenied
from awx.api.filters import FieldLookupBackend
from awx.main.models import Credential, JobTemplate


@pytest.mark.parametrize(u"empty_value", [u'', ''])
def test_empty_in(empty_value):
    field_lookup = FieldLookupBackend()
    with pytest.raises(ValueError) as excinfo:
        field_lookup.value_to_python(JobTemplate, 'project__in', empty_value)
    assert 'empty value for __in' in str(excinfo.value)


@pytest.mark.parametrize(u"valid_value", [u'foo', u'foo,'])
def test_valid_in(valid_value):
    field_lookup = FieldLookupBackend()
    value, new_lookup = field_lookup.value_to_python(JobTemplate, 'project__in', valid_value)
    assert 'foo' in value


@pytest.mark.parametrize('lookup_suffix', ['', 'contains', 'startswith', 'in'])
@pytest.mark.parametrize('password_field', Credential.PASSWORD_FIELDS)
def test_filter_on_password_field(password_field, lookup_suffix):
    field_lookup = FieldLookupBackend()
    lookup = '__'.join(filter(None, [password_field, lookup_suffix]))
    with pytest.raises(PermissionDenied) as excinfo:
        field, new_lookup = field_lookup.get_field_from_lookup(Credential, lookup)
    assert 'not allowed' in str(excinfo.value)


@pytest.mark.parametrize('lookup_suffix', ['', 'contains', 'startswith', 'in'])
@pytest.mark.parametrize('password_field', Credential.PASSWORD_FIELDS)
def test_filter_on_related_password_field(password_field, lookup_suffix):
    field_lookup = FieldLookupBackend()
    lookup = '__'.join(filter(None, ['credential', password_field, lookup_suffix]))
    with pytest.raises(PermissionDenied) as excinfo:
        field, new_lookup = field_lookup.get_field_from_lookup(JobTemplate, lookup)
    assert 'not allowed' in str(excinfo.value)
