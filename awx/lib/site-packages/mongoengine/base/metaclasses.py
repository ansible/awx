import warnings

import pymongo

from mongoengine.common import _import_class
from mongoengine.errors import InvalidDocumentError
from mongoengine.python_support import PY3
from mongoengine.queryset import (DO_NOTHING, DoesNotExist,
                                  MultipleObjectsReturned,
                                  QuerySet, QuerySetManager)

from mongoengine.base.common import _document_registry, ALLOW_INHERITANCE
from mongoengine.base.fields import BaseField, ComplexBaseField, ObjectIdField

__all__ = ('DocumentMetaclass', 'TopLevelDocumentMetaclass')


class DocumentMetaclass(type):

    """Metaclass for all documents.
    """

    def __new__(cls, name, bases, attrs):
        flattened_bases = cls._get_bases(bases)
        super_new = super(DocumentMetaclass, cls).__new__

        # If a base class just call super
        metaclass = attrs.get('my_metaclass')
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        attrs['_is_document'] = attrs.get('_is_document', False)
        attrs['_cached_reference_fields'] = []

        # EmbeddedDocuments could have meta data for inheritance
        if 'meta' in attrs:
            attrs['_meta'] = attrs.pop('meta')

        # EmbeddedDocuments should inherit meta data
        if '_meta' not in attrs:
            meta = MetaDict()
            for base in flattened_bases[::-1]:
                # Add any mixin metadata from plain objects
                if hasattr(base, 'meta'):
                    meta.merge(base.meta)
                elif hasattr(base, '_meta'):
                    meta.merge(base._meta)
            attrs['_meta'] = meta
            attrs['_meta']['abstract'] = False  # 789: EmbeddedDocument shouldn't inherit abstract

        if attrs['_meta'].get('allow_inheritance', ALLOW_INHERITANCE):
            StringField = _import_class('StringField')
            attrs['_cls'] = StringField()

        # Handle document Fields

        # Merge all fields from subclasses
        doc_fields = {}
        for base in flattened_bases[::-1]:
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)

            # Standard object mixin - merge in any Fields
            if not hasattr(base, '_meta'):
                base_fields = {}
                for attr_name, attr_value in base.__dict__.iteritems():
                    if not isinstance(attr_value, BaseField):
                        continue
                    attr_value.name = attr_name
                    if not attr_value.db_field:
                        attr_value.db_field = attr_name
                    base_fields[attr_name] = attr_value

                doc_fields.update(base_fields)

        # Discover any document fields
        field_names = {}
        for attr_name, attr_value in attrs.iteritems():
            if not isinstance(attr_value, BaseField):
                continue
            attr_value.name = attr_name
            if not attr_value.db_field:
                attr_value.db_field = attr_name
            doc_fields[attr_name] = attr_value

            # Count names to ensure no db_field redefinitions
            field_names[attr_value.db_field] = field_names.get(
                attr_value.db_field, 0) + 1

        # Ensure no duplicate db_fields
        duplicate_db_fields = [k for k, v in field_names.items() if v > 1]
        if duplicate_db_fields:
            msg = ("Multiple db_fields defined for: %s " %
                   ", ".join(duplicate_db_fields))
            raise InvalidDocumentError(msg)

        # Set _fields and db_field maps
        attrs['_fields'] = doc_fields
        attrs['_db_field_map'] = dict([(k, getattr(v, 'db_field', k))
                                       for k, v in doc_fields.iteritems()])
        attrs['_reverse_db_field_map'] = dict(
            (v, k) for k, v in attrs['_db_field_map'].iteritems())

        attrs['_fields_ordered'] = tuple(i[1] for i in sorted(
                                         (v.creation_counter, v.name)
                                         for v in doc_fields.itervalues()))

        #
        # Set document hierarchy
        #
        superclasses = ()
        class_name = [name]
        for base in flattened_bases:
            if (not getattr(base, '_is_base_cls', True) and
                    not getattr(base, '_meta', {}).get('abstract', True)):
                # Collate heirarchy for _cls and _subclasses
                class_name.append(base.__name__)

            if hasattr(base, '_meta'):
                # Warn if allow_inheritance isn't set and prevent
                # inheritance of classes where inheritance is set to False
                allow_inheritance = base._meta.get('allow_inheritance',
                                                   ALLOW_INHERITANCE)
                if (allow_inheritance is not True and
                        not base._meta.get('abstract')):
                    raise ValueError('Document %s may not be subclassed' %
                                     base.__name__)

        # Get superclasses from last base superclass
        document_bases = [b for b in flattened_bases
                          if hasattr(b, '_class_name')]
        if document_bases:
            superclasses = document_bases[0]._superclasses
            superclasses += (document_bases[0]._class_name, )

        _cls = '.'.join(reversed(class_name))
        attrs['_class_name'] = _cls
        attrs['_superclasses'] = superclasses
        attrs['_subclasses'] = (_cls, )
        attrs['_types'] = attrs['_subclasses']  # TODO depreciate _types

        # Create the new_class
        new_class = super_new(cls, name, bases, attrs)

        # Set _subclasses
        for base in document_bases:
            if _cls not in base._subclasses:
                base._subclasses += (_cls,)
            base._types = base._subclasses   # TODO depreciate _types

        (Document, EmbeddedDocument, DictField,
         CachedReferenceField) = cls._import_classes()

        if issubclass(new_class, Document):
            new_class._collection = None

        # Add class to the _document_registry
        _document_registry[new_class._class_name] = new_class

        # In Python 2, User-defined methods objects have special read-only
        # attributes 'im_func' and 'im_self' which contain the function obj
        # and class instance object respectively.  With Python 3 these special
        # attributes have been replaced by __func__ and __self__.  The Blinker
        # module continues to use im_func and im_self, so the code below
        # copies __func__ into im_func and __self__ into im_self for
        # classmethod objects in Document derived classes.
        if PY3:
            for key, val in new_class.__dict__.items():
                if isinstance(val, classmethod):
                    f = val.__get__(new_class)
                    if hasattr(f, '__func__') and not hasattr(f, 'im_func'):
                        f.__dict__.update({'im_func': getattr(f, '__func__')})
                    if hasattr(f, '__self__') and not hasattr(f, 'im_self'):
                        f.__dict__.update({'im_self': getattr(f, '__self__')})

        # Handle delete rules
        for field in new_class._fields.itervalues():
            f = field
            f.owner_document = new_class
            delete_rule = getattr(f, 'reverse_delete_rule', DO_NOTHING)
            if isinstance(f, CachedReferenceField):

                if issubclass(new_class, EmbeddedDocument):
                    raise InvalidDocumentError(
                        "CachedReferenceFields is not allowed in EmbeddedDocuments")
                if not f.document_type:
                    raise InvalidDocumentError(
                        "Document is not avaiable to sync")

                if f.auto_sync:
                    f.start_listener()

                f.document_type._cached_reference_fields.append(f)

            if isinstance(f, ComplexBaseField) and hasattr(f, 'field'):
                delete_rule = getattr(f.field,
                                      'reverse_delete_rule',
                                      DO_NOTHING)
                if isinstance(f, DictField) and delete_rule != DO_NOTHING:
                    msg = ("Reverse delete rules are not supported "
                           "for %s (field: %s)" %
                           (field.__class__.__name__, field.name))
                    raise InvalidDocumentError(msg)

                f = field.field

            if delete_rule != DO_NOTHING:
                if issubclass(new_class, EmbeddedDocument):
                    msg = ("Reverse delete rules are not supported for "
                           "EmbeddedDocuments (field: %s)" % field.name)
                    raise InvalidDocumentError(msg)
                f.document_type.register_delete_rule(new_class,
                                                     field.name, delete_rule)

            if (field.name and hasattr(Document, field.name) and
                    EmbeddedDocument not in new_class.mro()):
                msg = ("%s is a document method and not a valid "
                       "field name" % field.name)
                raise InvalidDocumentError(msg)

        return new_class

    def add_to_class(self, name, value):
        setattr(self, name, value)

    @classmethod
    def _get_bases(cls, bases):
        if isinstance(bases, BasesTuple):
            return bases
        seen = []
        bases = cls.__get_bases(bases)
        unique_bases = (b for b in bases if not (b in seen or seen.append(b)))
        return BasesTuple(unique_bases)

    @classmethod
    def __get_bases(cls, bases):
        for base in bases:
            if base is object:
                continue
            yield base
            for child_base in cls.__get_bases(base.__bases__):
                yield child_base

    @classmethod
    def _import_classes(cls):
        Document = _import_class('Document')
        EmbeddedDocument = _import_class('EmbeddedDocument')
        DictField = _import_class('DictField')
        CachedReferenceField = _import_class('CachedReferenceField')
        return (Document, EmbeddedDocument, DictField, CachedReferenceField)


