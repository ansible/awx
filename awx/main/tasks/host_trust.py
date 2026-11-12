"""Whether an adopted job's host ids can still be taken from its inventory, and what adoption does if not.

A normal run counts the inventory's hosts at start (count_hosts) and status_handler saves the count in
job_env. Adoption compares the inventory against that count and the job's start time (assess).
"""

import dataclasses
import logging
from typing import Optional

logger = logging.getLogger('awx.main.tasks.host_trust')

PROCEED = 'proceed'  # trusted, or canceled: the job ends the usual way
FAIL_WHEN_DONE = 'fail_when_done'  # let the job's run finish, then fail the job


@dataclasses.dataclass(frozen=True)
class Verdict:
    reason: Optional[str]  # why the host ids cannot be trusted; None when they can
    host_map: dict  # hostname -> host id; empty unless trusted and read
    action: str


def carries_host_ids(instance):
    """Only Job and AdHocCommand events carry host_id, so only they need the inventory to be unchanged."""
    from awx.main.models import AdHocCommand, Job  # Circular import

    return isinstance(instance, (Job, AdHocCommand))


def count_hosts(job):
    """The inventory's host count for status_handler to save, or None if the job needs none. Call it
    before the inventory is read: a host deleted in between then makes the count differ at adoption."""
    if carries_host_ids(job) and job.inventory_id:
        return job.inventory.hosts.count()
    return None


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


def change_since_start(job):
    """Why this job's host ids can no longer be taken from its inventory, or None if it is unchanged.

    Any of these counts: no host count was saved at job start, the inventory is gone, a host was
    added or removed (the count), a host was created or edited after the job started, or an
    inventory update was created after it. The update check is what sees a sync's renames and
    enabled toggles: the importer saves them with update_fields, which never moves Host.modified.
    """
    from awx.main.models import InventoryUpdate  # Circular import

    saved = (job.job_env or {}).get('host_count')
    inventory = job.inventory
    if inventory is None:
        # A job that never had an inventory has no hosts to attribute. One that had one is
        # known by its saved count, and its inventory has been deleted since.
        return None if saved is None else 'the inventory was deleted'
    if saved is None:
        return 'no host count was saved when the job started'
    if job.started is None:
        return 'the job has no start time'
    if inventory.hosts.count() != saved:
        return 'hosts were added or removed'
    if inventory.hosts.filter(modified__gt=job.started).exists():
        return 'a host was added or edited'
    # A smart inventory has no sources: its hosts are every matching host of its organization.
    updates = InventoryUpdate.objects.filter(created__gt=job.started)
    if inventory.kind == 'smart':
        updates = updates.filter(inventory_source__inventory__organization_id=inventory.organization_id)
    else:
        updates = updates.filter(inventory_source__inventory=inventory)
    if updates.exists():
        return 'the inventory was updated'
    return None


def assess(job, read_map=True):
    """Check the job's inventory against its start and say what adoption does with the job.

    The map is read only when read_map is set and the inventory is unchanged, then the check
    runs again, so a change made during the read counts. A map that cannot be read counts as a
    change. DB errors in the check itself propagate: the next adoption sweep retries.
    """
    if not carries_host_ids(job):
        return Verdict(None, {}, PROCEED)
    reason = change_since_start(job)
    host_map = {}
    if reason is None and read_map and job.inventory_id:
        try:
            host_map = host_map_from(job.inventory.get_script_data(**script_params(job)))
        except Exception:
            logger.warning('Could not populate host map for job %s; host_id will be unset on replayed events', job.id, exc_info=True)
            reason = 'the host map could not be read'
        else:
            reason = change_since_start(job)
    # The run is never stopped for a change: the playbook finishes on its hosts, and only the
    # job's recorded result is failed.
    action = PROCEED if reason is None or job.cancel_flag else FAIL_WHEN_DONE
    return Verdict(reason, {} if reason else host_map, action)
