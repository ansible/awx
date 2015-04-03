from mongoengine.errors import OperationError
from mongoengine.queryset.base import (BaseQuerySet, DO_NOTHING, NULLIFY,
                                       CASCADE, DENY, PULL)

__all__ = ('QuerySet', 'QuerySetNoCache', 'DO_NOTHING', 'NULLIFY', 'CASCADE',
           'DENY', 'PULL')

# The maximum number of items to display in a QuerySet.__repr__
REPR_OUTPUT_SIZE = 20
ITER_CHUNK_SIZE = 100


class QuerySet(BaseQuerySet):
    """The default queryset, that builds queries and handles a set of results
    returned from a query.

    Wraps a MongoDB cursor, providing :class:`~mongoengine.Document` objects as
    the results.
    """

    _has_more = True
    _len = None
    _result_cache = None

    def __iter__(self):
        """Iteration utilises a results cache which iterates the cursor
        in batches of ``ITER_CHUNK_SIZE``.

        If ``self._has_more`` the cursor hasn't been exhausted so cache then
        batch.  Otherwise iterate the result_cache.
        """
        self._iter = True
        if self._has_more:
            return self._iter_results()

        # iterating over the cache.
        return iter(self._result_cache)

    def __len__(self):
        """Since __len__ is called quite frequently (for example, as part of
        list(qs) we populate the result cache and cache the length.
        """
        if self._len is not None:
            return self._len
        if self._has_more:
            # populate the cache
            list(self._iter_results())

        self._len = len(self._result_cache)
        return self._len

    def __repr__(self):
        """Provides the string representation of the QuerySet
        """
        if self._iter:
            return '.. queryset mid-iteration ..'

        self._populate_cache()
        data = self._result_cache[:REPR_OUTPUT_SIZE + 1]
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)


    def _iter_results(self):
        """A generator for iterating over the result cache.

        Also populates the cache if there are more possible results to yield.
        Raises StopIteration when there are no more results"""
        if self._result_cache is None:
            self._result_cache = []
        pos = 0
        while True:
            upper = len(self._result_cache)
            while pos < upper:
                yield self._result_cache[pos]
                pos = pos + 1
            if not self._has_more:
                raise StopIteration
            if len(self._result_cache) <= pos:
                self._populate_cache()

    def _populate_cache(self):
        """
        Populates the result cache with ``ITER_CHUNK_SIZE`` more entries
        (until the cursor is exhausted).
        """
        if self._result_cache is None:
            self._result_cache = []
        if self._has_more:
            try:
                for i in xrange(ITER_CHUNK_SIZE):
                    self._result_cache.append(self.next())
            except StopIteration:
                self._has_more = False

    def count(self, with_limit_and_skip=False):
        """Count the selected elements in the query.

        :param with_limit_and_skip (optional): take any :meth:`limit` or
            :meth:`skip` that has been applied to this cursor into account when
            getting the count
        """
        if with_limit_and_skip is False:
            return super(QuerySet, self).count(with_limit_and_skip)

        if self._len is None:
            self._len = super(QuerySet, self).count(with_limit_and_skip)

        return self._len

    def no_cache(self):
        """Convert to a non_caching queryset

        .. versionadded:: 0.8.3 Convert to non caching queryset
        """
        if self._result_cache is not None:
            raise OperationError("QuerySet already cached")
        return self.clone_into(QuerySetNoCache(self._document, self._collection))


class QuerySetNoCache(BaseQuerySet):
    """A non caching QuerySet"""

    def cache(self):
        """Convert to a caching queryset

        .. versionadded:: 0.8.3 Convert to caching queryset
        """
        return self.clone_into(QuerySet(self._document, self._collection))

    def __repr__(self):
        """Provides the string representation of the QuerySet

        .. versionchanged:: 0.6.13 Now doesnt modify the cursor
        """
        if self._iter:
            return '.. queryset mid-iteration ..'

        data = []
        for i in xrange(REPR_OUTPUT_SIZE + 1):
            try:
                data.append(self.next())
            except StopIteration:
                break
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."

        self.rewind()
        return repr(data)

    def __iter__(self):
        queryset = self
        if queryset._iter:
            queryset = self.clone()
        queryset.rewind()
        return queryset


class QuerySetNoDeRef(QuerySet):
    """Special no_dereference QuerySet"""

    def __dereference(items, max_depth=1, instance=None, name=None):
        return items