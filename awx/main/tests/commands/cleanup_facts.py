# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved

# Python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mock

#Django
from django.core.management.base import CommandError

# AWX
from awx.main.tests.base import BaseTest
from awx.fact.tests.base import MongoDBRequired, FactScanBuilder, TEST_FACT_PACKAGES, TEST_FACT_ANSIBLE, TEST_FACT_SERVICES
from awx.main.tests.commands.base import BaseCommandMixin
from awx.main.management.commands.cleanup_facts import Command, CleanupFacts
from awx.fact.models.fact import * # noqa

__all__ = ['CommandTest','CleanupFactsUnitTest', 'CleanupFactsCommandFunctionalTest']

class CleanupFactsCommandFunctionalTest(BaseCommandMixin, BaseTest, MongoDBRequired):
    def setUp(self):
        super(CleanupFactsCommandFunctionalTest, self).setUp()
        self.create_test_license_file()
        self.builder = FactScanBuilder()
        self.builder.add_fact('ansible', TEST_FACT_ANSIBLE)

    def test_invoke_zero_ok(self):
        self.builder.set_epoch(datetime(year=2015, day=2, month=1, microsecond=0))
        self.builder.build(scan_count=20, host_count=10)

        result, stdout, stderr = self.run_command('cleanup_facts', granularity='2y', older_than='1d')
        self.assertEqual(stdout, 'Deleted %s facts.\n' % ((200 / 2)))

    def test_invoke_zero_deleted(self):
        result, stdout, stderr = self.run_command('cleanup_facts', granularity='1w',older_than='5d')
        self.assertEqual(stdout, 'Deleted 0 facts.\n')

    def test_invoke_all_deleted(self):
        self.builder.build(scan_count=20, host_count=10)

        result, stdout, stderr = self.run_command('cleanup_facts', granularity='0d', older_than='0d')
        self.assertEqual(stdout, 'Deleted 200 facts.\n')

    def test_invoke_params_required(self):
        result, stdout, stderr = self.run_command('cleanup_facts')
        self.assertIsInstance(result, CommandError)
        self.assertEqual(str(result), 'Both --granularity and --older_than are required.') 

    def test_module(self):
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.add_fact('services', TEST_FACT_SERVICES)
        self.builder.build(scan_count=5, host_count=5)

        result, stdout, stderr = self.run_command('cleanup_facts', granularity='0d', older_than='0d', module='packages')
        self.assertEqual(stdout, 'Deleted 25 facts.\n')

class CommandTest(BaseTest):
    def setUp(self):
        super(CommandTest, self).setUp()
        self.create_test_license_file()

    @mock.patch('awx.main.management.commands.cleanup_facts.CleanupFacts.run')
    def test_parameters_ok(self, run):

        kv = {
            'older_than': '1d',
            'granularity': '1d',
            'module': None,
        }
        cmd = Command()
        cmd.handle(None, **kv)
        run.assert_called_once_with(relativedelta(days=1), relativedelta(days=1), module=None)

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

        self.builder = FactScanBuilder()
        self.builder.add_fact('ansible', TEST_FACT_ANSIBLE)
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.build(scan_count=20, host_count=10)

    '''
    Create 10 hosts with 40 facts each. After cleanup, there should be 20 facts for each host.
    Then ensure the correct facts are deleted.
    '''
    def test_cleanup_logic(self):
        cleanup_facts = CleanupFacts()
        fact_oldest = FactVersion.objects.all().order_by('timestamp').first()
        granularity = relativedelta(years=2)

        deleted_count = cleanup_facts.cleanup(self.builder.get_timestamp(0), granularity)
        self.assertEqual(deleted_count, 2 * (self.builder.get_scan_count() * self.builder.get_host_count()) / 2)

        # Check the number of facts per host
        for host in self.builder.get_hosts():
            count = FactVersion.objects.filter(host=host).count()
            scan_count = (2 * self.builder.get_scan_count()) / 2
            self.assertEqual(count, scan_count)

            count = Fact.objects.filter(host=host).count()
            self.assertEqual(count, scan_count)

        # Ensure that only 2 facts (ansible and packages) exists per granularity time
        date_pivot = self.builder.get_timestamp(0)
        for host in self.builder.get_hosts():
            while date_pivot > fact_oldest.timestamp:
                date_pivot_next = date_pivot - granularity
                kv = {
                    'timestamp__lte': date_pivot,
                    'timestamp__gt': date_pivot_next,
                    'host': host,
                }
                count = FactVersion.objects.filter(**kv).count()
                self.assertEqual(count, 2, "should only be 2 FactVersion per the 2 year granularity")
                count = Fact.objects.filter(**kv).count()
                self.assertEqual(count, 2, "should only be 2 Fact per the 2 year granularity")
                date_pivot = date_pivot_next

    '''
    Create 10 hosts with 40 facts each. After cleanup, there should be 30 facts for each host.
    Then ensure the correct facts are deleted.
    '''
    def test_cleanup_module(self):
        cleanup_facts = CleanupFacts()
        fact_oldest = FactVersion.objects.all().order_by('timestamp').first()
        granularity = relativedelta(years=2)

        deleted_count = cleanup_facts.cleanup(self.builder.get_timestamp(0), granularity, module='ansible')
        self.assertEqual(deleted_count, (self.builder.get_scan_count() * self.builder.get_host_count()) / 2)

        # Check the number of facts per host
        for host in self.builder.get_hosts():
            count = FactVersion.objects.filter(host=host).count()
            self.assertEqual(count, 30)

            count = Fact.objects.filter(host=host).count()
            self.assertEqual(count, 30)

        # Ensure that only 1 ansible fact exists per granularity time
        date_pivot = self.builder.get_timestamp(0)
        for host in self.builder.get_hosts():
            while date_pivot > fact_oldest.timestamp:
                date_pivot_next = date_pivot - granularity
                kv = {
                    'timestamp__lte': date_pivot,
                    'timestamp__gt': date_pivot_next,
                    'host': host,
                    'module': 'ansible',
                }
                count = FactVersion.objects.filter(**kv).count()
                self.assertEqual(count, 1)
                count = Fact.objects.filter(**kv).count()
                self.assertEqual(count, 1)
                date_pivot = date_pivot_next






