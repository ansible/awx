import warnings

import hashlib
import pymongo
import re

from pymongo.read_preferences import ReadPreference
from bson import ObjectId
from bson.dbref import DBRef
from mongoengine import signals
from mongoengine.common import _import_class
from mongoengine.base import (
    DocumentMetaclass,
    TopLevelDocumentMetaclass,
    BaseDocument,
    BaseDict,
    BaseList,
    EmbeddedDocumentList,
    ALLOW_INHERITANCE,
    get_document
)
from mongoengine.errors import ValidationError, InvalidQueryError, InvalidDocumentError
from mongoengine.queryset import (OperationError, NotUniqueError,
                                  QuerySet, transform)
from mongoengine.connection import get_db, DEFAULT_CONNECTION_NAME
from mongoengine.context_managers import switch_db, switch_collection

__all__ = ('Document', 'EmbeddedDocument', 'DynamicDocument',
           'DynamicEmbeddedDocument', 'OperationError',
           'InvalidCollectionError', 'NotUniqueError', 'MapReduceDocument')


def includes_cls(fields):
    """ Helper function used for ensuring and comparing indexes
    """

    first_field = None
    if len(fields):
        if isinstance(fields[0], basestring):
            first_field = fields[0]
        elif isinstance(fields[0], (list, tuple)) and len(fields[0]):
            first_field = fields[0][0]
    return first_field == '_cls'


class InvalidCollectionError(Exception):
    pass


class EmbeddedDocument(BaseDocument):

    """A :class:`~mongoengine.Document` that isn't stored in its own
    collection.  :class:`~mongoengine.EmbeddedDocument`\ s should be used as
    fields on :class:`~mongoengine.Document`\ s through the
    :class:`~mongoengine.EmbeddedDocumentField` field type.

    A :class:`~mongoengine.EmbeddedDocument` subclass may be itself subclassed,
    to create a specialised version of the embedded document that will be
    stored in the same collection. To facilitate this behaviour a `_cls`
    field is added to documents (hidden though the MongoEngine interface).
    To disable this behaviour and remove the dependence on the presence of
    `_cls` set :attr:`allow_inheritance` to ``False`` in the :attr:`meta`
    dictionary.
    """

    __slots__ = ('_instance')

    # The __metaclass__ attribute is removed by 2to3 when running with Python3
    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = DocumentMetaclass
    __metaclass__ = DocumentMetaclass

    def __init__(self, *args, **kwargs):
        super(EmbeddedDocument, self).__init__(*args, **kwargs)
        self._instance = None
        self._changed_fields = []

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def save(self, *args, **kwargs):
        self._instance.save(*args, **kwargs)

    def reload(self, *args, **kwargs):
        self._instance.reload(*args, **kwargs)


