# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import httpretty

from novaclient.openstack.common import jsonutils
from novaclient.tests import fakes
from novaclient.tests.fixture_data import base


class FloatingFixture(base.Fixture):

    base_url = 'os-floating-ips'

    def setUp(self):
        super(FloatingFixture, self).setUp()

        floating_ips = [{'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
                        {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'}]

        get_os_floating_ips = {'floating_ips': floating_ips}
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_floating_ips),
                               content_type='application/json')

        for ip in floating_ips:
            get_os_floating_ip = {'floating_ip': ip}
            httpretty.register_uri(httpretty.GET, self.url(ip['id']),
                                   body=jsonutils.dumps(get_os_floating_ip),
                                   content_type='application/json')

            httpretty.register_uri(httpretty.DELETE, self.url(ip['id']),
                                   content_type='application/json',
                                   status=204)

        def post_os_floating_ips(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            ip = floating_ips[0].copy()
            ip['pool'] = body.get('pool')
            ip = jsonutils.dumps({'floating_ip': ip})
            return 200, headers, ip
        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_os_floating_ips,
                               content_type='application/json')


class DNSFixture(base.Fixture):

    base_url = 'os-floating-ip-dns'

    def setUp(self):
        super(DNSFixture, self).setUp()

        get_os_floating_ip_dns = {
            'domain_entries': [
                {'domain': 'example.org'},
                {'domain': 'example.com'}
            ]
        }
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_floating_ip_dns),
                               content_type='application/json',
                               status=205)

        get_dns_testdomain_entries_testname = {
            'dns_entry': {
                'ip': "10.10.10.10",
                'name': 'testname',
                'type': "A",
                'domain': 'testdomain'
            }
        }
        url = self.url('testdomain', 'entries', 'testname')
        body = jsonutils.dumps(get_dns_testdomain_entries_testname)
        httpretty.register_uri(httpretty.GET, url,
                               body=body,
                               content_type='application/json',
                               status=205)

        httpretty.register_uri(httpretty.DELETE, self.url('testdomain'),
                               status=200)

        url = self.url('testdomain', 'entries', 'testname')
        httpretty.register_uri(httpretty.DELETE, url, status=200)

        def put_dns_testdomain_entries_testname(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            fakes.assert_has_keys(body['dns_entry'],
                                  required=['ip', 'dns_type'])
            return 205, headers, request.body
        httpretty.register_uri(httpretty.PUT, url,
                               body=put_dns_testdomain_entries_testname,
                               content_type='application/json')

        url = self.url('testdomain', 'entries')
        httpretty.register_uri(httpretty.GET, url, status=404)

        get_os_floating_ip_dns_testdomain_entries = {
            'dns_entries': [
                {
                    'dns_entry': {
                         'ip': '1.2.3.4',
                         'name': "host1",
                         'type': "A",
                         'domain': 'testdomain'
                     }
                },
                {
                    'dns_entry': {
                         'ip': '1.2.3.4',
                         'name': "host2",
                         'type': "A",
                         'domain': 'testdomain'
                    }
                },
            ]
        }
        body = jsonutils.dumps(get_os_floating_ip_dns_testdomain_entries)
        httpretty.register_uri(httpretty.GET, url + '?ip=1.2.3.4',
                               body=body,
                               status=205,
                               content_type='application/json')

        def put_os_floating_ip_dns_testdomain(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            if body['domain_entry']['scope'] == 'private':
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['availability_zone', 'scope'])
            elif body['domain_entry']['scope'] == 'public':
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['project', 'scope'])
            else:
                fakes.assert_has_keys(body['domain_entry'],
                                      required=['project', 'scope'])

            headers['Content-Type'] = 'application/json'
            return (205, headers, request.body)

        httpretty.register_uri(httpretty.PUT, self.url('testdomain'),
                               body=put_os_floating_ip_dns_testdomain)


class BulkFixture(base.Fixture):

    base_url = 'os-floating-ips-bulk'

    def setUp(self):
        super(BulkFixture, self).setUp()

        get_os_floating_ips_bulk = {
            'floating_ip_info': [
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
                {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
            ]
        }
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_floating_ips_bulk),
                               content_type='application/json')
        httpretty.register_uri(httpretty.GET, self.url('testHost'),
                               body=jsonutils.dumps(get_os_floating_ips_bulk),
                               content_type='application/json')

        def put_os_floating_ips_bulk_delete(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            ip_range = body.get('ip_range')
            data = {'floating_ips_bulk_delete': ip_range}
            return 200, headers, jsonutils.dumps(data)

        httpretty.register_uri(httpretty.PUT, self.url('delete'),
                               body=put_os_floating_ips_bulk_delete,
                               content_type='application/json')

        def post_os_floating_ips_bulk(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            params = body.get('floating_ips_bulk_create')
            pool = params.get('pool', 'defaultPool')
            interface = params.get('interface', 'defaultInterface')
            data = {
                'floating_ips_bulk_create': {
                     'ip_range': '192.168.1.0/30',
                     'pool': pool,
                     'interface': interface
                }
            }
            return 200, headers, jsonutils.dumps(data)

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_os_floating_ips_bulk,
                               content_type='application/json')


class PoolsFixture(base.Fixture):

    base_url = 'os-floating-ip-pools'

    def setUp(self):
        super(PoolsFixture, self).setUp()

        get_os_floating_ip_pools = {
            'floating_ip_pools': [
                {'name': 'foo'},
                {'name': 'bar'}
            ]
        }
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_floating_ip_pools),
                               content_type='application/json')
