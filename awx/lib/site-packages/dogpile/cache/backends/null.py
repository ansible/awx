"""
Null Backend
-------------

The Null backend does not do any caching at all.  It can be
used to test behavior without caching, or as a means of disabling
caching for a region that is otherwise used normally.

.. versionadded:: 0.5.4

"""

from dogpile.cache.api import CacheBackend, NO_VALUE


__all__ = ['NullBackend']


class NullLock(object):
    def acquire(self):
        pass

    def release(self):
        pass


class NullBackend(CacheBackend):
    """A "null" backend that effectively disables all cache operations.

    Basic usage::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.null'
        )

    """

    def __init__(self, arguments):
        pass

    def get_mutex(self, key):
        return NullLock()

    def get(self, key):
        return NO_VALUE

    def get_multi(self, keys):
        return [NO_VALUE for k in keys]

    def set(self, key, value):
        pass

    def set_multi(self, mapping):
        pass

    def delete(self, key):
        pass

    def delete_multi(self, keys):
        pass