class Document(BaseDocument):

    """The base class used for defining the structure and properties of
    collections of documents stored in MongoDB. Inherit from this class, and
    add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~mongoengine.Document` subclass.

    By default, the MongoDB collection used to store documents created using a
    :class:`~mongoengine.Document` subclass will be the name of the subclass
    converted to lowercase. A different collection may be specified by
    providing :attr:`collection` to the :attr:`meta` dictionary in the class
    definition.

    A :class:`~mongoengine.Document` subclass may be itself subclassed, to
    create a specialised version of the document that will be stored in the
    same collection. To facilitate this behaviour a `_cls`
    field is added to documents (hidden though the MongoEngine interface).
    To disable this behaviour and remove the dependence on the presence of
    `_cls` set :attr:`allow_inheritance` to ``False`` in the :attr:`meta`
    dictionary.

    A :class:`~mongoengine.Document` may use a **Capped Collection** by
    specifying :attr:`max_documents` and :attr:`max_size` in the :attr:`meta`
    dictionary. :attr:`max_documents` is the maximum number of documents that
    is allowed to be stored in the collection, and :attr:`max_size` is the
    maximum size of the collection in bytes. If :attr:`max_size` is not
    specified and :attr:`max_documents` is, :attr:`max_size` defaults to
    10000000 bytes (10MB).

    Indexes may be created by specifying :attr:`indexes` in the :attr:`meta`
    dictionary. The value should be a list of field names or tuples of field
    names. Index direction may be specified by prefixing the field names with
    a **+** or **-** sign.

    Automatic index creation can be disabled by specifying
    :attr:`auto_create_index` in the :attr:`meta` dictionary. If this is set to
    False then indexes will not be created by MongoEngine.  This is useful in
    production systems where index creation is performed as part of a
    deployment system.

    By default, _cls will be added to the start of every index (that
    doesn't contain a list) if allow_inheritance is True. This can be
    disabled by either setting cls to False on the specific index or
    by setting index_cls to False on the meta dictionary for the document.
    """

    # The __metaclass__ attribute is removed by 2to3 when running with Python3
    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = TopLevelDocumentMetaclass
    __metaclass__ = TopLevelDocumentMetaclass

    __slots__ = ('__objects')

    def pk():
        """Primary key alias
        """

        def fget(self):
            return getattr(self, self._meta['id_field'])

        def fset(self, value):
            return setattr(self, self._meta['id_field'], value)
        return property(fget, fset)
    pk = pk()

    @classmethod
    def _get_db(cls):
        """Some Model using other db_alias"""
        return get_db(cls._meta.get("db_alias", DEFAULT_CONNECTION_NAME))

    @classmethod
    def _get_collection(cls):
        """Returns the collection for the document."""
        if not hasattr(cls, '_collection') or cls._collection is None:
            db = cls._get_db()
            collection_name = cls._get_collection_name()
            # Create collection as a capped collection if specified
            if cls._meta['max_size'] or cls._meta['max_documents']:
                # Get max document limit and max byte size from meta
                max_size = cls._meta['max_size'] or 10000000  # 10MB default
                max_documents = cls._meta['max_documents']

                if collection_name in db.collection_names():
                    cls._collection = db[collection_name]
                    # The collection already exists, check if its capped
                    # options match the specified capped options
                    options = cls._collection.options()
                    if options.get('max') != max_documents or \
                       options.get('size') != max_size:
                        msg = (('Cannot create collection "%s" as a capped '
                                'collection as it already exists')
                               % cls._collection)
                        raise InvalidCollectionError(msg)
                else:
                    # Create the collection as a capped collection
                    opts = {'capped': True, 'size': max_size}
                    if max_documents:
                        opts['max'] = max_documents
                    cls._collection = db.create_collection(
                        collection_name, **opts
                    )
            else:
                cls._collection = db[collection_name]
            if cls._meta.get('auto_create_index', True):
                cls.ensure_indexes()
        return cls._collection

    def modify(self, query={}, **update):
        """Perform an atomic update of the document in the database and reload
        the document object using updated version.

        Returns True if the document has been updated or False if the document
        in the database doesn't match the query.

        .. note:: All unsaved changes that has been made to the document are
            rejected if the method returns True.

        :param query: the update will be performed only if the document in the
            database matches the query
        :param update: Django-style update keyword arguments
        """

        if self.pk is None:
            raise InvalidDocumentError("The document does not have a primary key.")

        id_field = self._meta["id_field"]
        query = query.copy() if isinstance(query, dict) else query.to_query(self)

        if id_field not in query:
            query[id_field] = self.pk
        elif query[id_field] != self.pk:
            raise InvalidQueryError("Invalid document modify query: it must modify only this document.")

        updated = self._qs(**query).modify(new=True, **update)
        if updated is None:
            return False

        for field in self._fields_ordered:
            setattr(self, field, self._reload(field, updated[field]))

        self._changed_fields = updated._changed_fields
        self._created = False

        return True

    def save(self, force_insert=False, validate=True, clean=True,
             write_concern=None,  cascade=None, cascade_kwargs=None,
             _refs=None, save_condition=None, **kwargs):
        """Save the :class:`~mongoengine.Document` to the database. If the
        document already exists, it will be updated, otherwise it will be
        created.

        :param force_insert: only try to create a new document, don't allow
            updates of existing documents
        :param validate: validates the document; set to ``False`` to skip.
        :param clean: call the document clean method, requires `validate` to be
            True.
        :param write_concern: Extra keyword arguments are passed down to
            :meth:`~pymongo.collection.Collection.save` OR
            :meth:`~pymongo.collection.Collection.insert`
            which will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        :param cascade: Sets the flag for cascading saves.  You can set a
            default by setting "cascade" in the document __meta__
        :param cascade_kwargs: (optional) kwargs dictionary to be passed throw
            to cascading saves.  Implies ``cascade=True``.
        :param _refs: A list of processed references used in cascading saves
        :param save_condition: only perform save if matching record in db
            satisfies condition(s) (e.g., version number)

        .. versionchanged:: 0.5
            In existing documents it only saves changed fields using
            set / unset.  Saves are cascaded and any
            :class:`~bson.dbref.DBRef` objects that have changes are
            saved as well.
        .. versionchanged:: 0.6
            Added cascading saves
        .. versionchanged:: 0.8
            Cascade saves are optional and default to False.  If you want
            fine grain control then you can turn off using document
            meta['cascade'] = True.  Also you can pass different kwargs to
            the cascade save using cascade_kwargs which overwrites the
            existing kwargs with custom values.
        .. versionchanged:: 0.8.5
            Optional save_condition that only overwrites existing documents
            if the condition is satisfied in the current db record.
        """
        signals.pre_save.send(self.__class__, document=self)

        if validate:
            self.validate(clean=clean)

        if write_concern is None:
            write_concern = {"w": 1}

        doc = self.to_mongo()

        created = ('_id' not in doc or self._created or force_insert)

        signals.pre_save_post_validation.send(self.__class__, document=self,
                                              created=created)

        try:
            collection = self._get_collection()
            if self._meta.get('auto_create_index', True):
                self.ensure_indexes()
            if created:
                if force_insert:
                    object_id = collection.insert(doc, **write_concern)
                else:
                    object_id = collection.save(doc, **write_concern)
            else:
                object_id = doc['_id']
                updates, removals = self._delta()
                # Need to add shard key to query, or you get an error
                if save_condition is not None:
                    select_dict = transform.query(self.__class__,
                                                  **save_condition)
                else:
                    select_dict = {}
                select_dict['_id'] = object_id
                shard_key = self.__class__._meta.get('shard_key', tuple())
                for k in shard_key:
                    actual_key = self._db_field_map.get(k, k)
                    select_dict[actual_key] = doc[actual_key]

                def is_new_object(last_error):
                    if last_error is not None:
                        updated = last_error.get("updatedExisting")
                        if updated is not None:
                            return not updated
                    return created

                update_query = {}

                if updates:
                    update_query["$set"] = updates
                if removals:
                    update_query["$unset"] = removals
                if updates or removals:
                    upsert = save_condition is None
                    last_error = collection.update(select_dict, update_query,
                                                   upsert=upsert, **write_concern)
                    created = is_new_object(last_error)

            if cascade is None:
                cascade = self._meta.get(
                    'cascade', False) or cascade_kwargs is not None

            if cascade:
                kwargs = {
                    "force_insert": force_insert,
                    "validate": validate,
                    "write_concern": write_concern,
                    "cascade": cascade
                }
                if cascade_kwargs:  # Allow granular control over cascades
                    kwargs.update(cascade_kwargs)
                kwargs['_refs'] = _refs
                self.cascade_save(**kwargs)
        except pymongo.errors.DuplicateKeyError, err:
            message = u'Tried to save duplicate unique keys (%s)'
            raise NotUniqueError(message % unicode(err))
        except pymongo.errors.OperationFailure, err:
            message = 'Could not save document (%s)'
            if re.match('^E1100[01] duplicate key', unicode(err)):
                # E11000 - duplicate key error index
                # E11001 - duplicate key on update
                message = u'Tried to save duplicate unique keys (%s)'
                raise NotUniqueError(message % unicode(err))
            raise OperationError(message % unicode(err))
        id_field = self._meta['id_field']
        if created or id_field not in self._meta.get('shard_key', []):
            self[id_field] = self._fields[id_field].to_python(object_id)

        signals.post_save.send(self.__class__, document=self, created=created)
        self._clear_changed_fields()
        self._created = False
        return self

    def cascade_save(self, *args, **kwargs):
        """Recursively saves any references /
           generic references on an objects"""
        _refs = kwargs.get('_refs', []) or []

        ReferenceField = _import_class('ReferenceField')
        GenericReferenceField = _import_class('GenericReferenceField')

        for name, cls in self._fields.items():
            if not isinstance(cls, (ReferenceField,
                                    GenericReferenceField)):
                continue

            ref = self._data.get(name)
            if not ref or isinstance(ref, DBRef):
                continue

            if not getattr(ref, '_changed_fields', True):
                continue

            ref_id = "%s,%s" % (ref.__class__.__name__, str(ref._data))
            if ref and ref_id not in _refs:
                _refs.append(ref_id)
                kwargs["_refs"] = _refs
                ref.save(**kwargs)
                ref._changed_fields = []

    @property
    def _qs(self):
        """
        Returns the queryset to use for updating / reloading / deletions
        """
        if not hasattr(self, '__objects'):
            self.__objects = QuerySet(self, self._get_collection())
        return self.__objects

    @property
    def _object_key(self):
        """Dict to identify object in collection
        """
        select_dict = {'pk': self.pk}
        shard_key = self.__class__._meta.get('shard_key', tuple())
        for k in shard_key:
            select_dict[k] = getattr(self, k)
        return select_dict

    def update(self, **kwargs):
        """Performs an update on the :class:`~mongoengine.Document`
        A convenience wrapper to :meth:`~mongoengine.QuerySet.update`.

        Raises :class:`OperationError` if called on an object that has not yet
        been saved.
        """
        if not self.pk:
            if kwargs.get('upsert', False):
                query = self.to_mongo()
                if "_cls" in query:
                    del(query["_cls"])
                return self._qs.filter(**query).update_one(**kwargs)
            else:
                raise OperationError(
                    'attempt to update a document not yet saved')

        # Need to add shard key to query, or you get an error
        return self._qs.filter(**self._object_key).update_one(**kwargs)

    def delete(self, **write_concern):
        """Delete the :class:`~mongoengine.Document` from the database. This
        will only take effect if the document has been previously saved.

        :param write_concern: Extra keyword arguments are passed down which
            will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        """
        signals.pre_delete.send(self.__class__, document=self)

        try:
            self._qs.filter(
                **self._object_key).delete(write_concern=write_concern, _from_doc_delete=True)
        except pymongo.errors.OperationFailure, err:
            message = u'Could not delete document (%s)' % err.message
            raise OperationError(message)
        signals.post_delete.send(self.__class__, document=self)

    def switch_db(self, db_alias):
        """
        Temporarily switch the database for a document instance.

        Only really useful for archiving off data and calling `save()`::

            user = User.objects.get(id=user_id)
            user.switch_db('archive-db')
            user.save()

        :param str db_alias: The database alias to use for saving the document

        .. seealso::
            Use :class:`~mongoengine.context_managers.switch_collection`
            if you need to read from another collection
        """
        with switch_db(self.__class__, db_alias) as cls:
            collection = cls._get_collection()
            db = cls._get_db()
        self._get_collection = lambda: collection
        self._get_db = lambda: db
        self._collection = collection
        self._created = True
        self.__objects = self._qs
        self.__objects._collection_obj = collection
        return self

    def switch_collection(self, collection_name):
        """
        Temporarily switch the collection for a document instance.

        Only really useful for archiving off data and calling `save()`::

            user = User.objects.get(id=user_id)
            user.switch_collection('old-users')
            user.save()

        :param str collection_name: The database alias to use for saving the
            document

        .. seealso::
            Use :class:`~mongoengine.context_managers.switch_db`
            if you need to read from another database
        """
        with switch_collection(self.__class__, collection_name) as cls:
            collection = cls._get_collection()
        self._get_collection = lambda: collection
        self._collection = collection
        self._created = True
        self.__objects = self._qs
        self.__objects._collection_obj = collection
        return self

    def select_related(self, max_depth=1):
        """Handles dereferencing of :class:`~bson.dbref.DBRef` objects to
        a maximum depth in order to cut down the number queries to mongodb.

        .. versionadded:: 0.5
        """
        DeReference = _import_class('DeReference')
        DeReference()([self], max_depth + 1)
        return self

    def reload(self, *fields, **kwargs):
        """Reloads all attributes from the database.

        :param fields: (optional) args list of fields to reload
        :param max_depth: (optional) depth of dereferencing to follow

        .. versionadded:: 0.1.2
        .. versionchanged:: 0.6  Now chainable
        .. versionchanged:: 0.9  Can provide specific fields to reload
        """
        max_depth = 1
        if fields and isinstance(fields[0], int):
            max_depth = fields[0]
            fields = fields[1:]
        elif "max_depth" in kwargs:
            max_depth = kwargs["max_depth"]

        if not self.pk:
            raise self.DoesNotExist("Document does not exist")
        obj = self._qs.read_preference(ReadPreference.PRIMARY).filter(
            **self._object_key).only(*fields).limit(1
                                                    ).select_related(max_depth=max_depth)

        if obj:
            obj = obj[0]
        else:
            raise self.DoesNotExist("Document does not exist")

        for field in self._fields_ordered:
            if not fields or field in fields:
                try:
                    setattr(self, field, self._reload(field, obj[field]))
                except KeyError:
                    # If field is removed from the database while the object
                    # is in memory, a reload would cause a KeyError
                    # i.e. obj.update(unset__field=1) followed by obj.reload()
                    delattr(self, field)

        self._changed_fields = obj._changed_fields
        self._created = False
        return self

    def _reload(self, key, value):
        """Used by :meth:`~mongoengine.Document.reload` to ensure the
        correct instance is linked to self.
        """
        if isinstance(value, BaseDict):
            value = [(k, self._reload(k, v)) for k, v in value.items()]
            value = BaseDict(value, self, key)
        elif isinstance(value, EmbeddedDocumentList):
            value = [self._reload(key, v) for v in value]
            value = EmbeddedDocumentList(value, self, key)
        elif isinstance(value, BaseList):
            value = [self._reload(key, v) for v in value]
            value = BaseList(value, self, key)
        elif isinstance(value, (EmbeddedDocument, DynamicEmbeddedDocument)):
            value._instance = None
            value._changed_fields = []
        return value

    def to_dbref(self):
        """Returns an instance of :class:`~bson.dbref.DBRef` useful in
        `__raw__` queries."""
        if not self.pk:
            msg = "Only saved documents can have a valid dbref"
            raise OperationError(msg)
        return DBRef(self.__class__._get_collection_name(), self.pk)

    @classmethod
    def register_delete_rule(cls, document_cls, field_name, rule):
        """This method registers the delete rules to apply when removing this
        object.
        """
        classes = [get_document(class_name)
                   for class_name in cls._subclasses
                   if class_name != cls.__name__] + [cls]
        documents = [get_document(class_name)
                     for class_name in document_cls._subclasses
                     if class_name != document_cls.__name__] + [document_cls]

        for cls in classes:
            for document_cls in documents:
                delete_rules = cls._meta.get('delete_rules') or {}
                delete_rules[(document_cls, field_name)] = rule
                cls._meta['delete_rules'] = delete_rules

    @classmethod
    def drop_collection(cls):
        """Drops the entire collection associated with this
        :class:`~mongoengine.Document` type from the database.
        """
        cls._collection = None
        db = cls._get_db()
        db.drop_collection(cls._get_collection_name())

    @classmethod
    def ensure_index(cls, key_or_list, drop_dups=False, background=False,
                     **kwargs):
        """Ensure that the given indexes are in place.

        :param key_or_list: a single index key or a list of index keys (to
            construct a multi-field index); keys may be prefixed with a **+**
            or a **-** to determine the index ordering
        """
        index_spec = cls._build_index_spec(key_or_list)
        index_spec = index_spec.copy()
        fields = index_spec.pop('fields')
        index_spec['drop_dups'] = drop_dups
        index_spec['background'] = background
        index_spec.update(kwargs)

        return cls._get_collection().ensure_index(fields, **index_spec)

    @classmethod
    def ensure_indexes(cls):
        """Checks the document meta data and ensures all the indexes exist.

        Global defaults can be set in the meta - see :doc:`guide/defining-documents`

        .. note:: You can disable automatic index creation by setting
                  `auto_create_index` to False in the documents meta data
        """
        background = cls._meta.get('index_background', False)
        drop_dups = cls._meta.get('index_drop_dups', False)
        index_opts = cls._meta.get('index_opts') or {}
        index_cls = cls._meta.get('index_cls', True)

        collection = cls._get_collection()
        # 746: when connection is via mongos, the read preference is not necessarily an indication that
        # this code runs on a secondary
        if not collection.is_mongos and collection.read_preference > 1:
            return

        # determine if an index which we are creating includes
        # _cls as its first field; if so, we can avoid creating
        # an extra index on _cls, as mongodb will use the existing
        # index to service queries against _cls
        cls_indexed = False

        # Ensure document-defined indexes are created
        if cls._meta['index_specs']:
            index_spec = cls._meta['index_specs']
            for spec in index_spec:
                spec = spec.copy()
                fields = spec.pop('fields')
                cls_indexed = cls_indexed or includes_cls(fields)
                opts = index_opts.copy()
                opts.update(spec)
                collection.ensure_index(fields, background=background,
                                        drop_dups=drop_dups, **opts)

        # If _cls is being used (for polymorphism), it needs an index,
        # only if another index doesn't begin with _cls
        if (index_cls and not cls_indexed and
                cls._meta.get('allow_inheritance', ALLOW_INHERITANCE) is True):
            collection.ensure_index('_cls', background=background,
                                    **index_opts)

    @classmethod
    def list_indexes(cls, go_up=True, go_down=True):
        """ Lists all of the indexes that should be created for given
        collection. It includes all the indexes from super- and sub-classes.
        """

        if cls._meta.get('abstract'):
            return []

        # get all the base classes, subclasses and siblings
        classes = []

        def get_classes(cls):

            if (cls not in classes and
                    isinstance(cls, TopLevelDocumentMetaclass)):
                classes.append(cls)

            for base_cls in cls.__bases__:
                if (isinstance(base_cls, TopLevelDocumentMetaclass) and
                        base_cls != Document and
                        not base_cls._meta.get('abstract') and
                        base_cls._get_collection().full_name == cls._get_collection().full_name and
                        base_cls not in classes):
                    classes.append(base_cls)
                    get_classes(base_cls)
            for subclass in cls.__subclasses__():
                if (isinstance(base_cls, TopLevelDocumentMetaclass) and
                        subclass._get_collection().full_name == cls._get_collection().full_name and
                        subclass not in classes):
                    classes.append(subclass)
                    get_classes(subclass)

        get_classes(cls)

        # get the indexes spec for all of the gathered classes
        def get_indexes_spec(cls):
            indexes = []

            if cls._meta['index_specs']:
                index_spec = cls._meta['index_specs']
                for spec in index_spec:
                    spec = spec.copy()
                    fields = spec.pop('fields')
                    indexes.append(fields)
            return indexes

        indexes = []
        for cls in classes:
            for index in get_indexes_spec(cls):
                if index not in indexes:
                    indexes.append(index)

        # finish up by appending { '_id': 1 } and { '_cls': 1 }, if needed
        if [(u'_id', 1)] not in indexes:
            indexes.append([(u'_id', 1)])
        if (cls._meta.get('index_cls', True) and
                cls._meta.get('allow_inheritance', ALLOW_INHERITANCE) is True):
            indexes.append([(u'_cls', 1)])

        return indexes

    @classmethod
    def compare_indexes(cls):
        """ Compares the indexes defined in MongoEngine with the ones existing
        in the database. Returns any missing/extra indexes.
        """

        required = cls.list_indexes()
        existing = [info['key']
                    for info in cls._get_collection().index_information().values()]
        missing = [index for index in required if index not in existing]
        extra = [index for index in existing if index not in required]

        # if { _cls: 1 } is missing, make sure it's *really* necessary
        if [(u'_cls', 1)] in missing:
            cls_obsolete = False
            for index in existing:
                if includes_cls(index) and index not in extra:
                    cls_obsolete = True
                    break
            if cls_obsolete:
                missing.remove([(u'_cls', 1)])

        return {'missing': missing, 'extra': extra}


