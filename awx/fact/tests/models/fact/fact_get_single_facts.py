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

TEST_FACT_DATA = {
    'hostname': 'hostname_%d',
    'add_fact_data': {
        'timestamp': datetime.now(),
        'host': None,
        'module': 'packages',
        'fact': {
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
    }
}


class FactGetSingleFactsTest(BaseFactTest):
    def create_fact_scans_unique_hosts(self, host_count):
        self.fact_data = []
        self.fact_objs = []
        self.hostnames = []
        for i in range(1, host_count + 1):
            fact_data = deepcopy(TEST_FACT_DATA)
            fact_data['hostname'] = fact_data['hostname'] % (i)
            fact_data['add_fact_data']['timestamp'] = datetime.now().replace(year=2015 - i)
            BaseFactTest.normalize_timestamp(fact_data)

            self.create_host_document(fact_data)
            (fact_obj, version_obj) = Fact.add_fact(**fact_data['add_fact_data'])

            self.fact_data.append(fact_data)
            self.fact_objs.append(fact_obj)
            self.hostnames.append(fact_data['hostname'])

    def setUp(self):
        super(FactGetSingleFactsTest, self).setUp()
        self.host_count = 20
        self.create_fact_scans_unique_hosts(self.host_count)

    def check_query_results(self, facts_known, facts):
        # Transpose facts to a dict with key _id
        count = 0
        facts_dict = {}
        for fact in facts:
            count += 1
            facts_dict[fact['_id']] = fact
        self.assertEqual(count, len(facts_known))

        # For each fact that we put into the database on setup,
        # we should find that fact in the result set returned
        for fact_known in facts_known:
            key = fact_known.id
            self.assertIn(key, facts_dict)
            self.assertEqual(facts_dict[key]['fact']['acpid'], fact_known.fact['acpid'])
            self.assertEqual(facts_dict[key]['host'], fact_known.host.id)

    def test_get_single_facts_ok(self):
        timestamp = datetime.now().replace(year=2016)
        facts = Fact.get_single_facts(self.hostnames, 'acpid', timestamp, 'packages')
        self.assertIsNotNone(facts)

        self.check_query_results(self.fact_objs, facts)

    def test_get_single_facts_subset_by_timestamp(self):
        timestamp = datetime.now().replace(year=2010)
        facts = Fact.get_single_facts(self.hostnames, 'acpid', timestamp, 'packages')
        self.assertIsNotNone(facts)

        self.check_query_results(self.fact_objs[4:], facts)
        