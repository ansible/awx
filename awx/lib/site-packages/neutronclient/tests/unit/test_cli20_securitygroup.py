#!/usr/bin/env python
# Copyright 2012 Red Hat
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

import sys

from mox3 import mox
import six

from neutronclient.common import exceptions
from neutronclient.common import utils
from neutronclient.neutron.v2_0 import securitygroup
from neutronclient.tests.unit import test_cli20


class CLITestV20SecurityGroupsJSON(test_cli20.CLITestV20Base):
    def test_create_security_group(self):
        """Create security group: webservers."""
        resource = 'security_group'
        cmd = securitygroup.CreateSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        name = 'webservers'
        myid = 'myid'
        args = [name, ]
        position_names = ['name']
        position_values = [name]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_security_group_tenant(self):
        """Create security group: webservers."""
        resource = 'security_group'
        cmd = securitygroup.CreateSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        name = 'webservers'
        description = 'my webservers'
        myid = 'myid'
        args = ['--tenant_id', 'tenant_id', '--description', description, name]
        position_names = ['name', 'description']
        position_values = [name, description]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values,
                                   tenant_id='tenant_id')

    def test_create_security_group_with_description(self):
        """Create security group: webservers."""
        resource = 'security_group'
        cmd = securitygroup.CreateSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        name = 'webservers'
        description = 'my webservers'
        myid = 'myid'
        args = [name, '--description', description]
        position_names = ['name', 'description']
        position_values = [name, description]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_security_groups(self):
        resources = "security_groups"
        cmd = securitygroup.ListSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_list_security_groups_pagination(self):
        resources = "security_groups"
        cmd = securitygroup.ListSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_security_groups_sort(self):
        resources = "security_groups"
        cmd = securitygroup.ListSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_security_groups_limit(self):
        resources = "security_groups"
        cmd = securitygroup.ListSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_security_group_id(self):
        resource = 'security_group'
        cmd = securitygroup.ShowSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])

    def test_show_security_group_id_name(self):
        resource = 'security_group'
        cmd = securitygroup.ShowSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_delete_security_group(self):
        """Delete security group: myid."""
        resource = 'security_group'
        cmd = securitygroup.DeleteSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_update_security_group(self):
        """Update security group: myid --name myname --description desc."""
        resource = 'security_group'
        cmd = securitygroup.UpdateSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname',
                                    '--description', 'mydescription'],
                                   {'name': 'myname',
                                    'description': 'mydescription'}
                                   )

    def test_update_security_group_with_unicode(self):
        resource = 'security_group'
        cmd = securitygroup.UpdateSecurityGroup(
            test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', u'\u7f51\u7edc',
                                    '--description', u'\u7f51\u7edc'],
                                   {'name': u'\u7f51\u7edc',
                                    'description': u'\u7f51\u7edc'}
                                   )

    def test_create_security_group_rule_full(self):
        """Create security group rule."""
        resource = 'security_group_rule'
        cmd = securitygroup.CreateSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        direction = 'ingress'
        ethertype = 'IPv4'
        protocol = 'tcp'
        port_range_min = '22'
        port_range_max = '22'
        remote_ip_prefix = '10.0.0.0/24'
        security_group_id = '1'
        remote_group_id = '1'
        args = ['--remote_ip_prefix', remote_ip_prefix, '--direction',
                direction, '--ethertype', ethertype, '--protocol', protocol,
                '--port_range_min', port_range_min, '--port_range_max',
                port_range_max, '--remote_group_id', remote_group_id,
                security_group_id]
        position_names = ['remote_ip_prefix', 'direction', 'ethertype',
                          'protocol', 'port_range_min', 'port_range_max',
                          'remote_group_id', 'security_group_id']
        position_values = [remote_ip_prefix, direction, ethertype, protocol,
                           port_range_min, port_range_max, remote_group_id,
                           security_group_id]
        self._test_create_resource(resource, cmd, None, myid, args,
                                   position_names, position_values)

    def test_delete_security_group_rule(self):
        """Delete security group rule: myid."""
        resource = 'security_group_rule'
        cmd = securitygroup.DeleteSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_list_security_group_rules(self):
        resources = "security_group_rules"
        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(securitygroup.ListSecurityGroupRule,
                                 "extend_list")
        securitygroup.ListSecurityGroupRule.extend_list(mox.IsA(list),
                                                        mox.IgnoreArg())
        self._test_list_resources(resources, cmd, True)

    def _test_extend_list(self, mox_calls, data):
        resources = "security_groups"

        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")

        cmd.get_client().MultipleTimes().AndReturn(self.client)
        path = getattr(self.client, resources + '_path')
        mox_calls(path, data)
        self.mox.ReplayAll()
        known_args, _vs = cmd.get_parser(
            'list' + resources).parse_known_args()

        cmd.extend_list(data, known_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def _build_test_data(self, data, excess=0):
        # Length of a query filter on security group rule id
        # in these testcases, id='secgroupid%02d' (with len(id)=12)
        sec_group_id_filter_len = 12

        response = []
        replace_rules = {'security_group_id': 'security_group',
                         'remote_group_id': 'remote_group'}

        search_opts = {'fields': ['id', 'name']}
        sec_group_ids = set()
        for rule in data:
            for key in replace_rules:
                if rule.get(key):
                    sec_group_ids.add(rule[key])
                    response.append({'id': rule[key], 'name': 'default'})
        sec_group_ids = list(sec_group_ids)

        result = []

        sec_group_count = len(sec_group_ids)
        max_size = ((sec_group_id_filter_len * sec_group_count) - excess)
        chunk_size = max_size // sec_group_id_filter_len

        for i in range(0, sec_group_count, chunk_size):
            search_opts['id'] = sec_group_ids[i: i + chunk_size]
            params = utils.safe_encode_dict(search_opts)
            resp_str = self.client.serialize({'security_groups': response})

            result.append({
                'filter': six.moves.urllib.parse.urlencode(params, doseq=1),
                'response': (test_cli20.MyResp(200), resp_str),
            })

        return result

    def test_extend_list(self):
        def mox_calls(path, data):
            responses = self._build_test_data(data)
            self.client.httpclient.request(
                test_cli20.MyUrlComparator(test_cli20.end_url(
                    path, responses[0]['filter']), self.client),
                'GET',
                body=None,
                headers=mox.ContainsKeyValue(
                    'X-Auth-Token', test_cli20.TOKEN)).AndReturn(
                        responses[0]['response'])

        data = [{'name': 'default',
                 'remote_group_id': 'remgroupid%02d' % i}
                for i in range(10)]
        data.append({'name': 'default', 'remote_group_id': None})
        self._test_extend_list(mox_calls, data)

    def test_extend_list_exceed_max_uri_len(self):
        def mox_calls(path, data):
            # 1 char of extra URI len will cause a split in 2 requests
            self.mox.StubOutWithMock(self.client.httpclient,
                                     '_check_uri_length')
            self.client.httpclient._check_uri_length(mox.IgnoreArg()).AndRaise(
                exceptions.RequestURITooLong(excess=1))
            responses = self._build_test_data(data, excess=1)

            for item in responses:
                self.client.httpclient._check_uri_length(
                    mox.IgnoreArg()).AndReturn(None)
                self.client.httpclient.request(
                    test_cli20.end_url(path, item['filter']),
                    'GET',
                    body=None,
                    headers=mox.ContainsKeyValue(
                        'X-Auth-Token', test_cli20.TOKEN)).AndReturn(
                            item['response'])

        data = [{'name': 'default',
                 'security_group_id': 'secgroupid%02d' % i,
                 'remote_group_id': 'remgroupid%02d' % i}
                for i in range(10)]
        data.append({'name': 'default',
                     'security_group_id': 'secgroupid10',
                     'remote_group_id': None})
        self._test_extend_list(mox_calls, data)

    def test_list_security_group_rules_pagination(self):
        resources = "security_group_rules"
        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(securitygroup.ListSecurityGroupRule,
                                 "extend_list")
        securitygroup.ListSecurityGroupRule.extend_list(mox.IsA(list),
                                                        mox.IgnoreArg())
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_security_group_rules_sort(self):
        resources = "security_group_rules"
        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(securitygroup.ListSecurityGroupRule,
                                 "extend_list")
        securitygroup.ListSecurityGroupRule.extend_list(mox.IsA(list),
                                                        mox.IgnoreArg())
        self._test_list_resources(resources, cmd,
                                  sort_key=["name", "id"],
                                  sort_dir=["asc", "desc"])

    def test_list_security_group_rules_limit(self):
        resources = "security_group_rules"
        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(securitygroup.ListSecurityGroupRule,
                                 "extend_list")
        securitygroup.ListSecurityGroupRule.extend_list(mox.IsA(list),
                                                        mox.IgnoreArg())
        self._test_list_resources(resources, cmd, page_size=1000)

    def test_show_security_group_rule(self):
        resource = 'security_group_rule'
        cmd = securitygroup.ShowSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])

    def _test_list_security_group_rules_extend(self, data=None, expected=None,
                                               args=(), conv=True,
                                               query_field=False):
        def setup_list_stub(resources, data, query):
            reses = {resources: data}
            resstr = self.client.serialize(reses)
            resp = (test_cli20.MyResp(200), resstr)
            path = getattr(self.client, resources + '_path')
            self.client.httpclient.request(
                test_cli20.MyUrlComparator(
                    test_cli20.end_url(path, query),
                    self.client),
                'GET',
                body=None,
                headers=mox.ContainsKeyValue(
                    'X-Auth-Token', test_cli20.TOKEN)).AndReturn(resp)

        # Setup the default data
        _data = {'cols': ['id', 'security_group_id', 'remote_group_id'],
                 'data': [('ruleid1', 'myid1', 'myid1'),
                          ('ruleid2', 'myid2', 'myid3'),
                          ('ruleid3', 'myid2', 'myid2')]}
        _expected = {'cols': ['id', 'security_group', 'remote_group'],
                     'data': [('ruleid1', 'group1', 'group1'),
                              ('ruleid2', 'group2', 'group3'),
                              ('ruleid3', 'group2', 'group2')]}
        if data is None:
            data = _data
        list_data = [dict(zip(data['cols'], d)) for d in data['data']]
        if expected is None:
            expected = {}
        expected['cols'] = expected.get('cols', _expected['cols'])
        expected['data'] = expected.get('data', _expected['data'])

        cmd = securitygroup.ListSecurityGroupRule(
            test_cli20.MyApp(sys.stdout), None)
        self.mox.StubOutWithMock(cmd, 'get_client')
        self.mox.StubOutWithMock(self.client.httpclient, 'request')
        cmd.get_client().AndReturn(self.client)
        query = ''
        if query_field:
            query = '&'.join(['fields=' + f for f in data['cols']])
        setup_list_stub('security_group_rules', list_data, query)
        if conv:
            cmd.get_client().AndReturn(self.client)
            sec_ids = set()
            for n in data['data']:
                sec_ids.add(n[1])
                sec_ids.add(n[2])
            filters = ''
            for id in sec_ids:
                filters = filters + "&id=%s" % id
            setup_list_stub('security_groups',
                            [{'id': 'myid1', 'name': 'group1'},
                             {'id': 'myid2', 'name': 'group2'},
                             {'id': 'myid3', 'name': 'group3'}],
                            query='fields=id&fields=name' + filters)
        self.mox.ReplayAll()

        cmd_parser = cmd.get_parser('list_security_group_rules')
        parsed_args = cmd_parser.parse_args(args)
        result = cmd.get_data(parsed_args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        # Check columns
        self.assertEqual(result[0], expected['cols'])
        # Check data
        _result = [x for x in result[1]]
        self.assertEqual(len(_result), len(expected['data']))
        for res, exp in zip(_result, expected['data']):
            self.assertEqual(len(res), len(exp))
            self.assertEqual(res, exp)

    def test_list_security_group_rules_extend_source_id(self):
        self._test_list_security_group_rules_extend()

    def test_list_security_group_rules_extend_no_nameconv(self):
        expected = {'cols': ['id', 'security_group_id', 'remote_group_id'],
                    'data': [('ruleid1', 'myid1', 'myid1'),
                             ('ruleid2', 'myid2', 'myid3'),
                             ('ruleid3', 'myid2', 'myid2')]}
        args = ['--no-nameconv']
        self._test_list_security_group_rules_extend(expected=expected,
                                                    args=args, conv=False)

    def test_list_security_group_rules_extend_with_columns(self):
        args = '-c id -c security_group_id -c remote_group_id'.split()
        self._test_list_security_group_rules_extend(args=args)

    def test_list_security_group_rules_extend_with_columns_no_id(self):
        args = '-c id -c security_group -c remote_group'.split()
        self._test_list_security_group_rules_extend(args=args)

    def test_list_security_group_rules_extend_with_fields(self):
        args = '-F id -F security_group_id -F remote_group_id'.split()
        self._test_list_security_group_rules_extend(args=args,
                                                    query_field=True)

    def test_list_security_group_rules_extend_with_fields_no_id(self):
        args = '-F id -F security_group -F remote_group'.split()
        self._test_list_security_group_rules_extend(args=args,
                                                    query_field=True)


class CLITestV20SecurityGroupsXML(CLITestV20SecurityGroupsJSON):
    format = 'xml'
