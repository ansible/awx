# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# Django REST Framework
from rest_framework import serializers

# AWX
from awx.conf import fields
from awx.main.models import Credential

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


class OAuth2ProviderField(fields.DictField):

    default_error_messages = {
        'invalid_key_names': _('Invalid key names: {invalid_key_names}'),
    }
    valid_key_names = {'ACCESS_TOKEN_EXPIRE_SECONDS', 'AUTHORIZATION_CODE_EXPIRE_SECONDS', 'REFRESH_TOKEN_EXPIRE_SECONDS'}
    child = fields.IntegerField(min_value=1)

    def to_internal_value(self, data):
        data = super(OAuth2ProviderField, self).to_internal_value(data)
        invalid_flags = (set(data.keys()) - self.valid_key_names)
        if invalid_flags:
            self.fail('invalid_key_names', invalid_key_names=', '.join(list(invalid_flags)))
        return data


class DeprecatedCredentialField(serializers.IntegerField):

    def __init__(self, **kwargs):
        kwargs['allow_null'] = True
        kwargs['default'] = None
        kwargs['min_value'] = 1
        kwargs.setdefault('help_text', 'This resource has been deprecated and will be removed in a future release')
        super(DeprecatedCredentialField, self).__init__(**kwargs)

    def to_internal_value(self, pk):
        try:
            pk = int(pk)
        except ValueError:
            self.fail('invalid')
        try:
            Credential.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(_('Credential {} does not exist').format(pk))
        return pk
