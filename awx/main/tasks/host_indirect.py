import logging

import yaml

import jq

from awx.main.dispatch.publish import task
from awx.main.dispatch import get_task_queuename
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models.event_query import EventQuery
from awx.main.models import Job

logger = logging.getLogger(__name__)


def build_indirect_host_data(job, job_event_queries: dict[str, str]) -> list[IndirectManagedNodeAudit]:
    results = []
    compiled_jq_expressions = {}  # Cache for compiled jq expressions
    facts_missing_logged = False
    for event in job.job_events.filter(task__in=job_event_queries.keys()).iterator():
        if 'res' not in event.event_data:
            continue
        jq_str_for_event = job_event_queries[event.task]
        if jq_str_for_event not in compiled_jq_expressions:
            compiled_jq_expressions[event.task] = jq.compile(jq_str_for_event)
        compiled_jq = compiled_jq_expressions[event.task]
        for data in compiled_jq.input(event.event_data['res']).all():
            if not data.get('canonical_facts'):
                if not facts_missing_logged:
                    logger.error(f'jq output missing canonical_facts for module {event.task} on event {event.id} using jq:{jq_str_for_event}')
                continue
            canonical_facts = data['canonical_facts']
            facts = data.get('facts')
            results.append(IndirectManagedNodeAudit(canonical_facts=canonical_facts, facts=facts, job=job, organization=job.organization))
    return results


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
