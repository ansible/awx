from collections import defaultdict

import pymongo
from bson import SON

from mongoengine.connection import get_connection
from mongoengine.common import _import_class
from mongoengine.errors import InvalidQueryError, LookUpError

__all__ = ('query', 'update')


COMPARISON_OPERATORS = ('ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin', 'mod',
                        'all', 'size', 'exists', 'not', 'elemMatch', 'type')
GEO_OPERATORS = ('within_distance', 'within_spherical_distance',
                 'within_box', 'within_polygon', 'near', 'near_sphere',
                 'max_distance', 'geo_within', 'geo_within_box',
                 'geo_within_polygon', 'geo_within_center',
                 'geo_within_sphere', 'geo_intersects')
STRING_OPERATORS = ('contains', 'icontains', 'startswith',
                    'istartswith', 'endswith', 'iendswith',
                    'exact', 'iexact')
CUSTOM_OPERATORS = ('match',)
MATCH_OPERATORS = (COMPARISON_OPERATORS + GEO_OPERATORS +
                   STRING_OPERATORS + CUSTOM_OPERATORS)

UPDATE_OPERATORS = ('set', 'unset', 'inc', 'dec', 'pop', 'push',
                    'push_all', 'pull', 'pull_all', 'add_to_set',
                    'set_on_insert', 'min', 'max')


def query(_doc_cls=None, _field_operation=False, **query):
    """Transform a query from Django-style format to Mongo format.
    """
    mongo_query = {}
    merge_query = defaultdict(list)
    for key, value in sorted(query.items()):
        if key == "__raw__":
            mongo_query.update(value)
            continue

        parts = key.rsplit('__')
        indices = [(i, p) for i, p in enumerate(parts) if p.isdigit()]
        parts = [part for part in parts if not part.isdigit()]
        # Check for an operator and transform to mongo-style if there is
        op = None
        if len(parts) > 1 and parts[-1] in MATCH_OPERATORS:
            op = parts.pop()

        negate = False
        if len(parts) > 1 and parts[-1] == 'not':
            parts.pop()
            negate = True

        if _doc_cls:
            # Switch field names to proper names [set in Field(name='foo')]
            try:
                fields = _doc_cls._lookup_field(parts)
            except Exception, e:
                raise InvalidQueryError(e)
            parts = []

            CachedReferenceField = _import_class('CachedReferenceField')

            cleaned_fields = []
            for field in fields:
                append_field = True
                if isinstance(field, basestring):
                    parts.append(field)
                    append_field = False
                # is last and CachedReferenceField
                elif isinstance(field, CachedReferenceField) and fields[-1] == field:
                    parts.append('%s._id' % field.db_field)
                else:
                    parts.append(field.db_field)

                if append_field:
                    cleaned_fields.append(field)

            # Convert value to proper value
            field = cleaned_fields[-1]

            singular_ops = [None, 'ne', 'gt', 'gte', 'lt', 'lte', 'not']
            singular_ops += STRING_OPERATORS
            if op in singular_ops:
                if isinstance(field, basestring):
                    if (op in STRING_OPERATORS and
                            isinstance(value, basestring)):
                        StringField = _import_class('StringField')
                        value = StringField.prepare_query_value(op, value)
                    else:
                        value = field
                else:
                    value = field.prepare_query_value(op, value)

                    if isinstance(field, CachedReferenceField) and value:
                        value = value['_id']

            elif op in ('in', 'nin', 'all', 'near') and not isinstance(value, dict):
                # 'in', 'nin' and 'all' require a list of values
                value = [field.prepare_query_value(op, v) for v in value]

        # if op and op not in COMPARISON_OPERATORS:
        if op:
            if op in GEO_OPERATORS:
                value = _geo_operator(field, op, value)
            elif op in CUSTOM_OPERATORS:
                if op in ('elem_match', 'match'):
                    value = field.prepare_query_value(op, value)
                    value = {"$elemMatch": value}
                else:
                    NotImplementedError("Custom method '%s' has not "
                                        "been implemented" % op)
            elif op not in STRING_OPERATORS:
                value = {'$' + op: value}

        if negate:
            value = {'$not': value}

        for i, part in indices:
            parts.insert(i, part)
        key = '.'.join(parts)
        if op is None or key not in mongo_query:
            mongo_query[key] = value
        elif key in mongo_query:
            if key in mongo_query and isinstance(mongo_query[key], dict):
                mongo_query[key].update(value)
                # $maxDistance needs to come last - convert to SON
                value_dict = mongo_query[key]
                if ('$maxDistance' in value_dict and '$near' in value_dict):
                    value_son = SON()
                    if isinstance(value_dict['$near'], dict):
                        for k, v in value_dict.iteritems():
                            if k == '$maxDistance':
                                continue
                            value_son[k] = v
                        if (get_connection().max_wire_version <= 1):
                            value_son['$maxDistance'] = value_dict[
                                '$maxDistance']
                        else:
                            value_son['$near'] = SON(value_son['$near'])
                            value_son['$near'][
                                '$maxDistance'] = value_dict['$maxDistance']
                    else:
                        for k, v in value_dict.iteritems():
                            if k == '$maxDistance':
                                continue
                            value_son[k] = v
                        value_son['$maxDistance'] = value_dict['$maxDistance']

                    mongo_query[key] = value_son
            else:
                # Store for manually merging later
                merge_query[key].append(value)

    # The queryset has been filter in such a way we must manually merge
    for k, v in merge_query.items():
        merge_query[k].append(mongo_query[k])
        del mongo_query[k]
        if isinstance(v, list):
            value = [{k: val} for val in v]
            if '$and' in mongo_query.keys():
                mongo_query['$and'].extend(value)
            else:
                mongo_query['$and'] = value

    return mongo_query


