# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import pytest
from datetime import datetime
import json

# Django
from django.utils import timezone

# AWX
from awx.main.management.commands.run_fact_cache_receiver import FactBrokerWorker
from awx.main.models.fact import Fact
from awx.main.models.inventory import Host
from awx.main.models.base import PERM_INVENTORY_SCAN


@pytest.fixture
def mock_message(mocker):
    class Message():
        def ack():
            pass
    msg = Message()
    mocker.patch.object(msg, 'ack')
    return msg


@pytest.fixture
def mock_job_generator(mocker):
    def fn(store_facts=True, job_type=PERM_INVENTORY_SCAN):
        class Job():
            def __init__(self):
                self.store_facts = store_facts
                self.job_type = job_type
        job = Job()
        mocker.patch('awx.main.models.Job.objects.get', return_value=job)
        return job
    return fn


# TODO: Check that timestamp and other attributes are as expected
def check_process_fact_message_module(fact_returned, data, module_name, message):
    date_key = data['date_key']

    message.ack.assert_called_with()

    # Ensure 1, and only 1, fact created
    timestamp = datetime.fromtimestamp(date_key, timezone.utc)
    assert 1 == Fact.objects.all().count()

    host_obj = Host.objects.get(name=data['host'], inventory__id=data['inventory_id'])
    assert host_obj is not None
    fact_known = Fact.get_host_fact(host_obj.id, module_name, timestamp)
    assert fact_known is not None
    assert fact_known == fact_returned

    assert host_obj == fact_returned.host
    if module_name == 'ansible':
        assert data['facts'] == fact_returned.facts
    else:
        assert data['facts'][module_name] == fact_returned.facts
    assert timestamp  == fact_returned.timestamp
    assert module_name == fact_returned.module


@pytest.mark.django_db
def test_process_fact_message_ansible(fact_msg_ansible, monkeypatch_jsonbfield_get_db_prep_save, mock_message, mock_job_generator):
    receiver = FactBrokerWorker(None)
    mock_job_generator(store_facts=False, job_type=PERM_INVENTORY_SCAN)
    fact_returned = receiver.process_fact_message(fact_msg_ansible, mock_message)
    check_process_fact_message_module(fact_returned, fact_msg_ansible, 'ansible', mock_message)


@pytest.mark.django_db
def test_process_fact_message_packages(fact_msg_packages, monkeypatch_jsonbfield_get_db_prep_save, mock_message, mock_job_generator):
    receiver = FactBrokerWorker(None)
    mock_job_generator(store_facts=False, job_type=PERM_INVENTORY_SCAN)
    fact_returned = receiver.process_fact_message(fact_msg_packages, mock_message)
    check_process_fact_message_module(fact_returned, fact_msg_packages, 'packages', mock_message)


@pytest.mark.django_db
def test_process_fact_message_services(fact_msg_services, monkeypatch_jsonbfield_get_db_prep_save, mock_message, mock_job_generator):
    receiver = FactBrokerWorker(None)
    mock_job_generator(store_facts=False, job_type=PERM_INVENTORY_SCAN)
    fact_returned = receiver.process_fact_message(fact_msg_services, mock_message)
    check_process_fact_message_module(fact_returned, fact_msg_services, 'services', mock_message)


@pytest.mark.django_db
def test_process_facts_message_ansible_overwrite(fact_scans, fact_msg_ansible, monkeypatch_jsonbfield_get_db_prep_save, mock_message, mock_job_generator):
    '''
    We pickypack our fact sending onto the Ansible fact interface.
    The interface is <hostname, facts>. Where facts is a json blob of all the facts.
    This makes it hard to decipher what facts are new/changed.
    Because of this, we handle the same fact module data being sent multiple times
    and just keep the newest version.
    '''
    #epoch = timezone.now()
    mock_job_generator(store_facts=False, job_type=PERM_INVENTORY_SCAN)
    epoch = datetime.fromtimestamp(fact_msg_ansible['date_key'])
    fact_scans(fact_scans=1, timestamp_epoch=epoch)
    key = 'ansible.overwrite'
    value = 'hello world'

    receiver = FactBrokerWorker(None)
    receiver.process_fact_message(fact_msg_ansible, mock_message)

    fact_msg_ansible['facts'][key] = value
    fact_returned = receiver.process_fact_message(fact_msg_ansible, mock_message)

    fact_obj = Fact.objects.get(id=fact_returned.id)
    assert key in fact_obj.facts
    assert fact_msg_ansible['facts'] == (json.loads(fact_obj.facts) if isinstance(fact_obj.facts, unicode) else fact_obj.facts) # TODO: Just make response.data['facts'] when we're only dealing with postgres, or if jsonfields ever fixes this bug


@pytest.mark.django_db
def test_process_fact_store_facts(fact_msg_services, monkeypatch_jsonbfield_get_db_prep_save, mock_message, mock_job_generator):
    receiver = FactBrokerWorker(None)
    mock_job_generator(store_facts=True, job_type='run')
    receiver.process_fact_message(fact_msg_services, mock_message)

    host_obj = Host.objects.get(name=fact_msg_services['host'], inventory__id=fact_msg_services['inventory_id'])
    assert host_obj is not None

    assert host_obj.ansible_facts == fact_msg_services['facts']


