# Copyright 2012 OpenStack Foundation.
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

import socket

import mock
from mock import patch
import netifaces
from oslotest import base as test_base

from oslo_utils import netutils


class NetworkUtilsTest(test_base.BaseTestCase):

    def test_no_host(self):
        result = netutils.urlsplit('http://')
        self.assertEqual('', result.netloc)
        self.assertEqual(None, result.port)
        self.assertEqual(None, result.hostname)
        self.assertEqual('http', result.scheme)

    def test_parse_host_port(self):
        self.assertEqual(('server01', 80),
                         netutils.parse_host_port('server01:80'))
        self.assertEqual(('server01', None),
                         netutils.parse_host_port('server01'))
        self.assertEqual(('server01', 1234),
                         netutils.parse_host_port('server01',
                         default_port=1234))
        self.assertEqual(('::1', 80),
                         netutils.parse_host_port('[::1]:80'))
        self.assertEqual(('::1', None),
                         netutils.parse_host_port('[::1]'))
        self.assertEqual(('::1', 1234),
                         netutils.parse_host_port('[::1]',
                         default_port=1234))
        self.assertEqual(('2001:db8:85a3::8a2e:370:7334', 1234),
                         netutils.parse_host_port(
                             '2001:db8:85a3::8a2e:370:7334',
                             default_port=1234))

    def test_urlsplit(self):
        result = netutils.urlsplit('rpc://myhost?someparam#somefragment')
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'myhost')
        self.assertEqual(result.path, '')
        self.assertEqual(result.query, 'someparam')
        self.assertEqual(result.fragment, 'somefragment')

        result = netutils.urlsplit(
            'rpc://myhost/mypath?someparam#somefragment',
            allow_fragments=False)
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'myhost')
        self.assertEqual(result.path, '/mypath')
        self.assertEqual(result.query, 'someparam#somefragment')
        self.assertEqual(result.fragment, '')

        result = netutils.urlsplit(
            'rpc://user:pass@myhost/mypath?someparam#somefragment',
            allow_fragments=False)
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'user:pass@myhost')
        self.assertEqual(result.path, '/mypath')
        self.assertEqual(result.query, 'someparam#somefragment')
        self.assertEqual(result.fragment, '')

    def test_urlsplit_ipv6(self):
        ipv6_url = 'http://[::1]:443/v2.0/'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'http')
        self.assertEqual(result.netloc, '[::1]:443')
        self.assertEqual(result.path, '/v2.0/')
        self.assertEqual(result.hostname, '::1')
        self.assertEqual(result.port, 443)

        ipv6_url = 'http://user:pass@[::1]/v2.0/'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'http')
        self.assertEqual(result.netloc, 'user:pass@[::1]')
        self.assertEqual(result.path, '/v2.0/')
        self.assertEqual(result.hostname, '::1')
        self.assertEqual(result.port, None)

        ipv6_url = 'https://[2001:db8:85a3::8a2e:370:7334]:1234/v2.0/xy?ab#12'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'https')
        self.assertEqual(result.netloc, '[2001:db8:85a3::8a2e:370:7334]:1234')
        self.assertEqual(result.path, '/v2.0/xy')
        self.assertEqual(result.hostname, '2001:db8:85a3::8a2e:370:7334')
        self.assertEqual(result.port, 1234)
        self.assertEqual(result.query, 'ab')
        self.assertEqual(result.fragment, '12')

    def test_urlsplit_params(self):
        test_url = "http://localhost/?a=b&c=d"
        result = netutils.urlsplit(test_url)
        self.assertEqual({'a': 'b', 'c': 'd'}, result.params())
        self.assertEqual({'a': 'b', 'c': 'd'}, result.params(collapse=False))

        test_url = "http://localhost/?a=b&a=c&a=d"
        result = netutils.urlsplit(test_url)
        self.assertEqual({'a': 'd'}, result.params())
        self.assertEqual({'a': ['b', 'c', 'd']}, result.params(collapse=False))

        test_url = "http://localhost"
        result = netutils.urlsplit(test_url)
        self.assertEqual({}, result.params())

        test_url = "http://localhost?"
        result = netutils.urlsplit(test_url)
        self.assertEqual({}, result.params())

    def test_set_tcp_keepalive(self):
        mock_sock = mock.Mock()
        netutils.set_tcp_keepalive(mock_sock, True, 100, 10, 5)
        calls = [
            mock.call.setsockopt(socket.SOL_SOCKET,
                                 socket.SO_KEEPALIVE, True),
        ]
        if hasattr(socket, 'TCP_KEEPIDLE'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPIDLE, 100)
            ]
        if hasattr(socket, 'TCP_KEEPINTVL'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPINTVL, 10),
            ]
        if hasattr(socket, 'TCP_KEEPCNT'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPCNT, 5)
            ]
        mock_sock.assert_has_calls(calls)

        mock_sock.reset_mock()
        netutils.set_tcp_keepalive(mock_sock, False)
        self.assertEqual(1, len(mock_sock.mock_calls))

    def test_is_valid_ipv4(self):
        self.assertTrue(netutils.is_valid_ipv4('42.42.42.42'))

        self.assertFalse(netutils.is_valid_ipv4('-1.11.11.11'))

        self.assertFalse(netutils.is_valid_ipv4(''))

    def test_is_valid_ipv6(self):
        self.assertTrue(netutils.is_valid_ipv6('::1'))

        self.assertFalse(netutils.is_valid_ipv6(
            '1fff::a88:85a3::172.31.128.1'))

        self.assertFalse(netutils.is_valid_ipv6(''))

    def test_is_valid_ip(self):
        self.assertTrue(netutils.is_valid_ip('127.0.0.1'))

        self.assertTrue(netutils.is_valid_ip('2001:db8::ff00:42:8329'))

        self.assertFalse(netutils.is_valid_ip('256.0.0.0'))

        self.assertFalse(netutils.is_valid_ip('::1.2.3.'))

        self.assertFalse(netutils.is_valid_ip(''))

    def test_valid_port(self):
        valid_inputs = [1, '1', 2, '3', '5', 8, 13, 21,
                        '80', '3246', '65535']
        for input_str in valid_inputs:
            self.assertTrue(netutils.is_valid_port(input_str))

    def test_valid_port_fail(self):
        invalid_inputs = ['-32768', '0', 0, '65536', 528491, '528491',
                          '528.491', 'thirty-seven', None]
        for input_str in invalid_inputs:
            self.assertFalse(netutils.is_valid_port(input_str))

    def test_get_my_ip(self):
        sock_attrs = {
            'return_value.getsockname.return_value': ['1.2.3.4', '']}
        with mock.patch('socket.socket', **sock_attrs):
            addr = netutils.get_my_ipv4()
        self.assertEqual(addr, '1.2.3.4')

    @mock.patch('socket.socket')
    @mock.patch('oslo_utils.netutils._get_my_ipv4_address')
    def test_get_my_ip_socket_error(self, ip, mock_socket):
        mock_socket.side_effect = socket.error
        ip.return_value = '1.2.3.4'
        addr = netutils.get_my_ipv4()
        self.assertEqual(addr, '1.2.3.4')

    @mock.patch('netifaces.gateways')
    @mock.patch('netifaces.ifaddresses')
    def test_get_my_ipv4_address_with_default_route(
            self, ifaddr, gateways):
        with patch.dict(netifaces.__dict__, {'AF_INET': '0'}):
            ifaddr.return_value = {'0': [{'addr': '172.18.204.1'}]}
            addr = netutils._get_my_ipv4_address()
        self.assertEqual('172.18.204.1', addr)

    @mock.patch('netifaces.gateways')
    @mock.patch('netifaces.ifaddresses')
    def test_get_my_ipv4_address_without_default_route(
            self, ifaddr, gateways):
        with patch.dict(netifaces.__dict__, {'AF_INET': '0'}):
            ifaddr.return_value = {}
            addr = netutils._get_my_ipv4_address()
        self.assertEqual('127.0.0.1', addr)

    @mock.patch('netifaces.gateways')
    @mock.patch('netifaces.ifaddresses')
    def test_get_my_ipv4_address_without_default_interface(
            self, ifaddr, gateways):
        gateways.return_value = {}
        addr = netutils._get_my_ipv4_address()
        self.assertEqual('127.0.0.1', addr)
        self.assertFalse(ifaddr.called)


