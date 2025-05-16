import multiprocessing
import random

from django.db import connection
from django.utils.timezone import now

from awx.main.models import Inventory, Host
from awx.main.utils.db import bulk_update_sorted_by_id


def worker_delete_target(ready_event, continue_event, field_name):
    """Runs the bulk update, will be called in duplicate, in parallel"""
    inv = Inventory.objects.get(organization__name='Default', name='test_host_update_contention')
    host_list = list(inv.hosts.all())
    # Using random.shuffle for non-security-critical shuffling in a test
    random.shuffle(host_list)  # NOSONAR
    for i, host in enumerate(host_list):
        setattr(host, field_name, f'my_var: {i}')

    # ready to do the bulk_update
    print('worker has loaded all the hosts needed')
    ready_event.set()
    # wait for the coordination message
    continue_event.wait()

    # NOTE: did not reproduce the bug without batch_size
    bulk_update_sorted_by_id(Host, host_list, fields=[field_name], batch_size=100)
    print('finished doing the bulk update in worker')


def test_host_update_contention(default_org):
    inv_kwargs = dict(organization=default_org, name='test_host_update_contention')

    if Inventory.objects.filter(**inv_kwargs).exists():
        inv = Inventory.objects.get(**inv_kwargs).delete()

    inv = Inventory.objects.create(**inv_kwargs)
    right_now = now()
    hosts = [Host(inventory=inv, name=f'host-{i}', created=right_now, modified=right_now) for i in range(1000)]
    print('bulk creating hosts')
    Host.objects.bulk_create(hosts)

    # sanity check
    for host in hosts:
        assert not host.variables

    # Force our worker pool to make their own connection
    connection.close()

    ready_events = [multiprocessing.Event() for _ in range(2)]
    continue_event = multiprocessing.Event()

    print('spawning processes for concurrent bulk updates')
    processes = []
    fields = ['variables', 'ansible_facts']
    for i in range(2):
        p = multiprocessing.Process(target=worker_delete_target, args=(ready_events[i], continue_event, fields[i]))
        processes.append(p)
        p.start()

    # Assure both processes are connected and have loaded their host list
    for e in ready_events:
        print('waiting on subprocess ready event')
        e.wait()

    # Begin the bulk_update queries
    print('setting the continue event for the workers')
    continue_event.set()

    # if a Deadloack happens it will probably be surfaced by result here
    print('waiting on the workers to finish the bulk_update')
    for p in processes:
        p.join()

    print('checking workers have variables set')
    for host in inv.hosts.all():
        assert host.variables.startswith('my_var:')
        assert host.ansible_facts.startswith('my_var:')
