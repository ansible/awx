from types import SimpleNamespace
import logging

import jq

logger = logging.getLogger(__name__)


def build_indirect_host_data(job, event_query: dict):
    results = []
    compiled_jq_expressions = {}  # Cache for compiled jq expressions
    facts_missing_logged = False
    for event in job.job_events.filter(task__in=event_query.keys()):
        if 'res' not in event.event_data:
            continue
        jq_str_for_event = event_query[event.task]
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
            results.append(SimpleNamespace(canonical_facts=canonical_facts, facts=facts))
    return results
