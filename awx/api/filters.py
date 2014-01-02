# Copyright (c) 2014 AnsibleWorks, Inc.
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

    RESERVED_NAMES = ('page', 'page_size', 'format', 'order', 'order_by',
                      'search')

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
            # Apply filters specified via QUERY_PARAMS. Each entry in the lists
            # below is (negate, field, value).
            and_filters = []
            or_filters = []
            chain_filters = []
            for key, values in request.QUERY_PARAMS.lists():
                if key in self.RESERVED_NAMES:
                    continue

                # Custom __int filter suffix (internal use only).
                q_int = False
                if key.endswith('__int'):
                    key = key[:-5]
                    q_int = True

                # Custom chain__ and or__ filters, mutually exclusive (both can
                # precede not__).
                q_chain = False
                q_or = False
                if key.startswith('chain__'):
                    key = key[7:]
                    q_chain = True
                elif key.startswith('or__'):
                    key = key[4:]
                    q_or = True

                # Custom not__ filter prefix.
                q_not = False
                if key.startswith('not__'):
                    key = key[5:]
                    q_not = True

                # Convert value(s) to python and add to the appropriate list.
                for value in values:
                    if q_int:
                        value = int(value)
                    value = self.value_to_python(queryset.model, key, value)
                    if q_chain:
                        chain_filters.append((q_not, key, value))
                    elif q_or:
                        or_filters.append((q_not, key, value))
                    else:
                        and_filters.append((q_not, key, value))

            # Now build Q objects for database query filter.
            if and_filters or or_filters or chain_filters:
                args = []
                for n, k, v in and_filters:
                    if n:
                        args.append(~Q(**{k:v}))
                    else:
                        args.append(Q(**{k:v}))
                if or_filters:
                    q = Q()
                    for n,k,v in or_filters:
                        if n:
                            q |= ~Q(**{k:v})
                        else:
                            q |= Q(**{k:v})
                    args.append(q)
                for n,k,v in chain_filters:
                    if n:
                        q = ~Q(**{k:v})
                    else:
                        q = Q(**{k:v})
                    queryset = queryset.filter(q)
                queryset = queryset.filter(*args)
            return queryset.distinct()
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
