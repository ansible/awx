# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.utils.translation import ugettext_lazy as _


# South
from south.modelsinspector import add_introspection_rules

__all__ = ['AutoOneToOneField']

# Based on AutoOneToOneField from django-annoying:
# https://bitbucket.org/offline/django-annoying/src/a0de8b294db3/annoying/fields.py

class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor):
    """Descriptor for access to the object from its related class."""

    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor,
                         self).__get__(instance, instance_type)
        except self.related.model.DoesNotExist:
            obj = self.related.model(**{self.related.field.name: instance})
            if self.related.field.rel.parent_link:
                raise NotImplementedError('not supported with polymorphic!')
                for f in instance._meta.local_fields:
                    setattr(obj, f.name, getattr(instance, f.name))
            obj.save()
            return obj

class AutoOneToOneField(models.OneToOneField):
    """OneToOneField that creates related object if it doesn't exist."""

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(),
                AutoSingleRelatedObjectDescriptor(related))

add_introspection_rules([([AutoOneToOneField], [], {})],
                        [r'^awx\.main\.fields\.AutoOneToOneField'])


# Copied, flat out, from Django 1.6.
# Vendored here because Tower is run against Django 1.5.
#
# Original:
#   github.com/django/django/blob/master/django/db/models/fields/__init__.py
#
# Django is:
#   Copyright (c) Django Software Foundation and individual contributors.
#   All rights reserved.
#
# Used under license:
#   github.com/django/django/blob/master/LICENSE
class BinaryField(models.Field):
    description = _("Raw binary data")
    empty_values = [None, b'']

    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False
        super(BinaryField, self).__init__(*args, **kwargs)
        if self.max_length is not None:
            self.validators.append(validators.MaxLengthValidator(self.max_length))

    def get_internal_type(self):
        return "BinaryField"

    def get_default(self):
        if self.has_default() and not callable(self.default):
            return self.default
        default = super(BinaryField, self).get_default()
        if default == '':
            return b''
        return default

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super(BinaryField, self).get_db_prep_value(value, connection, prepared)
        if value is not None:
            return connection.Database.Binary(value)
        return value

    def value_to_string(self, obj):
        """Binary data is serialized as base64"""
        return b64encode(force_bytes(self._get_val_from_obj(obj))).decode('ascii')

    def to_python(self, value):
        # If it's a string, it should be base64-encoded data
        if isinstance(value, six.text_type):
            return six.memoryview(b64decode(force_bytes(value)))
        return value


add_introspection_rules([([BinaryField], [], {})],
                        [r'^awx\.main\.fields\.BinaryField'])
