# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from awx.main.utils.common import StubLicense


def test_stub_license():
    license_actual = StubLicense()
    assert license_actual['license_key'] == 'OPEN'
    assert license_actual['valid_key']
    assert license_actual['compliant']
    assert license_actual['license_type'] == 'open'

