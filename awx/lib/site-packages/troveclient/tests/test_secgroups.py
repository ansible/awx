# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient.v1 import security_groups

"""
Unit tests for security_groups.py
"""


class SecGroupTest(testtools.TestCase):

    def setUp(self):
        super(SecGroupTest, self).setUp()
        self.orig__init = security_groups.SecurityGroup.__init__
        security_groups.SecurityGroup.__init__ = mock.Mock(return_value=None)
        self.security_group = security_groups.SecurityGroup()
        self.security_groups = security_groups.SecurityGroups(1)

    def tearDown(self):
        super(SecGroupTest, self).tearDown()
        security_groups.SecurityGroup.__init__ = self.orig__init

    def test___repr__(self):
        self.security_group.name = "security_group-1"
        self.assertEqual('<SecurityGroup: security_group-1>',
                         self.security_group.__repr__())

    def test_list(self):
        sec_group_list = ['secgroup1', 'secgroup2']
        self.security_groups.list = mock.Mock(return_value=sec_group_list)
        self.assertEqual(sec_group_list, self.security_groups.list())

    def test_get(self):
        def side_effect_func(path, inst):
            return path, inst

        self.security_groups._get = mock.Mock(side_effect=side_effect_func)
        self.security_group.id = 1
        self.assertEqual(('/security-groups/1', 'security_group'),
                         self.security_groups.get(self.security_group))


class SecGroupRuleTest(testtools.TestCase):

    def setUp(self):
        super(SecGroupRuleTest, self).setUp()
        self.orig__init = security_groups.SecurityGroupRule.__init__
        security_groups.SecurityGroupRule.__init__ = mock.Mock(
            return_value=None
        )
        security_groups.SecurityGroupRules.__init__ = mock.Mock(
            return_value=None
        )
        self.security_group_rule = security_groups.SecurityGroupRule()
        self.security_group_rules = security_groups.SecurityGroupRules()

    def tearDown(self):
        super(SecGroupRuleTest, self).tearDown()
        security_groups.SecurityGroupRule.__init__ = self.orig__init

    def test___repr__(self):
        self.security_group_rule.group_id = 1
        self.security_group_rule.protocol = "tcp"
        self.security_group_rule.from_port = 80
        self.security_group_rule.to_port = 80
        self.security_group_rule.cidr = "0.0.0.0//0"
        representation = (
            "<SecurityGroupRule: "
            "( Security Group id: %d, "
            "Protocol: %s, From_Port: %d, "
            "To_Port: %d,  CIDR: %s )>"
            % (1, "tcp", 80, 80, "0.0.0.0//0")
        )

        self.assertEqual(representation,
                         self.security_group_rule.__repr__())

    def test_create(self):
        def side_effect_func(path, body, inst, return_raw=True):
            return path, body, inst

        self.security_group_rules._create = mock.Mock(
            side_effect=side_effect_func
        )
        p, b, i = self.security_group_rules.create(1, "0.0.0.0//0")
        self.assertEqual("/security-group-rules", p)
        self.assertEqual("security_group_rule", i)
        self.assertEqual(1, b["security_group_rule"]["group_id"])
        self.assertEqual("0.0.0.0//0", b["security_group_rule"]["cidr"])

    def test_delete(self):
        resp = mock.Mock()
        resp.status = 200
        body = None
        self.security_group_rules.api = mock.Mock()
        self.security_group_rules.api.client = mock.Mock()
        self.security_group_rules.api.client.delete = mock.Mock(
            return_value=(resp, body)
        )
        self.security_group_rules.delete(self.id)
        resp.status_code = 500
        self.assertRaises(Exception, self.security_group_rules.delete,
                          self.id)