class IPv6byEUI64TestCase(test_base.BaseTestCase):
    """Unit tests to generate IPv6 by EUI-64 operations."""

    def test_generate_IPv6_by_EUI64(self):
        addr = netutils.get_ipv6_addr_by_EUI64('2001:db8::',
                                               '00:16:3e:33:44:55')
        self.assertEqual('2001:db8::216:3eff:fe33:4455', addr.format())

    def test_generate_IPv6_with_IPv4_prefix(self):
        ipv4_prefix = '10.0.8'
        mac = '00:16:3e:33:44:55'
        self.assertRaises(ValueError, lambda:
                          netutils.get_ipv6_addr_by_EUI64(ipv4_prefix, mac))

    def test_generate_IPv6_with_bad_mac(self):
        bad_mac = '00:16:3e:33:44:5Z'
        prefix = '2001:db8::'
        self.assertRaises(ValueError, lambda:
                          netutils.get_ipv6_addr_by_EUI64(prefix, bad_mac))

    def test_generate_IPv6_with_bad_prefix(self):
        mac = '00:16:3e:33:44:55'
        bad_prefix = 'bb'
        self.assertRaises(ValueError, lambda:
                          netutils.get_ipv6_addr_by_EUI64(bad_prefix, mac))

    def test_generate_IPv6_with_error_prefix_type(self):
        mac = '00:16:3e:33:44:55'
        prefix = 123
        self.assertRaises(TypeError, lambda:
                          netutils.get_ipv6_addr_by_EUI64(prefix, mac))


class TestIsIPv6Enabled(test_base.BaseTestCase):

    def setUp(self):
        super(TestIsIPv6Enabled, self).setUp()

        def reset_detection_flag():
            netutils._IS_IPV6_ENABLED = None
        reset_detection_flag()
        self.addCleanup(reset_detection_flag)
        self.mock_exists = mock.patch("os.path.exists",
                                      return_value=True).start()
        mock_open = mock.patch("six.moves.builtins.open").start()
        self.mock_read = mock_open.return_value.__enter__.return_value.read

    def test_enabled(self):
        self.mock_read.return_value = "0"
        enabled = netutils.is_ipv6_enabled()
        self.assertTrue(enabled)

    def test_disabled(self):
        self.mock_read.return_value = "1"
        enabled = netutils.is_ipv6_enabled()
        self.assertFalse(enabled)

    def test_disabled_non_exists(self):
        self.mock_exists.return_value = False
        enabled = netutils.is_ipv6_enabled()
        self.assertFalse(enabled)
        self.assertFalse(self.mock_read.called)

    def test_memoize(self):
        self.mock_read.return_value = "0"
        netutils.is_ipv6_enabled()
        enabled = netutils.is_ipv6_enabled()
        self.assertTrue(enabled)
        self.mock_read.assert_called_once_with()
