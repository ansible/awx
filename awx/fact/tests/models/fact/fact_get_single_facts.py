# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
from datetime import datetime

# Django

# AWX
from awx.fact.models.fact import * # noqa
from awx.fact.tests.base import BaseFactTest, FactScanBuilder, TEST_FACT_PACKAGES

__all__ = ['FactGetSingleFactsTest', 'FactGetSingleFactsMultipleScansTest',]

class FactGetSingleFactsTest(BaseFactTest):
    def setUp(self):
        super(FactGetSingleFactsTest, self).setUp()
        self.builder = FactScanBuilder()
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.add_fact('nested', TEST_FACT_PACKAGES)
        self.builder.build(scan_count=1, host_count=20)

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
        facts = Fact.get_single_facts(self.builder.get_hostnames(0, 1), 'name', 'acpid', self.builder.get_timestamp(0), 'packages')

        self.check_query_results(self.builder.get_scan(0, 'packages')[:1], facts)

    def test_all(self):
        facts = Fact.get_single_facts(self.builder.get_hostnames(), 'name', 'acpid', self.builder.get_timestamp(0), 'packages')

        self.check_query_results(self.builder.get_scan(0, 'packages'), facts)

    def test_subset_hosts(self):
        host_count = (self.builder.get_host_count() / 2)
        facts = Fact.get_single_facts(self.builder.get_hostnames(0, host_count), 'name', 'acpid', self.builder.get_timestamp(0), 'packages')

        self.check_query_results(self.builder.get_scan(0, 'packages')[:host_count], facts)
        
    def test_get_single_facts_nested(self):
        facts = Fact.get_single_facts(self.builder.get_hostnames(), 'nested.name', 'acpid',  self.builder.get_timestamp(0), 'packages')

        self.check_query_results_nested(facts)

class FactGetSingleFactsMultipleScansTest(BaseFactTest):
    def setUp(self):
        super(FactGetSingleFactsMultipleScansTest, self).setUp()
        self.builder = FactScanBuilder()
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.build(scan_count=10, host_count=10)

    def test_1_host(self):
        facts = Fact.get_single_facts(self.builder.get_hostnames(0, 1), 'name', 'acpid',  self.builder.get_timestamp(0), 'packages')
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], self.builder.get_scan(0, 'packages')[0])

    def test_multiple_hosts(self):
        facts = Fact.get_single_facts(self.builder.get_hostnames(0, 3), 'name', 'acpid',  self.builder.get_timestamp(0), 'packages')
        self.assertEqual(len(facts), 3)
        for i, fact in enumerate(facts):
            self.assertEqual(fact, self.builder.get_scan(0, 'packages')[i])

    def test_middle_of_timeline(self):
        facts = Fact.get_single_facts(self.builder.get_hostnames(0, 3), 'name', 'acpid', self.builder.get_timestamp(4), 'packages')
        self.assertEqual(len(facts), 3)
        for i, fact in enumerate(facts):
            self.assertEqual(fact, self.builder.get_scan(4, 'packages')[i])

