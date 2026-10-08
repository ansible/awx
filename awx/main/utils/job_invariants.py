"""Invariants a finished job should satisfy, for failure-scenario tests.

Each check returns a dict with ``name``, ``ok`` and ``detail``. They read only the database,
so they can run from any node after a scenario, and they deliberately do not assume the
job went through adoption: the same checks apply to a job that never failed over, which is
the baseline a scenario is compared against.
"""

from django.db import connection

from awx.main.constants import ACTIVE_STATES
from awx.main.models import UnifiedJob


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


CHECKS = (
    check_terminal,
    check_no_duplicate_counters,
    check_no_counter_gaps,
    check_event_count_matches,
    check_single_notification_per_status,
    check_cancel_respected,
    check_status_matches_playbook,
    check_host_summaries_unique,
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
