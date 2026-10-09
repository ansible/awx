"""Invariants a finished job should satisfy, for failure-scenario tests.

Each check returns a dict with ``name``, ``ok`` and ``detail``. They read only the database,
so they can run from any node after a scenario, and they deliberately do not assume the
job went through adoption: the same checks apply to a job that never failed over, which is
the baseline a scenario is compared against.
"""

from django.db import connection
from django.db.models import Max

from awx.main.constants import ACTIVE_STATES
from awx.main.models import Host, UnifiedJob
from awx.main.utils.failpoints import get_snapshot


def _event_table(job):
    return job.get_event_queryset().model._meta.db_table


def _job_fk(job):
    return job.get_event_queryset().model.JOB_REFERENCE


def check_terminal(job):
    ok = job.status not in ACTIVE_STATES
    return {'name': 'terminal_status', 'ok': ok, 'detail': f'status={job.status}'}


def check_no_duplicate_counters(job):
    with connection.cursor() as cursor:
        cursor.execute(
            f'SELECT counter, count(*) FROM {_event_table(job)} WHERE {_job_fk(job)} = %s AND job_created = %s '
            f'GROUP BY counter HAVING count(*) > 1 ORDER BY counter',
            [job.id, job.created],
        )
        dups = cursor.fetchall()
    extra = sum(c - 1 for _, c in dups)
    sample = ', '.join(str(c) for c, _ in dups[:10])
    return {
        'name': 'no_duplicate_events',
        'ok': not dups,
        'detail': f'{len(dups)} counters duplicated, {extra} extra rows' + (f' (e.g. {sample})' if dups else ''),
    }


def check_no_counter_gaps(job):
    with connection.cursor() as cursor:
        cursor.execute(
            f'SELECT count(DISTINCT counter), coalesce(max(counter), 0) FROM {_event_table(job)} WHERE {_job_fk(job)} = %s AND job_created = %s',
            [job.id, job.created],
        )
        distinct, max_counter = cursor.fetchone()
    missing = max_counter - distinct
    return {'name': 'no_missing_events', 'ok': missing == 0, 'detail': f'{distinct} distinct counters, highest {max_counter}, {missing} missing'}


def check_event_count_matches(job):
    stored = job.get_event_queryset().count()
    ok = job.emitted_events == stored
    return {
        'name': 'emitted_matches_stored',
        'ok': ok,
        'detail': f'emitted_events={job.emitted_events} stored={stored} event_processing_finished={job.event_processing_finished}',
    }


def check_single_notification_per_status(job):
    """Each notification template should fire at most once per final status."""
    rows = list(job.notifications.values_list('notification_template_id', 'subject'))
    seen = {}
    for nt, subject in rows:
        seen[(nt, subject)] = seen.get((nt, subject), 0) + 1
    dup = {k: v for k, v in seen.items() if v > 1}
    return {
        'name': 'single_notification',
        'ok': not dup,
        'detail': f'{len(rows)} notifications' + (f', duplicated: {len(dup)} template/subject pairs' if dup else ''),
    }


def check_cancel_respected(job):
    if not job.cancel_flag:
        return {'name': 'cancel_respected', 'ok': True, 'detail': 'not canceled'}
    ok = job.status == 'canceled'
    return {'name': 'cancel_respected', 'ok': ok, 'detail': f'cancel_flag set, status={job.status}'}


def check_status_matches_playbook(job):
    """A job whose own playbook_on_stats reports no failed or unreachable host should be
    successful. Catches a status overwritten by a controller that lost a race, which the
    other checks cannot see because the event stream itself is complete."""
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'status_matches_playbook', 'ok': True, 'detail': 'not applicable'}
    stats = job.get_event_queryset().filter(event='playbook_on_stats').order_by('counter').first()
    if stats is None:
        return {'name': 'status_matches_playbook', 'ok': True, 'detail': 'no playbook_on_stats event'}
    data = stats.event_data or {}
    bad = sorted(set(data.get('failures') or {}) | set(data.get('dark') or {}))
    expected = 'failed' if bad else 'successful'
    ok = job.status == expected or job.cancel_flag
    return {
        'name': 'status_matches_playbook',
        'ok': ok,
        'detail': f'playbook_on_stats says {expected} (failed/dark hosts: {bad or "none"}), status={job.status}',
    }


def check_host_summaries_unique(job):
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'host_summaries', 'ok': True, 'detail': 'not applicable'}
    total = job.job_host_summaries.count()
    distinct = job.job_host_summaries.values('host_name').distinct().count()
    return {'name': 'host_summaries', 'ok': total == distinct, 'detail': f'{total} summaries for {distinct} hosts'}


