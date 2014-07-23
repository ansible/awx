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

import os
import sys
import os.path

from mock import patch

import libcloud.security

from libcloud.utils.py3 import reload
from libcloud.httplib_ssl import LibcloudHTTPSConnection

from libcloud.test import unittest

ORIGINAL_CA_CERS_PATH = libcloud.security.CA_CERTS_PATH


class TestHttpLibSSLTests(unittest.TestCase):

    def setUp(self):
        libcloud.security.VERIFY_SSL_CERT = False
        libcloud.security.CA_CERTS_PATH = ORIGINAL_CA_CERS_PATH
        self.httplib_object = LibcloudHTTPSConnection('foo.bar')

    def test_custom_ca_path_using_env_var_doesnt_exist(self):
        os.environ['SSL_CERT_FILE'] = '/foo/doesnt/exist'

        try:
            reload(libcloud.security)
        except ValueError:
            e = sys.exc_info()[1]
            msg = 'Certificate file /foo/doesnt/exist doesn\'t exist'
            self.assertEqual(str(e), msg)
        else:
            self.fail('Exception was not thrown')

    def test_custom_ca_path_using_env_var_is_directory(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.environ['SSL_CERT_FILE'] = file_path

        expected_msg = 'Certificate file can\'t be a directory'
        self.assertRaisesRegexp(ValueError, expected_msg,
                                reload, libcloud.security)

    def test_custom_ca_path_using_env_var_exist(self):
        # When setting a path we don't actually check that a valid CA file is
        # provided.
        # This happens later in the code in httplib_ssl.connect method
        file_path = os.path.abspath(__file__)
        os.environ['SSL_CERT_FILE'] = file_path

        reload(libcloud.security)

        self.assertEqual(libcloud.security.CA_CERTS_PATH, [file_path])

    def test_verify_hostname(self):
        # commonName
        cert1 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', 'somemachine.python.org'),))}

        # commonName
        cert2 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', 'somemachine.python.org'),)),
                 'subjectAltName': ((('DNS', 'foo.alt.name')),
                                    (('DNS', 'foo.alt.name.1')))}

        # commonName
        cert3 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', 'python.org'),))}

        # wildcard commonName
        cert4 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', '*.api.joyentcloud.com'),))}

        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='invalid', cert=cert1))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='machine.python.org', cert=cert1))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='foomachine.python.org', cert=cert1))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='somesomemachine.python.org', cert=cert1))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='somemachine.python.orga', cert=cert1))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='somemachine.python.org.org', cert=cert1))
        self.assertTrue(self.httplib_object._verify_hostname(
                        hostname='somemachine.python.org', cert=cert1))

        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='invalid', cert=cert2))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='afoo.alt.name.1', cert=cert2))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='a.foo.alt.name.1', cert=cert2))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='foo.alt.name.1.2', cert=cert2))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='afoo.alt.name.1.2', cert=cert2))
        self.assertTrue(self.httplib_object._verify_hostname(
                        hostname='foo.alt.name.1', cert=cert2))

        self.assertTrue(self.httplib_object._verify_hostname(
                        hostname='python.org', cert=cert3))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='opython.org', cert=cert3))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='ython.org', cert=cert3))

        self.assertTrue(self.httplib_object._verify_hostname(
                        hostname='us-east-1.api.joyentcloud.com', cert=cert4))
        self.assertTrue(self.httplib_object._verify_hostname(
                        hostname='useast-1.api.joyentcloud.com', cert=cert4))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='t1.useast-1.api.joyentcloud.com', cert=cert4))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='ponies.useast-1.api.joyentcloud.com', cert=cert4))
        self.assertFalse(self.httplib_object._verify_hostname(
                         hostname='api.useast-1.api.joyentcloud.com', cert=cert4))

    def test_get_subject_alt_names(self):
        cert1 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', 'somemachine.python.org'),))}

        cert2 = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                 'subject': ((('countryName', 'US'),),
                             (('stateOrProvinceName', 'Delaware'),),
                             (('localityName', 'Wilmington'),),
                             (('organizationName', 'Python Software Foundation'),),
                             (('organizationalUnitName', 'SSL'),),
                             (('commonName', 'somemachine.python.org'),)),
                 'subjectAltName': ((('DNS', 'foo.alt.name')),
                                    (('DNS', 'foo.alt.name.1')))}

        self.assertEqual(self.httplib_object._get_subject_alt_names(cert=cert1),
                         [])

        alt_names = self.httplib_object._get_subject_alt_names(cert=cert2)
        self.assertEqual(len(alt_names), 2)
        self.assertTrue('foo.alt.name' in alt_names)
        self.assertTrue('foo.alt.name.1' in alt_names)

    def test_get_common_name(self):
        cert = {'notAfter': 'Feb 16 16:54:50 2013 GMT',
                'subject': ((('countryName', 'US'),),
                            (('stateOrProvinceName', 'Delaware'),),
                            (('localityName', 'Wilmington'),),
                            (('organizationName', 'Python Software Foundation'),),
                            (('organizationalUnitName', 'SSL'),),
                            (('commonName', 'somemachine.python.org'),))}

        self.assertEqual(self.httplib_object._get_common_name(cert)[0],
                         'somemachine.python.org')
        self.assertEqual(self.httplib_object._get_common_name({}),
                         None)

    @patch('warnings.warn')
    def test_setup_verify(self, _):
        libcloud.security.CA_CERTS_PATH = []

        # Should throw a runtime error
        libcloud.security.VERIFY_SSL_CERT = True

        expected_msg = libcloud.security.CA_CERTS_UNAVAILABLE_ERROR_MSG
        self.assertRaisesRegexp(RuntimeError, expected_msg,
                                self.httplib_object._setup_verify)

        libcloud.security.VERIFY_SSL_CERT = False
        self.httplib_object._setup_verify()

    @patch('warnings.warn')
    def test_setup_ca_cert(self, _):
        # verify = False, _setup_ca_cert should be a no-op
        self.httplib_object.verify = False
        self.httplib_object._setup_ca_cert()

        self.assertEqual(self.httplib_object.ca_cert, None)

        # verify = True, a valid path is provided, self.ca_cert should be set to
        # a valid path
        self.httplib_object.verify = True

        libcloud.security.CA_CERTS_PATH = [os.path.abspath(__file__)]
        self.httplib_object._setup_ca_cert()

        self.assertTrue(self.httplib_object.ca_cert is not None)

        # verify = True, no CA certs are available, exception should be thrown
        libcloud.security.CA_CERTS_PATH = []

        expected_msg = libcloud.security.CA_CERTS_UNAVAILABLE_ERROR_MSG
        self.assertRaisesRegexp(RuntimeError, expected_msg,
                                self.httplib_object._setup_ca_cert)


if __name__ == '__main__':
    sys.exit(unittest.main())
