import copy
import operator
import numbers
from collections import Hashable
from functools import partial

import pymongo
from bson import json_util, ObjectId
from bson.dbref import DBRef
from bson.son import SON

from mongoengine import signals
from mongoengine.common import _import_class
from mongoengine.errors import (ValidationError, InvalidDocumentError,
                                LookUpError, FieldDoesNotExist)
from mongoengine.python_support import PY3, txt_type

from mongoengine.base.common import get_document, ALLOW_INHERITANCE
from mongoengine.base.datastructures import (
    BaseDict,
    BaseList,
    EmbeddedDocumentList,
    StrictDict,
    SemiStrictDict
)
from mongoengine.base.fields import ComplexBaseField

__all__ = ('BaseDocument', 'NON_FIELD_ERRORS')

NON_FIELD_ERRORS = '__all__'


class BaseDocument(object):
    __slots__ = ('_changed_fields', '_initialised', '_created', '_data',
                 '_dynamic_fields', '_auto_id_field', '_db_field_map', '__weakref__')

    _dynamic = False
    _dynamic_lock = True
    STRICT = False

    def __init__(self, *args, **values):
        """
        Initialise a document or embedded document

        :param __auto_convert: Try and will cast python objects to Object types
        :param values: A dictionary of values for the document
        """
        self._initialised = False
        self._created = True
        if args:
            # Combine positional arguments with named arguments.
            # We only want named arguments.
            field = iter(self._fields_ordered)
            # If its an automatic id field then skip to the first defined field
            if self._auto_id_field:
                next(field)
            for value in args:
                name = next(field)
                if name in values:
                    raise TypeError(
                        "Multiple values for keyword argument '" + name + "'")
                values[name] = value

        __auto_convert = values.pop("__auto_convert", True)

        # 399: set default values only to fields loaded from DB
        __only_fields = set(values.pop("__only_fields", values))

        _created = values.pop("_created", True)

        signals.pre_init.send(self.__class__, document=self, values=values)

        # Check if there are undefined fields supplied, if so raise an
        # Exception.
        if not self._dynamic:
            for var in values.keys():
                if var not in self._fields.keys() + ['id', 'pk', '_cls', '_text_score']:
                    msg = (
                        "The field '{0}' does not exist on the document '{1}'"
                    ).format(var, self._class_name)
                    raise FieldDoesNotExist(msg)

        if self.STRICT and not self._dynamic:
            self._data = StrictDict.create(allowed_keys=self._fields_ordered)()
        else:
            self._data = SemiStrictDict.create(
                allowed_keys=self._fields_ordered)()

        self._data = {}
        self._dynamic_fields = SON()

        # Assign default values to instance
        for key, field in self._fields.iteritems():
            if self._db_field_map.get(key, key) in __only_fields:
                continue
            value = getattr(self, key, None)
            setattr(self, key, value)

        if "_cls" not in values:
            self._cls = self._class_name

        # Set passed values after initialisation
        if self._dynamic:
            dynamic_data = {}
            for key, value in values.iteritems():
                if key in self._fields or key == '_id':
                    setattr(self, key, value)
                elif self._dynamic:
                    dynamic_data[key] = value
        else:
            FileField = _import_class('FileField')
            for key, value in values.iteritems():
                if key == '__auto_convert':
                    continue
                key = self._reverse_db_field_map.get(key, key)
                if key in self._fields or key in ('id', 'pk', '_cls'):
                    if __auto_convert and value is not None:
                        field = self._fields.get(key)
                        if field and not isinstance(field, FileField):
                            value = field.to_python(value)
                    setattr(self, key, value)
                else:
                    self._data[key] = value

        # Set any get_fieldname_display methods
        self.__set_field_display()

        if self._dynamic:
            self._dynamic_lock = False
            for key, value in dynamic_data.iteritems():
                setattr(self, key, value)

        # Flag initialised
        self._initialised = True
        self._created = _created
        signals.post_init.send(self.__class__, document=self)

    def __delattr__(self, *args, **kwargs):
        """Handle deletions of fields"""
        field_name = args[0]
        if field_name in self._fields:
            default = self._fields[field_name].default
            if callable(default):
                default = default()
            setattr(self, field_name, default)
        else:
            super(BaseDocument, self).__delattr__(*args, **kwargs)

    def __setattr__(self, name, value):
        # Handle dynamic data only if an initialised dynamic document
        if self._dynamic and not self._dynamic_lock:

            field = None
            if not hasattr(self, name) and not name.startswith('_'):
                DynamicField = _import_class("DynamicField")
                field = DynamicField(db_field=name)
                field.name = name
                self._dynamic_fields[name] = field
                self._fields_ordered += (name,)

            if not name.startswith('_'):
                value = self.__expand_dynamic_values(name, value)

            # Handle marking data as changed
            if name in self._dynamic_fields:
                self._data[name] = value
                if hasattr(self, '_changed_fields'):
                    self._mark_as_changed(name)
        try:
            self__created = self._created
        except AttributeError:
            self__created = True

        if (self._is_document and not self__created and
                name in self._meta.get('shard_key', tuple()) and
                self._data.get(name) != value):
            OperationError = _import_class('OperationError')
            msg = "Shard Keys are immutable. Tried to update %s" % name
            raise OperationError(msg)

        try:
            self__initialised = self._initialised
        except AttributeError:
            self__initialised = False
        # Check if the user has created a new instance of a class
        if (self._is_document and self__initialised
                and self__created and name == self._meta['id_field']):
            super(BaseDocument, self).__setattr__('_created', False)

        super(BaseDocument, self).__setattr__(name, value)

    def __getstate__(self):
        data = {}
        for k in ('_changed_fields', '_initialised', '_created',
                  '_dynamic_fields', '_fields_ordered'):
            if hasattr(self, k):
                data[k] = getattr(self, k)
        data['_data'] = self.to_mongo()
        return data

    def __setstate__(self, data):
        if isinstance(data["_data"], SON):
            data["_data"] = self.__class__._from_son(data["_data"])._data
        for k in ('_changed_fields', '_initialised', '_created', '_data',
                  '_dynamic_fields'):
            if k in data:
                setattr(self, k, data[k])
        if '_fields_ordered' in data:
            setattr(type(self), '_fields_ordered', data['_fields_ordered'])
        dynamic_fields = data.get('_dynamic_fields') or SON()
        for k in dynamic_fields.keys():
            setattr(self, k, data["_data"].get(k))

    def __iter__(self):
        return iter(self._fields_ordered)

    def __getitem__(self, name):
        """Dictionary-style field access, return a field's value if present.
        """
        try:
            if name in self._fields_ordered:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        """Dictionary-style field access, set a field's value.
        """
        # Ensure that the field exists before settings its value
        if not self._dynamic and name not in self._fields:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        try:
            u = self.__str__()
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        repr_type = str if u is None else type(u)
        return repr_type('<%s: %s>' % (self.__class__.__name__, u))

    def __str__(self):
        if hasattr(self, '__unicode__'):
            if PY3:
                return self.__unicode__()
            else:
                return unicode(self).encode('utf-8')
        return txt_type('%s object' % self.__class__.__name__)

    def __eq__(self, other):
        if isinstance(other, self.__class__) and hasattr(other, 'id') and other.id is not None:
            return self.id == other.id
        if isinstance(other, DBRef):
            return self._get_collection_name() == other.collection and self.id == other.id
        if self.id is None:
            return self is other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if getattr(self, 'pk', None) is None:
            # For new object
            return super(BaseDocument, self).__hash__()
        else:
            return hash(self.pk)

    def clean(self):
        """
        Hook for doing document level data cleaning before validation is run.

        Any ValidationError raised by this method will not be associated with
        a particular field; it will have a special-case association with the
        field defined by NON_FIELD_ERRORS.
        """
        pass

    def get_text_score(self):
        """
        Get text score from text query
        """

        if '_text_score' not in self._data:
            raise InvalidDocumentError('This document is not originally built from a text query')

        return self._data['_text_score']

    def to_mongo(self, use_db_field=True, fields=None):
        """
        Return as SON data ready for use with MongoDB.
        """
        if not fields:
            fields = []
        
        data = SON()
        data["_id"] = None
        data['_cls'] = self._class_name
        EmbeddedDocumentField = _import_class("EmbeddedDocumentField")
        # only root fields ['test1.a', 'test2'] => ['test1', 'test2']
        root_fields = set([f.split('.')[0] for f in fields])

        for field_name in self:
            if root_fields and field_name not in root_fields:
                continue

            value = self._data.get(field_name, None)
            field = self._fields.get(field_name)

            if field is None and self._dynamic:
                field = self._dynamic_fields.get(field_name)

            if value is not None:

                if isinstance(field, (EmbeddedDocumentField)):
                    if fields:
                        key = '%s.' % field_name
                        embedded_fields = [
                            i.replace(key, '') for i in fields
                            if i.startswith(key)]

                    else:
                        embedded_fields = []

                    value = field.to_mongo(value, use_db_field=use_db_field,
                                           fields=embedded_fields)
                else:
                    value = field.to_mongo(value)

            # Handle self generating fields
            if value is None and field._auto_gen:
                value = field.generate()
                self._data[field_name] = value

            if value is not None:
                if use_db_field:
                    data[field.db_field] = value
                else:
                    data[field.name] = value

        # If "_id" has not been set, then try and set it
        Document = _import_class("Document")
        if isinstance(self, Document):
            if data["_id"] is None:
                data["_id"] = self._data.get("id", None)

        if data['_id'] is None:
            data.pop('_id')

        # Only add _cls if allow_inheritance is True
        if (not hasattr(self, '_meta') or
                not self._meta.get('allow_inheritance', ALLOW_INHERITANCE)):
            data.pop('_cls')

        return data

    def validate(self, clean=True):
        """Ensure that all fields' values are valid and that required fields
        are present.
        """
        # Ensure that each field is matched to a valid value
        errors = {}
        if clean:
            try:
                self.clean()
            except ValidationError, error:
                errors[NON_FIELD_ERRORS] = error

        # Get a list of tuples of field names and their current values
        fields = [(self._fields.get(name, self._dynamic_fields.get(name)),
                   self._data.get(name)) for name in self._fields_ordered]

        EmbeddedDocumentField = _import_class("EmbeddedDocumentField")
        GenericEmbeddedDocumentField = _import_class(
            "GenericEmbeddedDocumentField")

        for field, value in fields:
            if value is not None:
                try:
                    if isinstance(field, (EmbeddedDocumentField,
                                          GenericEmbeddedDocumentField)):
                        field._validate(value, clean=clean)
                    else:
                        field._validate(value)
                except ValidationError, error:
                    errors[field.name] = error.errors or error
                except (ValueError, AttributeError, AssertionError), error:
                    errors[field.name] = error
            elif field.required and not getattr(field, '_auto_gen', False):
                errors[field.name] = ValidationError('Field is required',
                                                     field_name=field.name)

        if errors:
            pk = "None"
            if hasattr(self, 'pk'):
                pk = self.pk
            elif self._instance and hasattr(self._instance, 'pk'):
                pk = self._instance.pk
            message = "ValidationError (%s:%s) " % (self._class_name, pk)
            raise ValidationError(message, errors=errors)

    def to_json(self, *args, **kwargs):
        """Converts a document to JSON.
        :param use_db_field: Set to True by default but enables the output of the json structure with the field names and not the mongodb store db_names in case of set to False
        """
        use_db_field = kwargs.pop('use_db_field', True)
        return json_util.dumps(self.to_mongo(use_db_field),  *args, **kwargs)

    @classmethod
    def from_json(cls, json_data, created=False):
        """Converts json data to an unsaved document instance"""
        return cls._from_son(json_util.loads(json_data), created=created)

    def __expand_dynamic_values(self, name, value):
        """expand any dynamic values to their correct types / values"""
        if not isinstance(value, (dict, list, tuple)):
            return value

        EmbeddedDocumentListField = _import_class('EmbeddedDocumentListField')

        is_list = False
        if not hasattr(value, 'items'):
            is_list = True
            value = dict([(k, v) for k, v in enumerate(value)])

        if not is_list and '_cls' in value:
            cls = get_document(value['_cls'])
            return cls(**value)

        data = {}
        for k, v in value.items():
            key = name if is_list else k
            data[k] = self.__expand_dynamic_values(key, v)

        if is_list:  # Convert back to a list
            data_items = sorted(data.items(), key=operator.itemgetter(0))
            value = [v for k, v in data_items]
        else:
            value = data

        # Convert lists / values so we can watch for any changes on them
        if (isinstance(value, (list, tuple)) and
                not isinstance(value, BaseList)):
            if issubclass(type(self), EmbeddedDocumentListField):
                value = EmbeddedDocumentList(value, self, name)
            else:
                value = BaseList(value, self, name)
        elif isinstance(value, dict) and not isinstance(value, BaseDict):
            value = BaseDict(value, self, name)

        return value

    def _mark_as_changed(self, key):
        """Marks a key as explicitly changed by the user
        """
        if not key:
            return

        if not hasattr(self, '_changed_fields'):
            return

        if '.' in key:
            key, rest = key.split('.', 1)
            key = self._db_field_map.get(key, key)
            key = '%s.%s' % (key, rest)
        else:
            key = self._db_field_map.get(key, key)

        if key not in self._changed_fields:
            self._changed_fields.append(key)

    def _clear_changed_fields(self):
        """Using get_changed_fields iterate and remove any fields that are
        marked as changed"""
        for changed in self._get_changed_fields():
            parts = changed.split(".")
            data = self
            for part in parts:
                if isinstance(data, list):
                    try:
                        data = data[int(part)]
                    except IndexError:
                        data = None
                elif isinstance(data, dict):
                    data = data.get(part, None)
                else:
                    data = getattr(data, part, None)
                if hasattr(data, "_changed_fields"):
                    if hasattr(data, "_is_document") and data._is_document:
                        continue
                    data._changed_fields = []
        self._changed_fields = []

    def _nestable_types_changed_fields(self, changed_fields, key, data, inspected):
        # Loop list / dict fields as they contain documents
        # Determine the iterator to use
        if not hasattr(data, 'items'):
            iterator = enumerate(data)
        else:
            iterator = data.iteritems()

        for index, value in iterator:
            list_key = "%s%s." % (key, index)
            # don't check anything lower if this key is already marked
            # as changed.
            if list_key[:-1] in changed_fields:
                continue
            if hasattr(value, '_get_changed_fields'):
                changed = value._get_changed_fields(inspected)
                changed_fields += ["%s%s" % (list_key, k)
                                   for k in changed if k]
            elif isinstance(value, (list, tuple, dict)):
                self._nestable_types_changed_fields(
                    changed_fields, list_key, value, inspected)

    def _get_changed_fields(self, inspected=None):
        """Returns a list of all fields that have explicitly been changed.
        """
        EmbeddedDocument = _import_class("EmbeddedDocument")
        DynamicEmbeddedDocument = _import_class("DynamicEmbeddedDocument")
        ReferenceField = _import_class("ReferenceField")
        changed_fields = []
        changed_fields += getattr(self, '_changed_fields', [])

        inspected = inspected or set()
        if hasattr(self, 'id') and isinstance(self.id, Hashable):
            if self.id in inspected:
                return changed_fields
            inspected.add(self.id)

        for field_name in self._fields_ordered:
            db_field_name = self._db_field_map.get(field_name, field_name)
            key = '%s.' % db_field_name
            data = self._data.get(field_name, None)
            field = self._fields.get(field_name)

            if hasattr(data, 'id'):
                if data.id in inspected:
                    continue
                inspected.add(data.id)
            if isinstance(field, ReferenceField):
                continue
            elif (isinstance(data, (EmbeddedDocument, DynamicEmbeddedDocument))
                  and db_field_name not in changed_fields):
                 # Find all embedded fields that have been changed
                changed = data._get_changed_fields(inspected)
                changed_fields += ["%s%s" % (key, k) for k in changed if k]
            elif (isinstance(data, (list, tuple, dict)) and
                    db_field_name not in changed_fields):
                if (hasattr(field, 'field') and
                        isinstance(field.field, ReferenceField)):
                    continue
                self._nestable_types_changed_fields(
                    changed_fields, key, data, inspected)
        return changed_fields

    def _delta(self):
        """Returns the delta (set, unset) of the changes for a document.
        Gets any values that have been explicitly changed.
        """
        # Handles cases where not loaded from_son but has _id
        doc = self.to_mongo()

        set_fields = self._get_changed_fields()
        unset_data = {}
        parts = []
        if hasattr(self, '_changed_fields'):
            set_data = {}
            # Fetch each set item from its path
            for path in set_fields:
                parts = path.split('.')
                d = doc
                new_path = []
                for p in parts:
                    if isinstance(d, (ObjectId, DBRef)):
                        break
                    elif isinstance(d, list) and p.isdigit():
                        try:
                            d = d[int(p)]
                        except IndexError:
                            d = None
                    elif hasattr(d, 'get'):
                        d = d.get(p)
                    new_path.append(p)
                path = '.'.join(new_path)
                set_data[path] = d
        else:
            set_data = doc
            if '_id' in set_data:
                del(set_data['_id'])

        # Determine if any changed items were actually unset.
        for path, value in set_data.items():
            if value or isinstance(value, (numbers.Number, bool)):
                continue

            # If we've set a value that ain't the default value dont unset it.
            default = None
            if (self._dynamic and len(parts) and parts[0] in
                    self._dynamic_fields):
                del(set_data[path])
                unset_data[path] = 1
                continue
            elif path in self._fields:
                default = self._fields[path].default
            else:  # Perform a full lookup for lists / embedded lookups
                d = self
                parts = path.split('.')
                db_field_name = parts.pop()
                for p in parts:
                    if isinstance(d, list) and p.isdigit():
                        d = d[int(p)]
                    elif (hasattr(d, '__getattribute__') and
                          not isinstance(d, dict)):
                        real_path = d._reverse_db_field_map.get(p, p)
                        d = getattr(d, real_path)
                    else:
                        d = d.get(p)

                if hasattr(d, '_fields'):
                    field_name = d._reverse_db_field_map.get(db_field_name,
                                                             db_field_name)
                    if field_name in d._fields:
                        default = d._fields.get(field_name).default
                    else:
                        default = None

            if default is not None:
                if callable(default):
                    default = default()

            if default != value:
                continue

            del(set_data[path])
            unset_data[path] = 1
        return set_data, unset_data

    @classmethod
    def _get_collection_name(cls):
        """Returns the collection name for this class.
        """
        return cls._meta.get('collection', None)

    @classmethod
    def _from_son(cls, son, _auto_dereference=True, only_fields=None, created=False):
        """Create an instance of a Document (subclass) from a PyMongo SON.
        """
        if not only_fields:
            only_fields = []

        # get the class name from the document, falling back to the given
        # class if unavailable
        class_name = son.get('_cls', cls._class_name)
        data = dict(("%s" % key, value) for key, value in son.iteritems())

        # Return correct subclass for document type
        if class_name != cls._class_name:
            cls = get_document(class_name)

        changed_fields = []
        errors_dict = {}

        fields = cls._fields
        if not _auto_dereference:
            fields = copy.copy(fields)

        for field_name, field in fields.iteritems():
            field._auto_dereference = _auto_dereference
            if field.db_field in data:
                value = data[field.db_field]
                try:
                    data[field_name] = (value if value is None
                                        else field.to_python(value))
                    if field_name != field.db_field:
                        del data[field.db_field]
                except (AttributeError, ValueError), e:
                    errors_dict[field_name] = e
            elif field.default:
                default = field.default
                if callable(default):
                    default = default()
                if isinstance(default, BaseDocument):
                    changed_fields.append(field_name)
                elif not only_fields or field_name in only_fields:
                    changed_fields.append(field_name)

        if errors_dict:
            errors = "\n".join(["%s - %s" % (k, v)
                                for k, v in errors_dict.items()])
            msg = ("Invalid data to create a `%s` instance.\n%s"
                   % (cls._class_name, errors))
            raise InvalidDocumentError(msg)

        if cls.STRICT:
            data = dict((k, v)
                        for k, v in data.iteritems() if k in cls._fields)
        obj = cls(__auto_convert=False, _created=created, __only_fields=only_fields, **data)
        obj._changed_fields = changed_fields
        if not _auto_dereference:
            obj._fields = fields

        return obj

    @classmethod
    def _build_index_specs(cls, meta_indexes):
        """Generate and merge the full index specs
        """

        geo_indices = cls._geo_indices()
        unique_indices = cls._unique_with_indexes()
        index_specs = [cls._build_index_spec(spec)
                       for spec in meta_indexes]

        def merge_index_specs(index_specs, indices):
            if not indices:
                return index_specs

            spec_fields = [v['fields']
                           for k, v in enumerate(index_specs)]
            # Merge unique_indexes with existing specs
            for k, v in enumerate(indices):
                if v['fields'] in spec_fields:
                    index_specs[spec_fields.index(v['fields'])].update(v)
                else:
                    index_specs.append(v)
            return index_specs

        index_specs = merge_index_specs(index_specs, geo_indices)
        index_specs = merge_index_specs(index_specs, unique_indices)
        return index_specs

    @classmethod
    def _build_index_spec(cls, spec):
        """Build a PyMongo index spec from a MongoEngine index spec.
        """
        if isinstance(spec, basestring):
            spec = {'fields': [spec]}
        elif isinstance(spec, (list, tuple)):
            spec = {'fields': list(spec)}
        elif isinstance(spec, dict):
            spec = dict(spec)

        index_list = []
        direction = None

        # Check to see if we need to include _cls
        allow_inheritance = cls._meta.get('allow_inheritance',
                                          ALLOW_INHERITANCE)
        include_cls = (allow_inheritance and not spec.get('sparse', False) and
                       spec.get('cls',  True))

        # 733: don't include cls if index_cls is False unless there is an explicit cls with the index
        include_cls = include_cls and (spec.get('cls', False) or cls._meta.get('index_cls', True))
        if "cls" in spec:
            spec.pop('cls')
        for key in spec['fields']:
            # If inherited spec continue
            if isinstance(key, (list, tuple)):
                continue

            # ASCENDING from +
            # DESCENDING from -
            # GEO2D from *
            # TEXT from $
            direction = pymongo.ASCENDING
            if key.startswith("-"):
                direction = pymongo.DESCENDING
            elif key.startswith("*"):
                direction = pymongo.GEO2D
            elif key.startswith("$"):
                direction = pymongo.TEXT
            if key.startswith(("+", "-", "*", "$")):
                key = key[1:]

            # Use real field name, do it manually because we need field
            # objects for the next part (list field checking)
            parts = key.split('.')
            if parts in (['pk'], ['id'], ['_id']):
                key = '_id'
                fields = []
            else:
                fields = cls._lookup_field(parts)
                parts = []
                for field in fields:
                    try:
                        if field != "_id":
                            field = field.db_field
                    except AttributeError:
                        pass
                    parts.append(field)
                key = '.'.join(parts)
            index_list.append((key, direction))

        # Don't add cls to a geo index
        if include_cls and direction is not pymongo.GEO2D:
            index_list.insert(0, ('_cls', 1))

        if index_list:
            spec['fields'] = index_list
        if spec.get('sparse', False) and len(spec['fields']) > 1:
            raise ValueError(
                'Sparse indexes can only have one field in them. '
                'See https://jira.mongodb.org/browse/SERVER-2193')

        return spec

    @classmethod
    def _unique_with_indexes(cls, namespace=""):
        """
        Find and set unique indexes
        """
        unique_indexes = []
        for field_name, field in cls._fields.items():
            sparse = field.sparse
            # Generate a list of indexes needed by uniqueness constraints
            if field.unique:
                unique_fields = [field.db_field]

                # Add any unique_with fields to the back of the index spec
                if field.unique_with:
                    if isinstance(field.unique_with, basestring):
                        field.unique_with = [field.unique_with]

                    # Convert unique_with field names to real field names
                    unique_with = []
                    for other_name in field.unique_with:
                        parts = other_name.split('.')
                        # Lookup real name
                        parts = cls._lookup_field(parts)
                        name_parts = [part.db_field for part in parts]
                        unique_with.append('.'.join(name_parts))
                        # Unique field should be required
                        parts[-1].required = True
                        sparse = (not sparse and
                                  parts[-1].name not in cls.__dict__)
                    unique_fields += unique_with

                # Add the new index to the list
                fields = [("%s%s" % (namespace, f), pymongo.ASCENDING)
                          for f in unique_fields]
                index = {'fields': fields, 'unique': True, 'sparse': sparse}
                unique_indexes.append(index)

            if field.__class__.__name__ == "ListField":
                field = field.field

            # Grab any embedded document field unique indexes
            if (field.__class__.__name__ == "EmbeddedDocumentField" and
                    field.document_type != cls):
                field_namespace = "%s." % field_name
                doc_cls = field.document_type
                unique_indexes += doc_cls._unique_with_indexes(field_namespace)

        return unique_indexes

    @classmethod
    def _geo_indices(cls, inspected=None, parent_field=None):
        inspected = inspected or []
        geo_indices = []
        inspected.append(cls)

        geo_field_type_names = ["EmbeddedDocumentField", "GeoPointField",
                                "PointField", "LineStringField", "PolygonField"]

        geo_field_types = tuple([_import_class(field)
                                 for field in geo_field_type_names])

        for field in cls._fields.values():
            if not isinstance(field, geo_field_types):
                continue
            if hasattr(field, 'document_type'):
                field_cls = field.document_type
                if field_cls in inspected:
                    continue
                if hasattr(field_cls, '_geo_indices'):
                    geo_indices += field_cls._geo_indices(
                        inspected, parent_field=field.db_field)
            elif field._geo_index:
                field_name = field.db_field
                if parent_field:
                    field_name = "%s.%s" % (parent_field, field_name)
                geo_indices.append({'fields':
                                    [(field_name, field._geo_index)]})
        return geo_indices

    @classmethod
    def _lookup_field(cls, parts):
        """Lookup a field based on its attribute and return a list containing
        the field's parents and the field.
        """

        ListField = _import_class("ListField")

        if not isinstance(parts, (list, tuple)):
            parts = [parts]
        fields = []
        field = None

        for field_name in parts:
            # Handle ListField indexing:
            if field_name.isdigit() and isinstance(field, ListField):
                new_field = field.field
                fields.append(field_name)
                continue

            if field is None:
                # Look up first field from the document
                if field_name == 'pk':
                    # Deal with "primary key" alias
                    field_name = cls._meta['id_field']
                if field_name in cls._fields:
                    field = cls._fields[field_name]
                elif cls._dynamic:
                    DynamicField = _import_class('DynamicField')
                    field = DynamicField(db_field=field_name)
                elif cls._meta.get("allow_inheritance", False) or cls._meta.get("abstract", False):
                    # 744: in case the field is defined in a subclass
                    field = None
                    for subcls in cls.__subclasses__():
                        try:
                            field = subcls._lookup_field([field_name])[0]
                        except LookUpError:
                            continue

                        if field is not None:
                            break
                    else:
                        raise LookUpError('Cannot resolve field "%s"' % field_name)
                else:
                    raise LookUpError('Cannot resolve field "%s"'
                                      % field_name)
            else:
                ReferenceField = _import_class('ReferenceField')
                GenericReferenceField = _import_class('GenericReferenceField')
                if isinstance(field, (ReferenceField, GenericReferenceField)):
                    raise LookUpError('Cannot perform join in mongoDB: %s' %
                                      '__'.join(parts))
                if hasattr(getattr(field, 'field', None), 'lookup_member'):
                    new_field = field.field.lookup_member(field_name)
                else:
                   # Look up subfield on the previous field
                    new_field = field.lookup_member(field_name)
                if not new_field and isinstance(field, ComplexBaseField):
                    if hasattr(field.field, 'document_type') and cls._dynamic \
                            and field.field.document_type._dynamic:
                        DynamicField = _import_class('DynamicField')
                        new_field = DynamicField(db_field=field_name)
                    else:
                        fields.append(field_name)
                        continue
                elif not new_field and hasattr(field, 'document_type') and cls._dynamic \
                        and field.document_type._dynamic:
                    DynamicField = _import_class('DynamicField')
                    new_field = DynamicField(db_field=field_name)
                elif not new_field:
                    raise LookUpError('Cannot resolve field "%s"'
                                      % field_name)
                field = new_field  # update field to the new field type
            fields.append(field)
        return fields

    @classmethod
    def _translate_field_name(cls, field, sep='.'):
        """Translate a field attribute name to a database field name.
        """
        parts = field.split(sep)
        parts = [f.db_field for f in cls._lookup_field(parts)]
        return '.'.join(parts)

    def __set_field_display(self):
        """Dynamically set the display value for a field with choices"""
        for attr_name, field in self._fields.items():
            if field.choices:
                if self._dynamic:
                    obj = self
                else:
                    obj = type(self)
                setattr(obj,
                        'get_%s_display' % attr_name,
                        partial(self.__get_field_display, field=field))

    def __get_field_display(self, field):
        """Returns the display value for a choice field"""
        value = getattr(self, field.name)
        if field.choices and isinstance(field.choices[0], (list, tuple)):
            return dict(field.choices).get(value, value)
        return value
