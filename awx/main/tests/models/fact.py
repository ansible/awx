# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import datetime

# Django

# AWX
from awx.main.models.fact import *
from awx.main.tests.base import BaseTest

__all__ = ['FactHostTest', 'FactTest']

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
TEST_FACT_DATA['add_fact_data']['timestamp'] = TEST_FACT_DATA['add_fact_data']['timestamp'].replace(microsecond=0)

class FactHostTest(BaseTest):
    def test_create_host(self):
        host = FactHost(hostname=TEST_FACT_DATA['hostname'])
        host.save()

        host = FactHost.objects.get(hostname=TEST_FACT_DATA['hostname'])
        self.assertIsNotNone(host, "Host added but not found")
        self.assertEqual(TEST_FACT_DATA['hostname'], host.hostname, "Gotten record hostname does not match expected hostname")


class FactTest(BaseTest):
    def setUp(self):
        super(FactTest, self).setUp()
        TEST_FACT_DATA['add_fact_data']['host'] = FactHost(hostname=TEST_FACT_DATA['hostname']).save()

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


