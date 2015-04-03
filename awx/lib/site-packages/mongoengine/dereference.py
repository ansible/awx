from bson import DBRef, SON

from base import (
    BaseDict, BaseList, EmbeddedDocumentList,
    TopLevelDocumentMetaclass, get_document
)
from fields import (ReferenceField, ListField, DictField, MapField)
from connection import get_db
from queryset import QuerySet
from document import Document, EmbeddedDocument


class DeReference(object):

    def __call__(self, items, max_depth=1, instance=None, name=None):
        """
        Cheaply dereferences the items to a set depth.
        Also handles the conversion of complex data types.

        :param items: The iterable (dict, list, queryset) to be dereferenced.
        :param max_depth: The maximum depth to recurse to
        :param instance: The owning instance used for tracking changes by
            :class:`~mongoengine.base.ComplexBaseField`
        :param name: The name of the field, used for tracking changes by
            :class:`~mongoengine.base.ComplexBaseField`
        :param get: A boolean determining if being called by __get__
        """
        if items is None or isinstance(items, basestring):
            return items

        # cheapest way to convert a queryset to a list
        # list(queryset) uses a count() query to determine length
        if isinstance(items, QuerySet):
            items = [i for i in items]

        self.max_depth = max_depth
        doc_type = None

        if instance and isinstance(instance, (Document, EmbeddedDocument,
                                              TopLevelDocumentMetaclass)):
            doc_type = instance._fields.get(name)
            while hasattr(doc_type, 'field'):
                doc_type = doc_type.field

            if isinstance(doc_type, ReferenceField):
                field = doc_type
                doc_type = doc_type.document_type
                is_list = not hasattr(items, 'items')

                if is_list and all([i.__class__ == doc_type for i in items]):
                    return items
                elif not is_list and all([i.__class__ == doc_type
                                         for i in items.values()]):
                    return items
                elif not field.dbref:
                    if not hasattr(items, 'items'):

                        def _get_items(items):
                            new_items = []
                            for v in items:
                                if isinstance(v, list):
                                    new_items.append(_get_items(v))
                                elif not isinstance(v, (DBRef, Document)):
                                    new_items.append(field.to_python(v))
                                else:
                                    new_items.append(v)
                            return new_items

                        items = _get_items(items)
                    else:
                        items = dict([
                            (k, field.to_python(v))
                            if not isinstance(v, (DBRef, Document)) else (k, v)
                            for k, v in items.iteritems()]
                        )

        self.reference_map = self._find_references(items)
        self.object_map = self._fetch_objects(doc_type=doc_type)
        return self._attach_objects(items, 0, instance, name)

    def _find_references(self, items, depth=0):
        """
        Recursively finds all db references to be dereferenced

        :param items: The iterable (dict, list, queryset)
        :param depth: The current depth of recursion
        """
        reference_map = {}
        if not items or depth >= self.max_depth:
            return reference_map

        # Determine the iterator to use
        if not hasattr(items, 'items'):
            iterator = enumerate(items)
        else:
            iterator = items.iteritems()

        # Recursively find dbreferences
        depth += 1
        for k, item in iterator:
            if isinstance(item, (Document, EmbeddedDocument)):
                for field_name, field in item._fields.iteritems():
                    v = item._data.get(field_name, None)
                    if isinstance(v, (DBRef)):
                        reference_map.setdefault(field.document_type, []).append(v.id)
                    elif isinstance(v, (dict, SON)) and '_ref' in v:
                        reference_map.setdefault(get_document(v['_cls']), []).append(v['_ref'].id)
                    elif isinstance(v, (dict, list, tuple)) and depth <= self.max_depth:
                        field_cls = getattr(getattr(field, 'field', None), 'document_type', None)
                        references = self._find_references(v, depth)
                        for key, refs in references.iteritems():
                            if isinstance(field_cls, (Document, TopLevelDocumentMetaclass)):
                                key = field_cls
                            reference_map.setdefault(key, []).extend(refs)
            elif isinstance(item, (DBRef)):
                reference_map.setdefault(item.collection, []).append(item.id)
            elif isinstance(item, (dict, SON)) and '_ref' in item:
                reference_map.setdefault(get_document(item['_cls']), []).append(item['_ref'].id)
            elif isinstance(item, (dict, list, tuple)) and depth - 1 <= self.max_depth:
                references = self._find_references(item, depth - 1)
                for key, refs in references.iteritems():
                    reference_map.setdefault(key, []).extend(refs)

        return reference_map

    def _fetch_objects(self, doc_type=None):
        """Fetch all references and convert to their document objects
        """
        object_map = {}
        for collection, dbrefs in self.reference_map.iteritems():
            keys = object_map.keys()
            refs = list(set([dbref for dbref in dbrefs if unicode(dbref).encode('utf-8') not in keys]))
            if hasattr(collection, 'objects'):  # We have a document class for the refs
                references = collection.objects.in_bulk(refs)
                for key, doc in references.iteritems():
                    object_map[key] = doc
            else:  # Generic reference: use the refs data to convert to document
                if isinstance(doc_type, (ListField, DictField, MapField,)):
                    continue

                if doc_type:
                    references = doc_type._get_db()[collection].find({'_id': {'$in': refs}})
                    for ref in references:
                        doc = doc_type._from_son(ref)
                        object_map[doc.id] = doc
                else:
                    references = get_db()[collection].find({'_id': {'$in': refs}})
                    for ref in references:
                        if '_cls' in ref:
                            doc = get_document(ref["_cls"])._from_son(ref)
                        elif doc_type is None:
                            doc = get_document(
                                ''.join(x.capitalize()
                                    for x in collection.split('_')))._from_son(ref)
                        else:
                            doc = doc_type._from_son(ref)
                        object_map[doc.id] = doc
        return object_map

    def _attach_objects(self, items, depth=0, instance=None, name=None):
        """
        Recursively finds all db references to be dereferenced

        :param items: The iterable (dict, list, queryset)
        :param depth: The current depth of recursion
        :param instance: The owning instance used for tracking changes by
            :class:`~mongoengine.base.ComplexBaseField`
        :param name: The name of the field, used for tracking changes by
            :class:`~mongoengine.base.ComplexBaseField`
        """
        if not items:
            if isinstance(items, (BaseDict, BaseList)):
                return items

            if instance:
                if isinstance(items, dict):
                    return BaseDict(items, instance, name)
                else:
                    return BaseList(items, instance, name)

        if isinstance(items, (dict, SON)):
            if '_ref' in items:
                return self.object_map.get(items['_ref'].id, items)
            elif '_cls' in items:
                doc = get_document(items['_cls'])._from_son(items)
                _cls = doc._data.pop('_cls', None)
                del items['_cls']
                doc._data = self._attach_objects(doc._data, depth, doc, None)
                if _cls is not None:
                    doc._data['_cls'] = _cls
                return doc

        if not hasattr(items, 'items'):
            is_list = True
            list_type = BaseList
            if isinstance(items, EmbeddedDocumentList):
                list_type = EmbeddedDocumentList
            as_tuple = isinstance(items, tuple)
            iterator = enumerate(items)
            data = []
        else:
            is_list = False
            iterator = items.iteritems()
            data = {}

        depth += 1
        for k, v in iterator:
            if is_list:
                data.append(v)
            else:
                data[k] = v

            if k in self.object_map and not is_list:
                data[k] = self.object_map[k]
            elif isinstance(v, (Document, EmbeddedDocument)):
                for field_name, field in v._fields.iteritems():
                    v = data[k]._data.get(field_name, None)
                    if isinstance(v, (DBRef)):
                        data[k]._data[field_name] = self.object_map.get(v.id, v)
                    elif isinstance(v, (dict, SON)) and '_ref' in v:
                        data[k]._data[field_name] = self.object_map.get(v['_ref'].id, v)
                    elif isinstance(v, dict) and depth <= self.max_depth:
                        data[k]._data[field_name] = self._attach_objects(v, depth, instance=instance, name=name)
                    elif isinstance(v, (list, tuple)) and depth <= self.max_depth:
                        data[k]._data[field_name] = self._attach_objects(v, depth, instance=instance, name=name)
            elif isinstance(v, (dict, list, tuple)) and depth <= self.max_depth:
                item_name = '%s.%s' % (name, k) if name else name
                data[k] = self._attach_objects(v, depth - 1, instance=instance, name=item_name)
            elif hasattr(v, 'id'):
                data[k] = self.object_map.get(v.id, v)

        if instance and name:
            if is_list:
                return tuple(data) if as_tuple else list_type(data, instance, name)
            return BaseDict(data, instance, name)
        depth += 1
        return data
