from __future__ import absolute_import

import __builtin__
import os
import sys
import types

from functools import wraps
from StringIO import StringIO

import mock

from nose import SkipTest

try:
    import unittest
    unittest.skip
except AttributeError:
    import unittest2 as unittest  # noqa


class TestCase(unittest.TestCase):

    def assertItemsEqual(self, a, b, *args, **kwargs):
        return self.assertEqual(sorted(a), sorted(b), *args, **kwargs)
    assertSameElements = assertItemsEqual


class Mock(mock.Mock):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop('attrs', None) or {}
        super(Mock, self).__init__(*args, **kwargs)
        for attr_name, attr_value in attrs.items():
            setattr(self, attr_name, attr_value)


class ContextMock(Mock):

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass


class MockPool(object):

    def __init__(self, value=None):
        self.value = value or ContextMock()

    def acquire(self, **kwargs):
        return self.value


def redirect_stdouts(fun):

    @wraps(fun)
    def _inner(*args, **kwargs):
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        try:
            return fun(*args, **dict(kwargs,
                                     stdout=sys.stdout, stderr=sys.stderr))
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    return _inner


def module_exists(*modules):

    def _inner(fun):

        @wraps(fun)
        def __inner(*args, **kwargs):
            for module in modules:
                if isinstance(module, basestring):
                    module = types.ModuleType(module)
                sys.modules[module.__name__] = module
                try:
                    return fun(*args, **kwargs)
                finally:
                    sys.modules.pop(module.__name__, None)

        return __inner
    return _inner


# Taken from
# http://bitbucket.org/runeh/snippets/src/tip/missing_modules.py
def mask_modules(*modnames):
    def _inner(fun):

        @wraps(fun)
        def __inner(*args, **kwargs):
            realimport = __builtin__.__import__

            def myimp(name, *args, **kwargs):
                if name in modnames:
                    raise ImportError('No module named %s' % name)
                else:
                    return realimport(name, *args, **kwargs)

            __builtin__.__import__ = myimp
            try:
                return fun(*args, **kwargs)
            finally:
                __builtin__.__import__ = realimport

        return __inner
    return _inner


def skip_if_environ(env_var_name):

    def _wrap_test(fun):

        @wraps(fun)
        def _skips_if_environ(*args, **kwargs):
            if os.environ.get(env_var_name):
                raise SkipTest('SKIP %s: %s set\n' % (
                    fun.__name__, env_var_name))
            return fun(*args, **kwargs)

        return _skips_if_environ

    return _wrap_test


def skip_if_module(module):
    def _wrap_test(fun):
        @wraps(fun)
        def _skip_if_module(*args, **kwargs):
            try:
                __import__(module)
                raise SkipTest('SKIP %s: %s available\n' % (
                    fun.__name__, module))
            except ImportError:
                pass
            return fun(*args, **kwargs)
        return _skip_if_module
    return _wrap_test


def skip_if_not_module(module):
    def _wrap_test(fun):
        @wraps(fun)
        def _skip_if_not_module(*args, **kwargs):
            try:
                __import__(module)
            except ImportError:
                raise SkipTest('SKIP %s: %s available\n' % (
                    fun.__name__, module))
            return fun(*args, **kwargs)
        return _skip_if_not_module
    return _wrap_test


def skip_if_quick(fun):
    return skip_if_environ('QUICKTEST')(fun)
