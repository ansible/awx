# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import pytest
from datetime import datetime
import json

# Django
from django.utils import timezone

# AWX
from awx.main.management.commands.run_fact_cache_receiver import FactCacheReceiver
from awx.main.models.fact import Fact
from awx.main.models.inventory import Host

# TODO: Check that timestamp and other attributes are as expected
def check_process_fact_message_module(fact_returned, data, module_name):
    date_key = data['date_key']

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
def test_process_fact_message_ansible(fact_msg_ansible):
    receiver = FactCacheReceiver()
    fact_returned = receiver.process_fact_message(fact_msg_ansible)

    check_process_fact_message_module(fact_returned, fact_msg_ansible, 'ansible')

@pytest.mark.django_db
def test_process_fact_message_packages(fact_msg_packages):
    receiver = FactCacheReceiver()
    fact_returned = receiver.process_fact_message(fact_msg_packages)

    check_process_fact_message_module(fact_returned, fact_msg_packages, 'packages')

@pytest.mark.django_db
def test_process_fact_message_services(fact_msg_services):
    receiver = FactCacheReceiver()
    fact_returned = receiver.process_fact_message(fact_msg_services)

    check_process_fact_message_module(fact_returned, fact_msg_services, 'services')


'''
We pickypack our fact sending onto the Ansible fact interface.
The interface is <hostname, facts>. Where facts is a json blob of all the facts.
This makes it hard to decipher what facts are new/changed.
Because of this, we handle the same fact module data being sent multiple times
and just keep the newest version.
'''
@pytest.mark.django_db
def test_process_facts_message_ansible_overwrite(fact_scans, fact_msg_ansible):
    #epoch = timezone.now()
    epoch = datetime.fromtimestamp(fact_msg_ansible['date_key'])
    fact_scans(fact_scans=1, timestamp_epoch=epoch)
    key = 'ansible.overwrite'
    value = 'hello world'

    receiver = FactCacheReceiver()
    receiver.process_fact_message(fact_msg_ansible)

    fact_msg_ansible['facts'][key] = value
    fact_returned = receiver.process_fact_message(fact_msg_ansible)

    fact_obj = Fact.objects.get(id=fact_returned.id)
    assert key in fact_obj.facts
    assert fact_msg_ansible['facts'] == (json.loads(fact_obj.facts) if isinstance(fact_obj.facts, unicode) else fact_obj.facts) # TODO: Just make response.data['facts'] when we're only dealing with postgres, or if jsonfields ever fixes this bug

# Ensure that the message flows from the socket through to process_fact_message()
@pytest.mark.django_db
def test_run_receiver(mocker, fact_msg_ansible):
    mocker.patch("awx.main.socket_queue.Socket.listen", return_value=[fact_msg_ansible])

    receiver = FactCacheReceiver()
    mocker.patch.object(receiver, 'process_fact_message', return_value=None)

    receiver.run_receiver(use_processing_threads=False)

    receiver.process_fact_message.assert_called_once_with(fact_msg_ansible)
