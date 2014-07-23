# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import datetime

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlencode

from libcloud.loadbalancer.base import LoadBalancer, Member, Algorithm
from libcloud.loadbalancer.types import MemberCondition
from libcloud.loadbalancer.drivers.rackspace import RackspaceLBDriver, \
    RackspaceHealthMonitor, RackspaceHTTPHealthMonitor, \
    RackspaceConnectionThrottle, RackspaceAccessRule
from libcloud.loadbalancer.drivers.rackspace import RackspaceUKLBDriver
from libcloud.loadbalancer.drivers.rackspace import RackspaceAccessRuleType
from libcloud.common.types import LibcloudError

from libcloud.test import unittest
from libcloud.test import MockHttpTestCase
from libcloud.test.file_fixtures import LoadBalancerFileFixtures
from libcloud.test.file_fixtures import OpenStackFixtures


class RackspaceLBTests(unittest.TestCase):

    def setUp(self):
        RackspaceLBDriver.connectionCls.conn_classes = (None,
                                                        RackspaceLBMockHttp)
        RackspaceLBMockHttp.type = None
        self.driver = RackspaceLBDriver('user', 'key')
        self.driver.connection.poll_interval = 0.0
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()

    def test_force_auth_token_kwargs(self):
        base_url = 'https://ord.loadbalancer.api.rackspacecloud.com/v1.0/11111'
        kwargs = {
            'ex_force_auth_token': 'some-auth-token',
            'ex_force_base_url': base_url
        }
        driver = RackspaceLBDriver('user', 'key', **kwargs)
        driver.list_balancers()

        self.assertEqual(kwargs['ex_force_auth_token'],
                         driver.connection.auth_token)
        self.assertEqual('/v1.0/11111',
                         driver.connection.request_path)

    def test_force_auth_url_kwargs(self):
        kwargs = {
            'ex_force_auth_version': '2.0',
            'ex_force_auth_url': 'https://identity.api.rackspace.com'
        }
        driver = RackspaceLBDriver('user', 'key', **kwargs)

        self.assertEqual(kwargs['ex_force_auth_url'],
                         driver.connection._ex_force_auth_url)
        self.assertEqual(kwargs['ex_force_auth_version'],
                         driver.connection._auth_version)

    def test_gets_auth_2_0_endpoint_defaults_to_ord_region(self):
        driver = RackspaceLBDriver('user', 'key',
                                   ex_force_auth_version='2.0_password'
                                   )
        driver.connection._populate_hosts_and_request_paths()

        self.assertEqual(
            'https://ord.loadbalancers.api.rackspacecloud.com/v1.0/11111',
            driver.connection.get_endpoint())

    def test_gets_auth_2_0_endpoint_for_dfw(self):
        driver = RackspaceLBDriver('user', 'key',
                                   ex_force_auth_version='2.0_password',
                                   ex_force_region='dfw'
                                   )
        driver.connection._populate_hosts_and_request_paths()

        self.assertEqual(
            'https://dfw.loadbalancers.api.rackspacecloud.com/v1.0/11111',
            driver.connection.get_endpoint())

    def test_list_protocols(self):
        protocols = self.driver.list_protocols()

        self.assertEqual(len(protocols), 10)
        self.assertTrue('http' in protocols)

    def test_ex_list_protocols_with_default_ports(self):
        protocols = self.driver.ex_list_protocols_with_default_ports()

        self.assertEqual(len(protocols), 10)
        self.assertTrue(('http', 80) in protocols)

    def test_list_supported_algorithms(self):
        algorithms = self.driver.list_supported_algorithms()

        self.assertTrue(Algorithm.RANDOM in algorithms)
        self.assertTrue(Algorithm.ROUND_ROBIN in algorithms)
        self.assertTrue(Algorithm.LEAST_CONNECTIONS in algorithms)
        self.assertTrue(Algorithm.WEIGHTED_ROUND_ROBIN in algorithms)
        self.assertTrue(Algorithm.WEIGHTED_LEAST_CONNECTIONS in algorithms)

    def test_ex_list_algorithms(self):
        algorithms = self.driver.ex_list_algorithm_names()

        self.assertTrue("RANDOM" in algorithms)
        self.assertTrue("ROUND_ROBIN" in algorithms)
        self.assertTrue("LEAST_CONNECTIONS" in algorithms)
        self.assertTrue("WEIGHTED_ROUND_ROBIN" in algorithms)
        self.assertTrue("WEIGHTED_LEAST_CONNECTIONS" in algorithms)

    def test_list_balancers(self):
        balancers = self.driver.list_balancers()

        self.assertEqual(len(balancers), 2)
        self.assertEqual(balancers[0].name, "test0")
        self.assertEqual(balancers[0].id, "8155")
        self.assertEqual(balancers[0].port, 80)
        self.assertEqual(balancers[0].ip, "1.1.1.25")
        self.assertEqual(balancers[1].name, "test1")
        self.assertEqual(balancers[1].id, "8156")

    def test_list_balancers_ex_member_address(self):
        RackspaceLBMockHttp.type = 'EX_MEMBER_ADDRESS'
        balancers = self.driver.list_balancers(ex_member_address='127.0.0.1')

        self.assertEqual(len(balancers), 3)
        self.assertEqual(balancers[0].name, "First Loadbalancer")
        self.assertEqual(balancers[0].id, "1")
        self.assertEqual(balancers[1].name, "Second Loadbalancer")
        self.assertEqual(balancers[1].id, "2")
        self.assertEqual(balancers[2].name, "Third Loadbalancer")
        self.assertEqual(balancers[2].id, "8")

    def test_create_balancer(self):
        balancer = self.driver.create_balancer(name='test2',
                                               port=80,
                                               algorithm=Algorithm.ROUND_ROBIN,
                                               members=(
                                                   Member(
                                                       None, '10.1.0.10', 80,
                                                       extra={'condition': MemberCondition.DISABLED,
                                                              'weight': 10}),
                                                   Member(None, '10.1.0.11', 80))
                                               )

        self.assertEqual(balancer.name, 'test2')
        self.assertEqual(balancer.id, '8290')

    def test_ex_create_balancer(self):
        RackspaceLBDriver.connectionCls.conn_classes = (None,
                                                        RackspaceLBWithVIPMockHttp)
        RackspaceLBMockHttp.type = None
        driver = RackspaceLBDriver('user', 'key')
        balancer = driver.ex_create_balancer(name='test2',
                                             port=80,
                                             algorithm=Algorithm.ROUND_ROBIN,
                                             members=(
                                                 Member(
                                                     None, '10.1.0.11', 80),),
                                             vip='12af'
                                             )

        self.assertEqual(balancer.name, 'test2')
        self.assertEqual(balancer.id, '8290')

    def test_destroy_balancer(self):
        balancer = self.driver.list_balancers()[0]

        ret = self.driver.destroy_balancer(balancer)
        self.assertTrue(ret)

    def test_ex_destroy_balancers(self):
        balancers = self.driver.list_balancers()
        ret = self.driver.ex_destroy_balancers(balancers)
        self.assertTrue(ret)

    def test_get_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='8290')

        self.assertEqual(balancer.name, 'test2')
        self.assertEqual(balancer.id, '8290')

    def test_get_balancer_extra_vips(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        self.assertEqual(balancer.extra["virtualIps"],
                         [{"address": "50.56.49.149",
                           "id": 2359,
                           "type": "PUBLIC",
                           "ipVersion": "IPV4"}])

    def test_get_balancer_extra_public_source_ipv4(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        self.assertEqual(balancer.extra["ipv4PublicSource"], '184.106.100.25')

    def test_get_balancer_extra_public_source_ipv6(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        self.assertEqual(balancer.extra["ipv6PublicSource"],
                         '2001:4801:7901::6/64')

    def test_get_balancer_extra_private_source_ipv4(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        self.assertEqual(balancer.extra["ipv4PrivateSource"], '10.183.252.25')

    def test_get_balancer_extra_members(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.extra['members']
        self.assertEqual(3, len(members))
        self.assertEqual('10.1.0.11', members[0].ip)
        self.assertEqual('10.1.0.10', members[1].ip)
        self.assertEqual('10.1.0.9', members[2].ip)

    def test_get_balancer_extra_created(self):
        balancer = self.driver.get_balancer(balancer_id='8290')

        created_8290 = datetime.datetime(2011, 4, 7, 16, 27, 50)
        self.assertEqual(created_8290, balancer.extra['created'])

    def test_get_balancer_extra_updated(self):
        balancer = self.driver.get_balancer(balancer_id='8290')

        updated_8290 = datetime.datetime(2011, 4, 7, 16, 28, 12)
        self.assertEqual(updated_8290, balancer.extra['updated'])

    def test_get_balancer_extra_access_list(self):
        balancer = self.driver.get_balancer(balancer_id='94698')

        access_list = balancer.extra['accessList']

        self.assertEqual(3, len(access_list))
        self.assertEqual(2883, access_list[0].id)
        self.assertEqual("0.0.0.0/0", access_list[0].address)
        self.assertEqual(RackspaceAccessRuleType.DENY,
                         access_list[0].rule_type)

        self.assertEqual(2884, access_list[1].id)
        self.assertEqual("2001:4801:7901::6/64",
                         access_list[1].address)
        self.assertEqual(RackspaceAccessRuleType.ALLOW,
                         access_list[1].rule_type)

        self.assertEqual(3006, access_list[2].id)
        self.assertEqual("8.8.8.8/0", access_list[2].address)
        self.assertEqual(RackspaceAccessRuleType.DENY,
                         access_list[2].rule_type)

    def test_get_balancer_algorithm(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        self.assertEqual(balancer.extra["algorithm"], Algorithm.RANDOM)

    def test_get_balancer_protocol(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        self.assertEqual(balancer.extra['protocol'], 'HTTP')

    def test_get_balancer_weighted_round_robin_algorithm(self):
        balancer = self.driver.get_balancer(balancer_id='94692')
        self.assertEqual(balancer.extra["algorithm"],
                         Algorithm.WEIGHTED_ROUND_ROBIN)

    def test_get_balancer_weighted_least_connections_algorithm(self):
        balancer = self.driver.get_balancer(balancer_id='94693')
        self.assertEqual(balancer.extra["algorithm"],
                         Algorithm.WEIGHTED_LEAST_CONNECTIONS)

    def test_get_balancer_unknown_algorithm(self):
        balancer = self.driver.get_balancer(balancer_id='94694')
        self.assertFalse('algorithm' in balancer.extra)

    def test_get_balancer_connect_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        balancer_health_monitor = balancer.extra["healthMonitor"]

        self.assertEqual(balancer_health_monitor.type, "CONNECT")
        self.assertEqual(balancer_health_monitor.delay, 10)
        self.assertEqual(balancer_health_monitor.timeout, 5)
        self.assertEqual(balancer_health_monitor.attempts_before_deactivation,
                         2)

    def test_get_balancer_http_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='94696')
        balancer_health_monitor = balancer.extra["healthMonitor"]

        self.assertEqual(balancer_health_monitor.type, "HTTP")
        self.assertEqual(balancer_health_monitor.delay, 10)
        self.assertEqual(balancer_health_monitor.timeout, 5)
        self.assertEqual(balancer_health_monitor.attempts_before_deactivation,
                         2)
        self.assertEqual(balancer_health_monitor.path, "/")
        self.assertEqual(balancer_health_monitor.status_regex,
                         "^[234][0-9][0-9]$")
        self.assertEqual(balancer_health_monitor.body_regex,
                         "Hello World!")

    def test_get_balancer_https_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='94697')
        balancer_health_monitor = balancer.extra["healthMonitor"]

        self.assertEqual(balancer_health_monitor.type, "HTTPS")
        self.assertEqual(balancer_health_monitor.delay, 15)
        self.assertEqual(balancer_health_monitor.timeout, 12)
        self.assertEqual(balancer_health_monitor.attempts_before_deactivation,
                         5)
        self.assertEqual(balancer_health_monitor.path, "/test")
        self.assertEqual(balancer_health_monitor.status_regex,
                         "^[234][0-9][0-9]$")
        self.assertEqual(balancer_health_monitor.body_regex, "abcdef")

    def test_get_balancer_connection_throttle(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        balancer_connection_throttle = balancer.extra["connectionThrottle"]

        self.assertEqual(balancer_connection_throttle.min_connections, 50)
        self.assertEqual(balancer_connection_throttle.max_connections, 200)
        self.assertEqual(balancer_connection_throttle.max_connection_rate, 50)
        self.assertEqual(balancer_connection_throttle.rate_interval_seconds,
                         10)

    def test_get_session_persistence(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        self.assertEqual(balancer.extra["sessionPersistenceType"],
                         "HTTP_COOKIE")

    def test_get_connection_logging(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        self.assertEqual(balancer.extra["connectionLoggingEnabled"], True)

    def test_get_error_page(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        error_page = self.driver.ex_get_balancer_error_page(balancer)
        self.assertTrue("The service is temporarily unavailable" in error_page)

    def test_get_access_list(self):
        balancer = self.driver.get_balancer(balancer_id='18940')
        deny_rule, allow_rule = self.driver.ex_balancer_access_list(balancer)

        self.assertEqual(deny_rule.id, 2883)
        self.assertEqual(deny_rule.rule_type, RackspaceAccessRuleType.DENY)
        self.assertEqual(deny_rule.address, "0.0.0.0/0")

        self.assertEqual(allow_rule.id, 2884)
        self.assertEqual(allow_rule.address, "2001:4801:7901::6/64")
        self.assertEqual(allow_rule.rule_type, RackspaceAccessRuleType.ALLOW)

    def test_ex_create_balancer_access_rule(self):
        balancer = self.driver.get_balancer(balancer_id='94698')

        rule = RackspaceAccessRule(rule_type=RackspaceAccessRuleType.DENY,
                                   address='0.0.0.0/0')

        rule = self.driver.ex_create_balancer_access_rule(balancer, rule)

        self.assertEqual(2883, rule.id)

    def test_ex_create_balancer_access_rule_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94698')

        rule = RackspaceAccessRule(rule_type=RackspaceAccessRuleType.DENY,
                                   address='0.0.0.0/0')

        resp = self.driver.ex_create_balancer_access_rule_no_poll(balancer,
                                                                  rule)

        self.assertTrue(resp)

    def test_ex_create_balancer_access_rules(self):
        balancer = self.driver.get_balancer(balancer_id='94699')

        rules = [RackspaceAccessRule(rule_type=RackspaceAccessRuleType.ALLOW,
                                     address='2001:4801:7901::6/64'),
                 RackspaceAccessRule(rule_type=RackspaceAccessRuleType.DENY,
                                     address='8.8.8.8/0')]

        rules = self.driver.ex_create_balancer_access_rules(balancer, rules)

        self.assertEqual(2, len(rules))
        self.assertEqual(2884, rules[0].id)
        self.assertEqual(3006, rules[1].id)

    def test_ex_create_balancer_access_rules_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94699')

        rules = [RackspaceAccessRule(rule_type=RackspaceAccessRuleType.ALLOW,
                                     address='2001:4801:7901::6/64'),
                 RackspaceAccessRule(rule_type=RackspaceAccessRuleType.DENY,
                                     address='8.8.8.8/0')]

        resp = self.driver.ex_create_balancer_access_rules_no_poll(balancer,
                                                                   rules)

        self.assertTrue(resp)

    def test_ex_destroy_balancer_access_rule(self):
        balancer = self.driver.get_balancer(balancer_id='94698')

        rule = RackspaceAccessRule(id='1007',
                                   rule_type=RackspaceAccessRuleType.ALLOW,
                                   address="10.45.13.5/12"
                                   )

        balancer = self.driver.ex_destroy_balancer_access_rule(balancer, rule)

        rule_ids = [r.id for r in balancer.extra['accessList']]

        self.assertTrue(1007 not in rule_ids)

    def test_ex_destroy_balancer_access_rule_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94698')

        rule = RackspaceAccessRule(id=1007,
                                   rule_type=RackspaceAccessRuleType.ALLOW,
                                   address="10.45.13.5/12"
                                   )

        resp = self.driver.ex_destroy_balancer_access_rule_no_poll(balancer,
                                                                   rule)

        self.assertTrue(resp)

    def test_ex_destroy_balancer_access_rules(self):
        balancer = self.driver.get_balancer(balancer_id='94699')
        balancer = self.driver.ex_destroy_balancer_access_rules(balancer,
                                                                balancer.extra['accessList'])

        self.assertEqual('94699', balancer.id)

    def test_ex_destroy_balancer_access_rules_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94699')

        resp = self.driver.ex_destroy_balancer_access_rules_no_poll(balancer,
                                                                    balancer.extra['accessList'])

        self.assertTrue(resp)

    def test_ex_update_balancer_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        monitor = RackspaceHealthMonitor(type='CONNECT', delay=10, timeout=5,
                                         attempts_before_deactivation=2)

        balancer = self.driver.ex_update_balancer_health_monitor(
            balancer, monitor)
        updated_monitor = balancer.extra['healthMonitor']

        self.assertEqual('CONNECT', updated_monitor.type)
        self.assertEqual(10, updated_monitor.delay)
        self.assertEqual(5, updated_monitor.timeout)
        self.assertEqual(2, updated_monitor.attempts_before_deactivation)

    def test_ex_update_balancer_http_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='94696')
        monitor = RackspaceHTTPHealthMonitor(type='HTTP', delay=10, timeout=5,
                                             attempts_before_deactivation=2,
                                             path='/',
                                             status_regex='^[234][0-9][0-9]$',
                                             body_regex='Hello World!')

        balancer = self.driver.ex_update_balancer_health_monitor(
            balancer, monitor)
        updated_monitor = balancer.extra['healthMonitor']

        self.assertEqual('HTTP', updated_monitor.type)
        self.assertEqual(10, updated_monitor.delay)
        self.assertEqual(5, updated_monitor.timeout)
        self.assertEqual(2, updated_monitor.attempts_before_deactivation)
        self.assertEqual('/', updated_monitor.path)
        self.assertEqual('^[234][0-9][0-9]$', updated_monitor.status_regex)
        self.assertEqual('Hello World!', updated_monitor.body_regex)

    def test_ex_update_balancer_health_monitor_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        monitor = RackspaceHealthMonitor(type='CONNECT', delay=10, timeout=5,
                                         attempts_before_deactivation=2)

        resp = self.driver.ex_update_balancer_health_monitor_no_poll(balancer,
                                                                     monitor)

        self.assertTrue(resp)

    def test_ex_update_balancer_http_health_monitor_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94696')
        monitor = RackspaceHTTPHealthMonitor(type='HTTP', delay=10, timeout=5,
                                             attempts_before_deactivation=2,
                                             path='/',
                                             status_regex='^[234][0-9][0-9]$',
                                             body_regex='Hello World!')

        resp = self.driver.ex_update_balancer_health_monitor_no_poll(balancer,
                                                                     monitor)

        self.assertTrue(resp)

    def test_ex_update_balancer_http_health_monitor_with_no_option_body_regex(self):
        balancer = self.driver.get_balancer(balancer_id='94700')
        monitor = RackspaceHTTPHealthMonitor(type='HTTP', delay=10, timeout=5,
                                             attempts_before_deactivation=2,
                                             path='/',
                                             status_regex='^[234][0-9][0-9]$',
                                             body_regex='')

        balancer = self.driver.ex_update_balancer_health_monitor(
            balancer, monitor)
        updated_monitor = balancer.extra['healthMonitor']

        self.assertEqual('HTTP', updated_monitor.type)
        self.assertEqual(10, updated_monitor.delay)
        self.assertEqual(5, updated_monitor.timeout)
        self.assertEqual(2, updated_monitor.attempts_before_deactivation)
        self.assertEqual('/', updated_monitor.path)
        self.assertEqual('^[234][0-9][0-9]$', updated_monitor.status_regex)
        self.assertEqual('', updated_monitor.body_regex)

    def test_ex_disable_balancer_health_monitor(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        balancer = self.driver.ex_disable_balancer_health_monitor(balancer)

        self.assertTrue('healthMonitor' not in balancer.extra)

    def test_ex_disable_balancer_health_monitor_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        resp = self.driver.ex_disable_balancer_health_monitor_no_poll(balancer)

        self.assertTrue(resp)

    def test_ex_update_balancer_connection_throttle(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        connection_throttle = RackspaceConnectionThrottle(max_connections=200,
                                                          min_connections=50,
                                                          max_connection_rate=50,
                                                          rate_interval_seconds=10)

        balancer = self.driver.ex_update_balancer_connection_throttle(balancer,
                                                                      connection_throttle)
        updated_throttle = balancer.extra['connectionThrottle']

        self.assertEqual(200, updated_throttle.max_connections)
        self.assertEqual(50, updated_throttle.min_connections)
        self.assertEqual(50, updated_throttle.max_connection_rate)
        self.assertEqual(10, updated_throttle.rate_interval_seconds)

    def test_ex_update_balancer_connection_throttle_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        connection_throttle = RackspaceConnectionThrottle(max_connections=200,
                                                          min_connections=50,
                                                          max_connection_rate=50,
                                                          rate_interval_seconds=10)

        resp = self.driver.ex_update_balancer_connection_throttle_no_poll(
            balancer, connection_throttle)

        self.assertTrue(resp)

    def test_ex_disable_balancer_connection_throttle(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        balancer = self.driver.ex_disable_balancer_connection_throttle(
            balancer)

        self.assertTrue('connectionThrottle' not in balancer.extra)

    def test_ex_disable_balancer_connection_throttle_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        resp = self.driver.ex_disable_balancer_connection_throttle_no_poll(
            balancer)

        self.assertTrue(resp)

    def test_ex_enable_balancer_connection_logging(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        balancer = self.driver.ex_enable_balancer_connection_logging(
            balancer)

        self.assertTrue(balancer.extra["connectionLoggingEnabled"])

    def test_ex_enable_balancer_connection_logging_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        resp = self.driver.ex_enable_balancer_connection_logging_no_poll(
            balancer)

        self.assertTrue(resp)

    def test_ex_disable_balancer_connection_logging(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        balancer = self.driver.ex_disable_balancer_connection_logging(
            balancer
        )

        self.assertFalse(balancer.extra["connectionLoggingEnabled"])

    def test_ex_disable_balancer_connection_logging_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        resp = self.driver.ex_disable_balancer_connection_logging_no_poll(
            balancer
        )

        self.assertTrue(resp)

    def test_ex_enable_balancer_session_persistence(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        balancer = self.driver.ex_enable_balancer_session_persistence(balancer)

        persistence_type = balancer.extra['sessionPersistenceType']
        self.assertEqual('HTTP_COOKIE', persistence_type)

    def test_ex_enable_balancer_session_persistence_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        resp = self.driver.ex_enable_balancer_session_persistence_no_poll(
            balancer)

        self.assertTrue(resp)

    def test_disable_balancer_session_persistence(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        balancer = self.driver.ex_disable_balancer_session_persistence(
            balancer)

        self.assertTrue('sessionPersistenceType' not in balancer.extra)

    def test_disable_balancer_session_persistence_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        resp = self.driver.ex_disable_balancer_session_persistence_no_poll(
            balancer)

        self.assertTrue(resp)

    def test_ex_update_balancer_error_page(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        content = "<html>Generic Error Page</html>"
        balancer = self.driver.ex_update_balancer_error_page(
            balancer, content)

        error_page_content = self.driver.ex_get_balancer_error_page(balancer)
        self.assertEqual(content, error_page_content)

    def test_ex_update_balancer_error_page_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        content = "<html>Generic Error Page</html>"
        resp = self.driver.ex_update_balancer_error_page_no_poll(
            balancer, content)

        self.assertTrue(resp)

    def test_ex_disable_balancer_custom_error_page_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='94695')
        resp = self.driver.ex_disable_balancer_custom_error_page_no_poll(
            balancer)

        self.assertTrue(resp)

    def test_ex_disable_balancer_custom_error_page(self):
        fixtures = LoadBalancerFileFixtures('rackspace')
        error_page_fixture = json.loads(
            fixtures.load('error_page_default.json'))

        default_error_page = error_page_fixture['errorpage']['content']

        balancer = self.driver.get_balancer(balancer_id='94695')
        balancer = self.driver.ex_disable_balancer_custom_error_page(balancer)

        error_page_content = self.driver.ex_get_balancer_error_page(balancer)
        self.assertEqual(default_error_page, error_page_content)

    def test_balancer_list_members(self):
        expected = set(['10.1.0.10:80', '10.1.0.11:80', '10.1.0.9:8080'])
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        self.assertEqual(len(members), 3)
        self.assertEqual(members[0].balancer, balancer)
        self.assertEqual(expected, set(["%s:%s" % (member.ip, member.port) for
                                        member in members]))

    def test_balancer_members_extra_weight(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        self.assertEqual(12, members[0].extra['weight'])
        self.assertEqual(8, members[1].extra['weight'])

    def test_balancer_members_extra_condition(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        self.assertEqual(MemberCondition.ENABLED,
                         members[0].extra['condition'])
        self.assertEqual(MemberCondition.DISABLED,
                         members[1].extra['condition'])
        self.assertEqual(MemberCondition.DRAINING,
                         members[2].extra['condition'])

    def test_balancer_members_extra_status(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        self.assertEqual('ONLINE', members[0].extra['status'])
        self.assertEqual('OFFLINE', members[1].extra['status'])
        self.assertEqual('DRAINING', members[2].extra['status'])

    def test_balancer_attach_member(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        extra = {'condition': MemberCondition.DISABLED,
                 'weight': 10}
        member = balancer.attach_member(Member(None, ip='10.1.0.12',
                                               port='80', extra=extra))

        self.assertEqual(member.ip, '10.1.0.12')
        self.assertEqual(member.port, 80)

    def test_balancer_attach_member_with_no_condition_specified(self):
        balancer = self.driver.get_balancer(balancer_id='8291')
        member = balancer.attach_member(Member(None, ip='10.1.0.12',
                                               port='80'))

        self.assertEqual(member.ip, '10.1.0.12')
        self.assertEqual(member.port, 80)

    def test_balancer_attach_members(self):
        balancer = self.driver.get_balancer(balancer_id='8292')
        members = [Member(None, ip='10.1.0.12', port='80'),
                   Member(None, ip='10.1.0.13', port='80')]

        attached_members = self.driver.ex_balancer_attach_members(balancer,
                                                                  members)

        first_member = attached_members[0]
        second_member = attached_members[1]
        self.assertEqual(first_member.ip, '10.1.0.12')
        self.assertEqual(first_member.port, 80)
        self.assertEqual(second_member.ip, '10.1.0.13')
        self.assertEqual(second_member.port, 80)

    def test_balancer_detach_member(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        member = balancer.list_members()[0]

        ret = balancer.detach_member(member)
        self.assertTrue(ret)

    def test_ex_detach_members(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        balancer = self.driver.ex_balancer_detach_members(balancer, members)

        self.assertEqual('8290', balancer.id)

    def test_ex_detach_members_no_poll(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = balancer.list_members()

        ret = self.driver.ex_balancer_detach_members_no_poll(balancer, members)
        self.assertTrue(ret)

    def test_update_balancer_protocol(self):
        balancer = LoadBalancer(id='3130', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(
            balancer, protocol='HTTPS')
        self.assertEqual('HTTPS', updated_balancer.extra['protocol'])

    def test_update_balancer_protocol_to_imapv2(self):
        balancer = LoadBalancer(id='3135', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(
            balancer, protocol='imapv2')
        self.assertEqual('IMAPv2', updated_balancer.extra['protocol'])

    def test_update_balancer_protocol_to_imapv3(self):
        balancer = LoadBalancer(id='3136', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(
            balancer, protocol='IMAPV3')
        self.assertEqual('IMAPv3', updated_balancer.extra['protocol'])

    def test_update_balancer_protocol_to_imapv4(self):
        balancer = LoadBalancer(id='3137', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(
            balancer, protocol='IMAPv4')
        self.assertEqual('IMAPv4', updated_balancer.extra['protocol'])

    def test_update_balancer_port(self):
        balancer = LoadBalancer(id='3131', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(balancer, port=1337)
        self.assertEqual(1337, updated_balancer.port)

    def test_update_balancer_name(self):
        balancer = LoadBalancer(id='3132', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(
            balancer, name='new_lb_name')
        self.assertEqual('new_lb_name', updated_balancer.name)

    def test_update_balancer_algorithm(self):
        balancer = LoadBalancer(id='3133', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        updated_balancer = self.driver.update_balancer(balancer,
                                                       algorithm=Algorithm.ROUND_ROBIN)
        self.assertEqual(
            Algorithm.ROUND_ROBIN, updated_balancer.extra['algorithm'])

    def test_update_balancer_bad_algorithm_exception(self):
        balancer = LoadBalancer(id='3134', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        try:
            self.driver.update_balancer(balancer,
                                        algorithm='HAVE_MERCY_ON_OUR_SERVERS')
        except LibcloudError:
            pass
        else:
            self.fail(
                'Should have thrown an exception with bad algorithm value')

    def test_ex_update_balancer_no_poll_protocol(self):
        balancer = LoadBalancer(id='3130', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        action_succeeded = self.driver.ex_update_balancer_no_poll(
            balancer,
            protocol='HTTPS')
        self.assertTrue(action_succeeded)

    def test_ex_update_balancer_no_poll_port(self):
        balancer = LoadBalancer(id='3131', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        action_succeeded = self.driver.ex_update_balancer_no_poll(
            balancer,
            port=1337)
        self.assertTrue(action_succeeded)

    def test_ex_update_balancer_no_poll_name(self):
        balancer = LoadBalancer(id='3132', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)

        action_succeeded = self.driver.ex_update_balancer_no_poll(
            balancer,
            name='new_lb_name')
        self.assertTrue(action_succeeded)

    def test_ex_update_balancer_no_poll_algorithm(self):
        balancer = LoadBalancer(id='3133', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        action_succeeded = self.driver.ex_update_balancer_no_poll(balancer,
                                                                  algorithm=Algorithm.ROUND_ROBIN)
        self.assertTrue(action_succeeded)

    def test_ex_update_balancer_no_poll_bad_algorithm_exception(self):
        balancer = LoadBalancer(id='3134', name='LB_update',
                                state='PENDING_UPDATE', ip='10.34.4.3',
                                port=80, driver=self.driver)
        try:
            self.driver.update_balancer(balancer,
                                        algorithm='HAVE_MERCY_ON_OUR_SERVERS')
        except LibcloudError:
            pass
        else:
            self.fail('Should have thrown exception with bad algorithm value')

    def test_ex_update_balancer_member_extra_attributes(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = self.driver.balancer_list_members(balancer)

        first_member = members[0]

        member = self.driver.ex_balancer_update_member(balancer, first_member,
                                                       condition=MemberCondition.ENABLED, weight=12)

        self.assertEqual(MemberCondition.ENABLED, member.extra['condition'])
        self.assertEqual(12, member.extra['weight'])

    def test_ex_update_balancer_member_no_poll_extra_attributes(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        members = self.driver.balancer_list_members(balancer)

        first_member = members[0]

        resp = self.driver.ex_balancer_update_member_no_poll(
            balancer, first_member,
            condition=MemberCondition.ENABLED, weight=12)
        self.assertTrue(resp)

    def test_ex_list_current_usage(self):
        balancer = self.driver.get_balancer(balancer_id='8290')
        usage = self.driver.ex_list_current_usage(balancer=balancer)
        self.assertEqual(
            usage['loadBalancerUsageRecords'][0]['incomingTransferSsl'],
            6182163)


class RackspaceUKLBTests(RackspaceLBTests):

    def setUp(self):
        RackspaceLBDriver.connectionCls.conn_classes = (None,
                                                        RackspaceLBMockHttp)
        RackspaceLBMockHttp.type = None
        self.driver = RackspaceUKLBDriver('user', 'key')
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()


class RackspaceLBMockHttp(MockHttpTestCase):
    fixtures = LoadBalancerFileFixtures('rackspace')
    auth_fixtures = OpenStackFixtures()

    def _v2_0_tokens(self, method, url, body, headers):
        body = self.fixtures.load('_v2_0__auth.json')
        return (httplib.OK, body, headers,
                httplib.responses[httplib.OK])

    def _v1_0_11111_loadbalancers_protocols(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_loadbalancers_protocols.json')
        return (httplib.ACCEPTED, body, {},
                httplib.responses[httplib.ACCEPTED])

    def _v1_0_11111_loadbalancers_algorithms(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers_algorithms.json')
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == "POST":
            json_body = json.loads(body)

            loadbalancer_json = json_body['loadBalancer']
            member_1_json, member_2_json = loadbalancer_json['nodes']

            self.assertEqual(loadbalancer_json['protocol'], 'HTTP')
            self.assertEqual(loadbalancer_json['algorithm'], 'ROUND_ROBIN')
            self.assertEqual(loadbalancer_json['virtualIps'][0]['type'],
                             'PUBLIC')
            self.assertEqual(member_1_json['condition'], 'DISABLED')
            self.assertEqual(member_1_json['weight'], 10)
            self.assertEqual(member_2_json['condition'], 'ENABLED')

            body = self.fixtures.load('v1_slug_loadbalancers_post.json')
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])
        elif method == 'DELETE':
            balancers = self.fixtures.load('v1_slug_loadbalancers.json')
            balancers_json = json.loads(balancers)

            for balancer in balancers_json['loadBalancers']:
                id = balancer['id']
                self.assertTrue(urlencode([('id', id)]) in url,
                                msg='Did not delete balancer with id %d' % id)

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_EX_MEMBER_ADDRESS(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_loadbalancers_nodeaddress.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_0_11111_loadbalancers_8155(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers_8290.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_nodes(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers_8290_nodes.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == "POST":
            json_body = json.loads(body)
            json_node = json_body['nodes'][0]
            self.assertEqual('DISABLED', json_node['condition'])
            self.assertEqual(10, json_node['weight'])
            response_body = self.fixtures.load(
                'v1_slug_loadbalancers_8290_nodes_post.json')
            return (httplib.ACCEPTED, response_body, {},
                    httplib.responses[httplib.ACCEPTED])
        elif method == "DELETE":
            nodes = self.fixtures.load('v1_slug_loadbalancers_8290_nodes.json')
            json_nodes = json.loads(nodes)

            for node in json_nodes['nodes']:
                id = node['id']
                self.assertTrue(urlencode([('id', id)]) in url,
                                msg='Did not delete member with id %d' % id)

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8291(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers_8291.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8291_nodes(self, method, url, body, headers):
        if method == "POST":
            json_body = json.loads(body)
            json_node = json_body['nodes'][0]
            self.assertEqual('ENABLED', json_node['condition'])
            response_body = self.fixtures.load(
                'v1_slug_loadbalancers_8290_nodes_post.json')
            return (httplib.ACCEPTED, response_body, {},
                    httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8292(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers_8292.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8292_nodes(self, method, url, body, headers):
        if method == "POST":
            json_body = json.loads(body)
            json_node_1 = json_body['nodes'][0]
            json_node_2 = json_body['nodes'][1]
            self.assertEqual('10.1.0.12', json_node_1['address'])
            self.assertEqual('10.1.0.13', json_node_2['address'])
            response_body = self.fixtures.load(
                'v1_slug_loadbalancers_8292_nodes_post.json')
            return (httplib.ACCEPTED, response_body, {},
                    httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_nodes_30944(self, method, url, body, headers):
        if method == "PUT":
            json_body = json.loads(body)
            self.assertEqual('ENABLED', json_body['condition'])
            self.assertEqual(12, json_body['weight'])
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])
        elif method == "DELETE":
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_healthmonitor(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_connectionthrottle(self, method, url, body, headers):
        if method == 'DELETE':
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_connectionlogging(self, method, url, body, headers):
        # Connection Logging uses a PUT to disable connection logging
        if method == 'PUT':
            json_body = json.loads(body)
            self.assertFalse(json_body["connectionLogging"]["enabled"])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_sessionpersistence(self, method, url, body, headers):
        if method == 'DELETE':
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_errorpage(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'v1_slug_loadbalancers_8290_errorpage.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == 'PUT':
            json_body = json.loads(body)

            self.assertEqual('<html>Generic Error Page</html>',
                             json_body['errorpage']['content'])
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_18940(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_18940_ex_public_ips.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_18945(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_18945_ex_public_ips.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_18940_errorpage(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_18940_errorpage.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_18940_accesslist(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'v1_slug_loadbalancers_18940_accesslist.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_18941(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_18941_ex_private_ips.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94692(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94692_weighted_round_robin.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94693(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94693_weighted_least_connections.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94694(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94694_unknown_algorithm.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94695_full_details.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695_healthmonitor(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            self.assertEqual('CONNECT', json_body['type'])
            self.assertEqual(10, json_body['delay'])
            self.assertEqual(5, json_body['timeout'])
            self.assertEqual(2, json_body['attemptsBeforeDeactivation'])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695_connectionthrottle(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            self.assertEqual(50, json_body['minConnections'])
            self.assertEqual(200, json_body['maxConnections'])
            self.assertEqual(50, json_body['maxConnectionRate'])
            self.assertEqual(10, json_body['rateInterval'])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695_connectionlogging(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            self.assertTrue(json_body["connectionLogging"]["enabled"])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695_sessionpersistence(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            persistence_type = json_body[
                'sessionPersistence']['persistenceType']
            self.assertEqual('HTTP_COOKIE', persistence_type)

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94695_errorpage(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load("error_page_default.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == 'DELETE':
            return (httplib.OK, '', {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94696(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94696_http_health_monitor.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94696_healthmonitor(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            self.assertEqual('HTTP', json_body['type'])
            self.assertEqual(10, json_body['delay'])
            self.assertEqual(5, json_body['timeout'])
            self.assertEqual(2, json_body['attemptsBeforeDeactivation'])
            self.assertEqual('/', json_body['path'])
            self.assertEqual('^[234][0-9][0-9]$', json_body['statusRegex'])
            self.assertEqual('Hello World!', json_body['bodyRegex'])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94697(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94697_https_health_monitor.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94698(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94698_with_access_list.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94698_accesslist(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'v1_slug_loadbalancers_94698_accesslist.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == 'POST':
            json_body = json.loads(body)

            self.assertEqual('0.0.0.0/0', json_body['networkItem']['address'])
            self.assertEqual('DENY', json_body['networkItem']['type'])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94699(self, method, url, body, headers):
        if method == 'GET':
            # Use the same fixture for batch deletes as for single deletes
            body = self.fixtures.load(
                'v1_slug_loadbalancers_94698_with_access_list.json')
            json_body = json.loads(body)
            json_body['loadBalancer']['id'] = 94699

            updated_body = json.dumps(json_body)
            return (httplib.OK, updated_body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94699_accesslist(self, method, url, body, headers):
        if method == 'DELETE':
            fixture = 'v1_slug_loadbalancers_94698_with_access_list.json'
            fixture_json = json.loads(self.fixtures.load(fixture))
            access_list_json = fixture_json['loadBalancer']['accessList']

            for access_rule in access_list_json:
                id = access_rule['id']
                self.assertTrue(urlencode([('id', id)]) in url,
                                msg='Did not delete access rule with id %d' % id)

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])
        elif method == 'POST':

            json_body = json.loads(body)
            access_list = json_body['accessList']
            self.assertEqual('ALLOW', access_list[0]['type'])
            self.assertEqual('2001:4801:7901::6/64', access_list[0]['address'])
            self.assertEqual('DENY', access_list[1]['type'])
            self.assertEqual('8.8.8.8/0', access_list[1]['address'])

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94698_accesslist_1007(self, method, url, body, headers):
        if method == 'DELETE':
            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94700(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                "v1_slug_loadbalancers_94700_http_health_monitor_no_body_regex.json")
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_94700_healthmonitor(self, method, url, body, headers):
        if method == 'PUT':
            json_body = json.loads(body)

            self.assertEqual('HTTP', json_body['type'])
            self.assertEqual(10, json_body['delay'])
            self.assertEqual(5, json_body['timeout'])
            self.assertEqual(2, json_body['attemptsBeforeDeactivation'])
            self.assertEqual('/', json_body['path'])
            self.assertEqual('^[234][0-9][0-9]$', json_body['statusRegex'])
            self.assertFalse('bodyRegex' in json_body)

            return (httplib.ACCEPTED, '', {}, httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3130(self, method, url, body, headers):
        """ update_balancer(b, protocol='HTTPS'), then get_balancer('3130') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'protocol': 'HTTPS'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3130
            response_body['loadBalancer']['protocol'] = 'HTTPS'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3131(self, method, url, body, headers):
        """ update_balancer(b, port=443), then get_balancer('3131') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'port': 1337})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3131
            response_body['loadBalancer']['port'] = 1337
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3132(self, method, url, body, headers):
        """ update_balancer(b, name='new_lb_name'), then get_balancer('3132') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'name': 'new_lb_name'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3132
            response_body['loadBalancer']['name'] = 'new_lb_name'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3133(self, method, url, body, headers):
        """ update_balancer(b, algorithm='ROUND_ROBIN'), then get_balancer('3133') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'algorithm': 'ROUND_ROBIN'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3133
            response_body['loadBalancer']['algorithm'] = 'ROUND_ROBIN'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3134(self, method, url, body, headers):
        """ update.balancer(b, algorithm='HAVE_MERCY_ON_OUR_SERVERS') """
        if method == "PUT":
            return (httplib.BAD_REQUEST, "", {}, httplib.responses[httplib.BAD_REQUEST])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3135(self, method, url, body, headers):
        """ update_balancer(b, protocol='IMAPv3'), then get_balancer('3135') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'protocol': 'IMAPv2'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3135
            response_body['loadBalancer']['protocol'] = 'IMAPv2'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3136(self, method, url, body, headers):
        """ update_balancer(b, protocol='IMAPv3'), then get_balancer('3136') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'protocol': 'IMAPv3'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3136
            response_body['loadBalancer']['protocol'] = 'IMAPv3'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_3137(self, method, url, body, headers):
        """ update_balancer(b, protocol='IMAPv3'), then get_balancer('3137') """
        if method == "PUT":
            json_body = json.loads(body)
            self.assertDictEqual(json_body, {'protocol': 'IMAPv4'})
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        elif method == "GET":
            response_body = json.loads(
                self.fixtures.load("v1_slug_loadbalancers_3xxx.json"))
            response_body['loadBalancer']['id'] = 3137
            response_body['loadBalancer']['protocol'] = 'IMAPv4'
            return (httplib.OK, json.dumps(response_body), {}, httplib.responses[httplib.OK])
        raise NotImplementedError

    def _v1_0_11111_loadbalancers_8290_usage_current(self, method, url, body,
                                                     headers):
        if method == 'GET':
            body = self.fixtures.load(
                'v1_0_slug_loadbalancers_8290_usage_current.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        raise NotImplementedError


class RackspaceLBWithVIPMockHttp(MockHttpTestCase):
    fixtures = LoadBalancerFileFixtures('rackspace')
    auth_fixtures = OpenStackFixtures()

    def _v2_0_tokens(self, method, url, body, headers):
            body = self.fixtures.load('_v2_0__auth.json')
            return (httplib.OK, body, headers,
                    httplib.responses[httplib.OK])

    def _v1_0_11111_loadbalancers(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('v1_slug_loadbalancers.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == "POST":
            json_body = json.loads(body)
            loadbalancer_json = json_body['loadBalancer']

            self.assertEqual(loadbalancer_json['virtualIps'][0]['id'], '12af')

            body = self.fixtures.load('v1_slug_loadbalancers_post.json')
            return (httplib.ACCEPTED, body, {},
                    httplib.responses[httplib.ACCEPTED])

        raise NotImplementedError

if __name__ == "__main__":
    sys.exit(unittest.main())
