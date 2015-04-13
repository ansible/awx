# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mock

#Django
from django.core.management.base import CommandError

# AWX
from awx.main.tests.base import BaseTest, MongoDBRequired
from awx.main.tests.commands.base import BaseCommandMixin
from awx.main.management.commands.cleanup_facts import Command, CleanupFacts
from awx.fact.models.fact import * # noqa

__all__ = ['CommandTest','CleanupFactsUnitTest', 'CleanupFactsCommandFunctionalTest']

class CleanupFactsCommandFunctionalTest(BaseCommandMixin, BaseTest, MongoDBRequired):
    def test_invoke_zero_ok(self):
        self.create_hosts_and_facts(datetime(year=2015, day=2, month=1, microsecond=0), 10, 20)

        result, stdout, stderr = self.run_command('cleanup_facts', granularity='2y', older_than='1d')
        self.assertEqual(stdout, 'Deleted %s facts.\n' % ((200 / 2)))

    def test_invoke_zero_deleted(self):
        result, stdout, stderr = self.run_command('cleanup_facts', granularity='1w',older_than='5d')
        self.assertEqual(stdout, 'Deleted 0 facts.\n')

    def test_invoke_params_required(self):
        result, stdout, stderr = self.run_command('cleanup_facts')
        self.assertIsInstance(result, CommandError)
        self.assertEqual(str(result), 'Both --granularity and --older_than are required.') 

class CommandTest(BaseTest):
    @mock.patch('awx.main.management.commands.cleanup_facts.CleanupFacts.run')
    def test_parameters_ok(self, run):

        kv = {
            'older_than': '1d',
            'granularity': '1d',
        }
        cmd = Command()
        cmd.handle(None, **kv)
        run.assert_called_once_with(relativedelta(days=1), relativedelta(days=1))

    def test_string_time_to_timestamp_ok(self):
        kvs = [
            {
                'time': '2w',
                'timestamp': relativedelta(weeks=2),
                'msg': '2 weeks',
            },
            {
                'time': '23d',
                'timestamp': relativedelta(days=23),
                'msg': '23 days',
            },
            {
                'time': '11m',
                'timestamp': relativedelta(months=11),
                'msg': '11 months',
            },
            {
                'time': '14y',
                'timestamp': relativedelta(years=14),
                'msg': '14 years',
            },
        ]
        for kv in kvs:
            cmd = Command()
            res = cmd.string_time_to_timestamp(kv['time'])
            self.assertEqual(kv['timestamp'], res, "%s should convert to %s" % (kv['time'], kv['msg']))

    def test_string_time_to_timestamp_invalid(self):
        kvs = [
            {
                'time': '2weeks',
                'msg': 'weeks instead of w',
            },
            {
                'time': '2days',
                'msg': 'days instead of d',
            },
            {
                'time': '23',
                'msg': 'no unit specified',
            },
            {
                'time': None,
                'msg': 'no value specified',
            },
            {
                'time': 'zigzag',
                'msg': 'random string specified',
            },
        ]
        for kv in kvs:
            cmd = Command()
            res = cmd.string_time_to_timestamp(kv['time'])
            self.assertIsNone(res, kv['msg'])

    # Mock run() just in case, but it should never get called because an error should be thrown
    @mock.patch('awx.main.management.commands.cleanup_facts.CleanupFacts.run')
    def test_parameters_fail(self, run):
        kvs = [
            {
                'older_than': '1week',
                'granularity': '1d',
                'msg': 'Invalid older_than param value',
            },
            {
                'older_than': '1d',
                'granularity': '1year',
                'msg': 'Invalid granularity param value',
            }
        ]
        for kv in kvs:
            cmd = Command()
            with self.assertRaises(CommandError):
                cmd.handle(None, older_than=kv['older_than'], granularity=kv['granularity'])

class CleanupFactsUnitTest(BaseCommandMixin, BaseTest, MongoDBRequired):
    def setUp(self):
        super(CleanupFactsUnitTest, self).setUp()

        self.datetime_base = datetime(year=2015, day=2, month=1, microsecond=0)
        self.HOSTS = 10
        self.FACTS_PER_HOST = 20

        self.create_hosts_and_facts(self.datetime_base, self.HOSTS, self.FACTS_PER_HOST)

    '''
    Create 10 hosts with 20 facts each. A single fact a year for 20 years.
    After cleanup, there should be 10 facts for each host.
    Then ensure the correct facts are deleted.
    '''
    def test_cleanup_logic(self):
        cleanup_facts = CleanupFacts()
        fact_oldest = FactVersion.objects.all().order_by('timestamp').first()
        granularity = relativedelta(years=2)

        deleted_count = cleanup_facts.cleanup(self.datetime_base, granularity)
        self.assertEqual(deleted_count, (self.FACTS_PER_HOST * self.HOSTS) / 2)

        # Check the number of facts per host
        for host in self.hosts:
            count = FactVersion.objects.filter(host=host).count()
            self.assertEqual(count, self.FACTS_PER_HOST / 2, "should have half the number of FactVersion per host for host %s")

            count = Fact.objects.filter(host=host).count()
            self.assertEqual(count, self.FACTS_PER_HOST / 2, "should have half the number of Fact per host")

        # Ensure that only 1 fact exists per granularity time
        date_pivot = self.datetime_base
        for host in self.hosts:
            while date_pivot > fact_oldest.timestamp:
                date_pivot_next = date_pivot - granularity
                kv = {
                    'timestamp__lte': date_pivot,
                    'timestamp__gt': date_pivot_next,
                    'host': host,
                }
                count = FactVersion.objects.filter(**kv).count()
                self.assertEqual(count, 1, "should only be 1 FactVersion per the 2 year granularity")
                count = Fact.objects.filter(**kv).count()
                self.assertEqual(count, 1, "should only be 1 Fact per the 2 year granularity")
                date_pivot = date_pivot_next



