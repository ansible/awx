# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.


from awx.main.utils.insights import filter_insights_api_response
from awx.main.tests.data.insights import TEST_INSIGHTS_HOSTS, TEST_INSIGHTS_PLANS, TEST_INSIGHTS_REMEDIATIONS


def test_filter_insights_api_response():
    actual = filter_insights_api_response(
        TEST_INSIGHTS_HOSTS['results'][0], TEST_INSIGHTS_PLANS, TEST_INSIGHTS_REMEDIATIONS)

    assert actual['last_check_in'] == '2019-03-19T21:59:09.213151-04:00'
    assert len(actual['reports']) == 5
    assert len(actual['reports'][0]['maintenance_actions']) == 1
    assert actual['reports'][0]['maintenance_actions'][0]['name'] == "Fix Critical CVEs"
    rule = actual['reports'][0]['rule']

    assert rule['severity'] == 'WARN'
    assert rule['description'] == (
        "Kernel vulnerable to side-channel attacks in modern microprocessors (CVE-2017-5715/Spectre)")
    assert rule['category'] == 'Security'
    assert rule['summary'] == (
        "A vulnerability was discovered in modern microprocessors supported by the kernel,"
        " whereby an unprivileged attacker can use this flaw to bypass restrictions to gain read"
        " access to privileged memory.\nThe issue was reported as [CVE-2017-5715 / Spectre]"
        "(https://access.redhat.com/security/cve/CVE-2017-5715).\n")
