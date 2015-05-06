# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from datetime import datetime

# Django

# AWX
from awx.fact.models.fact import * # noqa
from .base import BaseFactTest

__all__ = ['FactGetSingleFactsTest', 'FactGetSingleFactsMultipleScansTest',]

TEST_FACT_PACKAGES = [
    {
        "name": "accountsservice",
        "architecture": "amd64",
        "source": "apt",
        "version": "0.6.35-0ubuntu7.1"
    },
    {
        "name": "acpid",
        "architecture": "amd64",
        "source": "apt",
        "version": "1:2.0.21-1ubuntu2"
    },
    {
        "name": "adduser",
        "architecture": "all",
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
    def setUp(self):
        super(FactGetSingleFactsTest, self).setUp()
        self.host_count = 20
        self.timestamp = datetime.now().replace(year=2016)
        self.create_fact_scans(TEST_FACT_DATA, self.host_count, scan_count=1)
        self.hosts = [self.hostnames[i].hostname for i in range(0, self.host_count)]

    def check_query_results(self, facts_known, facts):
        self.assertIsNotNone(facts)
        self.assertEqual(len(facts_known), len(facts), "More or less facts found than expected")
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
        self.assertIsNotNone(facts)
        for fact in facts:
            self.assertEqual(len(fact.fact), 1)
            self.assertEqual(fact.fact['nested'][0]['name'], 'acpid')

    def test_single_host(self):
        self.hosts = [self.hostnames[i].hostname for i in range(0, 1)]
        facts = Fact.get_single_facts(self.hosts, 'name', 'acpid', self.timestamp, 'packages')

        self.check_query_results(self.fact_objs[0][:1], facts)

    def test_all(self):
        facts = Fact.get_single_facts(self.hosts, 'name', 'acpid', self.timestamp, 'packages')

        self.check_query_results(self.fact_objs[0], facts)

    def test_subset_hosts(self):
        self.hosts = [self.hostnames[i].hostname for i in range(0, (self.host_count / 2))]
        facts = Fact.get_single_facts(self.hosts, 'name', 'acpid', self.timestamp, 'packages')

        self.check_query_results(self.fact_objs[0][:(self.host_count / 2)], facts)
        
    def test_get_single_facts_nested(self):
        facts = Fact.get_single_facts(self.hosts, 'nested.name', 'acpid',  self.timestamp, 'packages')

        self.check_query_results_nested(facts)

class FactGetSingleFactsMultipleScansTest(BaseFactTest):
    def setUp(self):
        super(FactGetSingleFactsMultipleScansTest, self).setUp()
        self.create_fact_scans(TEST_FACT_DATA, host_count=10, scan_count=10)

    def test_1_host(self):
        timestamp = datetime.now().replace(year=2016)
        facts = Fact.get_single_facts([self.hostnames[0].hostname], 'name', 'acpid',  timestamp, 'packages')
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], self.fact_objs[0][0])

    def test_multiple_hosts(self):
        timestamp = datetime.now().replace(year=2016)
        hosts = [self.hostnames[i].hostname for i in range(0, 3)]
        facts = Fact.get_single_facts(hosts, 'name', 'acpid',  timestamp, 'packages')
        self.assertEqual(len(facts), 3)
        for i, fact in enumerate(facts):
            self.assertEqual(fact, self.fact_objs[0][i])

    def test_middle_of_timeline(self):
        timestamp = datetime.now().replace(year=2013)
        hosts = [self.hostnames[i].hostname for i in range(0, 3)]
        facts = Fact.get_single_facts(hosts, 'name', 'acpid',  timestamp, 'packages')
        self.assertEqual(len(facts), 3)
        for i, fact in enumerate(facts):
            self.assertEqual(fact, self.fact_objs[2][i])
