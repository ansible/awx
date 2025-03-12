import logging
from typing import Tuple, Union

import yaml

import jq

from django.utils.timezone import now, timedelta
from django.conf import settings
from django.db import transaction

# Django flags
from flags.state import flag_enabled

from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models.event_query import EventQuery
from awx.main.models import Job

logger = logging.getLogger(__name__)


class UnhashableFacts(RuntimeError):
    pass


def get_hashable_form(input_data: Union[dict, list, Tuple, int, float, str, bool]) -> Tuple[Union[Tuple, int, float, str, bool]]:
    "Given a dictionary of JSON types, return something that can be hashed and is the same data"
    if isinstance(input_data, (int, float, str, bool)):
        return input_data  # return scalars as-is
    if isinstance(input_data, dict):
        # Can't hash because we got a dict? Make the dict a tuple of tuples.
        # Can't hash the data in the tuple in the tuple? We'll make tuples out of them too.
        return tuple(sorted(((get_hashable_form(k), get_hashable_form(v)) for k, v in input_data.items())))
    elif isinstance(input_data, (list, tuple)):
        # Nested list data might not be hashable, and lists were never hashable in the first place
        return tuple(get_hashable_form(item) for item in input_data)
    raise UnhashableFacts(f'Cannonical facts contains a {type(input_data)} type which can not be hashed.')


def build_indirect_host_data(job: Job, job_event_queries: dict[str, dict[str, str]]) -> list[IndirectManagedNodeAudit]:
    results = {}
    compiled_jq_expressions = {}  # Cache for compiled jq expressions
    facts_missing_logged = False
    unhashable_facts_logged = False

    for event in job.job_events.filter(event_data__isnull=False).iterator():
        if 'res' not in event.event_data:
            continue

        if 'resolved_action' not in event.event_data or event.event_data['resolved_action'] not in job_event_queries.keys():
            continue

        resolved_action = event.event_data['resolved_action']

        # We expect a dict with a 'query' key for the resolved_action
        if 'query' not in job_event_queries[resolved_action]:
            continue

        # Recall from cache, or process the jq expression, and loop over the jq results
        jq_str_for_event = job_event_queries[resolved_action]['query']

        if jq_str_for_event not in compiled_jq_expressions:
            compiled_jq_expressions[resolved_action] = jq.compile(jq_str_for_event)
        compiled_jq = compiled_jq_expressions[resolved_action]
        for data in compiled_jq.input(event.event_data['res']).all():
            # From this jq result (specific to a single Ansible module), get index information about this host record
            if not data.get('canonical_facts'):
                if not facts_missing_logged:
                    logger.error(f'jq output missing canonical_facts for module {resolved_action} on event {event.id} using jq:{jq_str_for_event}')
                    facts_missing_logged = True
                continue
            canonical_facts = data['canonical_facts']
            try:
                hashable_facts = get_hashable_form(canonical_facts)
            except UnhashableFacts:
                if not unhashable_facts_logged:
                    logger.info(f'Could not hash canonical_facts {canonical_facts}, skipping')
                    unhashable_facts_logged = True
                continue

            # Obtain the record based on the hashable canonical_facts now determined
            facts = data.get('facts')
            name = data.get('name')

            if hashable_facts in results:
                audit_record = results[hashable_facts]
            else:
                audit_record = IndirectManagedNodeAudit(
                    canonical_facts=canonical_facts,
                    facts=facts,
                    job=job,
                    organization=job.organization,
                    name=name,
                )
                results[hashable_facts] = audit_record

            # Increment rolling count fields
            if resolved_action not in audit_record.events:
                audit_record.events.append(resolved_action)
            audit_record.count += 1

    return list(results.values())


def fetch_job_event_query(job: Job) -> dict[str, dict[str, str]]:
    """Returns the following data structure
    {
        "demo.query.example": {"query": {canonical_facts: {host_name: .direct_host_name}}}
    }
    The keys are fully-qualified Ansible module names, and the values are dicts containing jq expressions.

    This contains all event query expressions that pertain to the given job
    """
    net_job_data = {}
    for fqcn, collection_data in job.installed_collections.items():
        event_query = EventQuery.objects.filter(fqcn=fqcn, collection_version=collection_data['version']).first()
        if event_query:
            collection_data = yaml.safe_load(event_query.event_query)
            net_job_data.update(collection_data)
    return net_job_data


def save_indirect_host_entries_of_job(job: Job) -> None:
    "Once we have a job and we know that we want to do indirect host processing, this is called"
    job_event_queries = fetch_job_event_query(job)
    records = build_indirect_host_data(job, job_event_queries)
    IndirectManagedNodeAudit.objects.bulk_create(records)
    job.event_queries_processed = True


def cleanup_old_indirect_host_entries() -> None:
    """
    We assume that indirect host audit results older than one week have already been collected for analysis
    and can be cleaned up
    """
    limit = now() - timedelta(days=settings.INDIRECT_HOST_AUDIT_RECORD_MAX_AGE_DAYS)
    IndirectManagedNodeAudit.objects.filter(created__lt=limit).delete()


@task(queue=get_task_queuename)
def save_indirect_host_entries(job_id: int, wait_for_events: bool = True) -> None:
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.debug(f'Job {job_id} seems to be deleted, bailing from save_indirect_host_entries')
        return

    if wait_for_events:
        # Gate running this task on the job having all events processed, not just EOF or playbook_on_stats
        current_events = job.job_events.count()
        if current_events < job.emitted_events:
            logger.info(f'Event count {current_events} < {job.emitted_events} for job_id={job_id}, delaying processing of indirect host tracking')
            return
        job.log_lifecycle(f'finished processing {current_events} events, running save_indirect_host_entries')

    with transaction.atomic():
        """
        Pre-emptively set the job marker to 'events processed'. This prevents other instances from running the
        same task.
        """
        try:
            job = Job.objects.select_for_update().get(id=job_id)
        except job.DoesNotExist:
            logger.debug(f'Job {job_id} seems to be deleted, bailing from save_indirect_host_entries')
            return

        if job.event_queries_processed is True:
            # this can mean one of two things:
            # 1. another instance has already processed the events of this job
            # 2. the artifacts_handler has not yet been called for this job
            return

        job.event_queries_processed = True
        job.save(update_fields=['event_queries_processed'])

    try:
        save_indirect_host_entries_of_job(job)
    except Exception:
        logger.exception(f'Error processing indirect host data for job_id={job_id}')


@task(queue=get_task_queuename)
def cleanup_and_save_indirect_host_entries_fallback() -> None:
    if not flag_enabled("FEATURE_INDIRECT_NODE_COUNTING_ENABLED"):
        return

    try:
        cleanup_old_indirect_host_entries()
    except Exception as e:
        logger.error(f"error cleaning up indirect host audit records: {e}")

    job_ct = 0
    right_now_time = now()
    window_end = right_now_time - timedelta(minutes=settings.INDIRECT_HOST_QUERY_FALLBACK_MINUTES)
    window_start = right_now_time - timedelta(days=settings.INDIRECT_HOST_QUERY_FALLBACK_GIVEUP_DAYS)
    for job in Job.objects.filter(event_queries_processed=False, finished__lte=window_end, finished__gte=window_start).iterator():
        save_indirect_host_entries(job.id, wait_for_events=True)
        job_ct += 1
    if job_ct:
        logger.info(f'Restarted event processing for {job_ct} jobs')
