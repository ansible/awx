import json

from django import forms
from django.utils import six

from .widgets import JSONWidget


class JSONFormField(forms.CharField):
    empty_values = [None, '']
    
    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = JSONWidget
        super(JSONFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, six.string_types) and value:
            try:
                return json.loads(value)
            except Exception as exc:
                raise forms.ValidationError(
                    'JSON decode error: %s' % (unicode(exc),)
                )
        else:
            return value
    
    def validate(self, value):
        # This is required in older django versions.
        if value in self.empty_values and self.required:
            raise forms.ValidationError(self.error_messages['required'], code='required')