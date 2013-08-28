from __future__ import absolute_import

import logging

from warnings import warn

from anyjson import deserialize, serialize
from celery import current_app
from celery import schedules
from celery.beat import Scheduler, ScheduleEntry
from celery.utils.encoding import safe_str, safe_repr
from celery.utils.timeutils import is_naive
from kombu.utils.finalize import Finalize

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .models import (PeriodicTask, PeriodicTasks,
                     CrontabSchedule, IntervalSchedule)
from .utils import DATABASE_ERRORS, make_aware

# This scheduler must wake up more frequently than the
# regular of 5 minutes because it needs to take external
# changes to the schedule into account.
DEFAULT_MAX_INTERVAL = 5  # seconds


class ModelEntry(ScheduleEntry):
    model_schedules = ((schedules.crontab, CrontabSchedule, 'crontab'),
                       (schedules.schedule, IntervalSchedule, 'interval'))
    save_fields = ['last_run_at', 'total_run_count', 'no_changes']

    def __init__(self, model):
        self.app = current_app._get_current_object()
        self.name = model.name
        self.task = model.task
        self.schedule = model.schedule
        try:
            self.args = deserialize(model.args or u'[]')
            self.kwargs = deserialize(model.kwargs or u'{}')
        except ValueError:
            logging.error('Failed to serialize arguments for %s.', self.name,
                          exc_info=1)
            logging.warning('Disabling %s', self.name)
            model.no_changes = True
            model.enabled = False
            model.save()

        self.options = {'queue': model.queue,
                        'exchange': model.exchange,
                        'routing_key': model.routing_key,
                        'expires': model.expires}
        self.total_run_count = model.total_run_count
        self.model = model

        if not model.last_run_at:
            model.last_run_at = self._default_now()
        orig = self.last_run_at = model.last_run_at
        if not is_naive(self.last_run_at):
            self.last_run_at = self.last_run_at.replace(tzinfo=None)
        assert orig.hour == self.last_run_at.hour  # timezone sanity

    def is_due(self):
        if not self.model.enabled:
            return False, 5.0   # 5 second delay for re-enable.
        return self.schedule.is_due(self.last_run_at)

    def _default_now(self):
        return self.app.now()

    def __next__(self):
        self.model.last_run_at = self.app.now()
        self.model.total_run_count += 1
        self.model.no_changes = True
        return self.__class__(self.model)
    next = __next__  # for 2to3

    def save(self):
        # Object may not be synchronized, so only
        # change the fields we care about.
        obj = self.model._default_manager.get(pk=self.model.pk)
        for field in self.save_fields:
            setattr(obj, field, getattr(self.model, field))
        obj.last_run_at = make_aware(obj.last_run_at)
        obj.save()

    @classmethod
    def to_model_schedule(cls, schedule):
        for schedule_type, model_type, model_field in cls.model_schedules:
            schedule = schedules.maybe_schedule(schedule)
            if isinstance(schedule, schedule_type):
                model_schedule = model_type.from_schedule(schedule)
                model_schedule.save()
                return model_schedule, model_field
        raise ValueError('Cannot convert schedule type %r to model' % schedule)

    @classmethod
    def from_entry(cls, name, skip_fields=('relative', 'options'), **entry):
        options = entry.get('options') or {}
        fields = dict(entry)
        for skip_field in skip_fields:
            fields.pop(skip_field, None)
        schedule = fields.pop('schedule')
        model_schedule, model_field = cls.to_model_schedule(schedule)
        fields[model_field] = model_schedule
        fields['args'] = serialize(fields.get('args') or [])
        fields['kwargs'] = serialize(fields.get('kwargs') or {})
        fields['queue'] = options.get('queue')
        fields['exchange'] = options.get('exchange')
        fields['routing_key'] = options.get('routing_key')
        return cls(PeriodicTask._default_manager.update_or_create(
            name=name, defaults=fields,
        ))

    def __repr__(self):
        return '<ModelEntry: %s %s(*%s, **%s) {%s}>' % (safe_str(self.name),
                                                        self.task,
                                                        safe_repr(self.args),
                                                        safe_repr(self.kwargs),
                                                        self.schedule)


