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
def start_fact_cache(hosts, artifacts_dir, timeout=None, inventory_id=None, log_data=None):
    log_data = log_data or {}
    log_data['inventory_id'] = inventory_id
    log_data['written_ct'] = 0
    hosts_cached = []

    # Create the fact_cache directory inside artifacts_dir
    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
    os.makedirs(fact_cache_dir, mode=0o700, exist_ok=True)

    if timeout is None:
        timeout = settings.ANSIBLE_FACT_CACHE_TIMEOUT

    last_write_time = None

    for host in hosts:
        hosts_cached.append(host.name)
        if not host.ansible_facts_modified or (timeout and host.ansible_facts_modified < now() - datetime.timedelta(seconds=timeout)):
            continue  # facts are expired - do not write them

        filepath = os.path.join(fact_cache_dir, host.name)
        if not os.path.realpath(filepath).startswith(fact_cache_dir):
            logger.error(f'facts for host {smart_str(host.name)} could not be cached')
            continue

        try:
            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                os.chmod(f.name, 0o600)
                json.dump(host.ansible_facts, f)
                log_data['written_ct'] += 1
                last_write_time = os.path.getmtime(filepath)
        except IOError:
            logger.error(f'facts for host {smart_str(host.name)} could not be cached')
            continue

    # Write summary file directly to the artifacts_dir
    if inventory_id is not None:
        summary_file = os.path.join(artifacts_dir, 'host_cache_summary.json')
        summary_data = {
            'last_write_time': last_write_time,
            'hosts_cached': hosts_cached,
            'written_ct': log_data['written_ct'],
        }
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)


@log_excess_runtime(
    logger,
    debug_cutoff=0.01,
    msg='Inventory {inventory_id} host facts: updated {updated_ct}, cleared {cleared_ct}, unchanged {unmodified_ct}, took {delta:.3f} s',
    add_log_data=True,
)
def finish_fact_cache(artifacts_dir, job_id=None, inventory_id=None, log_data=None):
    log_data = log_data or {}
    log_data['inventory_id'] = inventory_id
    log_data['updated_ct'] = 0
    log_data['unmodified_ct'] = 0
    log_data['cleared_ct'] = 0
    # The summary file is directly inside the artifacts dir
    summary_path = os.path.join(artifacts_dir, 'host_cache_summary.json')
    if not os.path.exists(summary_path):
        logger.error(f'Missing summary file at {summary_path}')
        return

    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        facts_write_time = os.path.getmtime(summary_path)  # After successful read
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f'Error reading summary file at {summary_path}: {e}')
        return

    host_names = summary.get('hosts_cached', [])
    hosts_cached = Host.objects.filter(name__in=host_names).order_by('id').iterator()
    # Path where individual fact files were written
    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
    hosts_to_update = []

    for host in hosts_cached:
        filepath = os.path.join(fact_cache_dir, host.name)
        if not os.path.realpath(filepath).startswith(fact_cache_dir):
            logger.error(f'Invalid path for facts file: {filepath}')
            continue

        if os.path.exists(filepath):
            # If the file changed since we wrote the last facts file, pre-playbook run...
            modified = os.path.getmtime(filepath)
            if not facts_write_time or modified >= facts_write_time:
                try:
                    with codecs.open(filepath, 'r', encoding='utf-8') as f:
                        ansible_facts = json.load(f)
                except ValueError:
                    continue

                if ansible_facts != host.ansible_facts:
                    host.ansible_facts = ansible_facts
                    host.ansible_facts_modified = now()
                    hosts_to_update.append(host)
                    logger.info(
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
                log_data['unmodified_ct'] += 1
        else:
            # if the file goes missing, ansible removed it (likely via clear_facts)
            # if the file goes missing, but the host has not started facts, then we should not clear the facts
            host.ansible_facts = {}
            host.ansible_facts_modified = now()
            hosts_to_update.append(host)
            logger.info(f'Facts cleared for inventory {smart_str(host.inventory.name)} host {smart_str(host.name)}')
            log_data['cleared_ct'] += 1

        if len(hosts_to_update) >= 100:
            bulk_update_sorted_by_id(Host, hosts_to_update, fields=['ansible_facts', 'ansible_facts_modified'])
            hosts_to_update = []

    bulk_update_sorted_by_id(Host, hosts_to_update, fields=['ansible_facts', 'ansible_facts_modified'])
