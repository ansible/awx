# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved

# Python
from __future__ import absolute_import
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

# Django

# AWX
from awx.fact.models.fact import * # noqa
from awx.fact.tests.base import BaseFactTest, FactScanBuilder, TEST_FACT_PACKAGES

__all__ = ['FactHostTest', 'FactTest', 'FactGetHostVersionTest', 'FactGetHostTimelineTest']

class FactHostTest(BaseFactTest):
    def test_create_host(self):
        host = FactHost(hostname='hosty')
        host.save()

        host = FactHost.objects.get(hostname='hosty')
        self.assertIsNotNone(host, "Host added but not found")
        self.assertEqual('hosty', host.hostname, "Gotten record hostname does not match expected hostname")

    # Ensure an error is raised for .get() that doesn't match a record.
    def test_get_host_id_no_result(self):
        host = FactHost(hostname='hosty')
        host.save()

        self.assertRaises(FactHost.DoesNotExist, FactHost.objects.get, hostname='doesnotexist')

class FactTest(BaseFactTest):
    def setUp(self):
        super(FactTest, self).setUp()

    def test_add_fact(self):
        timestamp = now().replace(microsecond=0)
        host = FactHost(hostname="hosty").save()
        (f_obj, v_obj) = Fact.add_fact(host=host, timestamp=timestamp, module='packages', fact=TEST_FACT_PACKAGES)
        f = Fact.objects.get(id=f_obj.id)
        v = FactVersion.objects.get(id=v_obj.id)

        self.assertEqual(f.id, f_obj.id)
        self.assertEqual(f.module, 'packages')
        self.assertEqual(f.fact, TEST_FACT_PACKAGES)
        self.assertEqual(f.timestamp, timestamp)

        # host relationship created
        self.assertEqual(f.host.id, host.id)

        # version created and related
        self.assertEqual(v.id, v_obj.id)
        self.assertEqual(v.timestamp, timestamp)
        self.assertEqual(v.host.id, host.id)
        self.assertEqual(v.fact.id, f_obj.id)
        self.assertEqual(v.fact.module, 'packages')

class FactGetHostVersionTest(BaseFactTest):
    def setUp(self):
        super(FactGetHostVersionTest, self).setUp()
        self.builder = FactScanBuilder()
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.build(scan_count=2, host_count=1)

    def test_get_host_version_exact_timestamp(self):
        fact_known = self.builder.get_scan(0, 'packages')[0]
        fact = Fact.get_host_version(hostname=self.builder.get_hostname(0), timestamp=self.builder.get_timestamp(0), module='packages')
        self.assertIsNotNone(fact)
        self.assertEqual(fact_known, fact)

    def test_get_host_version_lte_timestamp(self):
        timestamp = self.builder.get_timestamp(0) + relativedelta(days=1)
        fact_known = self.builder.get_scan(0, 'packages')[0]
        fact = Fact.get_host_version(hostname=self.builder.get_hostname(0), timestamp=timestamp, module='packages')
        self.assertIsNotNone(fact)
        self.assertEqual(fact_known, fact)

    def test_get_host_version_none(self):
        timestamp = self.builder.get_timestamp(0) - relativedelta(years=20)
        fact = Fact.get_host_version(hostname=self.builder.get_hostname(0), timestamp=timestamp, module='packages')
        self.assertIsNone(fact)

class FactGetHostTimelineTest(BaseFactTest):
    def setUp(self):
        super(FactGetHostTimelineTest, self).setUp()
        self.builder = FactScanBuilder()
        self.builder.add_fact('packages', TEST_FACT_PACKAGES)
        self.builder.build(scan_count=20, host_count=1)

    def test_get_host_timeline_ok(self):
        timestamps = Fact.get_host_timeline(hostname=self.builder.get_hostname(0), module='packages')
        self.assertIsNotNone(timestamps)
        self.assertEqual(len(timestamps), self.builder.get_scan_count())
        for i in range(0, self.builder.get_scan_count()):
            self.assertEqual(timestamps[i], self.builder.get_timestamp(i))
