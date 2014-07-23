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
"""
Subclass for httplib.HTTPSConnection with optional certificate name
verification, depending on libcloud.security settings.
"""
import os
import re
import socket
import ssl
import warnings

import libcloud.security
from libcloud.utils.py3 import httplib


class LibcloudHTTPSConnection(httplib.HTTPSConnection):
    """
    LibcloudHTTPSConnection

    Subclass of HTTPSConnection which verifies certificate names
    if and only if CA certificates are available.
    """
    verify = True         # verify by default
    ca_cert = None        # no default CA Certificate

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        self._setup_verify()
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def _setup_verify(self):
        """
        Setup Verify SSL or not

        Reads security module's VERIFY_SSL_CERT and toggles whether
        the class overrides the connect() class method or runs the
        inherited httplib.HTTPSConnection connect()
        """
        self.verify = libcloud.security.VERIFY_SSL_CERT

        if self.verify:
            self._setup_ca_cert()
        else:
            warnings.warn(libcloud.security.VERIFY_SSL_DISABLED_MSG)

    def _setup_ca_cert(self):
        """
        Setup CA Certs

        Search in CA_CERTS_PATH for valid candidates and
        return first match.  Otherwise, complain about certs
        not being available.
        """
        if not self.verify:
            return

        ca_certs_available = [cert
                              for cert in libcloud.security.CA_CERTS_PATH
                              if os.path.exists(cert) and os.path.isfile(cert)]
        if ca_certs_available:
            # use first available certificate
            self.ca_cert = ca_certs_available[0]
        else:
            raise RuntimeError(
                libcloud.security.CA_CERTS_UNAVAILABLE_ERROR_MSG)

    def connect(self):
        """
        Connect

        Checks if verification is toggled; if not, just call
        httplib.HTTPSConnection's connect
        """
        if not self.verify:
            return httplib.HTTPSConnection.connect(self)

        # otherwise, create a connection and verify the hostname
        # use socket.create_connection (in 2.6+) if possible
        if getattr(socket, 'create_connection', None):
            sock = socket.create_connection((self.host, self.port),
                                            self.timeout)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
        self.sock = ssl.wrap_socket(sock,
                                    self.key_file,
                                    self.cert_file,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    ca_certs=self.ca_cert,
                                    ssl_version=ssl.PROTOCOL_TLSv1)
        cert = self.sock.getpeercert()
        if not self._verify_hostname(self.host, cert):
            raise ssl.SSLError('Failed to verify hostname')

    def _verify_hostname(self, hostname, cert):
        """
        Verify hostname against peer cert

        Check both commonName and entries in subjectAltName, using a
        rudimentary glob to dns regex check to find matches
        """
        common_name = self._get_common_name(cert)
        alt_names = self._get_subject_alt_names(cert)

        # replace * with alphanumeric and dash
        # replace . with literal .
        # http://www.dns.net/dnsrd/trick.html#legal-hostnames
        valid_patterns = [
            re.compile('^' + pattern.replace(r".", r"\.")
                                    .replace(r"*", r"[0-9A-Za-z\-]+") + '$')
            for pattern in (set(common_name) | set(alt_names))]

        return any(
            pattern.search(hostname)
            for pattern in valid_patterns
        )

    def _get_subject_alt_names(self, cert):
        """
        Get SubjectAltNames

        Retrieve 'subjectAltName' attributes from cert data structure
        """
        if 'subjectAltName' not in cert:
            values = []
        else:
            values = [value
                      for field, value in cert['subjectAltName']
                      if field == 'DNS']
        return values

    def _get_common_name(self, cert):
        """
        Get Common Name

        Retrieve 'commonName' attribute from cert data structure
        """
        if 'subject' not in cert:
            return None
        values = [value[0][1]
                  for value in cert['subject']
                  if value[0][0] == 'commonName']
        return values
