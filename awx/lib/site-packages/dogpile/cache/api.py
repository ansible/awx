import operator
from .compat import py3k


class NoValue(object):
    """Describe a missing cache value.

    The :attr:`.NO_VALUE` module global
    should be used.

    """
    @property
    def payload(self):
        return self

    if py3k:
        def __bool__(self):  # pragma NO COVERAGE
            return False
    else:
        def __nonzero__(self):  # pragma NO COVERAGE
            return False

NO_VALUE = NoValue()
"""Value returned from ``get()`` that describes
a  key not present."""


class CachedValue(tuple):
    """Represent a value stored in the cache.

    :class:`.CachedValue` is a two-tuple of
    ``(payload, metadata)``, where ``metadata``
    is dogpile.cache's tracking information (
    currently the creation time).  The metadata
    and tuple structure is pickleable, if
    the backend requires serialization.

    """
    payload = property(operator.itemgetter(0))
    """Named accessor for the payload."""

    metadata = property(operator.itemgetter(1))
    """Named accessor for the dogpile.cache metadata dictionary."""

    def __new__(cls, payload, metadata):
        return tuple.__new__(cls, (payload, metadata))

    def __reduce__(self):
        return CachedValue, (self.payload, self.metadata)


class CacheBackend(object):
    """Base class for backend implementations."""

    key_mangler = None
    """Key mangling function.

    May be None, or otherwise declared
    as an ordinary instance method.

    """

    def __init__(self, arguments):  # pragma NO COVERAGE
        """Construct a new :class:`.CacheBackend`.

        Subclasses should override this to
        handle the given arguments.

        :param arguments: The ``arguments`` parameter
         passed to :func:`.make_registry`.

        """
        raise NotImplementedError()

    @classmethod
    def from_config_dict(cls, config_dict, prefix):
        prefix_len = len(prefix)
        return cls(
            dict(
                (key[prefix_len:], config_dict[key])
                for key in config_dict
                if key.startswith(prefix)
            )
        )

    def get_mutex(self, key):
        """Return an optional mutexing object for the given key.

        This object need only provide an ``acquire()``
        and ``release()`` method.

        May return ``None``, in which case the dogpile
        lock will use a regular ``threading.Lock``
        object to mutex concurrent threads for
        value creation.   The default implementation
        returns ``None``.

        Different backends may want to provide various
        kinds of "mutex" objects, such as those which
        link to lock files, distributed mutexes,
        memcached semaphores, etc.  Whatever
        kind of system is best suited for the scope
        and behavior of the caching backend.

        A mutex that takes the key into account will
        allow multiple regenerate operations across
        keys to proceed simultaneously, while a mutex
        that does not will serialize regenerate operations
        to just one at a time across all keys in the region.
        The latter approach, or a variant that involves
        a modulus of the given key's hash value,
        can be used as a means of throttling the total
        number of value recreation operations that may
        proceed at one time.

        """
        return None

    def get(self, key):  # pragma NO COVERAGE
        """Retrieve a value from the cache.

        The returned value should be an instance of
        :class:`.CachedValue`, or ``NO_VALUE`` if
        not present.

        """
        raise NotImplementedError()

    def get_multi(self, keys):  # pragma NO COVERAGE
        """Retrieve multiple values from the cache.

        The returned value should be a list, corresponding
        to the list of keys given.

        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()

    def set(self, key, value):  # pragma NO COVERAGE
        """Set a value in the cache.

        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.
        The value will always be an instance
        of :class:`.CachedValue`.

        """
        raise NotImplementedError()

    def set_multi(self, mapping):  # pragma NO COVERAGE
        """Set multiple values in the cache.

        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.
        The value will always be an instance
        of :class:`.CachedValue`.

        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()

    def delete(self, key):  # pragma NO COVERAGE
        """Delete a value from the cache.

        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.

        The behavior here should be idempotent,
        that is, can be called any number of times
        regardless of whether or not the
        key exists.
        """
        raise NotImplementedError()

    def delete_multi(self, keys):  # pragma NO COVERAGE
        """Delete multiple values from the cache.

        The key will be whatever was passed
        to the registry, processed by the
        "key mangling" function, if any.

        The behavior here should be idempotent,
        that is, can be called any number of times
        regardless of whether or not the
        key exists.

        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()
