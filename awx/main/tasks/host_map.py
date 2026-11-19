"""The hostname -> host id map that event_handler stamps host_id on events from.

A normal run builds it from the inventory script it writes. Adoption writes no inventory file, so
read_host_map reads the inventory as it is when the job is adopted.
"""

import logging

logger = logging.getLogger('awx.main.tasks.host_map')


def carries_host_ids(instance):
    """Only Job and AdHocCommand events carry host_id."""
    from awx.main.models import AdHocCommand, Job  # Circular import

    return isinstance(instance, (Job, AdHocCommand))


def script_params(job):
    """Arguments for Inventory.get_script_data, matching what build_inventory writes."""
    params = {"hostvars": True, "towervars": True}
    if hasattr(job, 'job_slice_number'):
        params['slice_number'] = job.job_slice_number
        params['slice_count'] = job.job_slice_count
    return params


def host_map_from(script_data):
    """Map hostname -> remote_tower_id so event_handler can stamp host_id on events."""
    return {hostname: hv.get('remote_tower_id', '') for hostname, hv in script_data.get('_meta', {}).get('hostvars', {}).items()}


def read_host_map(job):
    """The host map for an adopted job's replayed events, read from its inventory as it is now.

    Hosts edited, added or removed since the job started are not accounted for: a host that was
    renamed or removed gets no host_id, and one whose id was swapped gets the other host's. The
    map is empty if the job has no inventory or it cannot be read. DB errors there are logged,
    not raised, so the events are still replayed.
    """
    if not carries_host_ids(job) or not job.inventory_id:
        return {}
    try:
        return host_map_from(job.inventory.get_script_data(**script_params(job)))
    except Exception:
        logger.warning('Could not populate host map for job %s; host_id will be unset on replayed events', job.id, exc_info=True)
        return {}
