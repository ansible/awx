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
from django.contrib.contenttypes.models import ContentType

# Django REST Framework
from rest_framework.exceptions import ParseError
from rest_framework.filters import BaseFilterBackend

# Ansible Tower
from awx.main.utils import get_type_for_model, to_python_boolean

class MongoFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        return queryset

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

class TypeFilterBackend(BaseFilterBackend):
    '''
    Filter on type field now returned with all objects.
    '''

    def filter_queryset(self, request, queryset, view):
        try:
            types = None
            for key, value in request.QUERY_PARAMS.items():
                if key == 'type':
                    if ',' in value:
                        types = value.split(',')
                    else:
                        types = (value,)
            if types:
                types_map = {}
                for ct in ContentType.objects.filter(Q(app_label='main') | Q(app_label='auth', model='user')):
                    ct_model = ct.model_class()
                    if not ct_model:
                        continue
                    ct_type = get_type_for_model(ct_model)
                    types_map[ct_type] = ct.pk
                model = queryset.model
                model_type = get_type_for_model(model)
                if 'polymorphic_ctype' in model._meta.get_all_field_names():
                    types_pks = set([v for k,v in types_map.items() if k in types])
                    queryset = queryset.filter(polymorphic_ctype_id__in=types_pks)
                elif model_type in types:
                    queryset = queryset
                else:
                    queryset = queryset.none()
            return queryset
        except FieldError, e:
            # Return a 400 for invalid field names.
            raise ParseError(*e.args)

class FieldLookupBackend(BaseFilterBackend):
    '''
    Filter using field lookups provided via query string parameters.
    '''

    RESERVED_NAMES = ('page', 'page_size', 'format', 'order', 'order_by',
                      'search', 'type')

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
        new_parts = []
        for n, name in enumerate(parts[:-1]):

            # HACK: Make project and inventory source filtering by old field names work for backwards compatibility.
            if model._meta.object_name in ('Project', 'InventorySource'):
                name = {
                    'current_update': 'current_job',
                    'last_update': 'last_job',
                    'last_update_failed': 'last_job_failed',
                    'last_updated': 'last_job_run',
                }.get(name, name)

            if name == 'pk':
                field = model._meta.pk
            else:
                field = model._meta.get_field_by_name(name)[0]
            if n < (len(parts) - 2):
                if getattr(field, 'rel', None):
                    model = field.rel.to
                else:
                    model = field.model
            new_parts.append(name)
        if parts:
            new_parts.append(parts[-1])
        new_lookup = '__'.join(new_parts)
        return field, new_lookup

    def to_python_related(self, value):
        value = unicode(value)
        if value.lower() in ('none', 'null'):
            return None
        else:
            return int(value)

    def value_to_python_for_field(self, field, value):
        if isinstance(field, models.NullBooleanField):
            return to_python_boolean(value, allow_none=True)
        elif isinstance(field, models.BooleanField):
            return to_python_boolean(value)
        elif isinstance(field, RelatedObject):
            return self.to_python_related(value)
        else:
            return field.to_python(value)

    def value_to_python(self, model, lookup, value):
        field, new_lookup = self.get_field_from_lookup(model, lookup)
        if new_lookup.endswith('__isnull'):
            value = to_python_boolean(value)
        elif new_lookup.endswith('__in'):
            items = []
            for item in value.split(','):
                items.append(self.value_to_python_for_field(field, item))
            value = items
        elif new_lookup.endswith('__regex') or new_lookup.endswith('__iregex'):
            try:
                re.compile(value)
            except re.error, e:
                raise ValueError(e.args[0])
        else:
            value = self.value_to_python_for_field(field, value)
        return value, new_lookup

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
                
                # HACK: Make job event filtering by host name mostly work even
                # when not capturing job event hosts M2M.
                if queryset.model._meta.object_name == 'JobEvent' and key.startswith('hosts__name'):
                    key = key.replace('hosts__name', 'or__host__name')
                    or_filters.append((False, 'host__name__isnull', True))                 

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
                    value, new_key = self.value_to_python(queryset.model, key, value)
                    if q_chain:
                        chain_filters.append((q_not, new_key, value))
                    elif q_or:
                        or_filters.append((q_not, new_key, value))
                    else:
                        and_filters.append((q_not, new_key, value))

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
                # Special handling of the type field for ordering. In this
                # case, we're not sorting exactly on the type field, but
                # given the limited number of views with multiple types,
                # sorting on polymorphic_ctype.model is effectively the same.
                new_order_by = []
                if 'polymorphic_ctype' in queryset.model._meta.get_all_field_names():
                    for field in order_by:
                        if field == 'type':
                            new_order_by.append('polymorphic_ctype__model')
                        elif field == '-type':
                            new_order_by.append('-polymorphic_ctype__model')
                        else:
                            new_order_by.append(field)
                else:
                    for field in order_by:
                        if field not in ('type', '-type'):
                            new_order_by.append(field)
                queryset = queryset.order_by(*new_order_by)
            return queryset
        except FieldError, e:
            # Return a 400 for invalid field names.
            raise ParseError(*e.args)
