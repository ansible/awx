# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import json
import mock
import os
import tempfile
import time
import pytest
from datetime import datetime

from awx.main.models import Host
from awx.main.task_engine import TaskSerializer, TaskEngager


@pytest.mark.django_db
def test_license_writer(inventory, admin):
    writer = TaskEngager(
        company_name='acmecorp',
        contact_name='Michael DeHaan',
        contact_email='michael@ansibleworks.com',
        license_date=25000, # seconds since epoch
        instance_count=500)

    data = writer.get_data()

    Host.objects.bulk_create(
        [
            Host(
                name='host.%d' % n,
                inventory=inventory,
                created_by=admin,
                modified=datetime.now(),
                created=datetime.now())
            for n in range(12)
        ]
    )

    assert data['instance_count'] == 500
    assert data['contact_name'] == 'Michael DeHaan'
    assert data['contact_email'] == 'michael@ansibleworks.com'
    assert data['license_date'] == 25000
    assert data['license_key'] == "11bae31f31c6a6cdcb483a278cdbe98bd8ac5761acd7163a50090b0f098b3a13"

    strdata = writer.get_string()
    strdata_loaded = json.loads(strdata)
    assert strdata_loaded == data

    reader = TaskSerializer()

    vdata = reader.from_string(strdata)

    assert vdata['available_instances'] == 500
    assert vdata['current_instances'] == 12
    assert vdata['free_instances'] == 488
    assert vdata['date_warning'] is True
    assert vdata['date_expired'] is True
    assert vdata['license_date'] == 25000
    assert vdata['time_remaining'] < 0
    assert vdata['valid_key'] is True
    assert vdata['compliant'] is False
    assert vdata['subscription_name']

@pytest.mark.django_db
def test_expired_licenses():
    reader = TaskSerializer()
    writer = TaskEngager(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=True)
    strdata = writer.get_string()
    vdata = reader.from_string(strdata)

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    writer = TaskEngager(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 2592001),
        instance_count=100,
        trial=False)
    strdata = writer.get_string()
    vdata = reader.from_string(strdata)

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    writer = TaskEngager(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=False)
    strdata = writer.get_string()
    vdata = reader.from_string(strdata)

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] > 0

@pytest.mark.django_db
def test_aws_license():
    os.environ['AWX_LICENSE_FILE'] = 'non-existent-license-file.json'

    h, path = tempfile.mkstemp()
    with os.fdopen(h, 'w') as f:
        json.dump({'instance_count': 100}, f)

    def fetch_ami(_self):
        _self.attributes['ami-id'] = 'ami-00000000'
        return True

    def fetch_instance(_self):
        _self.attributes['instance-id'] = 'i-00000000'
        return True

    with mock.patch('awx.main.task_engine.TEMPORARY_TASK_FILE', path):
        with mock.patch('awx.main.task_engine.TemporaryTaskEngine.fetch_ami', fetch_ami):
            with mock.patch('awx.main.task_engine.TemporaryTaskEngine.fetch_instance', fetch_instance):
                reader = TaskSerializer()
                license = reader.from_file()
                assert license['is_aws']
                assert license['time_remaining']
                assert license['free_instances'] > 0
                assert license['grace_period_remaining'] > 0

    os.unlink(path)
