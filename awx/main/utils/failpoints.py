"""Failpoints: named spots in the code where a test can inject a fault.

A failpoint call is inert unless ``AWX_FAILPOINTS_ENABLED`` is true, and even then it does
nothing until a failpoint of that name is *armed*. Arming, releasing and inspecting
failpoints goes through a small Postgres table, because Postgres is the only store every
node in a cluster shares (Redis is node-local). That is what lets a test running anywhere
pause a dispatcher worker on node A, act on node B, then let A continue.

Typical use from a test or a shell::

    awx-manage failpoint arm heartbeat.start --action pause --match node=awx-1
    awx-manage failpoint wait heartbeat.start --fired
    ...do something elsewhere...
    awx-manage failpoint release heartbeat.start

Actions:
    pause   block until released or disarmed (``--timeout`` seconds, default 600)
    sleep   sleep for ``--seconds`` and continue
    raise   raise FailpointError at the call site, or ``--exception module.Class`` to raise
            a specific type (e.g. redis.exceptions.ConnectionError) the call site handles
    kill    SIGKILL the current process
    kill_parent  SIGKILL the parent process (for a dispatcher worker, the dispatcher)

Matching:
    ``--match key=value`` must equal the call's context (all values compared as strings).
    ``node`` and ``pid`` are always present in the context.
    ``--nth N`` fires only on the Nth matching hit. ``--times N`` caps how often it fires.

This is a test facility. Never enable it in production.
"""

import importlib
import json
import logging
import os
import signal
import threading
import time

from django.conf import settings
from django.db import connection, transaction

logger = logging.getLogger('awx.main.utils.failpoints')

# Every failpoint name must be registered here. A call with an unknown name raises when
# failpoints are enabled, so a typo in a test or in the code fails loudly instead of
# silently never firing.
REGISTRY = {
    'heartbeat.start': 'Start of cluster_node_heartbeat, before instance management. Pausing it makes this node miss heartbeats while staying alive.',
    'job.after_submit_before_unit_saved': 'Normal job path: work unit submitted to receptor, work_unit_id not yet saved on the job.',
    'job.stream_started': 'Normal job and adoption path: results stream opened, before the first event is read.',
    'callback.event': 'Every event handed to the callback (ctx: job_id, counter). Use with --match counter=N or --nth.',
    'job.before_finalize': 'Normal job path: playbook finished, before the terminal status is saved.',
    'job.after_finalize_before_release': 'Normal job path: terminal status saved, before the work unit is released.',
    'lost_instance.before_claim': 'Lost-instance path: job judged adoptable and capacity available, before the claim UPDATE.',
    'sweep.before_claim': 'Orphan sweep: capacity available, before the claim UPDATE.',
    'adoption.after_claim': 'adopt_job_async: job claimed for this controller, before the capacity check and streaming.',
    'adoption.after_snapshot': 'reattach_to_work_unit: dedup snapshot taken, before the replay starts.',
    'adoption.before_finalize': 'reattach_to_work_unit: stream finished, before hooks and the terminal status.',
    'adoption.after_finalize_before_release': 'reattach_to_work_unit: finalization done, before the work unit is released.',
    'callback_receiver.before_flush': 'Callback receiver worker: about to bulk insert its buffered events.',
    'events.stats_before_insert': 'Stats event: existing host summaries read, before the insert and host metrics update.',
    'shutdown.before_announce': 'dispatcherd exit path: run_service returned, before announce_shutdown.',
    'adoption.unit_status': 'get_adoption_unit_status: about to query the work unit. raise here reads as an unreachable unit.',
    'health_check.redis_ping': 'Instance.local_health_check: about to ping Redis. raise --exception redis.exceptions.ConnectionError marks this node unavailable.',
}

ACTIONS = ('pause', 'sleep', 'raise', 'kill', 'kill_parent')

TABLE = 'awx_failpoint'
HIT_TABLE = 'awx_failpoint_hit'

# How long an armed-set snapshot is trusted before it is re-read. Keeps the cost of a hot
# failpoint (callback.event) to a dict lookup between refreshes.
REFRESH_SECONDS = 1.0
PAUSE_POLL_SECONDS = 0.25


