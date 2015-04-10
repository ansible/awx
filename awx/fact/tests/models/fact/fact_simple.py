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

__all__ = ['FactHostTest', 'FactTest', 'FactGetHostVersionTest', 'FactGetHostTimelineTest']

TEST_FACT_DATA = {
    'hostname': 'hostname1',
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
# Strip off microseconds because mongo has less precision
BaseFactTest.normalize_timestamp(TEST_FACT_DATA)

def create_fact_scans(count=1):
    timestamps = []
    for i in range(0, count):
        data = deepcopy(TEST_FACT_DATA)
        t = datetime.now().replace(year=2015 - i, microsecond=0)
        data['add_fact_data']['timestamp'] = t
        (f, v) = Fact.add_fact(**data['add_fact_data'])
        timestamps.append(t)

    return timestamps


class FactHostTest(BaseFactTest):
    def test_create_host(self):
        host = FactHost(hostname=TEST_FACT_DATA['hostname'])
        host.save()

        host = FactHost.objects.get(hostname=TEST_FACT_DATA['hostname'])
        self.assertIsNotNone(host, "Host added but not found")
        self.assertEqual(TEST_FACT_DATA['hostname'], host.hostname, "Gotten record hostname does not match expected hostname")

    # Ensure an error is raised for .get() that doesn't match a record.
    def test_get_host_id_no_result(self):
        host = FactHost(hostname=TEST_FACT_DATA['hostname'])
        host.save()

        self.assertRaises(FactHost.DoesNotExist, FactHost.objects.get, hostname='doesnotexist')

class FactTest(BaseFactTest):
    def setUp(self):
        super(FactTest, self).setUp()
        self.create_host_document(TEST_FACT_DATA)

    def test_add_fact(self):
        (f_obj, v_obj) = Fact.add_fact(**TEST_FACT_DATA['add_fact_data'])
        f = Fact.objects.get(id=f_obj.id)
        v = FactVersion.objects.get(id=v_obj.id)

        self.assertEqual(f.id, f_obj.id)
        self.assertEqual(f.module, TEST_FACT_DATA['add_fact_data']['module'])
        self.assertEqual(f.fact, TEST_FACT_DATA['add_fact_data']['fact'])
        self.assertEqual(f.timestamp, TEST_FACT_DATA['add_fact_data']['timestamp'])

        # host relationship created
        self.assertEqual(f.host.id, TEST_FACT_DATA['add_fact_data']['host'].id)

        # version created and related
        self.assertEqual(v.id, v_obj.id)
        self.assertEqual(v.timestamp, TEST_FACT_DATA['add_fact_data']['timestamp'])
        self.assertEqual(v.host.id, TEST_FACT_DATA['add_fact_data']['host'].id)
        self.assertEqual(v.fact.id, f_obj.id)
        self.assertEqual(v.fact.module, TEST_FACT_DATA['add_fact_data']['module'])

class FactGetHostVersionTest(BaseFactTest):
    def setUp(self):
        super(FactGetHostVersionTest, self).setUp()
        self.create_host_document(TEST_FACT_DATA)

        self.t1 = datetime.now().replace(second=1, microsecond=0)
        self.t2 = datetime.now().replace(second=2, microsecond=0)
        data = deepcopy(TEST_FACT_DATA)
        data['add_fact_data']['timestamp'] = self.t1
        (self.f1, self.v1) = Fact.add_fact(**data['add_fact_data'])
        data = deepcopy(TEST_FACT_DATA)
        data['add_fact_data']['timestamp'] = self.t2
        (self.f2, self.v2) = Fact.add_fact(**data['add_fact_data'])

    def test_get_host_version_exact_timestamp(self):
        fact = Fact.get_host_version(hostname=TEST_FACT_DATA['hostname'], timestamp=self.t1, module=TEST_FACT_DATA['add_fact_data']['module'])
        self.assertIsNotNone(fact, "Set of Facts not found")
        self.assertEqual(self.f1.id, fact.id)
        self.assertEqual(self.f1.fact, fact.fact)

    def test_get_host_version_lte_timestamp(self):
        t3 = datetime.now().replace(second=3, microsecond=0)
        fact = Fact.get_host_version(hostname=TEST_FACT_DATA['hostname'], timestamp=t3, module=TEST_FACT_DATA['add_fact_data']['module'])
        self.assertEqual(self.f1.id, fact.id)
        self.assertEqual(self.f1.fact, fact.fact)

    def test_get_host_version_none(self):
        t3 = deepcopy(self.t1).replace(second=0)
        fact = Fact.get_host_version(hostname=TEST_FACT_DATA['hostname'], timestamp=t3, module=TEST_FACT_DATA['add_fact_data']['module'])
        self.assertIsNone(fact)

class FactGetHostTimelineTest(BaseFactTest):
    def setUp(self):
        super(FactGetHostTimelineTest, self).setUp()
        self.create_host_document(TEST_FACT_DATA)

        self.scans = 20
        self.timestamps = create_fact_scans(self.scans)

    def test_get_host_timeline_ok(self):
        timestamps = Fact.get_host_timeline(hostname=TEST_FACT_DATA['hostname'], module=TEST_FACT_DATA['add_fact_data']['module'])
        self.assertIsNotNone(timestamps)
        self.assertEqual(len(timestamps), len(self.timestamps))
        for i in range(0, self.scans):
            self.assertEqual(timestamps[i], self.timestamps[i])
