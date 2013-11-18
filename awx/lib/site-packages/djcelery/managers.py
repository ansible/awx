from __future__ import absolute_import, unicode_literals

import warnings

from functools import wraps
from itertools import count

from django.db import transaction, connection
try:
    from django.db import connections, router
except ImportError:  # pre-Django 1.2
    connections = router = None  # noqa

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings

from celery.utils.timeutils import maybe_timedelta

from .utils import now


class TxIsolationWarning(UserWarning):
    pass


def transaction_retry(max_retries=1):
    """Decorator for methods doing database operations.

    If the database operation fails, it will retry the operation
    at most ``max_retries`` times.

    """
    def _outer(fun):

        @wraps(fun)
        def _inner(*args, **kwargs):
            _max_retries = kwargs.pop('exception_retry_count', max_retries)
            for retries in count(0):
                try:
                    return fun(*args, **kwargs)
                except Exception:   # pragma: no cover
                    # Depending on the database backend used we can experience
                    # various exceptions. E.g. psycopg2 raises an exception
                    # if some operation breaks the transaction, so saving
                    # the task result won't be possible until we rollback
                    # the transaction.
                    if retries >= _max_retries:
                        raise
                    transaction.rollback_unless_managed()

        return _inner

    return _outer


def update_model_with_dict(obj, fields):
    [setattr(obj, attr_name, attr_value)
        for attr_name, attr_value in fields.items()]
    obj.save()
    return obj


class ExtendedQuerySet(QuerySet):

    def update_or_create(self, **kwargs):
        obj, created = self.get_or_create(**kwargs)

        if not created:
            fields = dict(kwargs.pop('defaults', {}))
            fields.update(kwargs)
            update_model_with_dict(obj, fields)

        return obj


class ExtendedManager(models.Manager):

    def get_query_set(self):
        return ExtendedQuerySet(self.model)

    def update_or_create(self, **kwargs):
        return self.get_query_set().update_or_create(**kwargs)

    def connection_for_write(self):
        if connections:
            return connections[router.db_for_write(self.model)]
        return connection

    def connection_for_read(self):
        if connections:
            return connections[self.db]
        return connection

    def current_engine(self):
        try:
            return settings.DATABASES[self.db]['ENGINE']
        except AttributeError:
            return settings.DATABASE_ENGINE


class ResultManager(ExtendedManager):

    def get_all_expired(self, expires):
        """Get all expired task results."""
        return self.filter(date_done__lt=now() - maybe_timedelta(expires))

    @transaction.commit_manually
    def delete_expired(self, expires):
        """Delete all expired taskset results."""
        meta = self.model._meta
        try:
            self.get_all_expired(expires).update(hidden=True)
            cursor = self.connection_for_write().cursor()
            cursor.execute(
                'DELETE FROM {0.db_table} WHERE hidden=%s'.format(meta),
                (True, ),
            )
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()


class PeriodicTaskManager(ExtendedManager):

    def enabled(self):
        return self.filter(enabled=True)


class TaskManager(ResultManager):
    """Manager for :class:`celery.models.Task` models."""
    _last_id = None

    def get_task(self, task_id):
        """Get task meta for task by ``task_id``.

        :keyword exception_retry_count: How many times to retry by
            transaction rollback on exception. This could theoretically
            happen in a race condition if another worker is trying to
            create the same task. The default is to retry once.

        """
        try:
            return self.get(task_id=task_id)
        except self.model.DoesNotExist:
            if self._last_id == task_id:
                self.warn_if_repeatable_read()
            self._last_id = task_id
            return self.model(task_id=task_id)

    @transaction_retry(max_retries=2)
    def store_result(self, task_id, result, status,
                     traceback=None, children=None):
        """Store the result and status of a task.

        :param task_id: task id

        :param result: The return value of the task, or an exception
            instance raised by the task.

        :param status: Task status. See
            :meth:`celery.result.AsyncResult.get_status` for a list of
            possible status values.

        :keyword traceback: The traceback at the point of exception (if the
            task failed).

        :keyword children: List of serialized results of subtasks
            of this task.

        :keyword exception_retry_count: How many times to retry by
            transaction rollback on exception. This could theoretically
            happen in a race condition if another worker is trying to
            create the same task. The default is to retry twice.

        """
        return self.update_or_create(task_id=task_id,
                                     defaults={'status': status,
                                               'result': result,
                                               'traceback': traceback,
                                               'meta': {'children': children}})

    def warn_if_repeatable_read(self):
        if 'mysql' in self.current_engine().lower():
            cursor = self.connection_for_read().cursor()
            if cursor.execute('SELECT @@tx_isolation'):
                isolation = cursor.fetchone()[0]
                if isolation == 'REPEATABLE-READ':
                    warnings.warn(TxIsolationWarning(
                        'Polling results with transaction isolation level '
                        'repeatable-read within the same transaction '
                        'may give outdated results. Be sure to commit the '
                        'transaction for each poll iteration.'))


class TaskSetManager(ResultManager):
    """Manager for :class:`celery.models.TaskSet` models."""

    def restore_taskset(self, taskset_id):
        """Get the async result instance by taskset id."""
        try:
            return self.get(taskset_id=taskset_id)
        except self.model.DoesNotExist:
            pass

    def delete_taskset(self, taskset_id):
        """Delete a saved taskset result."""
        s = self.restore_taskset(taskset_id)
        if s:
            s.delete()

    @transaction_retry(max_retries=2)
    def store_result(self, taskset_id, result):
        """Store the async result instance of a taskset.

        :param taskset_id: task set id

        :param result: The return value of the taskset

        """
        return self.update_or_create(taskset_id=taskset_id,
                                     defaults={'result': result})


class TaskStateManager(ExtendedManager):

    def active(self):
        return self.filter(hidden=False)

    def expired(self, states, expires, nowfun=now):
        return self.filter(state__in=states,
                           tstamp__lte=nowfun() - maybe_timedelta(expires))

    def expire_by_states(self, states, expires):
        if expires is not None:
            return self.expired(states, expires).update(hidden=True)

    def purge(self):
        meta = self.model._meta
        cursor = self.connection_for_write().cursor()
        cursor.execute(
            'DELETE FROM {0.db_table} WHERE hidden=%s'.format(meta),
            (True, ),
        )
        transaction.commit_unless_managed()
