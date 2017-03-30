# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.


# Django REST Framework
from rest_framework import serializers

__all__ = ['BooleanNullField', 'CharNullField', 'ChoiceNullField', 'VerbatimField']


class NullFieldMixin(object):
    '''
    Mixin to prevent shortcutting validation when we want to allow null input,
    but coerce the resulting value to another type.
    '''

    def validate_empty_values(self, data):
        (is_empty_value, data) = super(NullFieldMixin, self).validate_empty_values(data)
        if is_empty_value and data is None:
            return (False, data)
        return (is_empty_value, data)


class BooleanNullField(NullFieldMixin, serializers.NullBooleanField):
    '''
    Custom boolean field that allows null and empty string as False values.
    '''

    def to_internal_value(self, data):
        return bool(super(BooleanNullField, self).to_internal_value(data))


class CharNullField(NullFieldMixin, serializers.CharField):
    '''
    Custom char field that allows null as input and coerces to an empty string.
    '''

    def __init__(self, **kwargs):
        kwargs['allow_null'] = True
        super(CharNullField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return super(CharNullField, self).to_internal_value(data or u'')


class ChoiceNullField(NullFieldMixin, serializers.ChoiceField):
    '''
    Custom choice field that allows null as input and coerces to an empty string.
    '''

    def __init__(self, **kwargs):
        kwargs['allow_null'] = True
        super(ChoiceNullField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return super(ChoiceNullField, self).to_internal_value(data or u'')


class VerbatimField(serializers.Field):
    '''
    Custom field that passes the value through without changes.
    '''

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value
