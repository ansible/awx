# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.


from awx.main.utils.insights import filter_insights_api_response
from awx.main.tests.data.insights import TEST_INSIGHTS_PLANS


def test_filter_insights_api_response():
    actual = filter_insights_api_response(TEST_INSIGHTS_PLANS)

    assert actual['last_check_in'] == '2017-07-21T07:07:29.000Z'
    assert len(actual['reports']) == 9
    assert actual['reports'][0]['maintenance_actions'][0]['maintenance_plan']['name'] == "RHEL Demo Infrastructure"
    assert actual['reports'][0]['maintenance_actions'][0]['maintenance_plan']['maintenance_id'] == 29315
    assert actual['reports'][0]['rule']['severity'] == 'ERROR'
    assert actual['reports'][0]['rule']['description'] == 'Remote code execution vulnerability in libresolv via crafted DNS response (CVE-2015-7547)'
    assert actual['reports'][0]['rule']['category'] == 'Security'
    assert actual['reports'][0]['rule']['summary'] == ("A critical security flaw in the `glibc` library was found. "
                                                       "It allows an attacker to crash an application built against "
                                                       "that library or, potentially, execute arbitrary code with "
                                                       "privileges of the user running the application.")
    assert actual['reports'][0]['rule']['ansible_fix'] is False

