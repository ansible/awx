"""System checks for bounded text fields in AWX models.

Ported from django-ansible-base#1272, with AWX app scope and check IDs. E004
checks keys containing a BoundedTextField; other SQL Server schema limitations
are outside this preparatory change.
"""

import django.apps
from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from ansible_base.lib.fields import BoundedTextField


def _referenced_field_names(expressions):
    "Field names referenced by index/constraint expressions, e.g. Index(Lower('name'))."
    names = set()
    for expression in expressions or ():
        # root F expressions have no flatten(); Django wraps positional index/constraint strings in F
        subexpressions = expression.flatten() if hasattr(expression, 'flatten') else [expression]
        for subexpression in subexpressions:
            if isinstance(subexpression, models.F) and '__' not in subexpression.name:
                names.add(subexpression.name)
    return names


def _is_indexed_or_unique(field, model):
    "Return True if the field is indexed or made unique at the field, Meta, primary-key, or constraint level."
    if field.db_index or field.unique:
        return True
    pk = model._meta.pk
    if isinstance(pk, models.CompositePrimaryKey) and field.name in pk.field_names:
        return True  # primary-key columns are indexed (and clustered) on SQL Server
    unique_together = [set(ut) for ut in model._meta.unique_together]
    if any(field.name in fields for fields in unique_together):
        return True
    for constraint in model._meta.constraints:
        if isinstance(constraint, models.UniqueConstraint) and (
            field.name in (constraint.fields or []) or field.name in _referenced_field_names(constraint.expressions)
        ):
            return True
    for index in model._meta.indexes:
        if field.name in {name.lstrip('-') for name in index.fields} or field.name in _referenced_field_names(index.expressions):
            return True
    return False


def _awx_models():
    "Concrete, non-proxy models of AWX apps."
    for model in django.apps.apps.get_models():
        if not model._meta.proxy and not model._meta.abstract and django.apps.apps.get_app_config(model._meta.app_label).name.startswith('awx.'):
            yield model


def _local_fields(model):
    "The model's declared, non-auto-created fields."
    return [field for field in model._meta.fields if not field.auto_created]


@register('mssql')
def check_textfield_indexed_is_bounded(app_configs, **kwargs):
    "Error on TextFields that carry an index or unique constraint in AWX apps; SQL Server cannot index nvarchar(max)."
    errors = []
    for model in _awx_models():
        for field in _local_fields(model):
            if isinstance(field, models.TextField) and not isinstance(field, BoundedTextField) and _is_indexed_or_unique(field, model):
                errors.append(
                    Error(
                        f'{model._meta.label}.{field.name} is an indexed or unique TextField',
                        hint=f"Use BoundedTextField for '{field.name}' in {model._meta.label}; SQL Server cannot index nvarchar(max).",
                        obj=model,
                        id='awx.E002',
                    )
                )
    return errors


# SQL Server limits index keys to 1700 bytes for the nonclustered indexes Django creates
# for Index, UniqueConstraint, and unique_together. The budget is shared by every column
# in a composite key, so the check counts them all, not just the bounded ones.
MSSQL_INDEX_KEY_BYTES = 1700
NVARCHAR_BYTES_PER_CODE_UNIT = 2

# Primary keys are clustered on SQL Server (mssql-django never emits NONCLUSTERED), so
# they face the tighter clustered limit.
MSSQL_CLUSTERED_KEY_BYTES = 900

# the three key-size helpers report under one check id
INDEX_KEY_SIZE_ERROR = 'awx.E004'

# Storage widths, in bytes, of the fixed-width SQL Server column types that appear in indexes,
# matching the mssql-django 2.0.0 DDL mappings (UUIDField is char(32); DateTimeField is
# datetime2, or datetimeoffset when USE_TZ — see _index_key_width).
MSSQL_FIELD_WIDTHS = {
    models.BooleanField: 1,
    models.SmallIntegerField: 2,
    models.IntegerField: 4,
    models.BigIntegerField: 8,
    models.FloatField: 8,
    models.DateField: 3,
    models.DateTimeField: 8,
    models.TimeField: 5,
    models.UUIDField: 32,
}


def _index_key_width(field):
    "Bytes of SQL Server index key that field's column occupies (0 for types not worth counting, e.g. plain TextField)."
    if isinstance(field, BoundedTextField):
        bound = field.sql_server_max_length
        if not isinstance(bound, int) or isinstance(bound, bool):
            return 0  # E003 reports invalid bounds; E004 must not crash while summing widths
        return NVARCHAR_BYTES_PER_CODE_UNIT * bound
    if isinstance(field, models.CharField):
        # mssql-django maps CharField to nvarchar(max_length)
        return NVARCHAR_BYTES_PER_CODE_UNIT * (field.max_length or 0)
    if isinstance(field, models.ForeignKey):
        # a foreign key column mirrors the width of the target's primary key
        return _index_key_width(field.target_field)
    # walk the type's own mro so subclasses count as themselves before their parents (DateTimeField inherits DateField but is wider)
    for field_type in type(field).__mro__:
        if field_type in MSSQL_FIELD_WIDTHS:
            if field_type is models.DateTimeField and settings.USE_TZ:
                return MSSQL_FIELD_WIDTHS[field_type] + 2  # datetimeoffset adds a time-zone offset
            return MSSQL_FIELD_WIDTHS[field_type]
    return 0


