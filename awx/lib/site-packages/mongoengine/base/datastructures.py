import weakref
import functools
import itertools
from mongoengine.common import _import_class
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned

__all__ = ("BaseDict", "BaseList", "EmbeddedDocumentList")


class BaseDict(dict):
    """A special dict so we can watch any changes"""

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, dict_items, instance, name):
        Document = _import_class('Document')
        EmbeddedDocument = _import_class('EmbeddedDocument')

        if isinstance(instance, (Document, EmbeddedDocument)):
            self._instance = weakref.proxy(instance)
        self._name = name
        return super(BaseDict, self).__init__(dict_items)

    def __getitem__(self, key, *args, **kwargs):
        value = super(BaseDict, self).__getitem__(key)

        EmbeddedDocument = _import_class('EmbeddedDocument')
        if isinstance(value, EmbeddedDocument) and value._instance is None:
            value._instance = self._instance
        elif not isinstance(value, BaseDict) and isinstance(value, dict):
            value = BaseDict(value, None, '%s.%s' % (self._name, key))
            super(BaseDict, self).__setitem__(key, value)
            value._instance = self._instance
        elif not isinstance(value, BaseList) and isinstance(value, list):
            value = BaseList(value, None, '%s.%s' % (self._name, key))
            super(BaseDict, self).__setitem__(key, value)
            value._instance = self._instance
        return value

    def __setitem__(self, key, value, *args, **kwargs):
        self._mark_as_changed(key)
        return super(BaseDict, self).__setitem__(key, value)

    def __delete__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delete__(*args, **kwargs)

    def __delitem__(self, key, *args, **kwargs):
        self._mark_as_changed(key)
        return super(BaseDict, self).__delitem__(key)

    def __delattr__(self, key, *args, **kwargs):
        self._mark_as_changed(key)
        return super(BaseDict, self).__delattr__(key)

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    def clear(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).clear(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).pop(*args, **kwargs)

    def popitem(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).popitem(*args, **kwargs)

    def setdefault(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).setdefault(*args, **kwargs)

    def update(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).update(*args, **kwargs)

    def _mark_as_changed(self, key=None):
        if hasattr(self._instance, '_mark_as_changed'):
            if key:
                self._instance._mark_as_changed('%s.%s' % (self._name, key))
            else:
                self._instance._mark_as_changed(self._name)


class BaseList(list):
    """A special list so we can watch any changes
    """

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, list_items, instance, name):
        Document = _import_class('Document')
        EmbeddedDocument = _import_class('EmbeddedDocument')

        if isinstance(instance, (Document, EmbeddedDocument)):
            self._instance = weakref.proxy(instance)
        self._name = name
        super(BaseList, self).__init__(list_items)

    def __getitem__(self, key, *args, **kwargs):
        value = super(BaseList, self).__getitem__(key)

        EmbeddedDocument = _import_class('EmbeddedDocument')
        if isinstance(value, EmbeddedDocument) and value._instance is None:
            value._instance = self._instance
        elif not isinstance(value, BaseDict) and isinstance(value, dict):
            value = BaseDict(value, None, '%s.%s' % (self._name, key))
            super(BaseList, self).__setitem__(key, value)
            value._instance = self._instance
        elif not isinstance(value, BaseList) and isinstance(value, list):
            value = BaseList(value, None, '%s.%s' % (self._name, key))
            super(BaseList, self).__setitem__(key, value)
            value._instance = self._instance
        return value

    def __setitem__(self, key, value, *args, **kwargs):
        if isinstance(key, slice):
            self._mark_as_changed()
        else:
            self._mark_as_changed(key)
        return super(BaseList, self).__setitem__(key, value)

    def __delitem__(self, key, *args, **kwargs):
        if isinstance(key, slice):
            self._mark_as_changed()
        else:
            self._mark_as_changed(key)
        return super(BaseList, self).__delitem__(key)

    def __setslice__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__setslice__(*args, **kwargs)

    def __delslice__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__delslice__(*args, **kwargs)

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    def append(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).insert(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).remove(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).reverse(*args, **kwargs)

    def sort(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).sort(*args, **kwargs)

    def _mark_as_changed(self, key=None):
        if hasattr(self._instance, '_mark_as_changed'):
            if key:
                self._instance._mark_as_changed('%s.%s' % (self._name, key))
            else:
                self._instance._mark_as_changed(self._name)


