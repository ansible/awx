from __future__ import unicode_literals
import warnings
from mongoengine.errors import ValidationError
from rest_framework import serializers
from rest_framework import fields
import mongoengine
from mongoengine.base import BaseDocument
from django.core.paginator import Page
from django.db import models
from django.forms import widgets
from django.utils.datastructures import SortedDict
from rest_framework.compat import get_concrete_model
from .fields import ReferenceField, ListField, EmbeddedDocumentField, DynamicField


class MongoEngineModelSerializerOptions(serializers.ModelSerializerOptions):
    """
    Meta class options for MongoEngineModelSerializer
    """
    def __init__(self, meta):
        super(MongoEngineModelSerializerOptions, self).__init__(meta)
        self.depth = getattr(meta, 'depth', 5)


class MongoEngineModelSerializer(serializers.ModelSerializer):
    """
    Model Serializer that supports Mongoengine
    """
    _options_class = MongoEngineModelSerializerOptions

    def perform_validation(self, attrs):
        """
        Rest Framework built-in validation + related model validations
        """
        for field_name, field in self.fields.items():
            if field_name in self._errors:
                continue

            source = field.source or field_name
            if self.partial and source not in attrs:
                continue

            if field_name in attrs and hasattr(field, 'model_field'):
                try:
                    field.model_field.validate(attrs[field_name])
                except ValidationError as err:
                    self._errors[field_name] = str(err)

            try:
                validate_method = getattr(self, 'validate_%s' % field_name, None)
                if validate_method:
                    attrs = validate_method(attrs, source)
            except serializers.ValidationError as err:
                self._errors[field_name] = self._errors.get(field_name, []) + list(err.messages)

        if not self._errors:
            try:
                attrs = self.validate(attrs)
            except serializers.ValidationError as err:
                if hasattr(err, 'message_dict'):
                    for field_name, error_messages in err.message_dict.items():
                        self._errors[field_name] = self._errors.get(field_name, []) + list(error_messages)
                elif hasattr(err, 'messages'):
                    self._errors['non_field_errors'] = err.messages

        return attrs

    def restore_object(self, attrs, instance=None):
        if instance is None:
            instance = self.opts.model()

        dynamic_fields = self.get_dynamic_fields(instance)
        all_fields = dict(dynamic_fields, **self.fields)

        for key, val in attrs.items():
            field = all_fields.get(key)
            if not field or field.read_only:
                continue

            if isinstance(field, serializers.Serializer):
                many = field.many

                def _restore(field, item):
                    # looks like a bug, sometimes there are decerialized objects in attrs
                    # sometimes they are just dicts
                    if isinstance(item, BaseDocument):
                        return item
                    return field.from_native(item)

                if many:
                    val = [_restore(field, item) for item in val]
                else:
                    val = _restore(field, val)

            key = getattr(field, 'source', None) or key
            try:
                setattr(instance, key, val)
            except ValueError:
                self._errors[key] = self.error_messages['required']

        return instance

    def get_default_fields(self):
        cls = self.opts.model
        opts = get_concrete_model(cls)
        fields = []
        fields += [getattr(opts, field) for field in cls._fields_ordered]

        ret = SortedDict()

        for model_field in fields:
            if isinstance(model_field, mongoengine.ObjectIdField):
                field = self.get_pk_field(model_field)
            else:
                field = self.get_field(model_field)

            if field:
                field.initialize(parent=self, field_name=model_field.name)
                ret[model_field.name] = field

        for field_name in self.opts.read_only_fields:
            assert field_name in ret,\
            "read_only_fields on '%s' included invalid item '%s'" %\
            (self.__class__.__name__, field_name)
            ret[field_name].read_only = True

        for field_name in self.opts.write_only_fields:
            assert field_name in ret,\
            "write_only_fields on '%s' included invalid item '%s'" %\
            (self.__class__.__name__, field_name)
            ret[field_name].write_only = True

        return ret

    def get_dynamic_fields(self, obj):
        dynamic_fields = {}
        if obj is not None and obj._dynamic:
            for key, value in obj._dynamic_fields.items():
                dynamic_fields[key] = self.get_field(value)
        return dynamic_fields

    def get_field(self, model_field):
        kwargs = {}

        if model_field.__class__ in (mongoengine.ReferenceField, mongoengine.EmbeddedDocumentField,
                                     mongoengine.ListField, mongoengine.DynamicField):
            kwargs['model_field'] = model_field
            kwargs['depth'] = self.opts.depth

        if not model_field.__class__ == mongoengine.ObjectIdField:
            kwargs['required'] = model_field.required

        if model_field.__class__ == mongoengine.EmbeddedDocumentField:
            kwargs['document_type'] = model_field.document_type

        if model_field.default:
            kwargs['required'] = False
            kwargs['default'] = model_field.default

        if model_field.__class__ == models.TextField:
            kwargs['widget'] = widgets.Textarea

        field_mapping = {
            mongoengine.FloatField: fields.FloatField,
            mongoengine.IntField: fields.IntegerField,
            mongoengine.DateTimeField: fields.DateTimeField,
            mongoengine.EmailField: fields.EmailField,
            mongoengine.URLField: fields.URLField,
            mongoengine.StringField: fields.CharField,
            mongoengine.BooleanField: fields.BooleanField,
            mongoengine.FileField: fields.FileField,
            mongoengine.ImageField: fields.ImageField,
            mongoengine.ObjectIdField: fields.WritableField,
            mongoengine.ReferenceField: ReferenceField,
            mongoengine.ListField: ListField,
            mongoengine.EmbeddedDocumentField: EmbeddedDocumentField,
            mongoengine.DynamicField: DynamicField,
            mongoengine.DecimalField: fields.DecimalField,
            mongoengine.UUIDField: fields.CharField
        }

        attribute_dict = {
            mongoengine.StringField: ['max_length'],
            mongoengine.DecimalField: ['min_value', 'max_value'],
            mongoengine.EmailField: ['max_length'],
            mongoengine.FileField: ['max_length'],
            mongoengine.URLField: ['max_length'],
        }

        if model_field.__class__ in attribute_dict:
            attributes = attribute_dict[model_field.__class__]
            for attribute in attributes:
                kwargs.update({attribute: getattr(model_field, attribute)})

        try:
            return field_mapping[model_field.__class__](**kwargs)
        except KeyError:
            # Defaults to WritableField if not in field mapping
            return fields.WritableField(**kwargs)

    def to_native(self, obj):
        """
        Rest framework built-in to_native + transform_object
        """
        ret = self._dict_class()
        ret.fields = self._dict_class()

        #Dynamic Document Support
        dynamic_fields = self.get_dynamic_fields(obj)
        all_fields = self._dict_class()
        all_fields.update(self.fields)
        all_fields.update(dynamic_fields)

        for field_name, field in all_fields.items():
            if field.read_only and obj is None:
                continue
            field.initialize(parent=self, field_name=field_name)
            key = self.get_field_key(field_name)
            value = field.field_to_native(obj, field_name)
            #Override value with transform_ methods
            method = getattr(self, 'transform_%s' % field_name, None)
            if callable(method):
                value = method(obj, value)
            if not getattr(field, 'write_only', False):
                ret[key] = value
            ret.fields[key] = self.augment_field(field, field_name, key, value)

        return ret

    def from_native(self, data, files=None):
        self._errors = {}

        if data is not None or files is not None:
            attrs = self.restore_fields(data, files)
            for key in data.keys():
                if key not in attrs:
                    attrs[key] = data[key]
            if attrs is not None:
                attrs = self.perform_validation(attrs)
        else:
            self._errors['non_field_errors'] = ['No input provided']

        if not self._errors:
            return self.restore_object(attrs, instance=getattr(self, 'object', None))

    @property
    def data(self):
        """
        Returns the serialized data on the serializer.
        """
        if self._data is None:
            obj = self.object

            if self.many is not None:
                many = self.many
            else:
                many = hasattr(obj, '__iter__') and not isinstance(obj, (BaseDocument, Page, dict))
                if many:
                    warnings.warn('Implicit list/queryset serialization is deprecated. '
                                  'Use the `many=True` flag when instantiating the serializer.',
                                  DeprecationWarning, stacklevel=2)

            if many:
                self._data = [self.to_native(item) for item in obj]
            else:
                self._data = self.to_native(obj)

        return self._data