class FailpointError(Exception):
    """Raised at a failpoint armed with action=raise."""


_enabled = None
_armed = {}
_armed_at = 0.0
_lock = threading.Lock()
_table_ready = False


def enabled():
    global _enabled
    if _enabled is None:
        _enabled = bool(getattr(settings, 'AWX_FAILPOINTS_ENABLED', False))
    return _enabled


def ensure_tables():
    """Create the control tables if they do not exist.

    A prototype convenience: a real version would ship a migration. Kept idempotent so any
    process, on any node, can be the first to touch them.
    """
    global _table_ready
    if _table_ready:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {TABLE} (
                name text PRIMARY KEY,
                action text NOT NULL,
                arg jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                match jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                nth integer,
                times integer,
                hits integer NOT NULL DEFAULT 0,
                fired integer NOT NULL DEFAULT 0,
                released boolean NOT NULL DEFAULT false,
                armed_at timestamptz NOT NULL DEFAULT now()
            )'''
        )
        cursor.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {HIT_TABLE} (
                id bigserial PRIMARY KEY,
                name text NOT NULL,
                node text NOT NULL,
                pid integer NOT NULL,
                ctx jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                fired boolean NOT NULL,
                action text,
                at timestamptz NOT NULL DEFAULT now()
            )'''
        )
    _table_ready = True


def _load_armed():
    global _armed, _armed_at
    now = time.monotonic()
    if now - _armed_at < REFRESH_SECONDS:
        return _armed
    with _lock:
        if now - _armed_at < REFRESH_SECONDS:
            return _armed
        try:
            ensure_tables()
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT name, match FROM {TABLE}')
                _armed = {name: _json(match) for name, match in cursor.fetchall()}
        except Exception:
            logger.exception('Could not read armed failpoints; treating none as armed')
            _armed = {}
        _armed_at = now
    return _armed


def _json(value):
    """Decode a jsonb column. Django's psycopg setup hands jsonb back as text."""
    if isinstance(value, (bytes, str)):
        return json.loads(value) if value else {}
    return value or {}


def _matches(match, ctx):
    return all(str(ctx.get(k)) == str(v) for k, v in match.items())


