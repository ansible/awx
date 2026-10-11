"""Invariants a finished job should satisfy, for failure-scenario tests.

Each check returns a dict with ``name``, ``ok`` and ``detail``. They read only the database,
so they can run from any node after a scenario, and they deliberately do not assume the
job went through adoption: the same checks apply to a job that never failed over, which is
the baseline a scenario is compared against.
"""

from django.db import connection
from django.db.models import Max, OuterRef, Subquery

from awx.main.constants import ACTIVE_STATES
from awx.main.models import Host, HostMetric, JobHostSummary, UnifiedJob
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
    elif job.inventory_id:
        # Constructed inventory: the job-start map holds the constructed hosts' ids. A summary
        # carries that id as constructed_host_id, and the original (input inventory) host's id,
        # the constructed host's instance_id, as host_id.
        constructed = {h.pk: _host_id(h.instance_id) for h in Host.objects.filter(pk__in=[i for i in expected.values() if i is not None])}
        originals = set(Host.objects.filter(pk__in=[i for i in constructed.values() if i is not None]).values_list('pk', flat=True))
        for name, host_id, constructed_id in job.job_host_summaries.values_list('host_name', 'host_id', 'constructed_host_id'):
            if name not in expected:
                continue
            want_constructed = expected[name] if expected[name] in constructed else None
            original = constructed.get(expected[name])
            want_host = original if original in originals else None
            if constructed_id != want_constructed:
                bad_summaries.append(f'{name} constructed_host_id {constructed_id} != {want_constructed}')
            if host_id != want_host:
                bad_summaries.append(f'{name} host_id {host_id} != {want_host}')
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


def check_host_metrics_counted_once(job):
    """Each host the job automated should add exactly one to its HostMetric.automated_counter.

    A normal run counts a host once, when its playbook_on_stats is processed, and skips dark
    (unreachable) hosts. Processing the same stats twice (two controllers streaming one job, or
    a replay after adoption) must not count it again. Compares the counter now with a copy
    taken at job start (failpoints.record_snapshot('host_metrics', job.id, ...), hostname ->
    automated_counter, None for no row), so it is only exact while no other job has
    automated the same hosts since; run it right after the job ends.
    """
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'host_metrics_counted_once', 'ok': True, 'detail': 'not applicable'}
    snapshot = get_snapshot('host_metrics', job.id)
    if snapshot is None:
        return {'name': 'host_metrics_counted_once', 'ok': True, 'detail': 'no job-start host_metrics snapshot; not checked'}
    counted = {name.lower() for name, dark in job.job_host_summaries.values_list('host_name', 'dark') if not dark}
    now = dict(HostMetric.objects.filter(hostname__in=list(snapshot)).values_list('hostname', 'automated_counter'))
    wrong = []
    for name, before in sorted(snapshot.items()):
        delta = (now.get(name) or 0) - (before or 0)
        want = 1 if name in counted else 0
        if delta != want:
            wrong.append(f'{name} +{delta} (want +{want})')
    return {
        'name': 'host_metrics_counted_once',
        'ok': not wrong,
        'detail': '; '.join(wrong[:10]) if wrong else f'{len(snapshot)} hosts in the snapshot, {len(counted)} counted once each',
    }


