from __future__ import absolute_import

import copy
import itertools
import operator
import pprint
import re
import warnings

from bson import SON
from bson.code import Code
from bson import json_util
import pymongo
import pymongo.errors
from pymongo.common import validate_read_preference

from mongoengine import signals
from mongoengine.connection import get_db
from mongoengine.context_managers import switch_db
from mongoengine.common import _import_class
from mongoengine.base.common import get_document
from mongoengine.errors import (OperationError, NotUniqueError,
                                InvalidQueryError, LookUpError)
from mongoengine.queryset import transform
from mongoengine.queryset.field_list import QueryFieldList
from mongoengine.queryset.visitor import Q, QNode


__all__ = ('BaseQuerySet', 'DO_NOTHING', 'NULLIFY', 'CASCADE', 'DENY', 'PULL')

# Delete rules
DO_NOTHING = 0
NULLIFY = 1
CASCADE = 2
DENY = 3
PULL = 4

RE_TYPE = type(re.compile(''))


class BaseQuerySet(object):

    """A set of results returned from a query. Wraps a MongoDB cursor,
    providing :class:`~mongoengine.Document` objects as the results.
    """
    __dereference = False
    _auto_dereference = True

    def __init__(self, document, collection):
        self._document = document
        self._collection_obj = collection
        self._mongo_query = None
        self._query_obj = Q()
        self._initial_query = {}
        self._where_clause = None
        self._loaded_fields = QueryFieldList()
        self._ordering = None
        self._snapshot = False
        self._timeout = True
        self._class_check = True
        self._slave_okay = False
        self._read_preference = None
        self._iter = False
        self._scalar = []
        self._none = False
        self._as_pymongo = False
        self._as_pymongo_coerce = False
        self._search_text = None

        # If inheritance is allowed, only return instances and instances of
        # subclasses of the class being used
        if document._meta.get('allow_inheritance') is True:
            if len(self._document._subclasses) == 1:
                self._initial_query = {"_cls": self._document._subclasses[0]}
            else:
                self._initial_query = {
                    "_cls": {"$in": self._document._subclasses}}
            self._loaded_fields = QueryFieldList(always_include=['_cls'])
        self._cursor_obj = None
        self._limit = None
        self._skip = None
        self._hint = -1  # Using -1 as None is a valid value for hint
        self.only_fields = []
        self._max_time_ms = None

    def __call__(self, q_obj=None, class_check=True, slave_okay=False,
                 read_preference=None, **query):
        """Filter the selected documents by calling the
        :class:`~mongoengine.queryset.QuerySet` with a query.

        :param q_obj: a :class:`~mongoengine.queryset.Q` object to be used in
            the query; the :class:`~mongoengine.queryset.QuerySet` is filtered
            multiple times with different :class:`~mongoengine.queryset.Q`
            objects, only the last one will be used
        :param class_check: If set to False bypass class name check when
            querying collection
        :param slave_okay: if True, allows this query to be run against a
            replica secondary.
        :params read_preference: if set, overrides connection-level
            read_preference from `ReplicaSetConnection`.
        :param query: Django-style query keyword arguments
        """
        query = Q(**query)
        if q_obj:
            # make sure proper query object is passed
            if not isinstance(q_obj, QNode):
                msg = ("Not a query object: %s. "
                       "Did you intend to use key=value?" % q_obj)
                raise InvalidQueryError(msg)
            query &= q_obj

        if read_preference is None:
            queryset = self.clone()
        else:
            # Use the clone provided when setting read_preference
            queryset = self.read_preference(read_preference)

        queryset._query_obj &= query
        queryset._mongo_query = None
        queryset._cursor_obj = None
        queryset._class_check = class_check

        return queryset

    def __getitem__(self, key):
        """Support skip and limit using getitem and slicing syntax.
        """
        queryset = self.clone()

        # Slice provided
        if isinstance(key, slice):
            try:
                queryset._cursor_obj = queryset._cursor[key]
                queryset._skip, queryset._limit = key.start, key.stop
                if key.start and key.stop:
                    queryset._limit = key.stop - key.start
            except IndexError, err:
                # PyMongo raises an error if key.start == key.stop, catch it,
                # bin it, kill it.
                start = key.start or 0
                if start >= 0 and key.stop >= 0 and key.step is None:
                    if start == key.stop:
                        queryset.limit(0)
                        queryset._skip = key.start
                        queryset._limit = key.stop - start
                        return queryset
                raise err
            # Allow further QuerySet modifications to be performed
            return queryset
        # Integer index provided
        elif isinstance(key, int):
            if queryset._scalar:
                return queryset._get_scalar(
                    queryset._document._from_son(queryset._cursor[key],
                                                 _auto_dereference=self._auto_dereference,
                                                 only_fields=self.only_fields))

            if queryset._as_pymongo:
                return queryset._get_as_pymongo(queryset._cursor[key])
            return queryset._document._from_son(queryset._cursor[key],
                                               _auto_dereference=self._auto_dereference, only_fields=self.only_fields)

        raise AttributeError

    def __iter__(self):
        raise NotImplementedError

    def _has_data(self):
        """ Retrieves whether cursor has any data. """

        queryset = self.order_by()
        return False if queryset.first() is None else True

    def __nonzero__(self):
        """ Avoid to open all records in an if stmt in Py2. """

        return self._has_data()

    def __bool__(self):
        """ Avoid to open all records in an if stmt in Py3. """

        return self._has_data()

    # Core functions

    def all(self):
        """Returns all documents."""
        return self.__call__()

    def filter(self, *q_objs, **query):
        """An alias of :meth:`~mongoengine.queryset.QuerySet.__call__`
        """
        return self.__call__(*q_objs, **query)

    def search_text(self, text, language=None):
        """
        Start a text search, using text indexes.
        Require: MongoDB server version 2.6+.

        :param language:  The language that determines the list of stop words
            for the search and the rules for the stemmer and tokenizer.
            If not specified, the search uses the default language of the index.
            For supported languages, see `Text Search Languages <http://docs.mongodb.org/manual/reference/text-search-languages/#text-search-languages>`.
        """
        queryset = self.clone()
        if queryset._search_text:
            raise OperationError(
                "It is not possible to use search_text two times.")

        query_kwargs = SON({'$search': text})
        if language:
            query_kwargs['$language'] = language

        queryset._query_obj &= Q(__raw__={'$text': query_kwargs})
        queryset._mongo_query = None
        queryset._cursor_obj = None
        queryset._search_text = text

        return queryset

    def get(self, *q_objs, **query):
        """Retrieve the the matching object raising
        :class:`~mongoengine.queryset.MultipleObjectsReturned` or
        `DocumentName.MultipleObjectsReturned` exception if multiple results
        and :class:`~mongoengine.queryset.DoesNotExist` or
        `DocumentName.DoesNotExist` if no results are found.

        .. versionadded:: 0.3
        """
        queryset = self.clone()
        queryset = queryset.order_by().limit(2)
        queryset = queryset.filter(*q_objs, **query)

        try:
            result = queryset.next()
        except StopIteration:
            msg = ("%s matching query does not exist."
                   % queryset._document._class_name)
            raise queryset._document.DoesNotExist(msg)
        try:
            queryset.next()
        except StopIteration:
            return result

        queryset.rewind()
        message = u'%d items returned, instead of 1' % queryset.count()
        raise queryset._document.MultipleObjectsReturned(message)

    def create(self, **kwargs):
        """Create new object. Returns the saved object instance.

        .. versionadded:: 0.4
        """
        return self._document(**kwargs).save()

    def get_or_create(self, write_concern=None, auto_save=True,
                      *q_objs, **query):
        """Retrieve unique object or create, if it doesn't exist. Returns a
        tuple of ``(object, created)``, where ``object`` is the retrieved or
        created object and ``created`` is a boolean specifying whether a new
        object was created. Raises
        :class:`~mongoengine.queryset.MultipleObjectsReturned` or
        `DocumentName.MultipleObjectsReturned` if multiple results are found.
        A new document will be created if the document doesn't exists; a
        dictionary of default values for the new document may be provided as a
        keyword argument called :attr:`defaults`.

        .. note:: This requires two separate operations and therefore a
            race condition exists.  Because there are no transactions in
            mongoDB other approaches should be investigated, to ensure you
            don't accidentally duplicate data when using this method.  This is
            now scheduled to be removed before 1.0

        :param write_concern: optional extra keyword arguments used if we
            have to create a new document.
            Passes any write_concern onto :meth:`~mongoengine.Document.save`

        :param auto_save: if the object is to be saved automatically if
            not found.

        .. deprecated:: 0.8
        .. versionchanged:: 0.6 - added `auto_save`
        .. versionadded:: 0.3
        """
        msg = ("get_or_create is scheduled to be deprecated.  The approach is "
               "flawed without transactions. Upserts should be preferred.")
        warnings.warn(msg, DeprecationWarning)

        defaults = query.get('defaults', {})
        if 'defaults' in query:
            del query['defaults']

        try:
            doc = self.get(*q_objs, **query)
            return doc, False
        except self._document.DoesNotExist:
            query.update(defaults)
            doc = self._document(**query)

            if auto_save:
                doc.save(write_concern=write_concern)
            return doc, True

    def first(self):
        """Retrieve the first object matching the query.
        """
        queryset = self.clone()
        try:
            result = queryset[0]
        except IndexError:
            result = None
        return result

    def insert(self, doc_or_docs, load_bulk=True, write_concern=None):
        """bulk insert documents

        :param docs_or_doc: a document or list of documents to be inserted
        :param load_bulk (optional): If True returns the list of document
            instances
        :param write_concern: Extra keyword arguments are passed down to
                :meth:`~pymongo.collection.Collection.insert`
                which will be used as options for the resultant
                ``getLastError`` command.  For example,
                ``insert(..., {w: 2, fsync: True})`` will wait until at least
                two servers have recorded the write and will force an fsync on
                each server being written to.

        By default returns document instances, set ``load_bulk`` to False to
        return just ``ObjectIds``

        .. versionadded:: 0.5
        """
        Document = _import_class('Document')

        if write_concern is None:
            write_concern = {}

        docs = doc_or_docs
        return_one = False
        if isinstance(docs, Document) or issubclass(docs.__class__, Document):
            return_one = True
            docs = [docs]

        raw = []
        for doc in docs:
            if not isinstance(doc, self._document):
                msg = ("Some documents inserted aren't instances of %s"
                       % str(self._document))
                raise OperationError(msg)
            if doc.pk and not doc._created:
                msg = "Some documents have ObjectIds use doc.update() instead"
                raise OperationError(msg)
            raw.append(doc.to_mongo())

        signals.pre_bulk_insert.send(self._document, documents=docs)
        try:
            ids = self._collection.insert(raw, **write_concern)
        except pymongo.errors.DuplicateKeyError, err:
            message = 'Could not save document (%s)'
            raise NotUniqueError(message % unicode(err))
        except pymongo.errors.OperationFailure, err:
            message = 'Could not save document (%s)'
            if re.match('^E1100[01] duplicate key', unicode(err)):
                # E11000 - duplicate key error index
                # E11001 - duplicate key on update
                message = u'Tried to save duplicate unique keys (%s)'
                raise NotUniqueError(message % unicode(err))
            raise OperationError(message % unicode(err))

        if not load_bulk:
            signals.post_bulk_insert.send(
                self._document, documents=docs, loaded=False)
            return return_one and ids[0] or ids

        documents = self.in_bulk(ids)
        results = []
        for obj_id in ids:
            results.append(documents.get(obj_id))
        signals.post_bulk_insert.send(
            self._document, documents=results, loaded=True)
        return return_one and results[0] or results

    def count(self, with_limit_and_skip=False):
        """Count the selected elements in the query.

        :param with_limit_and_skip (optional): take any :meth:`limit` or
            :meth:`skip` that has been applied to this cursor into account when
            getting the count
        """
        if self._limit == 0 and with_limit_and_skip or self._none:
            return 0
        return self._cursor.count(with_limit_and_skip=with_limit_and_skip)

    def delete(self, write_concern=None, _from_doc_delete=False):
        """Delete the documents matched by the query.

        :param write_concern: Extra keyword arguments are passed down which
            will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        :param _from_doc_delete: True when called from document delete therefore
            signals will have been triggered so don't loop.

        :returns number of deleted documents
        """
        queryset = self.clone()
        doc = queryset._document

        if write_concern is None:
            write_concern = {}

        # Handle deletes where skips or limits have been applied or
        # there is an untriggered delete signal
        has_delete_signal = signals.signals_available and (
            signals.pre_delete.has_receivers_for(self._document) or
            signals.post_delete.has_receivers_for(self._document))

        call_document_delete = (queryset._skip or queryset._limit or
                                has_delete_signal) and not _from_doc_delete

        if call_document_delete:
            cnt = 0
            for doc in queryset:
                doc.delete(write_concern=write_concern)
                cnt += 1
            return cnt

        delete_rules = doc._meta.get('delete_rules') or {}
        # Check for DENY rules before actually deleting/nullifying any other
        # references
        for rule_entry in delete_rules:
            document_cls, field_name = rule_entry
            if document_cls._meta.get('abstract'):
                continue
            rule = doc._meta['delete_rules'][rule_entry]
            if rule == DENY and document_cls.objects(
                    **{field_name + '__in': self}).count() > 0:
                msg = ("Could not delete document (%s.%s refers to it)"
                       % (document_cls.__name__, field_name))
                raise OperationError(msg)

        for rule_entry in delete_rules:
            document_cls, field_name = rule_entry
            if document_cls._meta.get('abstract'):
                continue
            rule = doc._meta['delete_rules'][rule_entry]
            if rule == CASCADE:
                ref_q = document_cls.objects(**{field_name + '__in': self})
                ref_q_count = ref_q.count()
                if (doc != document_cls and ref_q_count > 0
                        or (doc == document_cls and ref_q_count > 0)):
                    ref_q.delete(write_concern=write_concern)
            elif rule == NULLIFY:
                document_cls.objects(**{field_name + '__in': self}).update(
                    write_concern=write_concern, **{'unset__%s' % field_name: 1})
            elif rule == PULL:
                document_cls.objects(**{field_name + '__in': self}).update(
                    write_concern=write_concern,
                    **{'pull_all__%s' % field_name: self})

        result = queryset._collection.remove(queryset._query, **write_concern)
        return result["n"]

    def update(self, upsert=False, multi=True, write_concern=None,
               full_result=False, **update):
        """Perform an atomic update on the fields matched by the query.

        :param upsert: Any existing document with that "_id" is overwritten.
        :param multi: Update multiple documents.
        :param write_concern: Extra keyword arguments are passed down which
            will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        :param full_result: Return the full result rather than just the number
            updated.
        :param update: Django-style update keyword arguments

        .. versionadded:: 0.2
        """
        if not update and not upsert:
            raise OperationError("No update parameters, would remove data")

        if write_concern is None:
            write_concern = {}

        queryset = self.clone()
        query = queryset._query
        update = transform.update(queryset._document, **update)

        # If doing an atomic upsert on an inheritable class
        # then ensure we add _cls to the update operation
        if upsert and '_cls' in query:
            if '$set' in update:
                update["$set"]["_cls"] = queryset._document._class_name
            else:
                update["$set"] = {"_cls": queryset._document._class_name}
        try:
            result = queryset._collection.update(query, update, multi=multi,
                                                 upsert=upsert, **write_concern)
            if full_result:
                return result
            elif result:
                return result['n']
        except pymongo.errors.DuplicateKeyError, err:
            raise NotUniqueError(u'Update failed (%s)' % unicode(err))
        except pymongo.errors.OperationFailure, err:
            if unicode(err) == u'multi not coded yet':
                message = u'update() method requires MongoDB 1.1.3+'
                raise OperationError(message)
            raise OperationError(u'Update failed (%s)' % unicode(err))

    def update_one(self, upsert=False, write_concern=None, **update):
        """Perform an atomic update on first field matched by the query.

        :param upsert: Any existing document with that "_id" is overwritten.
        :param write_concern: Extra keyword arguments are passed down which
            will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        :param update: Django-style update keyword arguments

        .. versionadded:: 0.2
        """
        return self.update(
            upsert=upsert, multi=False, write_concern=write_concern, **update)

    def modify(self, upsert=False, full_response=False, remove=False, new=False, **update):
        """Update and return the updated document.

        Returns either the document before or after modification based on `new`
        parameter. If no documents match the query and `upsert` is false,
        returns ``None``. If upserting and `new` is false, returns ``None``.

        If the full_response parameter is ``True``, the return value will be
        the entire response object from the server, including the 'ok' and
        'lastErrorObject' fields, rather than just the modified document.
        This is useful mainly because the 'lastErrorObject' document holds
        information about the command's execution.

        :param upsert: insert if document doesn't exist (default ``False``)
        :param full_response: return the entire response object from the
            server (default ``False``)
        :param remove: remove rather than updating (default ``False``)
        :param new: return updated rather than original document
            (default ``False``)
        :param update: Django-style update keyword arguments

        .. versionadded:: 0.9
        """

        if remove and new:
            raise OperationError("Conflicting parameters: remove and new")

        if not update and not upsert and not remove:
            raise OperationError(
                "No update parameters, must either update or remove")

        queryset = self.clone()
        query = queryset._query
        update = transform.update(queryset._document, **update)
        sort = queryset._ordering

        try:
            result = queryset._collection.find_and_modify(
                query, update, upsert=upsert, sort=sort, remove=remove, new=new,
                full_response=full_response, **self._cursor_args)
        except pymongo.errors.DuplicateKeyError, err:
            raise NotUniqueError(u"Update failed (%s)" % err)
        except pymongo.errors.OperationFailure, err:
            raise OperationError(u"Update failed (%s)" % err)

        if full_response:
            if result["value"] is not None:
                result["value"] = self._document._from_son(result["value"], only_fields=self.only_fields)
        else:
            if result is not None:
                result = self._document._from_son(result, only_fields=self.only_fields)

        return result

    def with_id(self, object_id):
        """Retrieve the object matching the id provided.  Uses `object_id` only
        and raises InvalidQueryError if a filter has been applied. Returns
        `None` if no document exists with that id.

        :param object_id: the value for the id of the document to look up

        .. versionchanged:: 0.6 Raises InvalidQueryError if filter has been set
        """
        queryset = self.clone()
        if not queryset._query_obj.empty:
            msg = "Cannot use a filter whilst using `with_id`"
            raise InvalidQueryError(msg)
        return queryset.filter(pk=object_id).first()

    def in_bulk(self, object_ids):
        """Retrieve a set of documents by their ids.

        :param object_ids: a list or tuple of ``ObjectId``\ s
        :rtype: dict of ObjectIds as keys and collection-specific
                Document subclasses as values.

        .. versionadded:: 0.3
        """
        doc_map = {}

        docs = self._collection.find({'_id': {'$in': object_ids}},
                                     **self._cursor_args)
        if self._scalar:
            for doc in docs:
                doc_map[doc['_id']] = self._get_scalar(
                    self._document._from_son(doc, only_fields=self.only_fields))
        elif self._as_pymongo:
            for doc in docs:
                doc_map[doc['_id']] = self._get_as_pymongo(doc)
        else:
            for doc in docs:
                doc_map[doc['_id']] = self._document._from_son(doc,
                        only_fields=self.only_fields,
                        _auto_dereference=self._auto_dereference)

        return doc_map

    def none(self):
        """Helper that just returns a list"""
        queryset = self.clone()
        queryset._none = True
        return queryset

    def no_sub_classes(self):
        """
        Only return instances of this document and not any inherited documents
        """
        if self._document._meta.get('allow_inheritance') is True:
            self._initial_query = {"_cls": self._document._class_name}

        return self

    def using(self, alias):
        """This method is for controlling which database the QuerySet will be evaluated against if you are using more than one database.

        :param alias: The database alias

        .. versionadded:: 0.9
        """

        with switch_db(self._document, alias) as cls:
            collection = cls._get_collection()

        return self.clone_into(self.__class__(self._document, collection))

    def clone(self):
        """Creates a copy of the current
          :class:`~mongoengine.queryset.QuerySet`

        .. versionadded:: 0.5
        """
        return self.clone_into(self.__class__(self._document, self._collection_obj))

    def clone_into(self, cls):
        """Creates a copy of the current
          :class:`~mongoengine.queryset.base.BaseQuerySet` into another child class
        """
        if not isinstance(cls, BaseQuerySet):
            raise OperationError(
                '%s is not a subclass of BaseQuerySet' % cls.__name__)

        copy_props = ('_mongo_query', '_initial_query', '_none', '_query_obj',
                      '_where_clause', '_loaded_fields', '_ordering', '_snapshot',
                      '_timeout', '_class_check', '_slave_okay', '_read_preference',
                      '_iter', '_scalar', '_as_pymongo', '_as_pymongo_coerce',
                      '_limit', '_skip', '_hint', '_auto_dereference',
                      '_search_text', 'only_fields', '_max_time_ms')

        for prop in copy_props:
            val = getattr(self, prop)
            setattr(cls, prop, copy.copy(val))

        if self._cursor_obj:
            cls._cursor_obj = self._cursor_obj.clone()

        return cls

    def select_related(self, max_depth=1):
        """Handles dereferencing of :class:`~bson.dbref.DBRef` objects or
        :class:`~bson.object_id.ObjectId` a maximum depth in order to cut down
        the number queries to mongodb.

        .. versionadded:: 0.5
        """
        # Make select related work the same for querysets
        max_depth += 1
        queryset = self.clone()
        return queryset._dereference(queryset, max_depth=max_depth)

    def limit(self, n):
        """Limit the number of returned documents to `n`. This may also be
        achieved using array-slicing syntax (e.g. ``User.objects[:5]``).

        :param n: the maximum number of objects to return
        """
        queryset = self.clone()
        if n == 0:
            queryset._cursor.limit(1)
        else:
            queryset._cursor.limit(n)
        queryset._limit = n
        # Return self to allow chaining
        return queryset

    def skip(self, n):
        """Skip `n` documents before returning the results. This may also be
        achieved using array-slicing syntax (e.g. ``User.objects[5:]``).

        :param n: the number of objects to skip before returning results
        """
        queryset = self.clone()
        queryset._cursor.skip(n)
        queryset._skip = n
        return queryset

    def hint(self, index=None):
        """Added 'hint' support, telling Mongo the proper index to use for the
        query.

        Judicious use of hints can greatly improve query performance. When
        doing a query on multiple fields (at least one of which is indexed)
        pass the indexed field as a hint to the query.

        Hinting will not do anything if the corresponding index does not exist.
        The last hint applied to this cursor takes precedence over all others.

        .. versionadded:: 0.5
        """
        queryset = self.clone()
        queryset._cursor.hint(index)
        queryset._hint = index
        return queryset

    def distinct(self, field):
        """Return a list of distinct values for a given field.

        :param field: the field to select distinct values from

        .. note:: This is a command and won't take ordering or limit into
           account.

        .. versionadded:: 0.4
        .. versionchanged:: 0.5 - Fixed handling references
        .. versionchanged:: 0.6 - Improved db_field refrence handling
        """
        queryset = self.clone()
        try:
            field = self._fields_to_dbfields([field]).pop()
        finally:
            distinct = self._dereference(queryset._cursor.distinct(field), 1,
                                         name=field, instance=self._document)

            doc_field = self._document._fields.get(field.split('.', 1)[0])
            instance = False
            # We may need to cast to the correct type eg. ListField(EmbeddedDocumentField)
            EmbeddedDocumentField = _import_class('EmbeddedDocumentField')
            ListField = _import_class('ListField')
            GenericEmbeddedDocumentField = _import_class('GenericEmbeddedDocumentField')
            if isinstance(doc_field, ListField):
                doc_field = getattr(doc_field, "field", doc_field)
            if isinstance(doc_field, (EmbeddedDocumentField, GenericEmbeddedDocumentField)):
                instance = getattr(doc_field, "document_type", False)
            # handle distinct on subdocuments
            if '.' in field:
                for field_part in field.split('.')[1:]:
                    # if looping on embedded document, get the document type instance
                    if instance and isinstance(doc_field, (EmbeddedDocumentField, GenericEmbeddedDocumentField)):
                        doc_field = instance
                    # now get the subdocument
                    doc_field = getattr(doc_field, field_part, doc_field)
                    # We may need to cast to the correct type eg. ListField(EmbeddedDocumentField)
                    if isinstance(doc_field, ListField):
                        doc_field = getattr(doc_field, "field", doc_field)
                    if isinstance(doc_field, (EmbeddedDocumentField, GenericEmbeddedDocumentField)):
                        instance = getattr(doc_field, "document_type", False)
            if instance and isinstance(doc_field, (EmbeddedDocumentField,
                                                   GenericEmbeddedDocumentField)):
                distinct = [instance(**doc) for doc in distinct]
            return distinct

    def only(self, *fields):
        """Load only a subset of this document's fields. ::

            post = BlogPost.objects(...).only("title", "author.name")

        .. note :: `only()` is chainable and will perform a union ::
            So with the following it will fetch both: `title` and `author.name`::

                post = BlogPost.objects.only("title").only("author.name")

        :func:`~mongoengine.queryset.QuerySet.all_fields` will reset any
        field filters.

        :param fields: fields to include

        .. versionadded:: 0.3
        .. versionchanged:: 0.5 - Added subfield support
        """
        fields = dict([(f, QueryFieldList.ONLY) for f in fields])
        self.only_fields = fields.keys()
        return self.fields(True, **fields)

    def exclude(self, *fields):
        """Opposite to .only(), exclude some document's fields. ::

            post = BlogPost.objects(...).exclude("comments")

        .. note :: `exclude()` is chainable and will perform a union ::
            So with the following it will exclude both: `title` and `author.name`::

                post = BlogPost.objects.exclude("title").exclude("author.name")

        :func:`~mongoengine.queryset.QuerySet.all_fields` will reset any
        field filters.

        :param fields: fields to exclude

        .. versionadded:: 0.5
        """
        fields = dict([(f, QueryFieldList.EXCLUDE) for f in fields])
        return self.fields(**fields)

    def fields(self, _only_called=False, **kwargs):
        """Manipulate how you load this document's fields.  Used by `.only()`
        and `.exclude()` to manipulate which fields to retrieve.  Fields also
        allows for a greater level of control for example:

        Retrieving a Subrange of Array Elements:

        You can use the $slice operator to retrieve a subrange of elements in
        an array. For example to get the first 5 comments::

            post = BlogPost.objects(...).fields(slice__comments=5)

        :param kwargs: A dictionary identifying what to include

        .. versionadded:: 0.5
        """

        # Check for an operator and transform to mongo-style if there is
        operators = ["slice"]
        cleaned_fields = []
        for key, value in kwargs.items():
            parts = key.split('__')
            op = None
            if parts[0] in operators:
                op = parts.pop(0)
                value = {'$' + op: value}
            key = '.'.join(parts)
            cleaned_fields.append((key, value))

        fields = sorted(cleaned_fields, key=operator.itemgetter(1))
        queryset = self.clone()
        for value, group in itertools.groupby(fields, lambda x: x[1]):
            fields = [field for field, value in group]
            fields = queryset._fields_to_dbfields(fields)
            queryset._loaded_fields += QueryFieldList(
                fields, value=value, _only_called=_only_called)

        return queryset

    def all_fields(self):
        """Include all fields. Reset all previously calls of .only() or
        .exclude(). ::

            post = BlogPost.objects.exclude("comments").all_fields()

        .. versionadded:: 0.5
        """
        queryset = self.clone()
        queryset._loaded_fields = QueryFieldList(
            always_include=queryset._loaded_fields.always_include)
        return queryset

    def order_by(self, *keys):
        """Order the :class:`~mongoengine.queryset.QuerySet` by the keys. The
        order may be specified by prepending each of the keys by a + or a -.
        Ascending order is assumed.

        :param keys: fields to order the query results by; keys may be
            prefixed with **+** or **-** to determine the ordering direction
        """
        queryset = self.clone()
        queryset._ordering = queryset._get_order_by(keys)
        return queryset

    def explain(self, format=False):
        """Return an explain plan record for the
        :class:`~mongoengine.queryset.QuerySet`\ 's cursor.

        :param format: format the plan before returning it
        """
        plan = self._cursor.explain()
        if format:
            plan = pprint.pformat(plan)
        return plan

    def snapshot(self, enabled):
        """Enable or disable snapshot mode when querying.

        :param enabled: whether or not snapshot mode is enabled

        ..versionchanged:: 0.5 - made chainable
        """
        queryset = self.clone()
        queryset._snapshot = enabled
        return queryset

    def timeout(self, enabled):
        """Enable or disable the default mongod timeout when querying.

        :param enabled: whether or not the timeout is used

        ..versionchanged:: 0.5 - made chainable
        """
        queryset = self.clone()
        queryset._timeout = enabled
        return queryset

    def slave_okay(self, enabled):
        """Enable or disable the slave_okay when querying.

        :param enabled: whether or not the slave_okay is enabled
        """
        queryset = self.clone()
        queryset._slave_okay = enabled
        return queryset

    def read_preference(self, read_preference):
        """Change the read_preference when querying.

        :param read_preference: override ReplicaSetConnection-level
            preference.
        """
        validate_read_preference('read_preference', read_preference)
        queryset = self.clone()
        queryset._read_preference = read_preference
        return queryset

    def scalar(self, *fields):
        """Instead of returning Document instances, return either a specific
        value or a tuple of values in order.

        Can be used along with
        :func:`~mongoengine.queryset.QuerySet.no_dereference` to turn off
        dereferencing.

        .. note:: This effects all results and can be unset by calling
                  ``scalar`` without arguments. Calls ``only`` automatically.

        :param fields: One or more fields to return instead of a Document.
        """
        queryset = self.clone()
        queryset._scalar = list(fields)

        if fields:
            queryset = queryset.only(*fields)
        else:
            queryset = queryset.all_fields()

        return queryset

    def values_list(self, *fields):
        """An alias for scalar"""
        return self.scalar(*fields)

    def as_pymongo(self, coerce_types=False):
        """Instead of returning Document instances, return raw values from
        pymongo.

        :param coerce_type: Field types (if applicable) would be use to
            coerce types.
        """
        queryset = self.clone()
        queryset._as_pymongo = True
        queryset._as_pymongo_coerce = coerce_types
        return queryset

    def max_time_ms(self, ms):
        """Wait `ms` milliseconds before killing the query on the server

        :param ms: the number of milliseconds before killing the query on the server
        """
        return self._chainable_method("max_time_ms", ms)

    # JSON Helpers

    def to_json(self, *args, **kwargs):
        """Converts a queryset to JSON"""
        return json_util.dumps(self.as_pymongo(), *args, **kwargs)

    def from_json(self, json_data):
        """Converts json data to unsaved objects"""
        son_data = json_util.loads(json_data)
        return [self._document._from_son(data, only_fields=self.only_fields) for data in son_data]

    def aggregate(self, *pipeline, **kwargs):
        """
        Perform a aggregate function based in your queryset params
        :param pipeline: list of aggregation commands,\
            see: http://docs.mongodb.org/manual/core/aggregation-pipeline/

        .. versionadded:: 0.9
        """
        initial_pipeline = []

        if self._query:
            initial_pipeline.append({'$match': self._query})

        if self._ordering:
            initial_pipeline.append({'$sort': dict(self._ordering)})

        if self._limit is not None:
            initial_pipeline.append({'$limit': self._limit})

        if self._skip is not None:
            initial_pipeline.append({'$skip': self._skip})

        pipeline = initial_pipeline + list(pipeline)

        return self._collection.aggregate(pipeline, cursor={}, **kwargs)

    # JS functionality
    def map_reduce(self, map_f, reduce_f, output, finalize_f=None, limit=None,
                   scope=None):
        """Perform a map/reduce query using the current query spec
        and ordering. While ``map_reduce`` respects ``QuerySet`` chaining,
        it must be the last call made, as it does not return a maleable
        ``QuerySet``.

        See the :meth:`~mongoengine.tests.QuerySetTest.test_map_reduce`
        and :meth:`~mongoengine.tests.QuerySetTest.test_map_advanced`
        tests in ``tests.queryset.QuerySetTest`` for usage examples.

        :param map_f: map function, as :class:`~bson.code.Code` or string
        :param reduce_f: reduce function, as
                         :class:`~bson.code.Code` or string
        :param output: output collection name, if set to 'inline' will try to
           use :class:`~pymongo.collection.Collection.inline_map_reduce`
           This can also be a dictionary containing output options
           see: http://docs.mongodb.org/manual/reference/command/mapReduce/#dbcmd.mapReduce
        :param finalize_f: finalize function, an optional function that
                           performs any post-reduction processing.
        :param scope: values to insert into map/reduce global scope. Optional.
        :param limit: number of objects from current query to provide
                      to map/reduce method

        Returns an iterator yielding
        :class:`~mongoengine.document.MapReduceDocument`.

        .. note::

            Map/Reduce changed in server version **>= 1.7.4**. The PyMongo
            :meth:`~pymongo.collection.Collection.map_reduce` helper requires
            PyMongo version **>= 1.11**.

        .. versionchanged:: 0.5
           - removed ``keep_temp`` keyword argument, which was only relevant
             for MongoDB server versions older than 1.7.4

        .. versionadded:: 0.3
        """
        queryset = self.clone()

        MapReduceDocument = _import_class('MapReduceDocument')

        if not hasattr(self._collection, "map_reduce"):
            raise NotImplementedError("Requires MongoDB >= 1.7.1")

        map_f_scope = {}
        if isinstance(map_f, Code):
            map_f_scope = map_f.scope
            map_f = unicode(map_f)
        map_f = Code(queryset._sub_js_fields(map_f), map_f_scope)

        reduce_f_scope = {}
        if isinstance(reduce_f, Code):
            reduce_f_scope = reduce_f.scope
            reduce_f = unicode(reduce_f)
        reduce_f_code = queryset._sub_js_fields(reduce_f)
        reduce_f = Code(reduce_f_code, reduce_f_scope)

        mr_args = {'query': queryset._query}

        if finalize_f:
            finalize_f_scope = {}
            if isinstance(finalize_f, Code):
                finalize_f_scope = finalize_f.scope
                finalize_f = unicode(finalize_f)
            finalize_f_code = queryset._sub_js_fields(finalize_f)
            finalize_f = Code(finalize_f_code, finalize_f_scope)
            mr_args['finalize'] = finalize_f

        if scope:
            mr_args['scope'] = scope

        if limit:
            mr_args['limit'] = limit

        if output == 'inline' and not queryset._ordering:
            map_reduce_function = 'inline_map_reduce'
        else:
            map_reduce_function = 'map_reduce'

            if isinstance(output, basestring):
                mr_args['out'] = output

            elif isinstance(output, dict):
                ordered_output = []

                for part in ('replace', 'merge', 'reduce'):
                    value = output.get(part)
                    if value:
                        ordered_output.append((part, value))
                        break

                else:
                    raise OperationError("actionData not specified for output")

                db_alias = output.get('db_alias')
                remaing_args = ['db', 'sharded', 'nonAtomic']

                if db_alias:
                    ordered_output.append(('db', get_db(db_alias).name))
                    del remaing_args[0]

                for part in remaing_args:
                    value = output.get(part)
                    if value:
                        ordered_output.append((part, value))

                mr_args['out'] = SON(ordered_output)

        results = getattr(queryset._collection, map_reduce_function)(
            map_f, reduce_f, **mr_args)

        if map_reduce_function == 'map_reduce':
            results = results.find()

        if queryset._ordering:
            results = results.sort(queryset._ordering)

        for doc in results:
            yield MapReduceDocument(queryset._document, queryset._collection,
                                    doc['_id'], doc['value'])

    def exec_js(self, code, *fields, **options):
        """Execute a Javascript function on the server. A list of fields may be
        provided, which will be translated to their correct names and supplied
        as the arguments to the function. A few extra variables are added to
        the function's scope: ``collection``, which is the name of the
        collection in use; ``query``, which is an object representing the
        current query; and ``options``, which is an object containing any
        options specified as keyword arguments.

        As fields in MongoEngine may use different names in the database (set
        using the :attr:`db_field` keyword argument to a :class:`Field`
        constructor), a mechanism exists for replacing MongoEngine field names
        with the database field names in Javascript code. When accessing a
        field, use square-bracket notation, and prefix the MongoEngine field
        name with a tilde (~).

        :param code: a string of Javascript code to execute
        :param fields: fields that you will be using in your function, which
            will be passed in to your function as arguments
        :param options: options that you want available to the function
            (accessed in Javascript through the ``options`` object)
        """
        queryset = self.clone()

        code = queryset._sub_js_fields(code)

        fields = [queryset._document._translate_field_name(f) for f in fields]
        collection = queryset._document._get_collection_name()

        scope = {
            'collection': collection,
            'options': options or {},
        }

        query = queryset._query
        if queryset._where_clause:
            query['$where'] = queryset._where_clause

        scope['query'] = query
        code = Code(code, scope=scope)

        db = queryset._document._get_db()
        return db.eval(code, *fields)

    def where(self, where_clause):
        """Filter ``QuerySet`` results with a ``$where`` clause (a Javascript
        expression). Performs automatic field name substitution like
        :meth:`mongoengine.queryset.Queryset.exec_js`.

        .. note:: When using this mode of query, the database will call your
                  function, or evaluate your predicate clause, for each object
                  in the collection.

        .. versionadded:: 0.5
        """
        queryset = self.clone()
        where_clause = queryset._sub_js_fields(where_clause)
        queryset._where_clause = where_clause
        return queryset

    def sum(self, field):
        """Sum over the values of the specified field.

        :param field: the field to sum over; use dot-notation to refer to
            embedded document fields

        .. versionchanged:: 0.5 - updated to map_reduce as db.eval doesnt work
            with sharding.
        """
        map_func = """
            function() {
                var path = '{{~%(field)s}}'.split('.'),
                field = this;

                for (p in path) {
                    if (typeof field != 'undefined')
                       field = field[path[p]];
                    else
                       break;
                }

                if (field && field.constructor == Array) {
                    field.forEach(function(item) {
                        emit(1, item||0);
                    });
                } else if (typeof field != 'undefined') {
                    emit(1, field||0);
                }
            }
        """ % dict(field=field)

        reduce_func = Code("""
            function(key, values) {
                var sum = 0;
                for (var i in values) {
                    sum += values[i];
                }
                return sum;
            }
        """)

        for result in self.map_reduce(map_func, reduce_func, output='inline'):
            return result.value
        else:
            return 0

    def average(self, field):
        """Average over the values of the specified field.

        :param field: the field to average over; use dot-notation to refer to
            embedded document fields

        .. versionchanged:: 0.5 - updated to map_reduce as db.eval doesnt work
            with sharding.
        """
        map_func = """
            function() {
                var path = '{{~%(field)s}}'.split('.'),
                field = this;

                for (p in path) {
                    if (typeof field != 'undefined')
                       field = field[path[p]];
                    else
                       break;
                }

                if (field && field.constructor == Array) {
                    field.forEach(function(item) {
                        emit(1, {t: item||0, c: 1});
                    });
                } else if (typeof field != 'undefined') {
                    emit(1, {t: field||0, c: 1});
                }
            }
        """ % dict(field=field)

        reduce_func = Code("""
            function(key, values) {
                var out = {t: 0, c: 0};
                for (var i in values) {
                    var value = values[i];
                    out.t += value.t;
                    out.c += value.c;
                }
                return out;
            }
        """)

        finalize_func = Code("""
            function(key, value) {
                return value.t / value.c;
            }
        """)

        for result in self.map_reduce(map_func, reduce_func,
                                      finalize_f=finalize_func, output='inline'):
            return result.value
        else:
            return 0

    def item_frequencies(self, field, normalize=False, map_reduce=True):
        """Returns a dictionary of all items present in a field across
        the whole queried set of documents, and their corresponding frequency.
        This is useful for generating tag clouds, or searching documents.

        .. note::

            Can only do direct simple mappings and cannot map across
            :class:`~mongoengine.fields.ReferenceField` or
            :class:`~mongoengine.fields.GenericReferenceField` for more complex
            counting a manual map reduce call would is required.

        If the field is a :class:`~mongoengine.fields.ListField`, the items within
        each list will be counted individually.

        :param field: the field to use
        :param normalize: normalize the results so they add to 1.0
        :param map_reduce: Use map_reduce over exec_js

        .. versionchanged:: 0.5 defaults to map_reduce and can handle embedded
                            document lookups
        """
        if map_reduce:
            return self._item_frequencies_map_reduce(field,
                                                     normalize=normalize)
        return self._item_frequencies_exec_js(field, normalize=normalize)

    # Iterator helpers

    def next(self):
        """Wrap the result in a :class:`~mongoengine.Document` object.
        """
        if self._limit == 0 or self._none:
            raise StopIteration

        raw_doc = self._cursor.next()
        if self._as_pymongo:
            return self._get_as_pymongo(raw_doc)
        doc = self._document._from_son(raw_doc,
                                       _auto_dereference=self._auto_dereference, only_fields=self.only_fields)

        if self._scalar:
            return self._get_scalar(doc)

        return doc

    def rewind(self):
        """Rewind the cursor to its unevaluated state.


        .. versionadded:: 0.3
        """
        self._iter = False
        self._cursor.rewind()

    # Properties

    @property
    def _collection(self):
        """Property that returns the collection object. This allows us to
        perform operations only if the collection is accessed.
        """
        return self._collection_obj

    @property
    def _cursor_args(self):
        cursor_args = {
            'snapshot': self._snapshot,
            'timeout': self._timeout
        }
        if self._read_preference is not None:
            cursor_args['read_preference'] = self._read_preference
        else:
            cursor_args['slave_okay'] = self._slave_okay
        if self._loaded_fields:
            cursor_args['fields'] = self._loaded_fields.as_dict()

        if self._search_text:
            if 'fields' not in cursor_args:
                cursor_args['fields'] = {}

            cursor_args['fields']['_text_score'] = {'$meta': "textScore"}

        return cursor_args

    @property
    def _cursor(self):
        if self._cursor_obj is None:

            self._cursor_obj = self._collection.find(self._query,
                                                     **self._cursor_args)
            # Apply where clauses to cursor
            if self._where_clause:
                where_clause = self._sub_js_fields(self._where_clause)
                self._cursor_obj.where(where_clause)

            if self._ordering:
                # Apply query ordering
                self._cursor_obj.sort(self._ordering)
            elif self._ordering is None and self._document._meta['ordering']:
                # Otherwise, apply the ordering from the document model, unless
                # it's been explicitly cleared via order_by with no arguments
                order = self._get_order_by(self._document._meta['ordering'])
                self._cursor_obj.sort(order)

            if self._limit is not None:
                self._cursor_obj.limit(self._limit)

            if self._skip is not None:
                self._cursor_obj.skip(self._skip)

            if self._hint != -1:
                self._cursor_obj.hint(self._hint)

        return self._cursor_obj

    def __deepcopy__(self, memo):
        """Essential for chained queries with ReferenceFields involved"""
        return self.clone()

    @property
    def _query(self):
        if self._mongo_query is None:
            self._mongo_query = self._query_obj.to_query(self._document)
            if self._class_check and self._initial_query:
                if "_cls" in self._mongo_query:
                    self._mongo_query = {"$and": [self._initial_query, self._mongo_query]}
                else:
                    self._mongo_query.update(self._initial_query)
        return self._mongo_query

    @property
    def _dereference(self):
        if not self.__dereference:
            self.__dereference = _import_class('DeReference')()
        return self.__dereference

    def no_dereference(self):
        """Turn off any dereferencing for the results of this queryset.
        """
        queryset = self.clone()
        queryset._auto_dereference = False
        return queryset

    # Helper Functions

    def _item_frequencies_map_reduce(self, field, normalize=False):
        map_func = """
            function() {
                var path = '{{~%(field)s}}'.split('.');
                var field = this;

                for (p in path) {
                    if (typeof field != 'undefined')
                       field = field[path[p]];
                    else
                       break;
                }
                if (field && field.constructor == Array) {
                    field.forEach(function(item) {
                        emit(item, 1);
                    });
                } else if (typeof field != 'undefined') {
                    emit(field, 1);
                } else {
                    emit(null, 1);
                }
            }
        """ % dict(field=field)
        reduce_func = """
            function(key, values) {
                var total = 0;
                var valuesSize = values.length;
                for (var i=0; i < valuesSize; i++) {
                    total += parseInt(values[i], 10);
                }
                return total;
            }
        """
        values = self.map_reduce(map_func, reduce_func, 'inline')
        frequencies = {}
        for f in values:
            key = f.key
            if isinstance(key, float):
                if int(key) == key:
                    key = int(key)
            frequencies[key] = int(f.value)

        if normalize:
            count = sum(frequencies.values())
            frequencies = dict([(k, float(v) / count)
                                for k, v in frequencies.items()])

        return frequencies

    def _item_frequencies_exec_js(self, field, normalize=False):
        """Uses exec_js to execute"""
        freq_func = """
            function(path) {
                var path = path.split('.');

                var total = 0.0;
                db[collection].find(query).forEach(function(doc) {
                    var field = doc;
                    for (p in path) {
                        if (field)
                            field = field[path[p]];
                         else
                            break;
                    }
                    if (field && field.constructor == Array) {
                       total += field.length;
                    } else {
                       total++;
                    }
                });

                var frequencies = {};
                var types = {};
                var inc = 1.0;

                db[collection].find(query).forEach(function(doc) {
                    field = doc;
                    for (p in path) {
                        if (field)
                            field = field[path[p]];
                        else
                            break;
                    }
                    if (field && field.constructor == Array) {
                        field.forEach(function(item) {
                            frequencies[item] = inc + (isNaN(frequencies[item]) ? 0: frequencies[item]);
                        });
                    } else {
                        var item = field;
                        types[item] = item;
                        frequencies[item] = inc + (isNaN(frequencies[item]) ? 0: frequencies[item]);
                    }
                });
                return [total, frequencies, types];
            }
        """
        total, data, types = self.exec_js(freq_func, field)
        values = dict([(types.get(k), int(v)) for k, v in data.iteritems()])

        if normalize:
            values = dict([(k, float(v) / total) for k, v in values.items()])

        frequencies = {}
        for k, v in values.iteritems():
            if isinstance(k, float):
                if int(k) == k:
                    k = int(k)

            frequencies[k] = v

        return frequencies

    def _fields_to_dbfields(self, fields, subdoc=False):
        """Translate fields paths to its db equivalents"""
        ret = []
        subclasses = []
        document = self._document
        if document._meta['allow_inheritance']:
            subclasses = [get_document(x)
                          for x in document._subclasses][1:]
        for field in fields:
            try:
                field = ".".join(f.db_field for f in
                                 document._lookup_field(field.split('.')))
                ret.append(field)
            except LookUpError, err:
                found = False
                for subdoc in subclasses:
                    try:
                        subfield = ".".join(f.db_field for f in
                                            subdoc._lookup_field(field.split('.')))
                        ret.append(subfield)
                        found = True
                        break
                    except LookUpError, e:
                        pass

                if not found:
                    raise err
        return ret

    def _get_order_by(self, keys):
        """Creates a list of order by fields
        """
        key_list = []
        for key in keys:
            if not key:
                continue

            if key == '$text_score':
                key_list.append(('_text_score', {'$meta': "textScore"}))
                continue

            direction = pymongo.ASCENDING
            if key[0] == '-':
                direction = pymongo.DESCENDING
            if key[0] in ('-', '+'):
                key = key[1:]
            key = key.replace('__', '.')
            try:
                key = self._document._translate_field_name(key)
            except:
                pass
            key_list.append((key, direction))

        if self._cursor_obj and key_list:
            self._cursor_obj.sort(key_list)
        return key_list

    def _get_scalar(self, doc):

        def lookup(obj, name):
            chunks = name.split('__')
            for chunk in chunks:
                obj = getattr(obj, chunk)
            return obj

        data = [lookup(doc, n) for n in self._scalar]
        if len(data) == 1:
            return data[0]

        return tuple(data)

    def _get_as_pymongo(self, row):
        # Extract which fields paths we should follow if .fields(...) was
        # used. If not, handle all fields.
        if not getattr(self, '__as_pymongo_fields', None):
            self.__as_pymongo_fields = []

            for field in self._loaded_fields.fields - set(['_cls']):
                self.__as_pymongo_fields.append(field)
                while '.' in field:
                    field, _ = field.rsplit('.', 1)
                    self.__as_pymongo_fields.append(field)

        all_fields = not self.__as_pymongo_fields

        def clean(data, path=None):
            path = path or ''

            if isinstance(data, dict):
                new_data = {}
                for key, value in data.iteritems():
                    new_path = '%s.%s' % (path, key) if path else key

                    if all_fields:
                        include_field = True
                    elif self._loaded_fields.value == QueryFieldList.ONLY:
                        include_field = new_path in self.__as_pymongo_fields
                    else:
                        include_field = new_path not in self.__as_pymongo_fields

                    if include_field:
                        new_data[key] = clean(value, path=new_path)
                data = new_data
            elif isinstance(data, list):
                data = [clean(d, path=path) for d in data]
            else:
                if self._as_pymongo_coerce:
                    # If we need to coerce types, we need to determine the
                    # type of this field and use the corresponding
                    # .to_python(...)
                    from mongoengine.fields import EmbeddedDocumentField

                    obj = self._document
                    for chunk in path.split('.'):
                        obj = getattr(obj, chunk, None)
                        if obj is None:
                            break
                        elif isinstance(obj, EmbeddedDocumentField):
                            obj = obj.document_type
                    if obj and data is not None:
                        data = obj.to_python(data)
            return data

        return clean(row)

    def _sub_js_fields(self, code):
        """When fields are specified with [~fieldname] syntax, where
        *fieldname* is the Python name of a field, *fieldname* will be
        substituted for the MongoDB name of the field (specified using the
        :attr:`name` keyword argument in a field's constructor).
        """

        def field_sub(match):
            # Extract just the field name, and look up the field objects
            field_name = match.group(1).split('.')
            fields = self._document._lookup_field(field_name)
            # Substitute the correct name for the field into the javascript
            return u'["%s"]' % fields[-1].db_field

        def field_path_sub(match):
            # Extract just the field name, and look up the field objects
            field_name = match.group(1).split('.')
            fields = self._document._lookup_field(field_name)
            # Substitute the correct name for the field into the javascript
            return ".".join([f.db_field for f in fields])

        code = re.sub(u'\[\s*~([A-z_][A-z_0-9.]+?)\s*\]', field_sub, code)
        code = re.sub(u'\{\{\s*~([A-z_][A-z_0-9.]+?)\s*\}\}', field_path_sub,
                      code)
        return code

    def _chainable_method(self, method_name, val):
        queryset = self.clone()
        method = getattr(queryset._cursor, method_name)
        method(val)
        setattr(queryset, "_" + method_name, val)
        return queryset

    # Deprecated
    def ensure_index(self, **kwargs):
        """Deprecated use :func:`Document.ensure_index`"""
        msg = ("Doc.objects()._ensure_index() is deprecated. "
               "Use Doc.ensure_index() instead.")
        warnings.warn(msg, DeprecationWarning)
        self._document.__class__.ensure_index(**kwargs)
        return self

    def _ensure_indexes(self):
        """Deprecated use :func:`~Document.ensure_indexes`"""
        msg = ("Doc.objects()._ensure_indexes() is deprecated. "
               "Use Doc.ensure_indexes() instead.")
        warnings.warn(msg, DeprecationWarning)
        self._document.__class__.ensure_indexes()
