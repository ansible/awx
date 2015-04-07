from __future__ import with_statement
from dogpile.core import Lock, NeedRegenerationException
from dogpile.core.nameregistry import NameRegistry
from . import exception
from .util import function_key_generator, PluginLoader, \
    memoized_property, coerce_string_conf, function_multi_key_generator
from .api import NO_VALUE, CachedValue
from .proxy import ProxyBackend
from . import compat
import time
import datetime
from numbers import Number
from functools import wraps
import threading

_backend_loader = PluginLoader("dogpile.cache")
register_backend = _backend_loader.register
from . import backends  # noqa

value_version = 1
"""An integer placed in the :class:`.CachedValue`
so that new versions of dogpile.cache can detect cached
values from a previous, backwards-incompatible version.

"""


class CacheRegion(object):
    """A front end to a particular cache backend.

    :param name: Optional, a string name for the region.
     This isn't used internally
     but can be accessed via the ``.name`` parameter, helpful
     for configuring a region from a config file.
    :param function_key_generator:  Optional.  A
     function that will produce a "cache key" given
     a data creation function and arguments, when using
     the :meth:`.CacheRegion.cache_on_arguments` method.
     The structure of this function
     should be two levels: given the data creation function,
     return a new function that generates the key based on
     the given arguments.  Such as::

        def my_key_generator(namespace, fn, **kw):
            fname = fn.__name__
            def generate_key(*arg):
                return namespace + "_" + fname + "_".join(str(s) for s in arg)
            return generate_key


        region = make_region(
            function_key_generator = my_key_generator
        ).configure(
            "dogpile.cache.dbm",
            expiration_time=300,
            arguments={
                "filename":"file.dbm"
            }
        )

     The ``namespace`` is that passed to
     :meth:`.CacheRegion.cache_on_arguments`.  It's not consulted
     outside this function, so in fact can be of any form.
     For example, it can be passed as a tuple, used to specify
     arguments to pluck from \**kw::

        def my_key_generator(namespace, fn):
            def generate_key(*arg, **kw):
                return ":".join(
                        [kw[k] for k in namespace] +
                        [str(x) for x in arg]
                    )
            return generate_key


     Where the decorator might be used as::

        @my_region.cache_on_arguments(namespace=('x', 'y'))
        def my_function(a, b, **kw):
            return my_data()

    :param function_multi_key_generator: Optional.
     Similar to ``function_key_generator`` parameter, but it's used in
     :meth:`.CacheRegion.cache_multi_on_arguments`. Generated function
     should return list of keys. For example::

        def my_multi_key_generator(namespace, fn, **kw):
            namespace = fn.__name__ + (namespace or '')

            def generate_keys(*args):
                return [namespace + ':' + str(a) for a in args]

            return generate_keys

    :param key_mangler: Function which will be used on all incoming
     keys before passing to the backend.  Defaults to ``None``,
     in which case the key mangling function recommended by
     the cache backend will be used.    A typical mangler
     is the SHA1 mangler found at :func:`.sha1_mangle_key`
     which coerces keys into a SHA1
     hash, so that the string length is fixed.  To
     disable all key mangling, set to ``False``.   Another typical
     mangler is the built-in Python function ``str``, which can be used
     to convert non-string or Unicode keys to bytestrings, which is
     needed when using a backend such as bsddb or dbm under Python 2.x
     in conjunction with Unicode keys.
    :param async_creation_runner:  A callable that, when specified,
     will be passed to and called by dogpile.lock when
     there is a stale value present in the cache.  It will be passed the
     mutex and is responsible releasing that mutex when finished.
     This can be used to defer the computation of expensive creator
     functions to later points in the future by way of, for example, a
     background thread, a long-running queue, or a task manager system
     like Celery.

     For a specific example using async_creation_runner, new values can
     be created in a background thread like so::

        import threading

        def async_creation_runner(cache, somekey, creator, mutex):
            ''' Used by dogpile.core:Lock when appropriate  '''
            def runner():
                try:
                    value = creator()
                    cache.set(somekey, value)
                finally:
                    mutex.release()

            thread = threading.Thread(target=runner)
            thread.start()


        region = make_region(
            async_creation_runner=async_creation_runner,
        ).configure(
            'dogpile.cache.memcached',
            expiration_time=5,
            arguments={
                'url': '127.0.0.1:11211',
                'distributed_lock': True,
            }
        )

     Remember that the first request for a key with no associated
     value will always block; async_creator will not be invoked.
     However, subsequent requests for cached-but-expired values will
     still return promptly.  They will be refreshed by whatever
     asynchronous means the provided async_creation_runner callable
     implements.

     By default the async_creation_runner is disabled and is set
     to ``None``.

     .. versionadded:: 0.4.2 added the async_creation_runner
        feature.

    """

    def __init__(
            self,
            name=None,
            function_key_generator=function_key_generator,
            function_multi_key_generator=function_multi_key_generator,
            key_mangler=None,
            async_creation_runner=None,
    ):
        """Construct a new :class:`.CacheRegion`."""
        self.name = name
        self.function_key_generator = function_key_generator
        self.function_multi_key_generator = function_multi_key_generator
        if key_mangler:
            self.key_mangler = key_mangler
        else:
            self.key_mangler = None
        self._hard_invalidated = None
        self._soft_invalidated = None
        self.async_creation_runner = async_creation_runner

    def configure(
            self, backend,
            expiration_time=None,
            arguments=None,
            _config_argument_dict=None,
            _config_prefix=None,
            wrap=None
    ):
        """Configure a :class:`.CacheRegion`.

        The :class:`.CacheRegion` itself
        is returned.

        :param backend:   Required.  This is the name of the
         :class:`.CacheBackend` to use, and is resolved by loading
         the class from the ``dogpile.cache`` entrypoint.

        :param expiration_time:   Optional.  The expiration time passed
         to the dogpile system.  May be passed as an integer number
         of seconds, or as a ``datetime.timedelta`` value.

         .. versionadded 0.5.0
            ``expiration_time`` may be optionally passed as a
            ``datetime.timedelta`` value.

         The :meth:`.CacheRegion.get_or_create`
         method as well as the :meth:`.CacheRegion.cache_on_arguments`
         decorator (though note:  **not** the :meth:`.CacheRegion.get`
         method) will call upon the value creation function after this
         time period has passed since the last generation.

        :param arguments: Optional.  The structure here is passed
         directly to the constructor of the :class:`.CacheBackend`
         in use, though is typically a dictionary.

        :param wrap: Optional.  A list of :class:`.ProxyBackend`
         classes and/or instances, each of which will be applied
         in a chain to ultimately wrap the original backend,
         so that custom functionality augmentation can be applied.

         .. versionadded:: 0.5.0

         .. seealso::

            :ref:`changing_backend_behavior`

         """

        if "backend" in self.__dict__:
            raise exception.RegionAlreadyConfigured(
                "This region is already "
                "configured with backend: %s"
                % self.backend)
        backend_cls = _backend_loader.load(backend)
        if _config_argument_dict:
            self.backend = backend_cls.from_config_dict(
                _config_argument_dict,
                _config_prefix
            )
        else:
            self.backend = backend_cls(arguments or {})

        if not expiration_time or isinstance(expiration_time, Number):
            self.expiration_time = expiration_time
        elif isinstance(expiration_time, datetime.timedelta):
            self.expiration_time = int(
                compat.timedelta_total_seconds(expiration_time))
        else:
            raise exception.ValidationError(
                'expiration_time is not a number or timedelta.')

        if self.key_mangler is None:
            self.key_mangler = self.backend.key_mangler

        self._lock_registry = NameRegistry(self._create_mutex)

        if getattr(wrap, '__iter__', False):
            for wrapper in reversed(wrap):
                self.wrap(wrapper)

        return self

    def wrap(self, proxy):
        ''' Takes a ProxyBackend instance or class and wraps the
        attached backend. '''

        # if we were passed a type rather than an instance then
        # initialize it.
        if type(proxy) == type:
            proxy = proxy()

        if not issubclass(type(proxy), ProxyBackend):
            raise TypeError("Type %s is not a valid ProxyBackend"
                            % type(proxy))

        self.backend = proxy.wrap(self.backend)

    def _mutex(self, key):
        return self._lock_registry.get(key)

    class _LockWrapper(object):
        """weakref-capable wrapper for threading.Lock"""
        def __init__(self):
            self.lock = threading.Lock()

        def acquire(self, wait=True):
            return self.lock.acquire(wait)

        def release(self):
            self.lock.release()

    def _create_mutex(self, key):
        mutex = self.backend.get_mutex(key)
        if mutex is not None:
            return mutex
        else:
            return self._LockWrapper()

    def invalidate(self, hard=True):
        """Invalidate this :class:`.CacheRegion`.

        Invalidation works by setting a current timestamp
        (using ``time.time()``)
        representing the "minimum creation time" for
        a value.  Any retrieved value whose creation
        time is prior to this timestamp
        is considered to be stale.  It does not
        affect the data in the cache in any way, and is also
        local to this instance of :class:`.CacheRegion`.

        Once set, the invalidation time is honored by
        the :meth:`.CacheRegion.get_or_create`,
        :meth:`.CacheRegion.get_or_create_multi` and
        :meth:`.CacheRegion.get` methods.

        The method supports both "hard" and "soft" invalidation
        options.  With "hard" invalidation,
        :meth:`.CacheRegion.get_or_create` will force an immediate
        regeneration of the value which all getters will wait for.
        With "soft" invalidation, subsequent getters will return the
        "old" value until the new one is available.

        Usage of "soft" invalidation requires that the region or the method
        is given a non-None expiration time.

        .. versionadded:: 0.3.0

        :param hard: if True, cache values will all require immediate
         regeneration; dogpile logic won't be used.  If False, the
         creation time of existing values will be pushed back before
         the expiration time so that a return+regen will be invoked.

         .. versionadded:: 0.5.1

        """
        if hard:
            self._hard_invalidated = time.time()
            self._soft_invalidated = None
        else:
            self._hard_invalidated = None
            self._soft_invalidated = time.time()

    def configure_from_config(self, config_dict, prefix):
        """Configure from a configuration dictionary
        and a prefix.

        Example::

            local_region = make_region()
            memcached_region = make_region()

            # regions are ready to use for function
            # decorators, but not yet for actual caching

            # later, when config is available
            myconfig = {
                "cache.local.backend":"dogpile.cache.dbm",
                "cache.local.arguments.filename":"/path/to/dbmfile.dbm",
                "cache.memcached.backend":"dogpile.cache.pylibmc",
                "cache.memcached.arguments.url":"127.0.0.1, 10.0.0.1",
            }
            local_region.configure_from_config(myconfig, "cache.local.")
            memcached_region.configure_from_config(myconfig,
                                                "cache.memcached.")

        """
        config_dict = coerce_string_conf(config_dict)
        return self.configure(
            config_dict["%sbackend" % prefix],
            expiration_time=config_dict.get(
                "%sexpiration_time" % prefix, None),
            _config_argument_dict=config_dict,
            _config_prefix="%sarguments." % prefix,
            wrap=config_dict.get(
                "%swrap" % prefix, None),
        )

    @memoized_property
    def backend(self):
        raise exception.RegionNotConfigured(
            "No backend is configured on this region.")

    @property
    def is_configured(self):
        """Return True if the backend has been configured via the
        :meth:`.CacheRegion.configure` method already.

        .. versionadded:: 0.5.1

        """
        return 'backend' in self.__dict__

    def get(self, key, expiration_time=None, ignore_expiration=False):
        """Return a value from the cache, based on the given key.

        If the value is not present, the method returns the token
        ``NO_VALUE``. ``NO_VALUE`` evaluates to False, but is separate from
        ``None`` to distinguish between a cached value of ``None``.

        By default, the configured expiration time of the
        :class:`.CacheRegion`, or alternatively the expiration
        time supplied by the ``expiration_time`` argument,
        is tested against the creation time of the retrieved
        value versus the current time (as reported by ``time.time()``).
        If stale, the cached value is ignored and the ``NO_VALUE``
        token is returned.  Passing the flag ``ignore_expiration=True``
        bypasses the expiration time check.

        .. versionchanged:: 0.3.0
           :meth:`.CacheRegion.get` now checks the value's creation time
           against the expiration time, rather than returning
           the value unconditionally.

        The method also interprets the cached value in terms
        of the current "invalidation" time as set by
        the :meth:`.invalidate` method.   If a value is present,
        but its creation time is older than the current
        invalidation time, the ``NO_VALUE`` token is returned.
        Passing the flag ``ignore_expiration=True`` bypasses
        the invalidation time check.

        .. versionadded:: 0.3.0
           Support for the :meth:`.CacheRegion.invalidate`
           method.

        :param key: Key to be retrieved. While it's typical for a key to be a
         string, it is ultimately passed directly down to the cache backend,
         before being optionally processed by the key_mangler function, so can
         be of any type recognized by the backend or by the key_mangler
         function, if present.

        :param expiration_time: Optional expiration time value
         which will supersede that configured on the :class:`.CacheRegion`
         itself.

         .. versionadded:: 0.3.0

        :param ignore_expiration: if ``True``, the value is returned
         from the cache if present, regardless of configured
         expiration times or whether or not :meth:`.invalidate`
         was called.

         .. versionadded:: 0.3.0

        """

        if self.key_mangler:
            key = self.key_mangler(key)
        value = self.backend.get(key)
        value = self._unexpired_value_fn(
            expiration_time, ignore_expiration)(value)

        return value.payload

    def _unexpired_value_fn(self, expiration_time, ignore_expiration):
        if ignore_expiration:
            return lambda value: value
        else:
            if expiration_time is None:
                expiration_time = self.expiration_time

            current_time = time.time()

            invalidated = self._hard_invalidated or self._soft_invalidated

            def value_fn(value):
                if value is NO_VALUE:
                    return value
                elif expiration_time is not None and \
                        current_time - value.metadata["ct"] > expiration_time:
                    return NO_VALUE
                elif invalidated and \
                        value.metadata["ct"] < invalidated:
                    return NO_VALUE
                else:
                    return value

            return value_fn

    def get_multi(self, keys, expiration_time=None, ignore_expiration=False):
        """Return multiple values from the cache, based on the given keys.

        Returns values as a list matching the keys given.

        E.g.::

            values = region.get_multi(["one", "two", "three"])

        To convert values to a dictionary, use ``zip()``::

            keys = ["one", "two", "three"]
            values = region.get_multi(keys)
            dictionary = dict(zip(keys, values))

        Keys which aren't present in the list are returned as
        the ``NO_VALUE`` token.  ``NO_VALUE`` evaluates to False,
        but is separate from
        ``None`` to distinguish between a cached value of ``None``.

        By default, the configured expiration time of the
        :class:`.CacheRegion`, or alternatively the expiration
        time supplied by the ``expiration_time`` argument,
        is tested against the creation time of the retrieved
        value versus the current time (as reported by ``time.time()``).
        If stale, the cached value is ignored and the ``NO_VALUE``
        token is returned.  Passing the flag ``ignore_expiration=True``
        bypasses the expiration time check.

        .. versionadded:: 0.5.0

        """
        if not keys:
            return []

        if self.key_mangler:
            keys = list(map(lambda key: self.key_mangler(key), keys))

        backend_values = self.backend.get_multi(keys)

        _unexpired_value_fn = self._unexpired_value_fn(
            expiration_time, ignore_expiration)
        return [
            value.payload if value is not NO_VALUE else value
            for value in
            (
                _unexpired_value_fn(value) for value in
                backend_values
            )
        ]

    def get_or_create(
            self, key, creator, expiration_time=None, should_cache_fn=None):
        """Return a cached value based on the given key.

        If the value does not exist or is considered to be expired
        based on its creation time, the given
        creation function may or may not be used to recreate the value
        and persist the newly generated value in the cache.

        Whether or not the function is used depends on if the
        *dogpile lock* can be acquired or not.  If it can't, it means
        a different thread or process is already running a creation
        function for this key against the cache.  When the dogpile
        lock cannot be acquired, the method will block if no
        previous value is available, until the lock is released and
        a new value available.  If a previous value
        is available, that value is returned immediately without blocking.

        If the :meth:`.invalidate` method has been called, and
        the retrieved value's timestamp is older than the invalidation
        timestamp, the value is unconditionally prevented from
        being returned.  The method will attempt to acquire the dogpile
        lock to generate a new value, or will wait
        until the lock is released to return the new value.

        .. versionchanged:: 0.3.0
          The value is unconditionally regenerated if the creation
          time is older than the last call to :meth:`.invalidate`.

        :param key: Key to be retrieved. While it's typical for a key to be a
         string, it is ultimately passed directly down to the cache backend,
         before being optionally processed by the key_mangler function, so can
         be of any type recognized by the backend or by the key_mangler
         function, if present.

        :param creator: function which creates a new value.

        :param expiration_time: optional expiration time which will overide
         the expiration time already configured on this :class:`.CacheRegion`
         if not None.   To set no expiration, use the value -1.

        :param should_cache_fn: optional callable function which will receive
         the value returned by the "creator", and will then return True or
         False, indicating if the value should actually be cached or not.  If
         it returns False, the value is still returned, but isn't cached.
         E.g.::

            def dont_cache_none(value):
                return value is not None

            value = region.get_or_create("some key",
                                create_value,
                                should_cache_fn=dont_cache_none)

         Above, the function returns the value of create_value() if
         the cache is invalid, however if the return value is None,
         it won't be cached.

         .. versionadded:: 0.4.3

        .. seealso::

            :meth:`.CacheRegion.cache_on_arguments` - applies
            :meth:`.get_or_create` to any function using a decorator.

            :meth:`.CacheRegion.get_or_create_multi` - multiple key/value
             version

        """
        orig_key = key
        if self.key_mangler:
            key = self.key_mangler(key)

        def get_value():
            value = self.backend.get(key)
            if value is NO_VALUE or \
                value.metadata['v'] != value_version or \
                    (
                        self._hard_invalidated and
                        value.metadata["ct"] < self._hard_invalidated):
                raise NeedRegenerationException()
            ct = value.metadata["ct"]
            if self._soft_invalidated:
                if ct < self._soft_invalidated:
                    ct = time.time() - expiration_time - .0001

            return value.payload, ct

        def gen_value():
            created_value = creator()
            value = self._value(created_value)

            if not should_cache_fn or \
                    should_cache_fn(created_value):
                self.backend.set(key, value)

            return value.payload, value.metadata["ct"]

        if expiration_time is None:
            expiration_time = self.expiration_time

        if expiration_time is None and self._soft_invalidated:
            raise exception.DogpileCacheException(
                "Non-None expiration time required "
                "for soft invalidation")

        if expiration_time == -1:
            expiration_time = None

        if self.async_creation_runner:
            def async_creator(mutex):
                return self.async_creation_runner(
                    self, orig_key, creator, mutex)
        else:
            async_creator = None

        with Lock(
                self._mutex(key),
                gen_value,
                get_value,
                expiration_time,
                async_creator) as value:
            return value

    def get_or_create_multi(
            self, keys, creator, expiration_time=None, should_cache_fn=None):
        """Return a sequence of cached values based on a sequence of keys.

        The behavior for generation of values based on keys corresponds
        to that of :meth:`.Region.get_or_create`, with the exception that
        the ``creator()`` function may be asked to generate any subset of
        the given keys.   The list of keys to be generated is passed to
        ``creator()``, and ``creator()`` should return the generated values
        as a sequence corresponding to the order of the keys.

        The method uses the same approach as :meth:`.Region.get_multi`
        and :meth:`.Region.set_multi` to get and set values from the
        backend.

        :param keys: Sequence of keys to be retrieved.

        :param creator: function which accepts a sequence of keys and
         returns a sequence of new values.

        :param expiration_time: optional expiration time which will overide
         the expiration time already configured on this :class:`.CacheRegion`
         if not None.   To set no expiration, use the value -1.

        :param should_cache_fn: optional callable function which will receive
         each value returned by the "creator", and will then return True or
         False, indicating if the value should actually be cached or not.  If
         it returns False, the value is still returned, but isn't cached.

        .. versionadded:: 0.5.0

        .. seealso::


            :meth:`.CacheRegion.cache_multi_on_arguments`

            :meth:`.CacheRegion.get_or_create`

        """

        def get_value(key):
            value = values.get(key, NO_VALUE)

            if value is NO_VALUE or \
                value.metadata['v'] != value_version or \
                    (self._hard_invalidated and
                        value.metadata["ct"] < self._hard_invalidated):
                # dogpile.core understands a 0 here as
                # "the value is not available", e.g.
                # _has_value() will return False.
                return value.payload, 0
            else:
                ct = value.metadata["ct"]
                if self._soft_invalidated:
                    if ct < self._soft_invalidated:
                        ct = time.time() - expiration_time - .0001

                return value.payload, ct

        def gen_value():
            raise NotImplementedError()

        def async_creator(key, mutex):
            mutexes[key] = mutex

        if expiration_time is None:
            expiration_time = self.expiration_time

        if expiration_time is None and self._soft_invalidated:
            raise exception.DogpileCacheException(
                "Non-None expiration time required "
                "for soft invalidation")

        if expiration_time == -1:
            expiration_time = None

        mutexes = {}

        sorted_unique_keys = sorted(set(keys))

        if self.key_mangler:
            mangled_keys = [self.key_mangler(k) for k in sorted_unique_keys]
        else:
            mangled_keys = sorted_unique_keys

        orig_to_mangled = dict(zip(sorted_unique_keys, mangled_keys))

        values = dict(zip(mangled_keys, self.backend.get_multi(mangled_keys)))

        for orig_key, mangled_key in orig_to_mangled.items():
            with Lock(
                    self._mutex(mangled_key),
                    gen_value,
                    lambda: get_value(mangled_key),
                    expiration_time,
                    async_creator=lambda mutex: async_creator(orig_key, mutex)
            ):
                pass
        try:
            if mutexes:
                # sort the keys, the idea is to prevent deadlocks.
                # though haven't been able to simulate one anyway.
                keys_to_get = sorted(mutexes)
                new_values = creator(*keys_to_get)

                values_w_created = dict(
                    (orig_to_mangled[k], self._value(v))
                    for k, v in zip(keys_to_get, new_values)
                )

                if not should_cache_fn:
                    self.backend.set_multi(values_w_created)
                else:
                    self.backend.set_multi(dict(
                        (k, v)
                        for k, v in values_w_created.items()
                        if should_cache_fn(v[0])
                    ))

                values.update(values_w_created)
            return [values[orig_to_mangled[k]].payload for k in keys]
        finally:
            for mutex in mutexes.values():
                mutex.release()

    def _value(self, value):
        """Return a :class:`.CachedValue` given a value."""
        return CachedValue(
            value,
            {
                "ct": time.time(),
                "v": value_version
            })

    def set(self, key, value):
        """Place a new value in the cache under the given key."""

        if self.key_mangler:
            key = self.key_mangler(key)
        self.backend.set(key, self._value(value))

    def set_multi(self, mapping):
        """Place new values in the cache under the given keys.

        .. versionadded:: 0.5.0

        """
        if not mapping:
            return

        if self.key_mangler:
            mapping = dict((
                self.key_mangler(k), self._value(v))
                for k, v in mapping.items())
        else:
            mapping = dict((k, self._value(v)) for k, v in mapping.items())
        self.backend.set_multi(mapping)

    def delete(self, key):
        """Remove a value from the cache.

        This operation is idempotent (can be called multiple times, or on a
        non-existent key, safely)
        """

        if self.key_mangler:
            key = self.key_mangler(key)

        self.backend.delete(key)

    def delete_multi(self, keys):
        """Remove multiple values from the cache.

        This operation is idempotent (can be called multiple times, or on a
        non-existent key, safely)

        .. versionadded:: 0.5.0

        """

        if self.key_mangler:
            keys = list(map(lambda key: self.key_mangler(key), keys))

        self.backend.delete_multi(keys)

    def cache_on_arguments(
            self, namespace=None,
            expiration_time=None,
            should_cache_fn=None,
            to_str=compat.string_type,
            function_key_generator=None):
        """A function decorator that will cache the return
        value of the function using a key derived from the
        function itself and its arguments.

        The decorator internally makes use of the
        :meth:`.CacheRegion.get_or_create` method to access the
        cache and conditionally call the function.  See that
        method for additional behavioral details.

        E.g.::

            @someregion.cache_on_arguments()
            def generate_something(x, y):
                return somedatabase.query(x, y)

        The decorated function can then be called normally, where
        data will be pulled from the cache region unless a new
        value is needed::

            result = generate_something(5, 6)

        The function is also given an attribute ``invalidate()``, which
        provides for invalidation of the value.  Pass to ``invalidate()``
        the same arguments you'd pass to the function itself to represent
        a particular value::

            generate_something.invalidate(5, 6)

        Another attribute ``set()`` is added to provide extra caching
        possibilities relative to the function.   This is a convenience
        method for :meth:`.CacheRegion.set` which will store a given
        value directly without calling the decorated function.
        The value to be cached is passed as the first argument, and the
        arguments which would normally be passed to the function
        should follow::

            generate_something.set(3, 5, 6)

        The above example is equivalent to calling
        ``generate_something(5, 6)``, if the function were to produce
        the value ``3`` as the value to be cached.

        .. versionadded:: 0.4.1 Added ``set()`` method to decorated function.

        Similar to ``set()`` is ``refresh()``.   This attribute will
        invoke the decorated function and populate a new value into
        the cache with the new value, as well as returning that value::

            newvalue = generate_something.refresh(5, 6)

        .. versionadded:: 0.5.0 Added ``refresh()`` method to decorated
           function.

        Lastly, the ``get()`` method returns either the value cached
        for the given key, or the token ``NO_VALUE`` if no such key
        exists::

            value = generate_something.get(5, 6)

        .. versionadded:: 0.5.3 Added ``get()`` method to decorated
           function.

        The default key generation will use the name
        of the function, the module name for the function,
        the arguments passed, as well as an optional "namespace"
        parameter in order to generate a cache key.

        Given a function ``one`` inside the module
        ``myapp.tools``::

            @region.cache_on_arguments(namespace="foo")
            def one(a, b):
                return a + b

        Above, calling ``one(3, 4)`` will produce a
        cache key as follows::

            myapp.tools:one|foo|3 4

        The key generator will ignore an initial argument
        of ``self`` or ``cls``, making the decorator suitable
        (with caveats) for use with instance or class methods.
        Given the example::

            class MyClass(object):
                @region.cache_on_arguments(namespace="foo")
                def one(self, a, b):
                    return a + b

        The cache key above for ``MyClass().one(3, 4)`` will
        again produce the same cache key of ``myapp.tools:one|foo|3 4`` -
        the name ``self`` is skipped.

        The ``namespace`` parameter is optional, and is used
        normally to disambiguate two functions of the same
        name within the same module, as can occur when decorating
        instance or class methods as below::

            class MyClass(object):
                @region.cache_on_arguments(namespace='MC')
                def somemethod(self, x, y):
                    ""

            class MyOtherClass(object):
                @region.cache_on_arguments(namespace='MOC')
                def somemethod(self, x, y):
                    ""

        Above, the ``namespace`` parameter disambiguates
        between ``somemethod`` on ``MyClass`` and ``MyOtherClass``.
        Python class declaration mechanics otherwise prevent
        the decorator from having awareness of the ``MyClass``
        and ``MyOtherClass`` names, as the function is received
        by the decorator before it becomes an instance method.

        The function key generation can be entirely replaced
        on a per-region basis using the ``function_key_generator``
        argument present on :func:`.make_region` and
        :class:`.CacheRegion`. If defaults to
        :func:`.function_key_generator`.

        :param namespace: optional string argument which will be
         established as part of the cache key.   This may be needed
         to disambiguate functions of the same name within the same
         source file, such as those
         associated with classes - note that the decorator itself
         can't see the parent class on a function as the class is
         being declared.

        :param expiration_time: if not None, will override the normal
         expiration time.

         May be specified as a callable, taking no arguments, that
         returns a value to be used as the ``expiration_time``. This callable
         will be called whenever the decorated function itself is called, in
         caching or retrieving. Thus, this can be used to
         determine a *dynamic* expiration time for the cached function
         result.  Example use cases include "cache the result until the
         end of the day, week or time period" and "cache until a certain date
         or time passes".

         .. versionchanged:: 0.5.0
            ``expiration_time`` may be passed as a callable to
            :meth:`.CacheRegion.cache_on_arguments`.

        :param should_cache_fn: passed to :meth:`.CacheRegion.get_or_create`.

         .. versionadded:: 0.4.3

        :param to_str: callable, will be called on each function argument
         in order to convert to a string.  Defaults to ``str()``.  If the
         function accepts non-ascii unicode arguments on Python 2.x, the
         ``unicode()`` builtin can be substituted, but note this will
         produce unicode cache keys which may require key mangling before
         reaching the cache.

         .. versionadded:: 0.5.0

        :param function_key_generator: a function that will produce a
         "cache key". This function will supersede the one configured on the
         :class:`.CacheRegion` itself.

         .. versionadded:: 0.5.5

        .. seealso::

            :meth:`.CacheRegion.cache_multi_on_arguments`

            :meth:`.CacheRegion.get_or_create`

        """
        expiration_time_is_callable = compat.callable(expiration_time)

        if function_key_generator is None:
            function_key_generator = self.function_key_generator

        def decorator(fn):
            if to_str is compat.string_type:
                # backwards compatible
                key_generator = function_key_generator(namespace, fn)
            else:
                key_generator = function_key_generator(
                    namespace, fn,
                    to_str=to_str)

            @wraps(fn)
            def decorate(*arg, **kw):
                key = key_generator(*arg, **kw)

                @wraps(fn)
                def creator():
                    return fn(*arg, **kw)
                timeout = expiration_time() if expiration_time_is_callable \
                    else expiration_time
                return self.get_or_create(key, creator, timeout,
                                          should_cache_fn)

            def invalidate(*arg, **kw):
                key = key_generator(*arg, **kw)
                self.delete(key)

            def set_(value, *arg, **kw):
                key = key_generator(*arg, **kw)
                self.set(key, value)

            def get(*arg, **kw):
                key = key_generator(*arg, **kw)
                return self.get(key)

            def refresh(*arg, **kw):
                key = key_generator(*arg, **kw)
                value = fn(*arg, **kw)
                self.set(key, value)
                return value

            decorate.set = set_
            decorate.invalidate = invalidate
            decorate.refresh = refresh
            decorate.get = get

            return decorate
        return decorator

    def cache_multi_on_arguments(
            self, namespace=None, expiration_time=None,
            should_cache_fn=None,
            asdict=False, to_str=compat.string_type,
            function_multi_key_generator=None):
        """A function decorator that will cache multiple return
        values from the function using a sequence of keys derived from the
        function itself and the arguments passed to it.

        This method is the "multiple key" analogue to the
        :meth:`.CacheRegion.cache_on_arguments` method.

        Example::

            @someregion.cache_multi_on_arguments()
            def generate_something(*keys):
                return [
                    somedatabase.query(key)
                    for key in keys
                ]

        The decorated function can be called normally.  The decorator
        will produce a list of cache keys using a mechanism similar to
        that of :meth:`.CacheRegion.cache_on_arguments`, combining the
        name of the function with the optional namespace and with the
        string form of each key.  It will then consult the cache using
        the same mechanism as that of :meth:`.CacheRegion.get_multi`
        to retrieve all current values; the originally passed keys
        corresponding to those values which aren't generated or need
        regeneration will be assembled into a new argument list, and
        the decorated function is then called with that subset of
        arguments.

        The returned result is a list::

            result = generate_something("key1", "key2", "key3")

        The decorator internally makes use of the
        :meth:`.CacheRegion.get_or_create_multi` method to access the
        cache and conditionally call the function.  See that
        method for additional behavioral details.

        Unlike the :meth:`.CacheRegion.cache_on_arguments` method,
        :meth:`.CacheRegion.cache_multi_on_arguments` works only with
        a single function signature, one which takes a simple list of
        keys as arguments.

        Like :meth:`.CacheRegion.cache_on_arguments`, the decorated function
        is also provided with a ``set()`` method, which here accepts a
        mapping of keys and values to set in the cache::

            generate_something.set({"k1": "value1",
                                    "k2": "value2", "k3": "value3"})

        ...an ``invalidate()`` method, which has the effect of deleting
        the given sequence of keys using the same mechanism as that of
        :meth:`.CacheRegion.delete_multi`::

            generate_something.invalidate("k1", "k2", "k3")

        ...a ``refresh()`` method, which will call the creation
        function, cache the new values, and return them::

            values = generate_something.refresh("k1", "k2", "k3")

        ...and a ``get()`` method, which will return values
        based on the given arguments::

            values = generate_something.get("k1", "k2", "k3")

        .. versionadded:: 0.5.3 Added ``get()`` method to decorated
           function.

        Parameters passed to :meth:`.CacheRegion.cache_multi_on_arguments`
        have the same meaning as those passed to
        :meth:`.CacheRegion.cache_on_arguments`.

        :param namespace: optional string argument which will be
         established as part of each cache key.

        :param expiration_time: if not None, will override the normal
         expiration time.  May be passed as an integer or a
         callable.

        :param should_cache_fn: passed to
         :meth:`.CacheRegion.get_or_create_multi`. This function is given a
         value as returned by the creator, and only if it returns True will
         that value be placed in the cache.

        :param asdict: if ``True``, the decorated function should return
         its result as a dictionary of keys->values, and the final result
         of calling the decorated function will also be a dictionary.
         If left at its default value of ``False``, the decorated function
         should return its result as a list of values, and the final
         result of calling the decorated function will also be a list.

         When ``asdict==True`` if the dictionary returned by the decorated
         function is missing keys, those keys will not be cached.

        :param to_str: callable, will be called on each function argument
         in order to convert to a string.  Defaults to ``str()``.  If the
         function accepts non-ascii unicode arguments on Python 2.x, the
         ``unicode()`` builtin can be substituted, but note this will
         produce unicode cache keys which may require key mangling before
         reaching the cache.

        .. versionadded:: 0.5.0

        :param function_multi_key_generator: a function that will produce a
         list of keys. This function will supersede the one configured on the
         :class:`.CacheRegion` itself.

         .. versionadded:: 0.5.5

        .. seealso::

            :meth:`.CacheRegion.cache_on_arguments`

            :meth:`.CacheRegion.get_or_create_multi`

        """
        expiration_time_is_callable = compat.callable(expiration_time)

        if function_multi_key_generator is None:
            function_multi_key_generator = self.function_multi_key_generator

        def decorator(fn):
            key_generator = function_multi_key_generator(
                namespace, fn,
                to_str=to_str)

            @wraps(fn)
            def decorate(*arg, **kw):
                cache_keys = arg
                keys = key_generator(*arg, **kw)
                key_lookup = dict(zip(keys, cache_keys))

                @wraps(fn)
                def creator(*keys_to_create):
                    return fn(*[key_lookup[k] for k in keys_to_create])

                timeout = expiration_time() if expiration_time_is_callable \
                    else expiration_time

                if asdict:
                    def dict_create(*keys):
                        d_values = creator(*keys)
                        return [
                            d_values.get(key_lookup[k], NO_VALUE)
                            for k in keys]

                    def wrap_cache_fn(value):
                        if value is NO_VALUE:
                            return False
                        elif not should_cache_fn:
                            return True
                        else:
                            return should_cache_fn(value)

                    result = self.get_or_create_multi(
                        keys, dict_create, timeout, wrap_cache_fn)
                    result = dict(
                        (k, v) for k, v in zip(cache_keys, result)
                        if v is not NO_VALUE)
                else:
                    result = self.get_or_create_multi(
                        keys, creator, timeout,
                        should_cache_fn)

                return result

            def invalidate(*arg):
                keys = key_generator(*arg)
                self.delete_multi(keys)

            def set_(mapping):
                keys = list(mapping)
                gen_keys = key_generator(*keys)
                self.set_multi(dict(
                    (gen_key, mapping[key])
                    for gen_key, key
                    in zip(gen_keys, keys))
                )

            def get(*arg):
                keys = key_generator(*arg)
                return self.get_multi(keys)

            def refresh(*arg):
                keys = key_generator(*arg)
                values = fn(*arg)
                if asdict:
                    self.set_multi(
                        dict(zip(keys, [values[a] for a in arg]))
                    )
                    return values
                else:
                    self.set_multi(
                        dict(zip(keys, values))
                    )
                    return values

            decorate.set = set_
            decorate.invalidate = invalidate
            decorate.refresh = refresh
            decorate.get = get

            return decorate
        return decorator


def make_region(*arg, **kw):
    """Instantiate a new :class:`.CacheRegion`.

    Currently, :func:`.make_region` is a passthrough
    to :class:`.CacheRegion`.  See that class for
    constructor arguments.

    """
    return CacheRegion(*arg, **kw)
