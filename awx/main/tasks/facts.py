import codecs
import datetime
import os
import json
import logging

# Django
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
from django.utils.timezone import now

# AWX
from awx.main.utils.common import log_excess_runtime


logger = logging.getLogger('awx.main.tasks.facts')
system_tracking_logger = logging.getLogger('awx.analytics.system_tracking')


def _get_inventory_hosts(inventory, slice_number, slice_count, only=('name', 'ansible_facts', 'ansible_facts_modified', 'modified', 'inventory_id'), **filters):
    """Return value is an iterable for the relevant hosts for this job"""
    if not inventory:
        return []
    host_queryset = inventory.hosts.only(*only)
    if filters:
        host_queryset = host_queryset.filter(**filters)
    host_queryset = inventory.get_sliced_hosts(host_queryset, slice_number, slice_count)
    if isinstance(host_queryset, QuerySet):
        return host_queryset.iterator()
    return host_queryset


@log_excess_runtime(logger, debug_cutoff=0.01, msg='Inventory {inventory_id} host facts prepared for {written_ct} hosts, took {delta:.3f} s', add_log_data=True)
def start_fact_cache(inventory, destination, log_data, timeout=None, slice_number=0, slice_count=1):
    log_data['inventory_id'] = inventory.id
    log_data['written_ct'] = 0
    try:
        os.makedirs(destination, mode=0o700)
    except FileExistsError:
        pass

    if timeout is None:
        timeout = settings.ANSIBLE_FACT_CACHE_TIMEOUT
    if timeout > 0:
        # exclude hosts with fact data older than `settings.ANSIBLE_FACT_CACHE_TIMEOUT seconds`
        timeout = now() - datetime.timedelta(seconds=timeout)
        hosts = _get_inventory_hosts(inventory, slice_number, slice_count, ansible_facts_modified__gte=timeout)
    else:
        hosts = _get_inventory_hosts(inventory, slice_number, slice_count)

    last_filepath_written = None
    for host in hosts:
        filepath = os.sep.join(map(str, [destination, host.name]))
        if not os.path.realpath(filepath).startswith(destination):
            system_tracking_logger.error('facts for host {} could not be cached'.format(smart_str(host.name)))
            continue
        try:
            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                os.chmod(f.name, 0o600)
                json.dump(host.ansible_facts, f)
                log_data['written_ct'] += 1
                last_filepath_written = filepath
        except IOError:
            system_tracking_logger.error('facts for host {} could not be cached'.format(smart_str(host.name)))
            continue
    # make note of the time we wrote the last file so we can check if any file changed later
    if last_filepath_written:
        return os.path.getmtime(last_filepath_written)
    return None


@log_excess_runtime(
    logger,
    debug_cutoff=0.01,
    msg='Inventory {inventory_id} host facts: updated {updated_ct}, cleared {cleared_ct}, unchanged {unmodified_ct}, took {delta:.3f} s',
    add_log_data=True,
)
def finish_fact_cache(inventory, destination, facts_write_time, log_data, slice_number=0, slice_count=1, job_id=None):
    log_data['inventory_id'] = inventory.id
    log_data['updated_ct'] = 0
    log_data['unmodified_ct'] = 0
    log_data['cleared_ct'] = 0
    hosts_to_update = []
    for host in _get_inventory_hosts(inventory, slice_number, slice_count):
        filepath = os.sep.join(map(str, [destination, host.name]))
        if not os.path.realpath(filepath).startswith(destination):
            system_tracking_logger.error('facts for host {} could not be cached'.format(smart_str(host.name)))
            continue
        if os.path.exists(filepath):
            # If the file changed since we wrote the last facts file, pre-playbook run...
            modified = os.path.getmtime(filepath)
            if (not facts_write_time) or modified > facts_write_time:
                with codecs.open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        ansible_facts = json.load(f)
                    except ValueError:
                        continue
                    host.ansible_facts = ansible_facts
                    host.ansible_facts_modified = now()
                    hosts_to_update.append(host)
                    system_tracking_logger.info(
                        'New fact for inventory {} host {}'.format(smart_str(host.inventory.name), smart_str(host.name)),
                        extra=dict(
                            inventory_id=host.inventory.id,
                            host_name=host.name,
                            ansible_facts=host.ansible_facts,
                            ansible_facts_modified=host.ansible_facts_modified.isoformat(),
                            job_id=job_id,
                        ),
                    )
                    log_data['updated_ct'] += 1
            else:
                log_data['unmodified_ct'] += 1
        else:
            # if the file goes missing, ansible removed it (likely via clear_facts)
            host.ansible_facts = {}
            host.ansible_facts_modified = now()
            hosts_to_update.append(host)
            system_tracking_logger.info('Facts cleared for inventory {} host {}'.format(smart_str(host.inventory.name), smart_str(host.name)))
            log_data['cleared_ct'] += 1
        if len(hosts_to_update) > 100:
            inventory.hosts.bulk_update(hosts_to_update, ['ansible_facts', 'ansible_facts_modified'])
            hosts_to_update = []
    if hosts_to_update:
        inventory.hosts.bulk_update(hosts_to_update, ['ansible_facts', 'ansible_facts_modified'])