def _host_id(value):
    """host_map values are remote_tower_id from the inventory script: an int, or '' when unset."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def check_host_ids_match_job_start(job):
    """Every event and host summary should carry the host ids the job started with.

    A normal run builds its hostname-to-id map once, when it writes the inventory, and
    records a copy (failpoints.record_snapshot). Adoption rebuilds the map from the live
    inventory, so an inventory change during the orphan window re-points replayed events and
    summaries. Expected, per host in the job-start map:

    - events: exactly the job-start id;
    - summaries: the job-start id if that host still exists, else None (a normal run nulls
      ids of hosts deleted before the stats event, and the foreign key nulls them after).

    Without a snapshot (failpoints were off at job start) it falls back to consistency: one
    host id per host name across all events.
    """
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'host_ids_match_job_start', 'ok': True, 'detail': 'not applicable'}
    pairs = job.get_event_queryset().exclude(host_name='').values_list('host_name', 'host_id').distinct()
    seen = {}
    for name, host_id in pairs:
        seen.setdefault(name, set()).add(host_id)

    snapshot = get_snapshot('host_map', job.id)
    if snapshot is None:
        mixed = sorted(name for name, ids in seen.items() if len(ids) > 1)
        return {
            'name': 'host_ids_match_job_start',
            'ok': not mixed,
            'detail': 'no job-start snapshot, checked consistency only: '
            + (f'{len(mixed)} hosts with more than one host id across events: {", ".join(mixed[:10])}' if mixed else f'{len(seen)} hosts consistent'),
        }

    expected = {name: _host_id(value) for name, value in snapshot.items()}
    bad_events = sorted(f'{name} {sorted(ids, key=str)} != {expected[name]}' for name, ids in seen.items() if name in expected and ids != {expected[name]})

    bad_summaries = []
    if job.inventory_id and job.inventory.kind != 'constructed':
        existing = set(Host.objects.filter(pk__in=[i for i in expected.values() if i is not None]).values_list('pk', flat=True))
        for name, host_id in job.job_host_summaries.values_list('host_name', 'host_id'):
            if name not in expected:
                continue
            want = expected[name] if expected[name] in existing else None
            if host_id != want:
                bad_summaries.append(f'{name} {host_id} != {want}')
    bad_summaries.sort()

    problems = []
    if bad_events:
        problems.append(f'events: {"; ".join(bad_events[:10])}')
    if bad_summaries:
        problems.append(f'summaries: {"; ".join(bad_summaries[:10])}')
    return {
        'name': 'host_ids_match_job_start',
        'ok': not problems,
        'detail': ' | '.join(problems) if problems else f'{len(expected)} hosts in the job-start map, events and summaries match',
    }


def check_playbook_events_complete(job):
    """Every event up to the playbook's final event should be stored.

    ``playbook_on_stats`` is the playbook's last event, so its counter is the number of
    events the playbook emitted up to that point. Catches a job that finished with its
    output cut short, which the gap check cannot see when nothing after the cut was stored
    (no gap, just a low maximum), and which emitted_events cannot see when it only counts
    what was replayed.

    A job canceled or in error may legitimately stop before its final event; for those the
    check only reports. A successful or failed job with no final event fails.
    """
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'playbook_events_complete', 'ok': True, 'detail': 'not applicable'}
    events = job.get_event_queryset()
    stats = events.filter(event='playbook_on_stats').order_by('counter').first()
    distinct = events.order_by().values('counter').distinct().count()
    max_counter = events.aggregate(m=Max('counter'))['m'] or 0
    may_stop_early = job.status in ('canceled', 'error') or job.cancel_flag
    if stats is None:
        return {
            'name': 'playbook_events_complete',
            'ok': may_stop_early,
            'detail': f'no playbook_on_stats event; {distinct} events stored, highest counter {max_counter}, status={job.status}',
        }
    final = stats.counter
    upto_final = events.filter(counter__lte=final).order_by().values('counter').distinct().count()
    missing = final - upto_final
    return {
        'name': 'playbook_events_complete',
        'ok': missing == 0,
        'detail': f'playbook final event at counter {final}; {upto_final} of {final} stored, {missing} missing',
    }


CHECKS = (
    check_terminal,
    check_no_duplicate_counters,
    check_no_counter_gaps,
    check_event_count_matches,
    check_single_notification_per_status,
    check_cancel_respected,
    check_status_matches_playbook,
    check_host_summaries_unique,
    check_host_ids_match_job_start,
    check_playbook_events_complete,
)


def check_job(job_id):
    job = UnifiedJob.objects.get(pk=job_id).get_real_instance()
    results = [check(job) for check in CHECKS]
    return {
        'job_id': job.id,
        'status': job.status,
        'controller_node': job.controller_node,
        'execution_node': job.execution_node,
        'job_explanation': job.job_explanation,
        'ok': all(r['ok'] for r in results),
        'checks': results,
    }
