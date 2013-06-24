"""
kombu.utils.finalize
====================

Execute cleanup handlers when objects go out of scope.

Taken from :class:`multiprocessing.util.Finalize`.

"""
from __future__ import absolute_import

import weakref

from itertools import count

__all__ = ['Finalize']


class Finalize(object):
    """Object finalization using weakrefs."""
    _count = count().next
    _registry = {}

    def __init__(self, obj, callback, args=(), kwargs=None,
                 exitpriority=None):

        if obj is not None:
            self._weakref = weakref.ref(obj, self)
        else:
            assert exitpriority is not None

        self._callback = callback
        self._args = args
        self._kwargs = kwargs or {}
        self._key = (exitpriority, self._count())

        self._registry[self._key] = self

    def __call__(self, wr=None):
        """Run the callback unless it has already been called or
        cancelled."""
        try:
            self._registry.pop(self._key)
        except KeyError:
            pass
        else:
            try:
                return self._callback(*self._args, **self._kwargs)
            finally:
                self._reset()

    def _reset(self):
        self._weakref = self._callback = self._args = \
            self._kwargs = self._key = None

    def cancel(self):
        """Cancel finalization of the object."""
        try:
            self._registry.pop(self._key)
        except KeyError:
            pass
        else:
            self._reset()

    def still_active(self):
        self._key in self._registry

    def __repr__(self):
        try:
            obj = self._weakref()
        except (AttributeError, TypeError):
            return '<Finalize: (dead)>'

        if obj is None:
            return

        x = '<Finalize object, callback=%s' % \
            getattr(self._callback, '__name__', self._callback)
        if self._args:
            x += ', args=%r' % (self._args, )
        if self._kwargs:
            x += ', kwargs=%r' % (self._kwargs, )
        if self._key[0] is not None:
            x += ', exitprority=%r' % (self._key[0], )
        return x + '>'
