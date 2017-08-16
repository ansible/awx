# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import re
import json

# Django
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField, ForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.filters import BaseFilterBackend

# AWX
from awx.main.utils import get_type_for_model, to_python_boolean
from awx.main.models.credential import CredentialType
from awx.main.models.rbac import RoleAncestorEntry


class MongoFilterBackend(BaseFilterBackend):

    # FIX: Note that MongoEngine can't use the filter backends from DRF
    def filter_queryset(self, request, queryset, view):
        return queryset


class V1CredentialFilterBackend(BaseFilterBackend):
    '''
    For /api/v1/ requests, filter out v2 (custom) credentials
    '''

    def filter_queryset(self, request, queryset, view):
        # TODO: remove in 3.3
        from awx.api.versioning import get_request_version
        if get_request_version(request) == 1:
            queryset = queryset.filter(credential_type__managed_by_tower=True)
        return queryset


class TypeFilterBackend(BaseFilterBackend):
    '''
    Filter on type field now returned with all objects.
    '''

    def filter_queryset(self, request, queryset, view):
        try:
            types = None
            for key, value in request.query_params.items():
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
        except FieldError as e:
            # Return a 400 for invalid field names.
            raise ParseError(*e.args)


class FieldLookupBackend(BaseFilterBackend):
    '''
    Filter using field lookups provided via query string parameters.
    '''

    RESERVED_NAMES = ('page', 'page_size', 'format', 'order', 'order_by',
                      'search', 'type', 'host_filter')

    SUPPORTED_LOOKUPS = ('exact', 'iexact', 'contains', 'icontains',
                         'startswith', 'istartswith', 'endswith', 'iendswith',
                         'regex', 'iregex', 'gt', 'gte', 'lt', 'lte', 'in',
                         'isnull', 'search')

    def get_field_from_lookup(self, model, lookup):
        field = None
        parts = lookup.split('__')
        if parts and parts[-1] not in self.SUPPORTED_LOOKUPS:
            parts.append('exact')
        # FIXME: Could build up a list of models used across relationships, use
        # those lookups combined with request.user.get_queryset(Model) to make
        # sure user cannot query using objects he could not view.
        new_parts = []

        # Store of all the fields used to detect repeats
        field_set = set([])

        for name in parts[:-1]:
            # HACK: Make project and inventory source filtering by old field names work for backwards compatibility.
            if model._meta.object_name in ('Project', 'InventorySource'):
                name = {
                    'current_update': 'current_job',
                    'last_update': 'last_job',
                    'last_update_failed': 'last_job_failed',
                    'last_updated': 'last_job_run',
                }.get(name, name)

            if name == 'type' and 'polymorphic_ctype' in model._meta.get_all_field_names():
                name = 'polymorphic_ctype'
                new_parts.append('polymorphic_ctype__model')
            else:
                new_parts.append(name)

            if name in getattr(model, 'PASSWORD_FIELDS', ()):
                raise PermissionDenied(_('Filtering on password fields is not allowed.'))
            elif name == 'pk':
                field = model._meta.pk
            else:
                name_alt = name.replace("_", "")
                if name_alt in model._meta.fields_map.keys():
                    field = model._meta.fields_map[name_alt]
                    new_parts.pop()
                    new_parts.append(name_alt)
                else:
                    field = model._meta.get_field_by_name(name)[0]
                if isinstance(field, ForeignObjectRel) and getattr(field.field, '__prevent_search__', False):
                    raise PermissionDenied(_('Filtering on %s is not allowed.' % name))
                elif getattr(field, '__prevent_search__', False):
                    raise PermissionDenied(_('Filtering on %s is not allowed.' % name))
            if field in field_set:
                # Field traversed twice, could create infinite JOINs, DoSing Tower
                raise ParseError(_('Loops not allowed in filters, detected on field {}.').format(field.name))
            field_set.add(field)
            model = getattr(field, 'related_model', None) or field.model

        if parts:
            new_parts.append(parts[-1])
        new_lookup = '__'.join(new_parts)
        return field, new_lookup

    def to_python_related(self, value):
        value = force_text(value)
        if value.lower() in ('none', 'null'):
            return None
        else:
            return int(value)

    def value_to_python_for_field(self, field, value):
        if isinstance(field, models.NullBooleanField):
            return to_python_boolean(value, allow_none=True)
        elif isinstance(field, models.BooleanField):
            return to_python_boolean(value)
        elif isinstance(field, (ForeignObjectRel, ManyToManyField, GenericForeignKey, ForeignKey)):
            return self.to_python_related(value)
        else:
            return field.to_python(value)

    def value_to_python(self, model, lookup, value):
        try:
            lookup = lookup.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("%r is not an allowed field name. Must be ascii encodable." % lookup)

        field, new_lookup = self.get_field_from_lookup(model, lookup)

        # Type names are stored without underscores internally, but are presented and
        # and serialized over the API containing underscores so we remove `_`
        # for polymorphic_ctype__model lookups.
        if new_lookup.startswith('polymorphic_ctype__model'):
            value = value.replace('_','')
        elif new_lookup.endswith('__isnull'):
            value = to_python_boolean(value)
        elif new_lookup.endswith('__in'):
            items = []
            if not value:
                raise ValueError('cannot provide empty value for __in')
            for item in value.split(','):
                items.append(self.value_to_python_for_field(field, item))
            value = items
        elif new_lookup.endswith('__regex') or new_lookup.endswith('__iregex'):
            try:
                re.compile(value)
            except re.error as e:
                raise ValueError(e.args[0])
        elif new_lookup.endswith('__search'):
            related_model = getattr(field, 'related_model', None)
            if not related_model:
                raise ValueError('%s is not searchable' % new_lookup[:-8])
            new_lookups = []
            for rm_field in related_model._meta.fields:
                if rm_field.name in ('username', 'first_name', 'last_name', 'email', 'name', 'description'):
                    new_lookups.append('{}__{}__icontains'.format(new_lookup[:-8], rm_field.name))
            return value, new_lookups
        else:
            value = self.value_to_python_for_field(field, value)
        return value, new_lookup

    def filter_queryset(self, request, queryset, view):
        try:
            # Apply filters specified via query_params. Each entry in the lists
            # below is (negate, field, value).
            and_filters = []
            or_filters = []
            chain_filters = []
            role_filters = []
            search_filters = []
            for key, values in request.query_params.lists():
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

                # RBAC filtering
                if key == 'role_level':
                    role_filters.append(values[0])
                    continue

                # Search across related objects.
                if key.endswith('__search'):
                    for value in values:
                        for search_term in force_text(value).replace(',', ' ').split():
                            search_value, new_keys = self.value_to_python(queryset.model, key, search_term)
                            assert isinstance(new_keys, list)
                            for new_key in new_keys:
                                search_filters.append((new_key, search_value))
                    continue

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

                # Make legacy v1 Job/Template fields work for backwards compatability
                # TODO: remove after API v1 deprecation period
                if queryset.model._meta.object_name in ('JobTemplate', 'Job') and key in ('cloud_credential', 'network_credential'):
                    key = 'extra_credentials'

                # Make legacy v1 Credential fields work for backwards compatability
                # TODO: remove after API v1 deprecation period
                #
                # convert v1 `Credential.kind` queries to `Credential.credential_type__pk`
                if queryset.model._meta.object_name == 'Credential' and key == 'kind':
                    key = key.replace('kind', 'credential_type')

                    if 'ssh' in values:
                        # In 3.2, SSH and Vault became separate credential types, but in the v1 API,
                        # they're both still "kind=ssh"
                        # under the hood, convert `/api/v1/credentials/?kind=ssh` to
                        # `/api/v1/credentials/?or__credential_type=<ssh_pk>&or__credential_type=<vault_pk>`
                        values = set(values)
                        values.add('vault')
                        values = list(values)
                        q_or = True

                    for i, kind in enumerate(values):
                        if kind == 'vault':
                            type_ = CredentialType.objects.get(kind=kind)
                        else:
                            type_ = CredentialType.from_v1_kind(kind)
                        if type_ is None:
                            raise ParseError(_('cannot filter on kind %s') % kind)
                        values[i] = type_.pk

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
            if and_filters or or_filters or chain_filters or role_filters or search_filters:
                args = []
                for n, k, v in and_filters:
                    if n:
                        args.append(~Q(**{k:v}))
                    else:
                        args.append(Q(**{k:v}))
                for role_name in role_filters:
                    args.append(
                        Q(pk__in=RoleAncestorEntry.objects.filter(
                            ancestor__in=request.user.roles.all(),
                            content_type_id=ContentType.objects.get_for_model(queryset.model).id,
                            role_field=role_name
                        ).values_list('object_id').distinct())
                    )
                if or_filters:
                    q = Q()
                    for n,k,v in or_filters:
                        if n:
                            q |= ~Q(**{k:v})
                        else:
                            q |= Q(**{k:v})
                    args.append(q)
                if search_filters:
                    q = Q()
                    for k,v in search_filters:
                        q |= Q(**{k:v})
                    args.append(q)
                for n,k,v in chain_filters:
                    if n:
                        q = ~Q(**{k:v})
                    else:
                        q = Q(**{k:v})
                    queryset = queryset.filter(q)
                queryset = queryset.filter(*args).distinct()
            return queryset
        except (FieldError, FieldDoesNotExist, ValueError, TypeError) as e:
            raise ParseError(e.args[0])
        except ValidationError as e:
            raise ParseError(json.dumps(e.messages, ensure_ascii=False))


class OrderByBackend(BaseFilterBackend):
    '''
    Filter to apply ordering based on query string parameters.
    '''

    def filter_queryset(self, request, queryset, view):
        try:
            order_by = None
            for key, value in request.query_params.items():
                if key in ('order', 'order_by'):
                    order_by = value
                    if ',' in value:
                        order_by = value.split(',')
                    else:
                        order_by = (value,)
            if order_by:
                order_by = self._strip_sensitive_model_fields(queryset.model, order_by)

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
        except FieldError as e:
            # Return a 400 for invalid field names.
            raise ParseError(*e.args)

    def _strip_sensitive_model_fields(self, model, order_by):
        for field_name in order_by:
            # strip off the negation prefix `-` if it exists
            _field_name = field_name.split('-')[-1]
            try:
                # if the field name is encrypted/sensitive, don't sort on it
                if _field_name in getattr(model, 'PASSWORD_FIELDS', ()) or \
                        getattr(model._meta.get_field(_field_name), '__prevent_search__', False):
                    raise ParseError(_('cannot order by field %s') % _field_name)
            except FieldDoesNotExist:
                pass
            yield field_name