class DatabaseScheduler(Scheduler):
    Entry = ModelEntry
    Model = PeriodicTask
    Changes = PeriodicTasks
    _schedule = None
    _last_timestamp = None
    _initial_read = False

    def __init__(self, *args, **kwargs):
        self._dirty = set()
        self._finalize = Finalize(self, self.sync, exitpriority=5)
        Scheduler.__init__(self, *args, **kwargs)
        self.max_interval = (
            kwargs.get('max_interval') or
            self.app.conf.CELERYBEAT_MAX_LOOP_INTERVAL or
            DEFAULT_MAX_INTERVAL)

    def setup_schedule(self):
        self.install_default_entries(self.schedule)
        self.update_from_dict(self.app.conf.CELERYBEAT_SCHEDULE)

    def all_as_schedule(self):
        self.logger.debug('DatabaseScheduler: Fetching database schedule')
        s = {}
        for model in self.Model.objects.enabled():
            try:
                s[model.name] = self.Entry(model)
            except ValueError:
                pass
        return s

    def schedule_changed(self):
        try:
            # If MySQL is running with transaction isolation level
            # REPEATABLE-READ (default), then we won't see changes done by
            # other transactions until the current transaction is
            # committed (Issue #41).
            try:
                transaction.commit()
            except transaction.TransactionManagementError:
                pass  # not in transaction management.

            last, ts = self._last_timestamp, self.Changes.last_change()
        except DATABASE_ERRORS, exc:
            warn(RuntimeWarning('Database gave error: %r' % (exc, )))
            return False
        try:
            if ts and ts > (last if last else ts):
                return True
        finally:
            self._last_timestamp = ts
        return False

    def reserve(self, entry):
        new_entry = Scheduler.reserve(self, entry)
        # Need to store entry by name, because the entry may change
        # in the mean time.
        self._dirty.add(new_entry.name)
        return new_entry

    @transaction.commit_manually
    def sync(self):
        self.logger.info('Writing entries...')
        _tried = set()
        try:
            try:
                while self._dirty:
                    try:
                        name = self._dirty.pop()
                        _tried.add(name)
                        self.schedule[name].save()
                    except (KeyError, ObjectDoesNotExist):
                        pass
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
        except DATABASE_ERRORS, exc:
            # retry later
            self._dirty |= _tried
            warn(RuntimeWarning('Database error while sync: %r' % (exc, )))

    def update_from_dict(self, dict_):
        s = {}
        for name, entry in dict_.items():
            try:
                s[name] = self.Entry.from_entry(name, **entry)
            except Exception, exc:
                self.logger.error(
                    'Could not add entry %r to database schedule: %r. '
                    'Contents: %r' % (name, exc, entry))
        self.schedule.update(s)

    def install_default_entries(self, data):
        entries = {}
        if self.app.conf.CELERY_TASK_RESULT_EXPIRES:
            entries.setdefault(
                'celery.backend_cleanup', {
                    'task': 'celery.backend_cleanup',
                    'schedule': schedules.crontab('0', '4', '*'),
                    'options': {'expires': 12 * 3600},
                },
            )
        self.update_from_dict(entries)

    @property
    def schedule(self):
        update = False
        if not self._initial_read:
            self.logger.debug('DatabaseScheduler: intial read')
            update = True
            self._initial_read = True
        elif self.schedule_changed():
            self.logger.info('DatabaseScheduler: Schedule changed.')
            update = True

        if update:
            self.sync()
            self._schedule = self.all_as_schedule()
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(
                    'Current schedule:\n' + '\n'.join(
                        repr(entry) for entry in self._schedule.values())
                )
        return self._schedule
