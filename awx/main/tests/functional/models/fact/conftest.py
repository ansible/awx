
import pytest
import six

from jsonbfield.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

def dumps(value):
    return DjangoJSONEncoder().encode(value)

# Taken from https://github.com/django-extensions/django-extensions/blob/54fe88df801d289882a79824be92d823ab7be33e/django_extensions/db/fields/json.py
def get_db_prep_save(self, value, connection, **kwargs):
    """Convert our JSON object to a string before we save"""
    if value is None and self.null:
	return None
    # default values come in as strings; only non-strings should be
    # run through `dumps`
    if not isinstance(value, six.string_types):
	value = dumps(value)

    return value

@pytest.fixture
def monkeypatch_jsonbfield_get_db_prep_save(mocker):
    JSONField.get_db_prep_save = get_db_prep_save

