from __future__ import absolute_import

from datetime import timedelta

from celery import current_app
from celery import states
from celery.result import AsyncResult
from celery.task import PeriodicTask
from celery.utils import gen_unique_id

from djcelery.backends.database import DatabaseBackend
from djcelery.utils import now
from djcelery.tests.utils import unittest


class SomeClass(object):

    def __init__(self, data):
        self.data = data


class MyPeriodicTask(PeriodicTask):
    name = 'c.u.my-periodic-task-244'
    run_every = timedelta(seconds=1)

    def run(self, **kwargs):
        return 42


class TestDatabaseBackend(unittest.TestCase):

    def test_backend(self):
        b = DatabaseBackend()
        tid = gen_unique_id()

        self.assertEqual(b.get_status(tid), states.PENDING)
        self.assertIsNone(b.get_result(tid))

        b.mark_as_done(tid, 42)
        self.assertEqual(b.get_status(tid), states.SUCCESS)
        self.assertEqual(b.get_result(tid), 42)

        tid2 = gen_unique_id()
        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        b.mark_as_done(tid2, result)
        # is serialized properly.
        rindb = b.get_result(tid2)
        self.assertEqual(rindb.get('foo'), 'baz')
        self.assertEqual(rindb.get('bar').data, 12345)

        tid3 = gen_unique_id()
        try:
            raise KeyError('foo')
        except KeyError, exception:
            pass
        b.mark_as_failure(tid3, exception)
        self.assertEqual(b.get_status(tid3), states.FAILURE)
        self.assertIsInstance(b.get_result(tid3), KeyError)

    def test_forget(self):
        b = DatabaseBackend()
        tid = gen_unique_id()
        b.mark_as_done(tid, {'foo': 'bar'})
        x = AsyncResult(tid)
        self.assertEqual(x.result.get('foo'), 'bar')
        x.forget()
        self.assertIsNone(x.result)

    def test_group_store(self):
        b = DatabaseBackend()
        tid = gen_unique_id()

        self.assertIsNone(b.restore_group(tid))

        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        b.save_group(tid, result)
        rindb = b.restore_group(tid)
        self.assertIsNotNone(rindb)
        self.assertEqual(rindb.get('foo'), 'baz')
        self.assertEqual(rindb.get('bar').data, 12345)
        b.delete_group(tid)
        self.assertIsNone(b.restore_group(tid))

    def test_cleanup(self):
        b = DatabaseBackend()
        b.TaskModel._default_manager.all().delete()
        ids = [gen_unique_id() for _ in xrange(3)]
        for i, res in enumerate((16, 32, 64)):
            b.mark_as_done(ids[i], res)

        self.assertEqual(b.TaskModel._default_manager.count(), 3)

        then = now() - current_app.conf.CELERY_TASK_RESULT_EXPIRES * 2
        # Have to avoid save() because it applies the auto_now=True.
        b.TaskModel._default_manager.filter(task_id__in=ids[:-1]) \
                                    .update(date_done=then)

        b.cleanup()
        self.assertEqual(b.TaskModel._default_manager.count(), 1)
