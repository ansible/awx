# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

import contextlib
import itertools
import sys

import fixtures
from mox3 import mox
from oslo.utils import encodeutils
from oslotest import base
import requests
import six
import six.moves.urllib.parse as urlparse

from neutronclient.common import constants
from neutronclient.common import exceptions
from neutronclient.common import utils
from neutronclient.neutron import v2_0 as neutronV2_0
from neutronclient import shell
from neutronclient.v2_0 import client

API_VERSION = "2.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


@contextlib.contextmanager
def capture_std_streams():
    fake_stdout, fake_stderr = six.StringIO(), six.StringIO()
    stdout, stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = fake_stdout, fake_stderr
        yield fake_stdout, fake_stderr
    finally:
        sys.stdout, sys.stderr = stdout, stderr


class FakeStdout:

    def __init__(self):
        self.content = []

    def write(self, text):
        self.content.append(text)

    def make_string(self):
        result = ''
        for line in self.content:
            result = result + line
        return result


class MyResp(object):
    def __init__(self, status_code, headers=None, reason=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.reason = reason


class MyApp(object):
    def __init__(self, _stdout):
        self.stdout = _stdout


def end_url(path, query=None, format=FORMAT):
    _url_str = ENDURL + "/v" + API_VERSION + path + "." + format
    return query and _url_str + "?" + query or _url_str


class MyUrlComparator(mox.Comparator):
    def __init__(self, lhs, client):
        self.lhs = lhs
        self.client = client

    def equals(self, rhs):
        lhsp = urlparse.urlparse(self.lhs)
        rhsp = urlparse.urlparse(rhs)

        return (lhsp.scheme == rhsp.scheme and
                lhsp.netloc == rhsp.netloc and
                lhsp.path == rhsp.path and
                urlparse.parse_qs(lhsp.query) == urlparse.parse_qs(rhsp.query))

    def __str__(self):
        if self.client and self.client.format != FORMAT:
            lhs_parts = self.lhs.split("?", 1)
            if len(lhs_parts) == 2:
                lhs = ("%s.%s?%s" % (lhs_parts[0][:-4],
                                     self.client.format,
                                     lhs_parts[1]))
            else:
                lhs = ("%s.%s" % (lhs_parts[0][:-4],
                                  self.client.format))
            return lhs
        return self.lhs

    def __repr__(self):
        return str(self)


class MyComparator(mox.Comparator):
    def __init__(self, lhs, client):
        self.lhs = lhs
        self.client = client

    def _com_dict(self, lhs, rhs):
        if len(lhs) != len(rhs):
            return False
        for key, value in six.iteritems(lhs):
            if key not in rhs:
                return False
            rhs_value = rhs[key]
            if not self._com(value, rhs_value):
                return False
        return True

    def _com_list(self, lhs, rhs):
        if len(lhs) != len(rhs):
            return False
        for lhs_value in lhs:
            if lhs_value not in rhs:
                return False
        return True

    def _com(self, lhs, rhs):
        if lhs is None:
            return rhs is None
        if isinstance(lhs, dict):
            if not isinstance(rhs, dict):
                return False
            return self._com_dict(lhs, rhs)
        if isinstance(lhs, list):
            if not isinstance(rhs, list):
                return False
            return self._com_list(lhs, rhs)
        if isinstance(lhs, tuple):
            if not isinstance(rhs, tuple):
                return False
            return self._com_list(lhs, rhs)
        return lhs == rhs

    def equals(self, rhs):
        if self.client:
            rhs = self.client.deserialize(rhs, 200)
        return self._com(self.lhs, rhs)

    def __repr__(self):
        if self.client:
            return self.client.serialize(self.lhs)
        return str(self.lhs)


class CLITestV20Base(base.BaseTestCase):

    format = 'json'
    test_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    id_field = 'id'

    def _find_resourceid(self, client, resource, name_or_id,
                         cmd_resource=None, parent_id=None):
        return name_or_id

    def _get_attr_metadata(self):
        return self.metadata

    def setUp(self, plurals=None):
        """Prepare the test environment."""
        super(CLITestV20Base, self).setUp()
        client.Client.EXTED_PLURALS.update(constants.PLURALS)
        if plurals is not None:
            client.Client.EXTED_PLURALS.update(plurals)
        self.metadata = {'plurals': client.Client.EXTED_PLURALS,
                         'xmlns': constants.XML_NS_V20,
                         constants.EXT_NS: {'prefix':
                                            'http://xxxx.yy.com'}}
        self.mox = mox.Mox()
        self.endurl = ENDURL
        self.fake_stdout = FakeStdout()
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', self.fake_stdout))
        self.useFixture(fixtures.MonkeyPatch(
            'neutronclient.neutron.v2_0.find_resourceid_by_name_or_id',
            self._find_resourceid))
        self.useFixture(fixtures.MonkeyPatch(
            'neutronclient.neutron.v2_0.find_resourceid_by_id',
            self._find_resourceid))
        self.useFixture(fixtures.MonkeyPatch(
            'neutronclient.v2_0.client.Client.get_attr_metadata',
            self._get_attr_metadata))
        self.client = client.Client(token=TOKEN, endpoint_url=self.endurl)

    def _test_create_resource(self, resource, cmd, name, myid, args,
                              position_names, position_values,
                              tenant_id=None, tags=None, admin_state_up=True,
                              extra_body=None, cmd_resource=None,
                              parent_id=None, **kwargs):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        non_admin_status_resources = ['subnet', 'floatingip', 'security_group',
                                      'security_group_rule', 'qos_queue',
                                      'network_gateway', 'gateway_device',
                                      'credential', 'network_profile',
                                      'policy_profile', 'ikepolicy',
                                      'ipsecpolicy', 'metering_label',
                                      'metering_label_rule', 'net_partition']
        if not cmd_resource:
            cmd_resource = resource
        if (resource in non_admin_status_resources):
            body = {resource: {}, }
        else:
            body = {resource: {'admin_state_up': admin_state_up, }, }
        if tenant_id:
            body[resource].update({'tenant_id': tenant_id})
        if tags:
            body[resource].update({'tags': tags})
        if extra_body:
            body[resource].update(extra_body)
        body[resource].update(kwargs)

        for i in range(len(position_names)):
            body[resource].update({position_names[i]: position_values[i]})
        ress = {resource:
                {self.id_field: myid}, }
        if name:
            ress[resource].update({'name': name})
        self.client.format = self.format
        resstr = self.client.serialize(ress)
        # url method body
        resource_plural = neutronV2_0._get_resource_plural(cmd_resource,
                                                           self.client)
        path = getattr(self.client, resource_plural + "_path")
        if parent_id:
            path = path % parent_id
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            mox_body = MyComparator(body, self.client)
        else:
            mox_body = self.client.serialize(body)
        self.client.httpclient.request(
            end_url(path, format=self.format), 'POST',
            body=mox_body,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('create_' + resource)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)
        if name:
            self.assertIn(name, _str)

    def _test_list_columns(self, cmd, resources,
                           resources_out, args=('-f', 'json'),
                           cmd_resources=None, parent_id=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        self.client.format = self.format
        if not cmd_resources:
            cmd_resources = resources

        resstr = self.client.serialize(resources_out)

        path = getattr(self.client, cmd_resources + "_path")
        if parent_id:
            path = path % parent_id
        self.client.httpclient.request(
            end_url(path, format=self.format), 'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr))
        args = tuple(args) + ('--request-format', self.format)
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("list_" + cmd_resources)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def _test_list_resources(self, resources, cmd, detail=False, tags=(),
                             fields_1=(), fields_2=(), page_size=None,
                             sort_key=(), sort_dir=(), response_contents=None,
                             base_args=None, path=None, cmd_resources=None,
                             parent_id=None, output_format=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resources:
            cmd_resources = resources
        if response_contents is None:
            contents = [{self.id_field: 'myid1', },
                        {self.id_field: 'myid2', }, ]
        else:
            contents = response_contents
        reses = {resources: contents}
        self.client.format = self.format
        resstr = self.client.serialize(reses)
        # url method body
        query = ""
        args = base_args if base_args is not None else []
        if detail:
            args.append('-D')
        args.extend(['--request-format', self.format])
        if fields_1:
            for field in fields_1:
                args.append('--fields')
                args.append(field)

        if tags:
            args.append('--')
            args.append("--tag")
        for tag in tags:
            args.append(tag)
            tag_query = urlparse.urlencode(
                {'tag': encodeutils.safe_encode(tag)})
            if query:
                query += "&" + tag_query
            else:
                query = tag_query
        if (not tags) and fields_2:
            args.append('--')
        if fields_2:
            args.append("--fields")
            for field in fields_2:
                args.append(field)
        if detail:
            query = query and query + '&verbose=True' or 'verbose=True'
        for field in itertools.chain(fields_1, fields_2):
            if query:
                query += "&fields=" + field
            else:
                query = "fields=" + field
        if page_size:
            args.append("--page-size")
            args.append(str(page_size))
            if query:
                query += "&limit=%s" % page_size
            else:
                query = "limit=%s" % page_size
        if sort_key:
            for key in sort_key:
                args.append('--sort-key')
                args.append(key)
                if query:
                    query += '&'
                query += 'sort_key=%s' % key
        if sort_dir:
            len_diff = len(sort_key) - len(sort_dir)
            if len_diff > 0:
                sort_dir = tuple(sort_dir) + ('asc',) * len_diff
            elif len_diff < 0:
                sort_dir = sort_dir[:len(sort_key)]
            for dir in sort_dir:
                args.append('--sort-dir')
                args.append(dir)
                if query:
                    query += '&'
                query += 'sort_dir=%s' % dir
        if path is None:
            path = getattr(self.client, cmd_resources + "_path")
            if parent_id:
                path = path % parent_id
        if output_format:
            args.append('-f')
            args.append(output_format)
        self.client.httpclient.request(
            MyUrlComparator(end_url(path, query, format=self.format),
                            self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr))
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("list_" + cmd_resources)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        if response_contents is None:
            self.assertIn('myid1', _str)
        return _str

    def _test_list_resources_with_pagination(self, resources, cmd,
                                             base_args=None,
                                             cmd_resources=None,
                                             parent_id=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resources:
            cmd_resources = resources

        path = getattr(self.client, cmd_resources + "_path")
        if parent_id:
            path = path % parent_id
        fake_query = "marker=myid2&limit=2"
        reses1 = {resources: [{'id': 'myid1', },
                              {'id': 'myid2', }],
                  '%s_links' % resources: [{'href': end_url(path, fake_query),
                                            'rel': 'next'}]}
        reses2 = {resources: [{'id': 'myid3', },
                              {'id': 'myid4', }]}
        self.client.format = self.format
        resstr1 = self.client.serialize(reses1)
        resstr2 = self.client.serialize(reses2)
        self.client.httpclient.request(
            end_url(path, "", format=self.format), 'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr1))
        self.client.httpclient.request(
            MyUrlComparator(end_url(path, fake_query, format=self.format),
                            self.client), 'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr2))
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("list_" + cmd_resources)
        args = base_args if base_args is not None else []
        args.extend(['--request-format', self.format])
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def _test_update_resource(self, resource, cmd, myid, args, extrafields,
                              cmd_resource=None, parent_id=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resource:
            cmd_resource = resource

        body = {resource: extrafields}
        path = getattr(self.client, cmd_resource + "_path")
        if parent_id:
            path = path % (parent_id, myid)
        else:
            path = path % myid
        self.client.format = self.format
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            mox_body = MyComparator(body, self.client)
        else:
            mox_body = self.client.serialize(body)
        self.client.httpclient.request(
            MyUrlComparator(end_url(path, format=self.format),
                            self.client),
            'PUT',
            body=mox_body,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(204), None))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("update_" + cmd_resource)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)

    def _test_show_resource(self, resource, cmd, myid, args, fields=(),
                            cmd_resource=None, parent_id=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resource:
            cmd_resource = resource

        query = "&".join(["fields=%s" % field for field in fields])
        expected_res = {resource:
                        {self.id_field: myid,
                         'name': 'myname', }, }
        self.client.format = self.format
        resstr = self.client.serialize(expected_res)
        path = getattr(self.client, cmd_resource + "_path")
        if parent_id:
            path = path % (parent_id, myid)
        else:
            path = path % myid
        self.client.httpclient.request(
            end_url(path, query, format=self.format), 'GET',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("show_" + cmd_resource)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)
        self.assertIn('myname', _str)

    def _test_delete_resource(self, resource, cmd, myid, args,
                              cmd_resource=None, parent_id=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resource:
            cmd_resource = resource
        path = getattr(self.client, cmd_resource + "_path")
        if parent_id:
            path = path % (parent_id, myid)
        else:
            path = path % (myid)
        self.client.httpclient.request(
            end_url(path, format=self.format), 'DELETE',
            body=None,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(204), None))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("delete_" + cmd_resource)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)

    def _test_update_resource_action(self, resource, cmd, myid, action, args,
                                     body, retval=None, cmd_resource=None):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resource:
            cmd_resource = resource
        path = getattr(self.client, cmd_resource + "_path")
        path_action = '%s/%s' % (myid, action)
        self.client.httpclient.request(
            end_url(path % path_action, format=self.format), 'PUT',
            body=MyComparator(body, self.client),
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(204), retval))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser("delete_" + cmd_resource)
        shell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)


class ClientV2TestJson(CLITestV20Base):
    def test_do_request_unicode(self):
        self.client.format = self.format
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        unicode_text = u'\u7f51\u7edc'
        # url with unicode
        action = u'/test'
        expected_action = action
        # query string with unicode
        params = {'test': unicode_text}
        expect_query = urlparse.urlencode(utils.safe_encode_dict(params))
        # request body with unicode
        body = params
        expect_body = self.client.serialize(body)
        self.client.httpclient.auth_token = encodeutils.safe_encode(
            unicode_text)
        expected_auth_token = encodeutils.safe_encode(unicode_text)

        self.client.httpclient.request(
            end_url(expected_action, query=expect_query, format=self.format),
            'PUT', body=expect_body,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token',
                expected_auth_token)).AndReturn((MyResp(200), expect_body))

        self.mox.ReplayAll()
        res_body = self.client.do_request('PUT', action, body=body,
                                          params=params)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

        # test response with unicode
        self.assertEqual(res_body, body)

    def test_do_request_error_without_response_body(self):
        self.client.format = self.format
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        params = {'test': 'value'}
        expect_query = six.moves.urllib.parse.urlencode(params)
        self.client.httpclient.auth_token = 'token'

        self.client.httpclient.request(
            MyUrlComparator(end_url(
                '/test', query=expect_query, format=self.format), self.client),
            'PUT', body='',
            headers=mox.ContainsKeyValue('X-Auth-Token', 'token')
        ).AndReturn((MyResp(400, reason='An error'), ''))

        self.mox.ReplayAll()
        error = self.assertRaises(exceptions.NeutronClientException,
                                  self.client.do_request, 'PUT', '/test',
                                  body='', params=params)
        self.assertEqual("An error", str(error))
        self.mox.VerifyAll()
        self.mox.UnsetStubs()


class ClientV2UnicodeTestXML(ClientV2TestJson):
    format = 'xml'


class CLITestV20ExceptionHandler(CLITestV20Base):

    def _test_exception_handler_v20(
        self, expected_exception, status_code, expected_msg,
        error_type=None, error_msg=None, error_detail=None,
        error_content=None):
        if error_content is None:
            error_content = {'NeutronError': {'type': error_type,
                                              'message': error_msg,
                                              'detail': error_detail}}

        e = self.assertRaises(expected_exception,
                              client.exception_handler_v20,
                              status_code, error_content)
        self.assertEqual(status_code, e.status_code)

        if expected_msg is None:
            if error_detail:
                expected_msg = '\n'.join([error_msg, error_detail])
            else:
                expected_msg = error_msg
        self.assertEqual(expected_msg, e.message)

    def test_exception_handler_v20_ip_address_in_use(self):
        err_msg = ('Unable to complete operation for network '
                   'fake-network-uuid. The IP address fake-ip is in use.')
        self._test_exception_handler_v20(
            exceptions.IpAddressInUseClient, 409, err_msg,
            'IpAddressInUse', err_msg, '')

    def test_exception_handler_v20_neutron_known_error(self):
        known_error_map = [
            ('NetworkNotFound', exceptions.NetworkNotFoundClient, 404),
            ('PortNotFound', exceptions.PortNotFoundClient, 404),
            ('NetworkInUse', exceptions.NetworkInUseClient, 409),
            ('PortInUse', exceptions.PortInUseClient, 409),
            ('StateInvalid', exceptions.StateInvalidClient, 400),
            ('IpAddressInUse', exceptions.IpAddressInUseClient, 409),
            ('IpAddressGenerationFailure',
             exceptions.IpAddressGenerationFailureClient, 409),
            ('MacAddressInUse', exceptions.MacAddressInUseClient, 409),
            ('ExternalIpAddressExhausted',
             exceptions.ExternalIpAddressExhaustedClient, 400),
            ('OverQuota', exceptions.OverQuotaClient, 409),
            ('InvalidIpForNetwork', exceptions.InvalidIpForNetworkClient, 400),
        ]

        error_msg = 'dummy exception message'
        error_detail = 'sample detail'
        for server_exc, client_exc, status_code in known_error_map:
            self._test_exception_handler_v20(
                client_exc, status_code,
                error_msg + '\n' + error_detail,
                server_exc, error_msg, error_detail)

    def test_exception_handler_v20_neutron_known_error_without_detail(self):
        error_msg = 'Network not found'
        error_detail = ''
        self._test_exception_handler_v20(
            exceptions.NetworkNotFoundClient, 404,
            error_msg,
            'NetworkNotFound', error_msg, error_detail)

    def test_exception_handler_v20_unknown_error_to_per_code_exception(self):
        for status_code, client_exc in exceptions.HTTP_EXCEPTION_MAP.items():
            error_msg = 'Unknown error'
            error_detail = 'This is detail'
            self._test_exception_handler_v20(
                client_exc, status_code,
                error_msg + '\n' + error_detail,
                'UnknownError', error_msg, error_detail)

    def test_exception_handler_v20_neutron_unknown_status_code(self):
        error_msg = 'Unknown error'
        error_detail = 'This is detail'
        self._test_exception_handler_v20(
            exceptions.NeutronClientException, 501,
            error_msg + '\n' + error_detail,
            'UnknownError', error_msg, error_detail)

    def test_exception_handler_v20_bad_neutron_error(self):
        error_content = {'NeutronError': {'unknown_key': 'UNKNOWN'}}
        self._test_exception_handler_v20(
            exceptions.NeutronClientException, 500,
            expected_msg={'unknown_key': 'UNKNOWN'},
            error_content=error_content)

    def test_exception_handler_v20_error_dict_contains_message(self):
        error_content = {'message': 'This is an error message'}
        self._test_exception_handler_v20(
            exceptions.NeutronClientException, 500,
            expected_msg='This is an error message',
            error_content=error_content)

    def test_exception_handler_v20_error_dict_not_contain_message(self):
        error_content = {'error': 'This is an error message'}
        expected_msg = '%s-%s' % (500, error_content)
        self._test_exception_handler_v20(
            exceptions.NeutronClientException, 500,
            expected_msg=expected_msg,
            error_content=error_content)

    def test_exception_handler_v20_default_fallback(self):
        error_content = 'This is an error message'
        expected_msg = '%s-%s' % (500, error_content)
        self._test_exception_handler_v20(
            exceptions.NeutronClientException, 500,
            expected_msg=expected_msg,
            error_content=error_content)

    def test_exception_status(self):
        e = exceptions.BadRequest()
        self.assertEqual(e.status_code, 400)

        e = exceptions.BadRequest(status_code=499)
        self.assertEqual(e.status_code, 499)

        # SslCertificateValidationError has no explicit status_code,
        # but should have a 'safe' defined fallback.
        e = exceptions.SslCertificateValidationError()
        self.assertIsNotNone(e.status_code)

        e = exceptions.SslCertificateValidationError(status_code=599)
        self.assertEqual(e.status_code, 599)

    def test_connection_failed(self):
        self.mox.StubOutWithMock(self.client.httpclient, 'request')
        self.client.httpclient.auth_token = 'token'

        self.client.httpclient.request(
            end_url('/test'), 'GET',
            headers=mox.ContainsKeyValue('X-Auth-Token', 'token')
        ).AndRaise(requests.exceptions.ConnectionError('Connection refused'))

        self.mox.ReplayAll()

        error = self.assertRaises(exceptions.ConnectionFailed,
                                  self.client.get, '/test')
        # NB: ConnectionFailed has no explicit status_code, so this
        # tests that there is a fallback defined.
        self.assertIsNotNone(error.status_code)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
