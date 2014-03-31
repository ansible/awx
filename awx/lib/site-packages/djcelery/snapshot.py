from __future__ import absolute_import, unicode_literals

from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings

from celery import states
from celery.events.state import Task
from celery.events.snapshot import Polaroid
from celery.five import monotonic
from celery.utils.log import get_logger
from celery.utils.timeutils import maybe_iso8601

from .models import WorkerState, TaskState
from .utils import maybe_make_aware

WORKER_UPDATE_FREQ = 60  # limit worker timestamp write freq.
SUCCESS_STATES = frozenset([states.SUCCESS])

# Expiry can be timedelta or None for never expire.
EXPIRE_SUCCESS = getattr(settings, 'CELERYCAM_EXPIRE_SUCCESS',
                         timedelta(days=1))
EXPIRE_ERROR = getattr(settings, 'CELERYCAM_EXPIRE_ERROR',
                       timedelta(days=3))
EXPIRE_PENDING = getattr(settings, 'CELERYCAM_EXPIRE_PENDING',
                         timedelta(days=5))
NOT_SAVED_ATTRIBUTES = frozenset(['name', 'args', 'kwargs', 'eta'])

logger = get_logger(__name__)
debug = logger.debug


def aware_tstamp(secs):
    """Event timestamps uses the local timezone."""
    return maybe_make_aware(datetime.utcfromtimestamp(secs))


class Camera(Polaroid):
    TaskState = TaskState
    WorkerState = WorkerState

    clear_after = True
    worker_update_freq = WORKER_UPDATE_FREQ
    expire_states = {
        SUCCESS_STATES: EXPIRE_SUCCESS,
        states.EXCEPTION_STATES: EXPIRE_ERROR,
        states.UNREADY_STATES: EXPIRE_PENDING,
    }

    def __init__(self, *args, **kwargs):
        super(Camera, self).__init__(*args, **kwargs)
        self._last_worker_write = defaultdict(lambda: (None, None))

    def get_heartbeat(self, worker):
        try:
            heartbeat = worker.heartbeats[-1]
        except IndexError:
            return
        # Check for timezone settings
        if getattr(settings, "USE_TZ", False):
            return aware_tstamp(heartbeat)
        return datetime.fromtimestamp(heartbeat)

    def handle_worker(self, hostname_worker):
        (hostname, worker) = hostname_worker
        last_write, obj = self._last_worker_write[hostname]
        if not last_write or \
                monotonic() - last_write > self.worker_update_freq:
            obj = self.WorkerState.objects.update_or_create(
                hostname=hostname,
                defaults={'last_heartbeat': self.get_heartbeat(worker)},
            )
            self._last_worker_write[hostname] = (monotonic(), obj)
        return obj

    def handle_task(self, uuid_task, worker=None):
        """Handle snapshotted event."""
        uuid, task = uuid_task
        if task.worker and task.worker.hostname:
            worker = self.handle_worker(
                (task.worker.hostname, task.worker),
            )

        defaults = {
            'name': task.name,
            'args': task.args,
            'kwargs': task.kwargs,
            'eta': maybe_make_aware(maybe_iso8601(task.eta)),
            'expires': maybe_make_aware(maybe_iso8601(task.expires)),
            'state': task.state,
            'tstamp': aware_tstamp(task.timestamp),
            'result': task.result or task.exception,
            'traceback': task.traceback,
            'runtime': task.runtime,
            'worker': worker
        }
        # Some fields are only stored in the RECEIVED event,
        # so we should remove these from default values,
        # so that they are not overwritten by subsequent states.
        [defaults.pop(attr, None) for attr in NOT_SAVED_ATTRIBUTES
         if defaults[attr] is None]
        return self.update_task(task.state,
                                task_id=uuid, defaults=defaults)

    def update_task(self, state, **kwargs):
        objects = self.TaskState.objects
        defaults = kwargs.pop('defaults', None) or {}
        if not defaults.get('name'):
            return
        obj, created = objects.get_or_create(defaults=defaults, **kwargs)
        if created:
            return obj
        else:
            if states.state(state) < states.state(obj.state):
                keep = Task.merge_rules[states.RECEIVED]
                defaults = dict(
                    (k, v) for k, v in defaults.items()
                    if k not in keep
                )

        for k, v in defaults.items():
            setattr(obj, k, v)
        for datefield in ('eta', 'expires', 'tstamp'):
            # Brute force trying to fix #183
            setattr(obj, datefield, maybe_make_aware(getattr(obj, datefield)))
        obj.save()

        return obj

    def on_shutter(self, state, commit_every=100):

        def _handle_tasks():
            for i, task in enumerate(state.tasks.items()):
                self.handle_task(task)

        for worker in state.workers.items():
            self.handle_worker(worker)
        _handle_tasks()

    def on_cleanup(self):
        expired = (self.TaskState.objects.expire_by_states(states, expires)
                   for states, expires in self.expire_states.items())
        dirty = sum(item for item in expired if item is not None)
        if dirty:
            debug('Cleanup: Marked %s objects as dirty.', dirty)
            self.TaskState.objects.purge()
            debug('Cleanup: %s objects purged.', dirty)
            return dirty
        return 0
