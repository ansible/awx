# Copyright 2011 Andrew Bogott for The Wikimedia Foundation
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

from novaclient import base
from novaclient.openstack.common.py3kcompat import urlutils


def _quote_domain(domain):
    """Special quoting rule for placing domain names on a url line.

    Domain names tend to have .'s in them.  Urllib doesn't quote dots,
    but Routes tends to choke on them, so we need an extra level of
    by-hand quoting here.
    """
    return urlutils.quote(domain.replace('.', '%2E'))


class FloatingIPDNSDomain(base.Resource):
    def delete(self):
        self.manager.delete(self.domain)

    def create(self):
        if self.scope == 'public':
            self.manager.create_public(self.domain, self.project)
        else:
            self.manager.create_private(self.domain, self.availability_zone)

    def get(self):
        entries = self.manager.domains()
        for entry in entries:
            if entry.get('domain') == self.domain:
                return entry

        return None


class FloatingIPDNSDomainManager(base.Manager):
    resource_class = FloatingIPDNSDomain

    def domains(self):
        """Return the list of available dns domains."""
        return self._list("/os-floating-ip-dns", "domain_entries")

    def create_private(self, fqdomain, availability_zone):
        """Add or modify a private DNS domain."""
        body = {'domain_entry':
                 {'scope': 'private',
                  'availability_zone': availability_zone}}
        return self._update('/os-floating-ip-dns/%s' % _quote_domain(fqdomain),
                            body,
                            'domain_entry')

    def create_public(self, fqdomain, project):
        """Add or modify a public DNS domain."""
        body = {'domain_entry':
                 {'scope': 'public',
                  'project': project}}

        return self._update('/os-floating-ip-dns/%s' % _quote_domain(fqdomain),
                            body,
                            'domain_entry')

    def delete(self, fqdomain):
        """Delete the specified domain."""
        self._delete("/os-floating-ip-dns/%s" % _quote_domain(fqdomain))


class FloatingIPDNSEntry(base.Resource):
    def delete(self):
        self.manager.delete(self.name, self.domain)

    def create(self):
        self.manager.create(self.domain, self.name,
                                  self.ip, self.dns_type)

    def get(self):
        return self.manager.get(self.domain, self.name)


class FloatingIPDNSEntryManager(base.Manager):
    resource_class = FloatingIPDNSEntry

    def get(self, domain, name):
        """Return a list of entries for the given domain and ip or name."""
        return self._get("/os-floating-ip-dns/%s/entries/%s" %
                              (_quote_domain(domain), name),
                          "dns_entry")

    def get_for_ip(self, domain, ip):
        """Return a list of entries for the given domain and ip or name."""
        qparams = {'ip': ip}
        params = "?%s" % urlutils.urlencode(qparams)

        return self._list("/os-floating-ip-dns/%s/entries%s" %
                              (_quote_domain(domain), params),
                          "dns_entries")

    def create(self, domain, name, ip, dns_type):
        """Add a new DNS entry."""
        body = {'dns_entry':
                 {'ip': ip,
                  'dns_type': dns_type}}

        return self._update("/os-floating-ip-dns/%s/entries/%s" %
                            (_quote_domain(domain), name),
                            body,
                            "dns_entry")

    def modify_ip(self, domain, name, ip):
        """Add a new DNS entry."""
        body = {'dns_entry':
                 {'ip': ip,
                  'dns_type': 'A'}}

        return self._update("/os-floating-ip-dns/%s/entries/%s" %
                            (_quote_domain(domain), name),
                            body,
                            "dns_entry")

    def delete(self, domain, name):
        """Delete entry specified by name and domain."""
        self._delete("/os-floating-ip-dns/%s/entries/%s" %
                                (_quote_domain(domain), name))