class DynamicDocument(Document):

    """A Dynamic Document class allowing flexible, expandable and uncontrolled
    schemas.  As a :class:`~mongoengine.Document` subclass, acts in the same
    way as an ordinary document but has expando style properties.  Any data
    passed or set against the :class:`~mongoengine.DynamicDocument` that is
    not a field is automatically converted into a
    :class:`~mongoengine.fields.DynamicField` and data can be attributed to that
    field.

    .. note::

        There is one caveat on Dynamic Documents: fields cannot start with `_`
    """

    # The __metaclass__ attribute is removed by 2to3 when running with Python3
    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = TopLevelDocumentMetaclass
    __metaclass__ = TopLevelDocumentMetaclass

    _dynamic = True

    def __delattr__(self, *args, **kwargs):
        """Deletes the attribute by setting to None and allowing _delta to unset
        it"""
        field_name = args[0]
        if field_name in self._dynamic_fields:
            setattr(self, field_name, None)
        else:
            super(DynamicDocument, self).__delattr__(*args, **kwargs)


class DynamicEmbeddedDocument(EmbeddedDocument):

    """A Dynamic Embedded Document class allowing flexible, expandable and
    uncontrolled schemas. See :class:`~mongoengine.DynamicDocument` for more
    information about dynamic documents.
    """

    # The __metaclass__ attribute is removed by 2to3 when running with Python3
    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = DocumentMetaclass
    __metaclass__ = DocumentMetaclass

    _dynamic = True

    def __delattr__(self, *args, **kwargs):
        """Deletes the attribute by setting to None and allowing _delta to unset
        it"""
        field_name = args[0]
        if field_name in self._fields:
            default = self._fields[field_name].default
            if callable(default):
                default = default()
            setattr(self, field_name, default)
        else:
            setattr(self, field_name, None)


class MapReduceDocument(object):

    """A document returned from a map/reduce query.

    :param collection: An instance of :class:`~pymongo.Collection`
    :param key: Document/result key, often an instance of
                :class:`~bson.objectid.ObjectId`. If supplied as
                an ``ObjectId`` found in the given ``collection``,
                the object can be accessed via the ``object`` property.
    :param value: The result(s) for this key.

    .. versionadded:: 0.3
    """

    def __init__(self, document, collection, key, value):
        self._document = document
        self._collection = collection
        self.key = key
        self.value = value

    @property
    def object(self):
        """Lazy-load the object referenced by ``self.key``. ``self.key``
        should be the ``primary_key``.
        """
        id_field = self._document()._meta['id_field']
        id_field_type = type(id_field)

        if not isinstance(self.key, id_field_type):
            try:
                self.key = id_field_type(self.key)
            except:
                raise Exception("Could not cast key as %s" %
                                id_field_type.__name__)

        if not hasattr(self, "_key_object"):
            self._key_object = self._document.objects.with_id(self.key)
            return self._key_object
        return self._key_object
