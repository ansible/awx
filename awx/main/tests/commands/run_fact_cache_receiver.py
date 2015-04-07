# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import time
from datetime import datetime
import mock
import unittest
from copy import deepcopy
from mock import MagicMock

# AWX
from awx.main.tests.base import BaseTest, MongoDBRequired
from awx.main.tests.commands.base import BaseCommandMixin
from awx.main.management.commands.run_fact_cache_receiver import FactCacheReceiver
from awx.fact.models.fact import * # noqa

__all__ = ['RunFactCacheReceiverUnitTest', 'RunFactCacheReceiverFunctionalTest']

TEST_MSG_BASE = {
    'host': 'hostname1',
    'date_key': time.mktime(datetime.utcnow().timetuple()),
    'facts' : { }
}

TEST_MSG_MODULES = {
    'packages': {
        "accountsservice": [
            {
                "architecture": "amd64",
                "name": "accountsservice",
                "source": "apt",
                "version": "0.6.35-0ubuntu7.1"
            }
        ],
        "acpid": [
            {
                "architecture": "amd64",
                "name": "acpid",
                "source": "apt",
                "version": "1:2.0.21-1ubuntu2"
            }
        ],
        "adduser": [
            {
                "architecture": "all",
                "name": "adduser",
                "source": "apt",
                "version": "3.113+nmu3ubuntu3"
            }
        ],
    },
    'services': [
        {
            "name": "acpid",
            "source": "sysv",
            "state": "running"
        },
        {
            "name": "apparmor",
            "source": "sysv",
            "state": "stopped"
        },
        {
            "name": "atd",
            "source": "sysv",
            "state": "running"
        },
        {
            "name": "cron",
            "source": "sysv",
            "state": "running"
        }
    ],
    'ansible': {
        'ansible_fact_simple': 'hello world',
        'ansible_fact_complex': {
            'foo': 'bar',
            'hello': [
                'scooby',
                'dooby',
                'doo'
            ]
        },
    }
}
# Derived from TEST_MSG_BASE
TEST_MSG = dict(TEST_MSG_BASE)

def copy_only_module(data, module):
    data = deepcopy(data)
    data['facts'] = {}
    if module == 'ansible':
        data['facts'] = deepcopy(TEST_MSG_MODULES[module])
    else:
        data['facts'][module] = deepcopy(TEST_MSG_MODULES[module])
    return data


class RunFactCacheReceiverFunctionalTest(BaseCommandMixin, BaseTest, MongoDBRequired):
    @unittest.skip('''\
TODO: run_fact_cache_receiver enters a while True loop that never exists. \
This differs from most other commands that we test for. More logic and work \
would be required to invoke this case from the command line with little return \
in terms of increase coverage and confidence.''')
    def test_invoke(self):
        result, stdout, stderr = self.run_command('run_fact_cache_receiver')
        self.assertEqual(result, None)

class RunFactCacheReceiverUnitTest(BaseTest, MongoDBRequired):

    # TODO: Check that timestamp and other attributes are as expected
    def check_process_fact_message_module(self, data, module):
        fact_found = None
        facts = Fact.objects.all()
        self.assertEqual(len(facts), 1)
        for fact in facts:
            if fact.module == module:
                fact_found = fact
                break
        self.assertIsNotNone(fact_found)
        #self.assertEqual(data['facts'][module], fact_found[module])

        fact_found = None
        fact_versions = FactVersion.objects.all()
        self.assertEqual(len(fact_versions), 1)
        for fact in fact_versions:
            if fact.module == module:
                fact_found = fact
                break
        self.assertIsNotNone(fact_found)


    # Ensure that the message flows from the socket through to process_fact_message()
    @mock.patch('awx.main.socket.Socket.listen')
    def test_run_receiver(self, listen_mock):
        listen_mock.return_value = [TEST_MSG]

        receiver = FactCacheReceiver()
        receiver.process_fact_message = MagicMock(name='process_fact_message')
        receiver.run_receiver()

        receiver.process_fact_message.assert_called_once_with(TEST_MSG)

    def test_process_fact_message_ansible(self):
        data = copy_only_module(TEST_MSG, 'ansible')

        receiver = FactCacheReceiver()
        receiver.process_fact_message(data)

        self.check_process_fact_message_module(data, 'ansible')

    def test_process_fact_message_packages(self):
        data = copy_only_module(TEST_MSG, 'packages')

        receiver = FactCacheReceiver()
        receiver.process_fact_message(data)

        self.check_process_fact_message_module(data, 'packages')

    def test_process_fact_message_services(self):
        data = copy_only_module(TEST_MSG, 'services')

        receiver = FactCacheReceiver()
        receiver.process_fact_message(data)

        self.check_process_fact_message_module(data, 'services')


    # Ensure that only a single host gets created for multiple invocations with the same hostname
    def test_process_fact_message_single_host_created(self):
        receiver = FactCacheReceiver()

        data = deepcopy(TEST_MSG)
        receiver.process_fact_message(data)
        data = deepcopy(TEST_MSG)
        data['date_key'] = time.mktime(datetime.utcnow().timetuple())
        receiver.process_fact_message(data)

        fact_hosts = FactHost.objects.all()
        self.assertEqual(len(fact_hosts), 1)

    def test_process_facts_message_ansible_overwrite(self):
        data = copy_only_module(TEST_MSG, 'ansible')
        key = 'ansible_overwrite'
        value = 'hello world'

        receiver = FactCacheReceiver()
        receiver.process_fact_message(data)

        fact = Fact.objects.all()[0]

        data = copy_only_module(TEST_MSG, 'ansible')
        data['facts'][key] = value
        receiver.process_fact_message(data)

        fact = Fact.objects.get(id=fact.id)
        self.assertIn(key, fact.fact)
        self.assertEqual(fact.fact[key], value)
