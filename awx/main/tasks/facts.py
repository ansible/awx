import codecs
import datetime
import os
import json
import logging

# Django
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.timezone import now

# django-ansible-base
from ansible_base.lib.logging.runtime import log_excess_runtime

# AWX
from awx.main.utils.db import bulk_update_sorted_by_id
from awx.main.models import Host


logger = logging.getLogger('awx.main.tasks.facts')
system_tracking_logger = logging.getLogger('awx.analytics.system_tracking')


@log_excess_runtime(logger, debug_cutoff=0.01, msg='Inventory {inventory_id} host facts prepared for {written_ct} hosts, took {delta:.3f} s', add_log_data=True)
def start_fact_cache(hosts, destination, log_data, timeout=None, inventory_id=None):
    log_data['inventory_id'] = inventory_id
    log_data['written_ct'] = 0
    hosts_cached = []

    try:
        os.makedirs(destination, mode=0o700)
    except FileExistsError:
        pass

    if timeout is None:
        timeout = settings.ANSIBLE_FACT_CACHE_TIMEOUT

    last_write_time = None

    for host in hosts:
        hosts_cached.append(host.name)
        if not host.ansible_facts_modified or (timeout and host.ansible_facts_modified < now() - datetime.timedelta(seconds=timeout)):
            continue  # facts are expired - do not write them

        filepath = os.path.join(destination, host.name)
        if not os.path.realpath(filepath).startswith(destination):
            system_tracking_logger.error(f'facts for host {smart_str(host.name)} could not be cached')
            continue

        try:
            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                os.chmod(f.name, 0o600)
                json.dump(host.ansible_facts, f)
                log_data['written_ct'] += 1
                last_write_time = os.path.getmtime(filepath)
        except IOError:
            system_tracking_logger.error(f'facts for host {smart_str(host.name)} could not be cached')
            continue

    # Write summary file to artifacts dir
    if inventory_id is not None:
        artifact_dir = os.path.join('artifacts', f'inventory_{inventory_id}')
        os.makedirs(artifact_dir, exist_ok=True)
        summary_file = os.path.join(artifact_dir, 'host_cache_summary.json')
        summary_data = {'last_write_time': last_write_time, 'hosts_cached': hosts_cached, 'written_ct': log_data['written_ct']}
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)


@log_excess_runtime(
    logger,
    debug_cutoff=0.01,
    msg='Inventory {inventory_id} host facts: updated {updated_ct}, cleared {cleared_ct}, unchanged {unmodified_ct}, took {delta:.3f} s',
    add_log_data=True,
)
def finish_fact_cache(destination, log_data, job_id=None, inventory_id=None):
    log_data['inventory_id'] = inventory_id
    log_data['updated_ct'] = 0
    log_data['unmodified_ct'] = 0
    log_data['cleared_ct'] = 0

    summary_path = os.path.join(destination, 'host_cache_summary.json')
    if not os.path.exists(summary_path):
        system_tracking_logger.error(f'Missing summary file at {summary_path}')
        return

    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        facts_write_time = os.path.getmtime(summary_path)  # Get mtime *after* successful read
    except (json.JSONDecodeError, OSError) as e:
        system_tracking_logger.error(f'Error reading summary file at {summary_path}: {e}')
        return

    host_names = summary.get('hosts_cached', [])

    # Lookup Host objects.  Use iterator() for large queries.  Order by 'id'.
    hosts_cached = Host.objects.filter(name__in=host_names, inventory_id=inventory_id).order_by('id').iterator()

    hosts_to_update = []
    host_facts_dir = os.path.join(settings.ANSIBLE_FACT_CACHE, str(inventory_id))

    for host in hosts_cached:
        filepath = os.path.join(host_facts_dir, host.name)
        if not os.path.realpath(filepath).startswith(host_facts_dir):
            system_tracking_logger.error(f'Invalid path for facts file: {filepath}')
            continue

        if os.path.exists(filepath):
            modified = os.path.getmtime(filepath)
            if not facts_write_time or modified > facts_write_time:
                try:
                    with codecs.open(filepath, 'r', encoding='utf-8') as f:
                        ansible_facts = json.load(f)
                except ValueError:
                    continue

                host.ansible_facts = ansible_facts
                host.ansible_facts_modified = now()  # Use Django's timezone-aware now()
                hosts_to_update.append(host)
                system_tracking_logger.info(
                    f'New fact for inventory {smart_str(host.inventory.name)} host {smart_str(host.name)}',
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
            host.ansible_facts = {}
            host.ansible_facts_modified = now()  # Use Django's timezone-aware now()
            hosts_to_update.append(host)
            system_tracking_logger.info(f'Facts cleared for inventory {smart_str(host.inventory.name)} host {smart_str(host.name)}')
            log_data['cleared_ct'] += 1

        if len(hosts_to_update) >= 100:
            bulk_update_sorted_by_id(Host, hosts_to_update, fields=['ansible_facts', 'ansible_facts_modified'])
            hosts_to_update = []

    bulk_update_sorted_by_id(Host, hosts_to_update, fields=['ansible_facts', 'ansible_facts_modified'])
