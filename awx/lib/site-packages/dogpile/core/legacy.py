from __future__ import with_statement

from .util import threading
from .readwrite_lock import ReadWriteMutex
from .dogpile import Lock
import time
import contextlib

class Dogpile(object):
    """Dogpile lock class.

    .. deprecated:: 0.4.0
        The :class:`.Lock` object specifies the full
        API of the :class:`.Dogpile` object in a single way,
        rather than providing multiple modes of usage which
        don't necessarily work in the majority of cases.
        :class:`.Dogpile` is now a wrapper around the :class:`.Lock` object
        which provides dogpile.core's original usage pattern.
        This usage pattern began as something simple, but was
        not of general use in real-world caching environments without
        several extra complicating factors; the :class:`.Lock`
        object presents the "real-world" API more succinctly,
        and also fixes a cross-process concurrency issue.

    :param expiretime: Expiration time in seconds.  Set to
     ``None`` for never expires.
    :param init: if True, set the 'createdtime' to the
     current time.
    :param lock: a mutex object that provides
     ``acquire()`` and ``release()`` methods.

    """
    def __init__(self, expiretime, init=False, lock=None):
        """Construct a new :class:`.Dogpile`.

        """
        if lock:
            self.dogpilelock = lock
        else:
            self.dogpilelock = threading.Lock()

        self.expiretime = expiretime
        if init:
            self.createdtime = time.time()

    createdtime = -1
    """The last known 'creation time' of the value,
    stored as an epoch (i.e. from ``time.time()``).

    If the value here is -1, it is assumed the value
    should recreate immediately.

    """

    def acquire(self, creator,
                        value_fn=None,
                        value_and_created_fn=None):
        """Acquire the lock, returning a context manager.

        :param creator: Creation function, used if this thread
         is chosen to create a new value.

        :param value_fn: Optional function that returns
         the value from some datasource.  Will be returned
         if regeneration is not needed.

        :param value_and_created_fn: Like value_fn, but returns a tuple
         of (value, createdtime).  The returned createdtime
         will replace the "createdtime" value on this dogpile
         lock.   This option removes the need for the dogpile lock
         itself to remain persistent across usages; another
         dogpile can come along later and pick up where the
         previous one left off.

        """

        if value_and_created_fn is None:
            if value_fn is None:
                def value_and_created_fn():
                    return None, self.createdtime
            else:
                def value_and_created_fn():
                    return value_fn(), self.createdtime

            def creator_wrapper():
                value = creator()
                self.createdtime = time.time()
                return value, self.createdtime
        else:
            def creator_wrapper():
                value = creator()
                self.createdtime = time.time()
                return value

        return Lock(
            self.dogpilelock,
            creator_wrapper,
            value_and_created_fn,
            self.expiretime
        )

    @property
    def is_expired(self):
        """Return true if the expiration time is reached, or no
        value is available."""

        return not self.has_value or \
            (
                self.expiretime is not None and
                time.time() - self.createdtime > self.expiretime
            )

    @property
    def has_value(self):
        """Return true if the creation function has proceeded
        at least once."""
        return self.createdtime > 0


class SyncReaderDogpile(Dogpile):
    """Provide a read-write lock function on top of the :class:`.Dogpile`
    class.

    .. deprecated:: 0.4.0
        The :class:`.ReadWriteMutex` object can be used directly.

    """
    def __init__(self, *args, **kw):
        super(SyncReaderDogpile, self).__init__(*args, **kw)
        self.readwritelock = ReadWriteMutex()

    @contextlib.contextmanager
    def acquire_write_lock(self):
        """Return the "write" lock context manager.

        This will provide a section that is mutexed against
        all readers/writers for the dogpile-maintained value.

        """

        self.readwritelock.acquire_write_lock()
        try:
            yield
        finally:
            self.readwritelock.release_write_lock()

    @contextlib.contextmanager
    def acquire(self, *arg, **kw):
        with super(SyncReaderDogpile, self).acquire(*arg, **kw) as value:
            self.readwritelock.acquire_read_lock()
            try:
                yield value
            finally:
                self.readwritelock.release_read_lock()
