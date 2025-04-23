import multiprocessing
import json

import pytest

import requests
from requests.auth import HTTPBasicAuth

from django.db import connection

from awx.main.models import User, JobTemplate


def create_in_subprocess(project_id, ready_event, continue_event, admin_auth):
    connection.connect()

    print('setting ready event')
    ready_event.set()
    print('waiting for continue event')
    continue_event.wait()

    if JobTemplate.objects.filter(name='test_jt_duplicate_name').exists():
        for jt in JobTemplate.objects.filter(name='test_jt_duplicate_name'):
            jt.delete()
    assert JobTemplate.objects.filter(name='test_jt_duplicate_name').count() == 0

    jt_data = {'name': 'test_jt_duplicate_name', 'project': project_id, 'playbook': 'hello_world.yml', 'ask_inventory_on_launch': True}
    response = requests.post('http://localhost:8013/api/v2/job_templates/', json=jt_data, auth=admin_auth)
    # should either have a conflict or create
    assert response.status_code in (400, 201)
    print(f'Subprocess got {response.status_code}')
    if response.status_code == 400:
        print(json.dumps(response.json(), indent=2))
    return response.status_code


@pytest.fixture
def admin_for_test():
    user, created = User.objects.get_or_create(username='admin_for_test', defaults={'is_superuser': True})
    if created:
        user.set_password('for_test_123!')
        user.save()
        print(f'Created user {user.username}')
    return user


@pytest.fixture
def admin_auth(admin_for_test):
    return HTTPBasicAuth(admin_for_test.username, 'for_test_123!')


def test_jt_duplicate_name(admin_auth, demo_proj):
    N_processes = 5
    ready_events = [multiprocessing.Event() for _ in range(N_processes)]
    continue_event = multiprocessing.Event()

    processes = []
    for i in range(N_processes):
        p = multiprocessing.Process(target=create_in_subprocess, args=(demo_proj.id, ready_events[i], continue_event, admin_auth))
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
    print('waiting on the workers to finish the creation')
    for p in processes:
        p.join()

    assert JobTemplate.objects.filter(name='test_jt_duplicate_name').count() == 1