class EmbeddedDocumentList(BaseList):

    @classmethod
    def __match_all(cls, i, kwargs):
        items = kwargs.items()
        return all([
            getattr(i, k) == v or str(getattr(i, k)) == v for k, v in items
        ])

    @classmethod
    def __only_matches(cls, obj, kwargs):
        if not kwargs:
            return obj
        return filter(lambda i: cls.__match_all(i, kwargs), obj)

    def __init__(self, list_items, instance, name):
        super(EmbeddedDocumentList, self).__init__(list_items, instance, name)
        self._instance = instance

    def filter(self, **kwargs):
        """
        Filters the list by only including embedded documents with the
        given keyword arguments.

        :param kwargs: The keyword arguments corresponding to the fields to
         filter on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: A new ``EmbeddedDocumentList`` containing the matching
         embedded documents.

        Raises ``AttributeError`` if a given keyword is not a valid field for
        the embedded document class.
        """
        values = self.__only_matches(self, kwargs)
        return EmbeddedDocumentList(values, self._instance, self._name)

    def exclude(self, **kwargs):
        """
        Filters the list by excluding embedded documents with the given
        keyword arguments.

        :param kwargs: The keyword arguments corresponding to the fields to
         exclude on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: A new ``EmbeddedDocumentList`` containing the non-matching
         embedded documents.

        Raises ``AttributeError`` if a given keyword is not a valid field for
        the embedded document class.
        """
        exclude = self.__only_matches(self, kwargs)
        values = [item for item in self if item not in exclude]
        return EmbeddedDocumentList(values, self._instance, self._name)

    def count(self):
        """
        The number of embedded documents in the list.

        :return: The length of the list, equivalent to the result of ``len()``.
        """
        return len(self)

    def get(self, **kwargs):
        """
        Retrieves an embedded document determined by the given keyword
        arguments.

        :param kwargs: The keyword arguments corresponding to the fields to
         search on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: The embedded document matched by the given keyword arguments.

        Raises ``DoesNotExist`` if the arguments used to query an embedded
        document returns no results. ``MultipleObjectsReturned`` if more
        than one result is returned.
        """
        values = self.__only_matches(self, kwargs)
        if len(values) == 0:
            raise DoesNotExist(
                "%s matching query does not exist." % self._name
            )
        elif len(values) > 1:
            raise MultipleObjectsReturned(
                "%d items returned, instead of 1" % len(values)
            )

        return values[0]

    def first(self):
        """
        Returns the first embedded document in the list, or ``None`` if empty.
        """
        if len(self) > 0:
            return self[0]

    def create(self, **values):
        """
        Creates a new embedded document and saves it to the database.

        .. note::
            The embedded document changes are not automatically saved
            to the database after calling this method.

        :param values: A dictionary of values for the embedded document.
        :return: The new embedded document instance.
        """
        name = self._name
        EmbeddedClass = self._instance._fields[name].field.document_type_obj
        self._instance[self._name].append(EmbeddedClass(**values))

        return self._instance[self._name][-1]

    def save(self, *args, **kwargs):
        """
        Saves the ancestor document.

        :param args: Arguments passed up to the ancestor Document's save
         method.
        :param kwargs: Keyword arguments passed up to the ancestor Document's
         save method.
        """
        self._instance.save(*args, **kwargs)

    def delete(self):
        """
        Deletes the embedded documents from the database.

        .. note::
            The embedded document changes are not automatically saved
            to the database after calling this method.

        :return: The number of entries deleted.
        """
        values = list(self)
        for item in values:
            self._instance[self._name].remove(item)

        return len(values)

    def update(self, **update):
        """
        Updates the embedded documents with the given update values.

        .. note::
            The embedded document changes are not automatically saved
            to the database after calling this method.

        :param update: A dictionary of update values to apply to each
         embedded document.
        :return: The number of entries updated.
        """
        if len(update) == 0:
            return 0
        values = list(self)
        for item in values:
            for k, v in update.items():
                setattr(item, k, v)

        return len(values)


class StrictDict(object):
    __slots__ = ()
    _special_fields = set(['get', 'pop', 'iteritems', 'items', 'keys', 'create'])
    _classes = {}
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)
    def __getitem__(self, key):
        key = '_reserved_' + key if key in self._special_fields else key
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)
    def __setitem__(self, key, value):
        key = '_reserved_' + key if key in self._special_fields else key
        return setattr(self, key, value)
    def __contains__(self, key):
        return hasattr(self, key)
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    def pop(self, key, default=None):
        v = self.get(key, default)
        try:
            delattr(self, key)
        except AttributeError:
            pass
        return v
    def iteritems(self):
        for key in self:
            yield key, self[key]
    def items(self):
        return [(k, self[k]) for k in iter(self)]
    def keys(self):
        return list(iter(self))
    def __iter__(self):
        return (key for key in self.__slots__ if hasattr(self, key))
    def __len__(self):
        return len(list(self.iteritems()))
    def __eq__(self, other):
        return self.items() == other.items()
    def __neq__(self, other):
        return self.items() != other.items()

    @classmethod
    def create(cls, allowed_keys):
        allowed_keys_tuple = tuple(('_reserved_' + k if k in cls._special_fields else k) for k in allowed_keys)
        allowed_keys = frozenset(allowed_keys_tuple)
        if allowed_keys not in cls._classes:
            class SpecificStrictDict(cls):
                __slots__ = allowed_keys_tuple
                def __repr__(self):
                    return "{%s}" % ', '.join('"{0!s}": {0!r}'.format(k,v) for (k,v) in self.iteritems())
            cls._classes[allowed_keys] = SpecificStrictDict
        return cls._classes[allowed_keys]


class SemiStrictDict(StrictDict):
    __slots__ = ('_extras')
    _classes = {}
    def __getattr__(self, attr):
        try:
            super(SemiStrictDict, self).__getattr__(attr)
        except AttributeError:
            try:
                return self.__getattribute__('_extras')[attr]
            except KeyError as e:
                raise AttributeError(e)
    def __setattr__(self, attr, value):
        try:
            super(SemiStrictDict, self).__setattr__(attr, value)
        except AttributeError:
            try:
                self._extras[attr] = value
            except AttributeError:
                self._extras = {attr: value}

    def __delattr__(self, attr):
        try:
            super(SemiStrictDict, self).__delattr__(attr)
        except AttributeError:
            try:
                del self._extras[attr]
            except KeyError as e:
                raise AttributeError(e)

    def __iter__(self):
        try:
            extras_iter = iter(self.__getattribute__('_extras'))
        except AttributeError:
            extras_iter = ()
        return itertools.chain(super(SemiStrictDict, self).__iter__(), extras_iter)
