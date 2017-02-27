# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import time
import pytest
from datetime import datetime

from awx.main.models import Host
from awx.main.task_engine import TaskEnhancer


@pytest.mark.django_db
def test_license_writer(inventory, admin):
    task_enhancer = TaskEnhancer(
        company_name='acmecorp',
        contact_name='Michael DeHaan',
        contact_email='michael@ansibleworks.com',
        license_date=25000, # seconds since epoch
        instance_count=500)

    data = task_enhancer.enhance()

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

    vdata = task_enhancer.validate_enhancements()

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
    task_enhancer = TaskEnhancer(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=True)
    task_enhancer.enhance()
    vdata = task_enhancer.validate_enhancements()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    task_enhancer = TaskEnhancer(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 2592001),
        instance_count=100,
        trial=False)
    task_enhancer.enhance()
    vdata = task_enhancer.validate_enhancements()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    task_enhancer = TaskEnhancer(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=False)
    task_enhancer.enhance()
    vdata = task_enhancer.validate_enhancements()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] > 0
