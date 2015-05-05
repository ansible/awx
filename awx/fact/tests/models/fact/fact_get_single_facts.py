# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from datetime import datetime
from copy import deepcopy

# Django

# AWX
from awx.fact.models.fact import * # noqa
from .base import BaseFactTest

__all__ = ['FactGetSingleFactsTest']

TEST_FACT_PACKAGES = [
    {
        "name": "accountsservice",
        "architecture": "amd64",
        "name": "accountsservice",
        "source": "apt",
        "version": "0.6.35-0ubuntu7.1"
    },
    {
        "name": "acpid",
        "architecture": "amd64",
        "name": "acpid",
        "source": "apt",
        "version": "1:2.0.21-1ubuntu2"
    },
    {
        "name": "adduser",
        "architecture": "all",
        "name": "adduser",
        "source": "apt",
        "version": "3.113+nmu3ubuntu3"
    },
]

TEST_FACT_DATA = {
    'hostname': 'hostname_%d',
    'add_fact_data': {
        'timestamp': datetime.now(),
        'host': None,
        'module': 'packages',
        'fact': TEST_FACT_PACKAGES,
    }
}

TEST_FACT_NESTED_DATA = {
    'hostname': 'hostname_%d',
    'add_fact_data': {
        'timestamp': datetime.now(),
        'host': None,
        'module': 'packages',
        'fact': {
            'nested': TEST_FACT_PACKAGES
        },
    }
}


class FactGetSingleFactsTest(BaseFactTest):
    def create_fact_scans_unique_hosts(self, data, host_count):
        self.fact_data = []
        self.fact_objs = []
        self.hostnames = []
        for i in range(1, host_count + 1):
            fact_data = deepcopy(data)
            fact_data['hostname'] = fact_data['hostname'] % (i)
            fact_data['add_fact_data']['timestamp'] = datetime.now().replace(year=2015 - i)
            BaseFactTest.normalize_timestamp(fact_data)

            self.create_host_document(fact_data)
            (fact_obj, version_obj) = Fact.add_fact(**fact_data['add_fact_data'])

            self.fact_data.append(fact_data)
            self.fact_objs.append(fact_obj)
            self.hostnames.append(fact_data['hostname'])

    def setup_test_fact_data(self):
        self.host_count = 20
        self.create_fact_scans_unique_hosts(TEST_FACT_DATA, self.host_count)

    def setup_test_fact_nested_data(self):
        self.host_count = 20
        self.create_fact_scans_unique_hosts(TEST_FACT_NESTED_DATA, self.host_count)

    def check_query_results(self, facts_known, facts):
        # Ensure only 'acpid' is returned
        for fact in facts:
            self.assertEqual(len(fact.fact), 1)
            self.assertEqual(fact.fact[0]['name'], 'acpid')

        # Transpose facts to a dict with key id
        count = 0
        facts_dict = {}
        for fact in facts:
            count += 1
            facts_dict[fact.id] = fact
        self.assertEqual(count, len(facts_known))

        # For each fact that we put into the database on setup,
        # we should find that fact in the result set returned
        for fact_known in facts_known:
            key = fact_known.id
            self.assertIn(key, facts_dict)
            self.assertEqual(len(facts_dict[key].fact), 1)

    def check_query_results_nested(self, facts):
        for fact in facts:
            self.assertEqual(len(fact.fact), 1)
            self.assertEqual(fact.fact['nested'][0]['name'], 'acpid')

    def test_get_single_facts_ok(self):
        self.setup_test_fact_data()

        timestamp = datetime.now().replace(year=2016)
        facts = Fact.get_single_facts(self.hostnames, 'name', 'acpid',  timestamp, 'packages')
        self.assertIsNotNone(facts)

        self.check_query_results(self.fact_objs, facts)

    def test_get_single_facts_subset_by_timestamp(self):
        self.setup_test_fact_data()

        timestamp = datetime.now().replace(year=2010)
        facts = Fact.get_single_facts(self.hostnames, 'name', 'acpid', timestamp, 'packages')
        self.assertIsNotNone(facts)

        self.check_query_results(self.fact_objs[4:], facts)
        
    def test_get_single_facts_nested(self):
        self.setup_test_fact_nested_data()

        timestamp = datetime.now().replace(year=2016)
        facts = Fact.get_single_facts(self.hostnames, 'nested.name', 'acpid',  timestamp, 'packages')
        self.assertIsNotNone(facts)

        self.check_query_results_nested(facts)
