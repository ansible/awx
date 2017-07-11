# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import time
import pytest
from datetime import datetime

from awx.main.models import Host
from awx.main.utils import get_licenser, StubLicense
from tower_license import TowerLicense


@pytest.mark.django_db
def test_license_writer(inventory, admin):
    license_actual = TowerLicense(
        company_name='acmecorp',
        contact_name='Michael DeHaan',
        contact_email='michael@ansibleworks.com',
        license_date=25000, # seconds since epoch
        instance_count=500)

    data = license_actual.generate()

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

    vdata = license_actual.validate()

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


def test_stub_license():
    license_actual = StubLicense()
    assert license_actual['license_key'] == 'OPEN'
    assert license_actual['valid_key']
    assert license_actual['compliant']
    assert license_actual['license_type'] == 'open'


@pytest.mark.django_db
def test_expired_licenses():
    license_actual = TowerLicense(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=True)
    license_actual.generate()
    vdata = license_actual.validate()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    license_actual = TowerLicense(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 2592001),
        instance_count=100,
        trial=False)
    license_actual.generate()
    vdata = license_actual.validate()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] < 0

    license_actual = TowerLicense(
        company_name='Tower',
        contact_name='Tower Admin',
        contact_email='tower@ansible.com',
        license_date=int(time.time() - 3600),
        instance_count=100,
        trial=False)
    license_actual.generate()
    vdata = license_actual.validate()

    assert vdata['compliant'] is False
    assert vdata['grace_period_remaining'] > 0


@pytest.mark.django_db
def test_cloudforms_license(mocker):
    with mocker.patch('tower_license.TowerLicense._check_cloudforms_subscription', return_value=True):
        license_actual = TowerLicense()
        vdata = license_actual.validate()
        assert vdata['compliant'] is True
        assert vdata['subscription_name'] == "Red Hat CloudForms License"
        assert vdata['available_instances'] == 9999999
        assert vdata['license_type'] == 'enterprise'
        assert vdata['features']['ha'] is True
