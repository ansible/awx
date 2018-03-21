import logging
import json
from time import time
from functools import wraps
from inspect import isfunction

# Django
from django.db.models import DateTimeField, Model, CharField
from django.db import connection, transaction, IntegrityError

# solo, Django app
from solo.models import SingletonModel

# AWX
from awx.main.utils.pglock import advisory_lock
from awx.main.dispatch.publish import task


__all__ = ['TowerScheduleState', 'lazy_task']

logger = logging.getLogger('awx.main.models.tasks')


class TowerScheduleState(SingletonModel):
    schedule_last_run = DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.schedule_last_run.strftime('%Y%m%dT%H%M%SZ')


class TaskRescheduleFlag(Model):
    """Used by the lazy_task decorator.
    Names are a slug, corresponding to task combined with arguments.
    """
    name = CharField(unique=True, max_length=512, primary_key=True)

    class Meta:
        app_label = 'main'

    def __unicode__(self):
        return self.name

    @staticmethod
    def gently_set_flag(name):
        """Create a flag in a way that avoids interference with any
        other actomic blocks that may be active
        """
        if connection.in_atomic_block:
            # Nesting transaction block does not set parent rollback
            with transaction.atomic():
                TaskRescheduleFlag.objects.create(name=name)
        else:
            # Preferable option, immediate and efficient
            TaskRescheduleFlag.objects.create(name=name)

    @staticmethod
    def get_lock_name(func_name, args):
        name = func_name
        # If function takes args, then make lock specific to those args
        if args:
            name += ':' + json.dumps(args)
        return name


def lazy_execute(f):
    @wraps(f)
    def new_func(*args, **kwargs):
        name = TaskRescheduleFlag.get_lock_name(f.__name__, args)

        def resubmit(reason):
            try:
                f.apply_async(args=args, kwargs=kwargs)
                logger.info('Resubmitted lazy task {}. {}'.format(name, reason))
            except Exception:
                logger.exception('Resubmission check of task {} failed, unexecuted work could remain.'.format(name))

        ret = None
        flag_exists = True  # may not exist, arbitrary initial value
        with advisory_lock(name, wait=False) as compute_lock:  # non-blocking, acquire lock
            if not compute_lock:
                try:
                    TaskRescheduleFlag.gently_set_flag(name)
                    logger.debug('Another process is doing {}, rescheduled for after it completes.'.format(name))
                    with advisory_lock(name, wait=False) as compute_lock2:
                        gave_up_lock = bool(compute_lock2)
                    if gave_up_lock:
                        resubmit('Continuity gap due to race condition.')
                except IntegrityError:
                    logger.debug('Another process is doing {}, reschedule is already planned, no-op.'.format(name))
                return

            logger.debug('Obtained {} lock, performing task work.'.format(name))
            # Claim flag, flag may or may not exist, this is fire-and-forget
            TaskRescheduleFlag.objects.filter(name=name).delete()

            start_time = time()
            ret = f(*args, **kwargs)
            delta = time() - start_time

            flag_exists = TaskRescheduleFlag.objects.filter(name=name).exists()

        if flag_exists:
            resubmit('Work finished in {0:.3f}s, but flag was reset.'.format(delta))
        else:
            logger.debug('Cleared work for lock {0} in {1:.3f}s.'.format(name, delta))

        return ret

    return new_func


def lazy_task(*args, **kwargs):
    """
    task wrapper to schedule time-sensitive idempotent tasks efficiently
    see section in docs/tasks.md
    """

    def new_decorator(fn):
        if not isfunction(fn):
            raise RuntimeError('lazy tasks only supported for functions, given {}'.format(fn))

        # This is passing-through the original task decorator that all tasks use
        task_fn = task(*args, **kwargs)(fn)

        # This converts the function into a lazier version of itself which
        # uses a non-blocking lock combined with a reschedule flag to make
        # sure it runs after the last request received
        lazy_fn = lazy_execute(task_fn)

        # copy tasks bound to the PublisherMixin from dispatch code
        setattr(lazy_fn, 'name', task_fn.name)
        setattr(lazy_fn, 'apply_async', task_fn.apply_async)
        setattr(lazy_fn, 'delay', task_fn.delay)

        return lazy_fn

    return new_decorator
