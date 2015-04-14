"""
Proxy Backends
------------------

Provides a utility and a decorator class that allow for modifying the behavior
of different backends without altering the class itself or having to extend the
base backend.

.. versionadded:: 0.5.0  Added support for the :class:`.ProxyBackend` class.

"""

from .api import CacheBackend


class ProxyBackend(CacheBackend):
    """A decorator class for altering the functionality of backends.

    Basic usage::

        from dogpile.cache import make_region
        from dogpile.cache.proxy import ProxyBackend

        class MyFirstProxy(ProxyBackend):
            def get(self, key):
                # ... custom code goes here ...
                return self.proxied.get(key)

            def set(self, key, value):
                # ... custom code goes here ...
                self.proxied.set(key)

        class MySecondProxy(ProxyBackend):
            def get(self, key):
                # ... custom code goes here ...
                return self.proxied.get(key)


        region = make_region().configure(
            'dogpile.cache.dbm',
            expiration_time = 3600,
            arguments = {
                "filename":"/path/to/cachefile.dbm"
            },
            wrap = [ MyFirstProxy, MySecondProxy ]
        )

    Classes that extend :class:`.ProxyBackend` can be stacked
    together.  The ``.proxied`` property will always
    point to either the concrete backend instance or
    the next proxy in the chain that a method can be
    delegated towards.

    .. versionadded:: 0.5.0

    """

    def __init__(self, *args, **kwargs):
        self.proxied = None

    def wrap(self, backend):
        ''' Take a backend as an argument and setup the self.proxied property.
        Return an object that be used as a backend by a :class:`.CacheRegion`
        object.
        '''
        assert(
            isinstance(backend, CacheBackend) or
            isinstance(backend, ProxyBackend))
        self.proxied = backend
        return self

    #
    # Delegate any functions that are not already overridden to
    # the proxies backend
    #
    def get(self, key):
        return self.proxied.get(key)

    def set(self, key, value):
        self.proxied.set(key, value)

    def delete(self, key):
        self.proxied.delete(key)

    def get_multi(self, keys):
        return self.proxied.get_multi(keys)

    def set_multi(self, keys):
        self.proxied.set_multi(keys)

    def delete_multi(self, keys):
        self.proxied.delete_multi(keys)

    def get_mutex(self, key):
        return self.proxied.get_mutex(key)
