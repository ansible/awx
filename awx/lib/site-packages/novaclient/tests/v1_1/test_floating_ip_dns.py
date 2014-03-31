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

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes
from novaclient.v1_1 import floating_ip_dns


cs = fakes.FakeClient()


class FloatingIPDNSDomainTest(utils.TestCase):

    testdomain = "testdomain"

    def test_dns_domains(self):
        domainlist = cs.dns_domains.domains()
        self.assertEqual(len(domainlist), 2)

        for entry in domainlist:
            self.assertIsInstance(entry,
                                  floating_ip_dns.FloatingIPDNSDomain)

        self.assertEqual(domainlist[1].domain, 'example.com')

    def test_create_private_domain(self):
        cs.dns_domains.create_private(self.testdomain, 'test_avzone')
        cs.assert_called('PUT', '/os-floating-ip-dns/%s' %
                         self.testdomain)

    def test_create_public_domain(self):
        cs.dns_domains.create_public(self.testdomain, 'test_project')
        cs.assert_called('PUT', '/os-floating-ip-dns/%s' %
                         self.testdomain)

    def test_delete_domain(self):
        cs.dns_domains.delete(self.testdomain)
        cs.assert_called('DELETE', '/os-floating-ip-dns/%s' %
                         self.testdomain)


class FloatingIPDNSEntryTest(utils.TestCase):

    testname = "testname"
    testip = "1.2.3.4"
    testdomain = "testdomain"
    testtype = "A"

    def test_get_dns_entries_by_ip(self):
        entries = cs.dns_entries.get_for_ip(self.testdomain, ip=self.testip)
        self.assertEqual(len(entries), 2)

        for entry in entries:
            self.assertIsInstance(entry,
                                  floating_ip_dns.FloatingIPDNSEntry)

        self.assertEqual(entries[1].dns_entry['name'], 'host2')
        self.assertEqual(entries[1].dns_entry['ip'], self.testip)

    def test_get_dns_entry_by_name(self):
        entry = cs.dns_entries.get(self.testdomain,
                                   self.testname)
        self.assertIsInstance(entry, floating_ip_dns.FloatingIPDNSEntry)
        self.assertEqual(entry.name, self.testname)

    def test_create_entry(self):
        cs.dns_entries.create(self.testdomain,
                                         self.testname,
                                         self.testip,
                                         self.testtype)

        cs.assert_called('PUT', '/os-floating-ip-dns/%s/entries/%s' %
                         (self.testdomain, self.testname))

    def test_delete_entry(self):
        cs.dns_entries.delete(self.testdomain, self.testname)
        cs.assert_called('DELETE', '/os-floating-ip-dns/%s/entries/%s' %
                         (self.testdomain, self.testname))