def _record_hit(name, ctx):
    """Count this hit against the armed row and decide whether it fires.

    Returns the row (action, arg) when it fires, None otherwise. Done in one UPDATE so
    concurrent hits on different nodes cannot both claim the Nth hit.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                UPDATE {TABLE} SET hits = hits + 1
                WHERE name = %s
                RETURNING action, arg, nth, times, hits, fired
                ''',
                [name],
            )
            row = cursor.fetchone()
            if row is None:
                return None
            action, arg, nth, times, hits, fired = row
            fire = (nth is None or hits == nth) and (times is None or fired < times)
            if fire:
                cursor.execute(f'UPDATE {TABLE} SET fired = fired + 1 WHERE name = %s', [name])
            cursor.execute(
                f'INSERT INTO {HIT_TABLE} (name, node, pid, ctx, fired, action) VALUES (%s, %s, %s, %s, %s, %s)',
                [name, ctx['node'], ctx['pid'], json.dumps(ctx, default=str), fire, action if fire else None],
            )
    return (action, _json(arg)) if fire else None


def _pause(name, arg):
    timeout = float(arg.get('timeout', 600))
    deadline = time.monotonic() + timeout
    logger.warning(f'Failpoint {name}: pausing pid={os.getpid()} until released (timeout {timeout}s)')
    while time.monotonic() < deadline:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT released FROM {TABLE} WHERE name = %s', [name])
            row = cursor.fetchone()
        if row is None or row[0]:
            logger.warning(f'Failpoint {name}: released pid={os.getpid()}')
            return
        time.sleep(PAUSE_POLL_SECONDS)
    logger.error(f'Failpoint {name}: pause timed out after {timeout}s, continuing')


def _exception_class(path):
    """Resolve a dotted exception class path; FailpointError when none is given."""
    if not path:
        return FailpointError
    module, _, cls = path.rpartition('.')
    exc = getattr(importlib.import_module(module), cls)
    if not (isinstance(exc, type) and issubclass(exc, BaseException)):
        raise TypeError(f'{path} is not an exception class')
    return exc


def failpoint(name, **ctx):
    """Mark a spot where a test may inject a fault. Inert unless enabled and armed."""
    if not enabled():
        return
    if name not in REGISTRY:
        raise KeyError(f'Unregistered failpoint {name!r}; add it to awx.main.utils.failpoints.REGISTRY')
    armed = _load_armed()
    if name not in armed:
        return
    ctx = dict(ctx, node=settings.CLUSTER_HOST_ID, pid=os.getpid())
    try:
        if not _matches(armed[name], ctx):
            return
    except Exception:
        logger.exception(f'Failpoint {name}: bad match {armed[name]!r}; not firing')
        return
    try:
        fired = _record_hit(name, ctx)
    except Exception:
        logger.exception(f'Failpoint {name}: could not record hit; not firing')
        return
    if not fired:
        return
    action, arg = fired
    logger.warning(f'Failpoint {name} fired: action={action} ctx={ctx}')
    if action == 'pause':
        _pause(name, arg)
    elif action == 'sleep':
        time.sleep(float(arg.get('seconds', 1)))
    elif action == 'raise':
        raise _exception_class(arg.get('exception'))(f'Failpoint {name} raised (ctx={ctx})')
    elif action == 'kill':
        os.kill(os.getpid(), signal.SIGKILL)
    elif action == 'kill_parent':
        os.kill(os.getppid(), signal.SIGKILL)


# --- Control API, used by the management command and by tests ---------------------------


def arm(name, action, match=None, nth=None, times=None, **arg):
    if name not in REGISTRY:
        raise KeyError(f'Unregistered failpoint {name!r}')
    if action not in ACTIONS:
        raise ValueError(f'Unknown action {action!r}; expected one of {ACTIONS}')
    if arg.get('exception'):
        _exception_class(arg['exception'])  # fail at arm time, not at the call site
    ensure_tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f'''
            INSERT INTO {TABLE} (name, action, arg, match, nth, times)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET action = EXCLUDED.action, arg = EXCLUDED.arg,
                match = EXCLUDED.match, nth = EXCLUDED.nth, times = EXCLUDED.times,
                hits = 0, fired = 0, released = false, armed_at = now()
            ''',
            [name, action, json.dumps(arg), json.dumps(match or {}), nth, times],
        )


def release(name):
    ensure_tables()
    with connection.cursor() as cursor:
        cursor.execute(f'UPDATE {TABLE} SET released = true WHERE name = %s', [name])
        return cursor.rowcount


def disarm(name=None):
    """Remove one failpoint, or all of them. Paused callers continue on their next poll."""
    ensure_tables()
    with connection.cursor() as cursor:
        if name:
            cursor.execute(f'DELETE FROM {TABLE} WHERE name = %s', [name])
        else:
            cursor.execute(f'DELETE FROM {TABLE}')
        return cursor.rowcount


def clear_hits():
    ensure_tables()
    with connection.cursor() as cursor:
        cursor.execute(f'DELETE FROM {HIT_TABLE}')


def armed_list():
    ensure_tables()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT name, action, arg, match, nth, times, hits, fired, released, armed_at FROM {TABLE} ORDER BY name')
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    for row in rows:
        row['arg'], row['match'] = _json(row['arg']), _json(row['match'])
    return rows


def hits(name=None, fired_only=False, since_id=0):
    ensure_tables()
    sql = f'SELECT id, name, node, pid, ctx, fired, action, at FROM {HIT_TABLE} WHERE id > %s'
    params = [since_id]
    if name:
        sql += ' AND name = %s'
        params.append(name)
    if fired_only:
        sql += ' AND fired'
    sql += ' ORDER BY id'
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    for row in rows:
        row['ctx'] = _json(row['ctx'])
    return rows


def wait_for_hit(name, fired_only=True, timeout=300, poll=0.5):
    """Block until the named failpoint has a (fired) hit. Returns the first one, or None."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = hits(name, fired_only=fired_only)
        if found:
            return found[0]
        time.sleep(poll)
    return None
