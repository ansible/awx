from __future__ import absolute_import, unicode_literals

import sys

from datetime import timedelta

from billiard.einfo import ExceptionInfo
import django
from django.core.cache.backends.base import InvalidCacheBackendError

from celery import result
from celery import states
from celery.utils import gen_unique_id

from djcelery.app import app
from djcelery.backends.cache import CacheBackend
from djcelery.tests.utils import unittest


class SomeClass(object):

    def __init__(self, data):
        self.data = data


class test_CacheBackend(unittest.TestCase):

    def test_mark_as_done(self):
        cb = CacheBackend(app=app)

        tid = gen_unique_id()

        self.assertEqual(cb.get_status(tid), states.PENDING)
        self.assertIsNone(cb.get_result(tid))

        cb.mark_as_done(tid, 42)
        self.assertEqual(cb.get_status(tid), states.SUCCESS)
        self.assertEqual(cb.get_result(tid), 42)
        self.assertTrue(cb.get_result(tid), 42)

    def test_forget(self):
        b = CacheBackend(app=app)
        tid = gen_unique_id()
        b.mark_as_done(tid, {'foo': 'bar'})
        self.assertEqual(b.get_result(tid).get('foo'), 'bar')
        b.forget(tid)
        self.assertNotIn(tid, b._cache)
        self.assertIsNone(b.get_result(tid))

    def test_save_restore_delete_group(self):
        backend = CacheBackend(app=app)
        group_id = gen_unique_id()
        subtask_ids = [gen_unique_id() for i in range(10)]
        subtasks = map(result.AsyncResult, subtask_ids)
        res = result.GroupResult(group_id, subtasks)
        res.save(backend=backend)
        saved = result.GroupResult.restore(group_id, backend=backend)
        self.assertListEqual(saved.subtasks, subtasks)
        self.assertEqual(saved.id, group_id)
        saved.delete(backend=backend)
        self.assertIsNone(result.GroupResult.restore(group_id,
                                                     backend=backend))

    def test_is_pickled(self):
        cb = CacheBackend(app=app)

        tid2 = gen_unique_id()
        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        cb.mark_as_done(tid2, result)
        # is serialized properly.
        rindb = cb.get_result(tid2)
        self.assertEqual(rindb.get('foo'), 'baz')
        self.assertEqual(rindb.get('bar').data, 12345)

    def test_mark_as_failure(self):
        cb = CacheBackend(app=app)

        einfo = None
        tid3 = gen_unique_id()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            einfo = ExceptionInfo(sys.exc_info())
            pass
        cb.mark_as_failure(tid3, exception, traceback=einfo.traceback)
        self.assertEqual(cb.get_status(tid3), states.FAILURE)
        self.assertIsInstance(cb.get_result(tid3), KeyError)
        self.assertEqual(cb.get_traceback(tid3), einfo.traceback)

    def test_process_cleanup(self):
        cb = CacheBackend(app=app)
        cb.process_cleanup()

    def test_set_expires(self):
        cb1 = CacheBackend(app=app, expires=timedelta(seconds=16))
        self.assertEqual(cb1.expires, 16)
        cb2 = CacheBackend(app=app, expires=32)
        self.assertEqual(cb2.expires, 32)


class test_custom_CacheBackend(unittest.TestCase):

    def test_custom_cache_backend(self):
        from celery import current_app
        prev_backend = current_app.conf.CELERY_CACHE_BACKEND
        prev_module = sys.modules['djcelery.backends.cache']

        if django.VERSION >= (1, 3):
            current_app.conf.CELERY_CACHE_BACKEND = \
                'django.core.cache.backends.dummy.DummyCache'
        else:
            # Django 1.2 used 'scheme://' style cache backends
            current_app.conf.CELERY_CACHE_BACKEND = 'dummy://'
        sys.modules.pop('djcelery.backends.cache')
        try:
            from djcelery.backends.cache import cache
            from django.core.cache import cache as django_cache
            self.assertEqual(cache.__class__.__module__,
                             'django.core.cache.backends.dummy')
            self.assertIsNot(cache, django_cache)
        finally:
            current_app.conf.CELERY_CACHE_BACKEND = prev_backend
            sys.modules['djcelery.backends.cache'] = prev_module


class test_MemcacheWrapper(unittest.TestCase):

    def test_memcache_wrapper(self):

        try:
            from django.core.cache.backends import memcached
            from django.core.cache.backends import locmem
        except InvalidCacheBackendError:
            sys.stderr.write(
                '\n* Memcache library is not installed. Skipping test.\n')
            return
        try:
            prev_cache_cls = memcached.CacheClass
            memcached.CacheClass = locmem.CacheClass
        except AttributeError:
            return
        prev_backend_module = sys.modules.pop('djcelery.backends.cache')
        try:
            from djcelery.backends.cache import cache
            key = 'cu.test_memcache_wrapper'
            val = 'The quick brown fox.'
            default = 'The lazy dog.'

            self.assertEqual(cache.get(key, default=default), default)
            cache.set(key, val)
            self.assertEqual(cache.get(key, default=default), val)
        finally:
            memcached.CacheClass = prev_cache_cls
            sys.modules['djcelery.backends.cache'] = prev_backend_module