def update(_doc_cls=None, **update):
    """Transform an update spec from Django-style format to Mongo format.
    """
    mongo_update = {}
    for key, value in update.items():
        if key == "__raw__":
            mongo_update.update(value)
            continue
        parts = key.split('__')
        # if there is no operator, default to "set"
        if len(parts) < 3 and parts[0] not in UPDATE_OPERATORS:
            parts.insert(0, 'set')
        # Check for an operator and transform to mongo-style if there is
        op = None
        if parts[0] in UPDATE_OPERATORS:
            op = parts.pop(0)
            # Convert Pythonic names to Mongo equivalents
            if op in ('push_all', 'pull_all'):
                op = op.replace('_all', 'All')
            elif op == 'dec':
                # Support decrement by flipping a positive value's sign
                # and using 'inc'
                op = 'inc'
                if value > 0:
                    value = -value
            elif op == 'add_to_set':
                op = 'addToSet'
            elif op == 'set_on_insert':
                op = "setOnInsert"

        match = None
        if parts[-1] in COMPARISON_OPERATORS:
            match = parts.pop()

        if _doc_cls:
            # Switch field names to proper names [set in Field(name='foo')]
            try:
                fields = _doc_cls._lookup_field(parts)
            except Exception, e:
                raise InvalidQueryError(e)
            parts = []

            cleaned_fields = []
            appended_sub_field = False
            for field in fields:
                append_field = True
                if isinstance(field, basestring):
                    # Convert the S operator to $
                    if field == 'S':
                        field = '$'
                    parts.append(field)
                    append_field = False
                else:
                    parts.append(field.db_field)
                if append_field:
                    appended_sub_field = False
                    cleaned_fields.append(field)
                    if hasattr(field, 'field'):
                        cleaned_fields.append(field.field)
                        appended_sub_field = True

            # Convert value to proper value
            if appended_sub_field:
                field = cleaned_fields[-2]
            else:
                field = cleaned_fields[-1]

            GeoJsonBaseField = _import_class("GeoJsonBaseField")
            if isinstance(field, GeoJsonBaseField):
                value = field.to_mongo(value)

            if op in (None, 'set', 'push', 'pull'):
                if field.required or value is not None:
                    value = field.prepare_query_value(op, value)
            elif op in ('pushAll', 'pullAll'):
                value = [field.prepare_query_value(op, v) for v in value]
            elif op in ('addToSet', 'setOnInsert'):
                if isinstance(value, (list, tuple, set)):
                    value = [field.prepare_query_value(op, v) for v in value]
                elif field.required or value is not None:
                    value = field.prepare_query_value(op, value)
            elif op == "unset":
                value = 1

        if match:
            match = '$' + match
            value = {match: value}

        key = '.'.join(parts)

        if not op:
            raise InvalidQueryError("Updates must supply an operation "
                                    "eg: set__FIELD=value")

        if 'pull' in op and '.' in key:
            # Dot operators don't work on pull operations
            # unless they point to a list field
            # Otherwise it uses nested dict syntax
            if op == 'pullAll':
                raise InvalidQueryError("pullAll operations only support "
                                        "a single field depth")

            # Look for the last list field and use dot notation until there
            field_classes = [c.__class__ for c in cleaned_fields]
            field_classes.reverse()
            ListField = _import_class('ListField')
            if ListField in field_classes:
                # Join all fields via dot notation to the last ListField
                # Then process as normal
                last_listField = len(
                    cleaned_fields) - field_classes.index(ListField)
                key = ".".join(parts[:last_listField])
                parts = parts[last_listField:]
                parts.insert(0, key)

            parts.reverse()
            for key in parts:
                value = {key: value}
        elif op == 'addToSet' and isinstance(value, list):
            value = {key: {"$each": value}}
        else:
            value = {key: value}
        key = '$' + op

        if key not in mongo_update:
            mongo_update[key] = value
        elif key in mongo_update and isinstance(mongo_update[key], dict):
            mongo_update[key].update(value)

    return mongo_update