def check_host_pointers(job):
    """Host and inventory fields derived from this job's summaries should be consistent.

    A host's last_job, last_job_host_summary and has_active_failures come from its newest
    JobHostSummary. For every host in this job's summaries, unless a later job has summarized
    it since: the newest summary is this job's, there is one per host, and its failed flag
    matches its own counts. The summary counts must equal the stored playbook_on_stats. The
    inventory's stored computed fields (total_hosts, hosts_with_active_failures,
    has_active_failures) must equal what update_computed_fields would compute now.

    A job with no playbook_on_stats has no summaries, so its hosts keep pointing at earlier
    jobs. That is reported, not failed (playbook_events_complete fails such a job).
    """
    if not hasattr(job, 'job_host_summaries'):
        return {'name': 'host_pointers', 'ok': True, 'detail': 'not applicable'}
    problems = []
    notes = []
    summaries = list(job.job_host_summaries.all())
    stats = job.get_event_queryset().filter(event='playbook_on_stats').order_by('counter').first()
    if stats is None:
        notes.append(f'no playbook_on_stats; {len(summaries)} summaries')
    else:
        data = stats.event_data or {}
        for s in summaries:
            for field in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped', 'rescued', 'ignored'):
                want = (data.get(field) or {}).get(s.host_name, 0)
                if getattr(s, field) != want:
                    problems.append(f'{s.host_name} {field}={getattr(s, field)} != stats {want}')
            if s.failed != bool(s.dark or s.failures):
                problems.append(f'{s.host_name} failed={s.failed} with dark={s.dark} failures={s.failures}')
        named = set()
        for field in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
            named.update((data.get(field) or {}).keys())
        missing = sorted(named - {s.host_name for s in summaries})
        if missing:
            problems.append(f'no summary for {", ".join(missing[:10])}')
    superseded = []
    for s in summaries:
        if s.host_id is None:
            continue
        newest = JobHostSummary.objects.filter(host_id=s.host_id).order_by('-id').first()
        if newest.id == s.id:
            continue
        if newest.job_id != job.id and newest.id > s.id:
            superseded.append(s.host_name)
        else:
            problems.append(f'{s.host_name} newest summary {newest.id} (job {newest.job_id}) is not this job\'s {s.id}')
    if superseded:
        notes.append(f'superseded by later jobs: {", ".join(sorted(superseded)[:10])}')
    inv = job.inventory
    if inv is not None:
        latest_failed = JobHostSummary.objects.filter(host_id=OuterRef('pk')).order_by('-id').values('failed')[:1]
        failed_hosts = inv.hosts.annotate(_latest_failed=Subquery(latest_failed)).filter(_latest_failed=True).count()
        want = {'total_hosts': inv.hosts.count(), 'hosts_with_active_failures': failed_hosts, 'has_active_failures': bool(failed_hosts)}
        for field, value in want.items():
            if getattr(inv, field) != value:
                problems.append(f'inventory {field}={getattr(inv, field)} != computed {value}')
        notes.append(f'inventory total_hosts={inv.total_hosts} hosts_with_active_failures={inv.hosts_with_active_failures}')
    detail = '; '.join(problems[:10]) if problems else f'{len(summaries)} summaries consistent'
    if notes:
        detail += ' (' + '; '.join(notes) + ')'
    return {'name': 'host_pointers', 'ok': not problems, 'detail': detail}


def check_stdout_lines_contiguous(job):
    """Events' stdout line ranges should tile the output: each event's start_line is the
    previous event's end_line, from line 0, with no gap and no overlap.

    The job's stdout is the events' stdout ordered by start_line, so a gap is output lost from
    the middle and an overlap (a range stored twice, e.g. by two streams of one job) is output
    printed twice. Events with no stdout (start_line == end_line) cannot overlap anything.
    """
    rows = list(job.get_event_queryset().order_by('start_line', 'end_line', 'counter').values_list('start_line', 'end_line', 'counter'))
    if not rows:
        return {'name': 'stdout_lines_contiguous', 'ok': True, 'detail': 'no events'}
    expected = 0
    gaps, overlaps = [], []
    for start, end, counter in rows:
        if start > expected:
            gaps.append(f'lines {expected}-{start} before counter {counter}')
        elif start < expected and end > start:
            overlaps.append(f'counter {counter} lines {start}-{end}')
        expected = max(expected, end)
    problems = []
    if gaps:
        problems.append(f'{len(gaps)} gaps ({"; ".join(gaps[:5])})')
    if overlaps:
        problems.append(f'{len(overlaps)} overlapping events ({"; ".join(overlaps[:5])})')
    return {
        'name': 'stdout_lines_contiguous',
        'ok': not problems,
        'detail': ' | '.join(problems) if problems else f'{len(rows)} events tile lines 0-{expected}',
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
    check_host_metrics_counted_once,
    check_host_pointers,
    check_stdout_lines_contiguous,
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
