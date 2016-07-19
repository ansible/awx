import pytest

from awx.api.filters import FieldLookupBackend
from awx.main.models import JobTemplate

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
