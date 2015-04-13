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

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import floatingips as data
from novaclient.tests.unit import utils
from novaclient.v2 import floating_ip_dns


class FloatingIPDNSDomainTest(utils.FixturedTestCase):

    testdomain = "testdomain"
    client_fixture_class = client.V1
    data_fixture_class = data.DNSFixture

    def test_dns_domains(self):
        domainlist = self.cs.dns_domains.domains()
        self.assertEqual(2, len(domainlist))

        for entry in domainlist:
            self.assertIsInstance(entry,
                                  floating_ip_dns.FloatingIPDNSDomain)

        self.assertEqual('example.com', domainlist[1].domain)

    def test_create_private_domain(self):
        self.cs.dns_domains.create_private(self.testdomain, 'test_avzone')
        self.assert_called('PUT', '/os-floating-ip-dns/%s' %
                           self.testdomain)

    def test_create_public_domain(self):
        self.cs.dns_domains.create_public(self.testdomain, 'test_project')
        self.assert_called('PUT', '/os-floating-ip-dns/%s' %
                           self.testdomain)

    def test_delete_domain(self):
        self.cs.dns_domains.delete(self.testdomain)
        self.assert_called('DELETE', '/os-floating-ip-dns/%s' %
                           self.testdomain)


class FloatingIPDNSEntryTest(utils.FixturedTestCase):

    testname = "testname"
    testip = "1.2.3.4"
    testdomain = "testdomain"
    testtype = "A"
    client_fixture_class = client.V1
    data_fixture_class = data.DNSFixture

    def test_get_dns_entries_by_ip(self):
        entries = self.cs.dns_entries.get_for_ip(self.testdomain,
                                                 ip=self.testip)
        self.assertEqual(2, len(entries))

        for entry in entries:
            self.assertIsInstance(entry,
                                  floating_ip_dns.FloatingIPDNSEntry)

        self.assertEqual('host2', entries[1].dns_entry['name'])
        self.assertEqual(entries[1].dns_entry['ip'], self.testip)

    def test_get_dns_entry_by_name(self):
        entry = self.cs.dns_entries.get(self.testdomain,
                                        self.testname)
        self.assertIsInstance(entry, floating_ip_dns.FloatingIPDNSEntry)
        self.assertEqual(entry.name, self.testname)

    def test_create_entry(self):
        self.cs.dns_entries.create(self.testdomain,
                                   self.testname,
                                   self.testip,
                                   self.testtype)

        self.assert_called('PUT', '/os-floating-ip-dns/%s/entries/%s' %
                           (self.testdomain, self.testname))

    def test_delete_entry(self):
        self.cs.dns_entries.delete(self.testdomain, self.testname)
        self.assert_called('DELETE', '/os-floating-ip-dns/%s/entries/%s' %
                           (self.testdomain, self.testname))
