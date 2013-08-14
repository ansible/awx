# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import re

# Django
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.related import RelatedObject
from django.db.models.fields import FieldDoesNotExist

# Django REST Framework
from rest_framework.exceptions import ParseError
from rest_framework.filters import BaseFilterBackend

class ActiveOnlyBackend(BaseFilterBackend):
    '''
    Filter to show only objects where is_active/active is True.
    '''

    def filter_queryset(self, request, queryset, view):
        for field in queryset.model._meta.fields:
            if field.name == 'is_active':
                queryset = queryset.filter(is_active=True)
            elif field.name == 'active':
                queryset = queryset.filter(active=True)
        return queryset

class FieldLookupBackend(BaseFilterBackend):
    '''
    Filter using field lookups provided via query string parameters.
    '''

    RESERVED_NAMES = ('page', 'page_size', 'format', 'order', 'order_by')

    SUPPORTED_LOOKUPS = ('exact', 'iexact', 'contains', 'icontains',
                         'startswith', 'istartswith', 'endswith', 'iendswith',
                         'regex', 'iregex', 'gt', 'gte', 'lt', 'lte', 'in',
                         'isnull')

    def get_field_from_lookup(self, model, lookup):
        field = None
        parts = lookup.split('__')
        if parts and parts[-1] not in self.SUPPORTED_LOOKUPS:
            parts.append('exact')
        # FIXME: Could build up a list of models used across relationships, use
        # those lookups combined with request.user.get_queryset(Model) to make
        # sure user cannot query using objects he could not view.
        for n, name in enumerate(parts[:-1]):
            if name == 'pk':
                field = model._meta.pk
            else:
                field = model._meta.get_field_by_name(name)[0]
            if n < (len(parts) - 2):
                if getattr(field, 'rel', None):
                    model = field.rel.to
                else:
                    model = field.model
        return field

    def to_python_boolean(self, value, allow_none=False):
        value = unicode(value)
        if value.lower() in ('true', '1'):
            return True
        elif value.lower() in ('false', '0'):
            return False
        elif allow_none and value.lower() in ('none', 'null'):
            return None
        else:
            raise ValueError(u'Unable to convert "%s" to boolean' % unicode(value))

    def to_python_related(self, value):
        value = unicode(value)
        if value.lower() in ('none', 'null'):
            return None
        else:
            return int(value)

    def value_to_python_for_field(self, field, value):
        if isinstance(field, models.NullBooleanField):
            return self.to_python_boolean(value, allow_none=True)
        elif isinstance(field, models.BooleanField):
            return self.to_python_boolean(value)
        elif isinstance(field, RelatedObject):
            return self.to_python_related(value)
        else:
            return field.to_python(value)

    def value_to_python(self, model, lookup, value):
        field = self.get_field_from_lookup(model, lookup)
        if lookup.endswith('__isnull'):
            value = self.to_python_boolean(value)
        elif lookup.endswith('__in'):
            items = []
            for item in value.split(','):
                items.append(self.value_to_python_for_field(field, item))
            value = items
        elif lookup.endswith('__regex') or lookup.endswith('__iregex'):
            try:
                re.compile(value)
            except re.error, e:
                raise ValueError(e.args[0])
            return value
        else:
            value = self.value_to_python_for_field(field, value)
        return value

    def filter_queryset(self, request, queryset, view):
        try:
            # Apply filters and excludes specified via QUERY_PARAMS.
            filters = {}
            excludes = {}
            for key, value in request.QUERY_PARAMS.items():
                if key in self.RESERVED_NAMES:
                    continue
                # Custom __int filter suffix (internal use only).
                if key.endswith('__int'):
                    key = key[:-5]
                    value = int(value)
                # Custom not__ filter prefix.
                q_not = False
                if key.startswith('not__'):
                    key = key[5:]
                    q_not = True
            
                # Convert value to python and add to the appropriate dict.
                value = self.value_to_python(queryset.model, key, value)
                if q_not:
                    excludes[key] = value
                else:
                    filters[key] = value

            if filters:
                queryset = queryset.filter(**filters)
            if excludes:
                queryset = queryset.exclude(**excludes)
            return queryset
        except (FieldError, FieldDoesNotExist, ValueError), e:
            raise ParseError(e.args[0])
        except ValidationError, e:
            raise ParseError(e.messages)

class OrderByBackend(BaseFilterBackend):
    '''
    Filter to apply ordering based on query string parameters.
    '''

    def filter_queryset(self, request, queryset, view):
        try:
            order_by = None
            for key, value in request.QUERY_PARAMS.items():
                if key in ('order', 'order_by'):
                    order_by = value
                    if ',' in value:
                        order_by = value.split(',')
                    else:
                        order_by = (value,)
            if order_by:
                queryset = queryset.order_by(*order_by)
                # Fetch the first result to run the query, otherwise we don't
                # always catch the FieldError for invalid field names.
                try:
                    queryset[0]
                except IndexError:
                    pass
            return queryset
        except FieldError, e:
            # Return a 400 for invalid field names.
            raise ParseError(*e.args)