class TopLevelDocumentMetaclass(DocumentMetaclass):

    """Metaclass for top-level documents (i.e. documents that have their own
    collection in the database.
    """

    def __new__(cls, name, bases, attrs):
        flattened_bases = cls._get_bases(bases)
        super_new = super(TopLevelDocumentMetaclass, cls).__new__

        # Set default _meta data if base class, otherwise get user defined meta
        if (attrs.get('my_metaclass') == TopLevelDocumentMetaclass):
            # defaults
            attrs['_meta'] = {
                'abstract': True,
                'max_documents': None,
                'max_size': None,
                'ordering': [],  # default ordering applied at runtime
                'indexes': [],  # indexes to be ensured at runtime
                'id_field': None,
                'index_background': False,
                'index_drop_dups': False,
                'index_opts': None,
                'delete_rules': None,
                'allow_inheritance': None,
            }
            attrs['_is_base_cls'] = True
            attrs['_meta'].update(attrs.get('meta', {}))
        else:
            attrs['_meta'] = attrs.get('meta', {})
            # Explictly set abstract to false unless set
            attrs['_meta']['abstract'] = attrs['_meta'].get('abstract', False)
            attrs['_is_base_cls'] = False

        # Set flag marking as document class - as opposed to an object mixin
        attrs['_is_document'] = True

        # Ensure queryset_class is inherited
        if 'objects' in attrs:
            manager = attrs['objects']
            if hasattr(manager, 'queryset_class'):
                attrs['_meta']['queryset_class'] = manager.queryset_class

        # Clean up top level meta
        if 'meta' in attrs:
            del(attrs['meta'])

        # Find the parent document class
        parent_doc_cls = [b for b in flattened_bases
                          if b.__class__ == TopLevelDocumentMetaclass]
        parent_doc_cls = None if not parent_doc_cls else parent_doc_cls[0]

        # Prevent classes setting collection different to their parents
        # If parent wasn't an abstract class
        if (parent_doc_cls and 'collection' in attrs.get('_meta', {})
                and not parent_doc_cls._meta.get('abstract', True)):
            msg = "Trying to set a collection on a subclass (%s)" % name
            warnings.warn(msg, SyntaxWarning)
            del(attrs['_meta']['collection'])

        # Ensure abstract documents have abstract bases
        if attrs.get('_is_base_cls') or attrs['_meta'].get('abstract'):
            if (parent_doc_cls and
                    not parent_doc_cls._meta.get('abstract', False)):
                msg = "Abstract document cannot have non-abstract base"
                raise ValueError(msg)
            return super_new(cls, name, bases, attrs)

        # Merge base class metas.
        # Uses a special MetaDict that handles various merging rules
        meta = MetaDict()
        for base in flattened_bases[::-1]:
            # Add any mixin metadata from plain objects
            if hasattr(base, 'meta'):
                meta.merge(base.meta)
            elif hasattr(base, '_meta'):
                meta.merge(base._meta)

            # Set collection in the meta if its callable
            if (getattr(base, '_is_document', False) and
                    not base._meta.get('abstract')):
                collection = meta.get('collection', None)
                if callable(collection):
                    meta['collection'] = collection(base)

        meta.merge(attrs.get('_meta', {}))  # Top level meta

        # Only simple classes (direct subclasses of Document)
        # may set allow_inheritance to False
        simple_class = all([b._meta.get('abstract')
                            for b in flattened_bases if hasattr(b, '_meta')])
        if (not simple_class and meta['allow_inheritance'] is False and
                not meta['abstract']):
            raise ValueError('Only direct subclasses of Document may set '
                             '"allow_inheritance" to False')

        # Set default collection name
        if 'collection' not in meta:
            meta['collection'] = ''.join('_%s' % c if c.isupper() else c
                                         for c in name).strip('_').lower()
        attrs['_meta'] = meta

        # Call super and get the new class
        new_class = super_new(cls, name, bases, attrs)

        meta = new_class._meta

        # Set index specifications
        meta['index_specs'] = new_class._build_index_specs(meta['indexes'])

        # If collection is a callable - call it and set the value
        collection = meta.get('collection')
        if callable(collection):
            new_class._meta['collection'] = collection(new_class)

        # Provide a default queryset unless exists or one has been set
        if 'objects' not in dir(new_class):
            new_class.objects = QuerySetManager()

        # Validate the fields and set primary key if needed
        for field_name, field in new_class._fields.iteritems():
            if field.primary_key:
                # Ensure only one primary key is set
                current_pk = new_class._meta.get('id_field')
                if current_pk and current_pk != field_name:
                    raise ValueError('Cannot override primary key field')

                # Set primary key
                if not current_pk:
                    new_class._meta['id_field'] = field_name
                    new_class.id = field

        # Set primary key if not defined by the document
        new_class._auto_id_field = getattr(parent_doc_cls,
                                           '_auto_id_field', False)
        if not new_class._meta.get('id_field'):
            new_class._auto_id_field = True
            new_class._meta['id_field'] = 'id'
            new_class._fields['id'] = ObjectIdField(db_field='_id')
            new_class._fields['id'].name = 'id'
            new_class.id = new_class._fields['id']

        # Prepend id field to _fields_ordered
        if 'id' in new_class._fields and 'id' not in new_class._fields_ordered:
            new_class._fields_ordered = ('id', ) + new_class._fields_ordered

        # Merge in exceptions with parent hierarchy
        exceptions_to_merge = (DoesNotExist, MultipleObjectsReturned)
        module = attrs.get('__module__')
        for exc in exceptions_to_merge:
            name = exc.__name__
            parents = tuple(getattr(base, name) for base in flattened_bases
                            if hasattr(base, name)) or (exc,)
            # Create new exception and set to new_class
            exception = type(name, parents, {'__module__': module})
            setattr(new_class, name, exception)

        return new_class


class MetaDict(dict):

    """Custom dictionary for meta classes.
    Handles the merging of set indexes
    """
    _merge_options = ('indexes',)

    def merge(self, new_options):
        for k, v in new_options.iteritems():
            if k in self._merge_options:
                self[k] = self.get(k, []) + v
            else:
                self[k] = v


class BasesTuple(tuple):

    """Special class to handle introspection of bases tuple in __new__"""
    pass