def _geo_operator(field, op, value):
    """Helper to return the query for a given geo query"""
    if field._geo_index == pymongo.GEO2D:
        if op == "within_distance":
            value = {'$within': {'$center': value}}
        elif op == "within_spherical_distance":
            value = {'$within': {'$centerSphere': value}}
        elif op == "within_polygon":
            value = {'$within': {'$polygon': value}}
        elif op == "near":
            value = {'$near': value}
        elif op == "near_sphere":
            value = {'$nearSphere': value}
        elif op == 'within_box':
            value = {'$within': {'$box': value}}
        elif op == "max_distance":
            value = {'$maxDistance': value}
        else:
            raise NotImplementedError("Geo method '%s' has not "
                                      "been implemented for a GeoPointField" % op)
    else:
        if op == "geo_within":
            value = {"$geoWithin": _infer_geometry(value)}
        elif op == "geo_within_box":
            value = {"$geoWithin": {"$box": value}}
        elif op == "geo_within_polygon":
            value = {"$geoWithin": {"$polygon": value}}
        elif op == "geo_within_center":
            value = {"$geoWithin": {"$center": value}}
        elif op == "geo_within_sphere":
            value = {"$geoWithin": {"$centerSphere": value}}
        elif op == "geo_intersects":
            value = {"$geoIntersects": _infer_geometry(value)}
        elif op == "near":
            value = {'$near': _infer_geometry(value)}
        elif op == "max_distance":
            value = {'$maxDistance': value}
        else:
            raise NotImplementedError("Geo method '%s' has not "
                                      "been implemented for a %s " % (op, field._name))
    return value


def _infer_geometry(value):
    """Helper method that tries to infer the $geometry shape for a given value"""
    if isinstance(value, dict):
        if "$geometry" in value:
            return value
        elif 'coordinates' in value and 'type' in value:
            return {"$geometry": value}
        raise InvalidQueryError("Invalid $geometry dictionary should have "
                                "type and coordinates keys")
    elif isinstance(value, (list, set)):
        try:
            value[0][0][0]
            return {"$geometry": {"type": "Polygon", "coordinates": value}}
        except:
            pass
        try:
            value[0][0]
            return {"$geometry": {"type": "LineString", "coordinates": value}}
        except:
            pass
        try:
            value[0]
            return {"$geometry": {"type": "Point", "coordinates": value}}
        except:
            pass

    raise InvalidQueryError("Invalid $geometry data. Can be either a dictionary "
                            "or (nested) lists of coordinate(s)")
