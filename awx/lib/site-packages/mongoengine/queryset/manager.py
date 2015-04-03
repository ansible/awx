from functools import partial
from mongoengine.queryset.queryset import QuerySet

__all__ = ('queryset_manager', 'QuerySetManager')


class QuerySetManager(object):
    """
    The default QuerySet Manager.

    Custom QuerySet Manager functions can extend this class and users can
    add extra queryset functionality.  Any custom manager methods must accept a
    :class:`~mongoengine.Document` class as its first argument, and a
    :class:`~mongoengine.queryset.QuerySet` as its second argument.

    The method function should return a :class:`~mongoengine.queryset.QuerySet`
    , probably the same one that was passed in, but modified in some way.
    """

    get_queryset = None
    default = QuerySet

    def __init__(self, queryset_func=None):
        if queryset_func:
            self.get_queryset = queryset_func

    def __get__(self, instance, owner):
        """Descriptor for instantiating a new QuerySet object when
        Document.objects is accessed.
        """
        if instance is not None:
            # Document class being used rather than a document object
            return self

        # owner is the document that contains the QuerySetManager
        queryset_class = owner._meta.get('queryset_class', self.default)
        queryset = queryset_class(owner, owner._get_collection())
        if self.get_queryset:
            arg_count = self.get_queryset.func_code.co_argcount
            if arg_count == 1:
                queryset = self.get_queryset(queryset)
            elif arg_count == 2:
                queryset = self.get_queryset(owner, queryset)
            else:
                queryset = partial(self.get_queryset, owner, queryset)
        return queryset


def queryset_manager(func):
    """Decorator that allows you to define custom QuerySet managers on
    :class:`~mongoengine.Document` classes. The manager must be a function that
    accepts a :class:`~mongoengine.Document` class as its first argument, and a
    :class:`~mongoengine.queryset.QuerySet` as its second argument. The method
    function should return a :class:`~mongoengine.queryset.QuerySet`, probably
    the same one that was passed in, but modified in some way.
    """
    return QuerySetManager(func)