def _index_key_fields(model, field_names):
    "Resolve field_names to model fields, skipping names that do not resolve."
    fields = []
    for name in field_names:
        try:
            fields.append(model._meta.get_field(name))
        except FieldDoesNotExist:
            continue
    return fields


def _keyed_field_names(index_or_constraint):
    "Field names an index or unique constraint keys on, via fields or expressions."
    names = {name.lstrip('-') for name in (index_or_constraint.fields or [])}
    names |= _referenced_field_names(getattr(index_or_constraint, 'expressions', None))
    return names


def _model_keys(model):
    "The model's unique_together entries, unique constraints, and indexes, as (key, unique) pairs."
    yield from ((unique_together, True) for unique_together in model._meta.unique_together)
    yield from ((constraint, True) for constraint in model._meta.constraints if isinstance(constraint, models.UniqueConstraint))
    yield from ((index, bool(getattr(index, 'unique', False))) for index in model._meta.indexes)


def _pk_fields(model):
    "The primary-key fields: the pk itself, or the members of a CompositePrimaryKey."
    pk = model._meta.pk
    if isinstance(pk, models.CompositePrimaryKey):
        return _index_key_fields(model, pk.field_names)
    return [pk] if pk is not None else []


def _pk_key_width(model, field_names=()):
    "Width of the primary-key columns not already named in field_names. Non-unique indexes carry the clustered key on SQL Server."
    return sum(_index_key_width(field) for field in _pk_fields(model) if field.name not in field_names)


def _composite_pk_key_size_error(model):
    "E004 for a composite primary key whose columns exceed the clustered-index budget, or None. Only keys containing a BoundedTextField are checked."
    fields = _pk_fields(model)
    if not any(isinstance(field, BoundedTextField) for field in fields):
        return None
    key_bytes = sum(_index_key_width(field) for field in fields)
    if key_bytes <= MSSQL_CLUSTERED_KEY_BYTES:
        return None
    return Error(
        f'{model._meta.label} primary key needs {key_bytes} bytes of SQL Server index key',
        hint=f"Lower the sql_server_max_length of the BoundedTextField columns in the primary key; "
        f"primary keys are clustered on SQL Server, which limits index keys to {MSSQL_CLUSTERED_KEY_BYTES} bytes.",
        obj=model,
        id=INDEX_KEY_SIZE_ERROR,
    )


def _field_key_size_error(model, field):
    "E004 for a field-level indexed or unique BoundedTextField whose column alone exceeds the budget, or None."
    if not (isinstance(field, BoundedTextField) and (field.db_index or field.unique)):
        return None
    # a plain db_index is a non-unique index: it carries the clustered key at no extra budget for unique indexes
    key_bytes = _index_key_width(field) + (0 if field.unique else _pk_key_width(model, {field.name}))
    if key_bytes <= MSSQL_INDEX_KEY_BYTES:
        return None
    return Error(
        f'{model._meta.label}.{field.name} needs {key_bytes} bytes of SQL Server index key',
        hint=f"Lower sql_server_max_length on '{field.name}' in {model._meta.label} to 850 or less; "
        f"nvarchar takes 2 bytes per code unit and SQL Server limits nonclustered index keys to {MSSQL_INDEX_KEY_BYTES} bytes.",
        obj=model,
        id=INDEX_KEY_SIZE_ERROR,
    )


def _composite_key_size_error(model, key, unique):
    "E004 for an index or unique constraint whose columns together exceed the budget, or None. Only keys containing a BoundedTextField are checked."
    field_names = _keyed_field_names(key) if hasattr(key, 'fields') else set(key)  # unique_together entries are plain tuples of names
    fields = _index_key_fields(model, field_names)
    if not any(isinstance(field, BoundedTextField) for field in fields):
        return None
    # a non-unique index carries the clustered key; a unique index keeps the clustered key in the leaf as included columns, which do not count
    key_bytes = sum(_index_key_width(field) for field in fields) + (0 if unique else _pk_key_width(model, field_names))
    if key_bytes <= MSSQL_INDEX_KEY_BYTES:
        return None
    name = getattr(key, 'name', key)  # unique_together entries are plain tuples
    return Error(
        f'{model._meta.label} key {name} needs {key_bytes} bytes of SQL Server index key',
        hint=f"Lower the sql_server_max_length of the BoundedTextField columns in {name}; "
        f"SQL Server limits nonclustered index keys to {MSSQL_INDEX_KEY_BYTES} bytes, shared by every column in the key.",
        obj=model,
        id=INDEX_KEY_SIZE_ERROR,
    )


@register('mssql')
def check_bounded_textfield_index_key_size(app_configs, **kwargs):
    "Error when an index or unique constraint containing a BoundedTextField exceeds SQL Server's index key-size budget."
    errors = []
    for model in _awx_models():
        for field in _local_fields(model):
            if error := _field_key_size_error(model, field):
                errors.append(error)
        for key, unique in _model_keys(model):
            if error := _composite_key_size_error(model, key, unique):
                errors.append(error)
        if error := _composite_pk_key_size_error(model):
            errors.append(error)
    return errors
