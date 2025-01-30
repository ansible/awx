import logging
from typing import Tuple, Union

import yaml

import jq

from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models.event_query import EventQuery
from awx.main.models import Job

logger = logging.getLogger(__name__)


class UnhashableFacts(RuntimeError):
    pass


def get_hashable_form(input_data: Union[dict, list, int, float, str, bool]) -> Tuple[Union[Tuple, dict, int, float]]:
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


def build_indirect_host_data(job, job_event_queries: dict[str, str]) -> list[IndirectManagedNodeAudit]:
    results = {}
    compiled_jq_expressions = {}  # Cache for compiled jq expressions
    facts_missing_logged = False
    unhashable_facts_logged = False
    for event in job.job_events.filter(task__in=job_event_queries.keys()).iterator():
        if 'res' not in event.event_data:
            continue

        # Recall from cache, or process the jq expression, and loop over the jq results
        jq_str_for_event = job_event_queries[event.task]
        if jq_str_for_event not in compiled_jq_expressions:
            compiled_jq_expressions[event.task] = jq.compile(jq_str_for_event)
        compiled_jq = compiled_jq_expressions[event.task]
        for data in compiled_jq.input(event.event_data['res']).all():

            # From this jq result (specific to a single Ansible module), get index information about this host record
            if not data.get('canonical_facts'):
                if not facts_missing_logged:
                    logger.error(f'jq output missing canonical_facts for module {event.task} on event {event.id} using jq:{jq_str_for_event}')
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
            if hashable_facts in results:
                audit_record = results[hashable_facts]
            else:
                audit_record = IndirectManagedNodeAudit(
                    canonical_facts=canonical_facts,
                    facts=facts,
                    job=job,
                    organization=job.organization,
                    name=event.host_name,
                )
                results[hashable_facts] = audit_record

            # Increment rolling count fields
            if event.task not in audit_record.events:
                audit_record.events.append(event.task)
            audit_record.count += 1

    return list(results.values())


def fetch_job_event_query(job) -> dict[str, str]:
    """Returns the following data structure
    {
        "demo.query.example": "{canonical_facts: {host_name: .direct_host_name}}"
    }
    The keys are fully-qualified Ansible module names, and the values are strings which are jq expressions.

    This contains all event query expressions that pertain to the given job
    """
    net_job_data = {}
    for fqcn, collection_data in job.installed_collections.items():
        event_query = EventQuery.objects.filter(fqcn=fqcn, collection_version=collection_data['version']).first()
        if event_query:
            collection_data = yaml.safe_load(event_query.event_query)
            net_job_data.update(collection_data)
    return net_job_data


@task(queue=get_task_queuename)
def save_indirect_host_entries(job_id):
    job = Job.objects.get(id=job_id)
    job_event_queries = fetch_job_event_query(job)
    records = build_indirect_host_data(job, job_event_queries)
    IndirectManagedNodeAudit.objects.bulk_create(records)
    job.event_queries_processed = True
    job.save(update_fields=['event_queries_processed'])
