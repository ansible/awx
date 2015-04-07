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

import errno
import os
import subprocess

import mock
import testresources
from testtools import matchers

from keystoneclient.common import cms
from keystoneclient import exceptions
from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit import utils


class CMSTest(utils.TestCase, testresources.ResourcedTestCase):

    """Unit tests for the keystoneclient.common.cms module."""

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def __init__(self, *args, **kwargs):
        super(CMSTest, self).__init__(*args, **kwargs)
        process = subprocess.Popen(['openssl', 'version'],
                                   stdout=subprocess.PIPE)
        out, err = process.communicate()
        # Example output: 'OpenSSL 0.9.8za 5 Jun 2014'
        openssl_version = out.split()[1]

        if err or openssl_version.startswith(b'0'):
            raise Exception('Your version of OpenSSL is not supported. '
                            'You will need to update it to 1.0 or later.')

    def test_cms_verify(self):
        self.assertRaises(exceptions.CertificateConfigError,
                          cms.cms_verify,
                          'data',
                          'no_exist_cert_file',
                          'no_exist_ca_file')

    def test_token_tocms_to_token(self):
        with open(os.path.join(client_fixtures.CMSDIR,
                               'auth_token_scoped.pem')) as f:
            AUTH_TOKEN_SCOPED_CMS = f.read()

        self.assertEqual(cms.token_to_cms(self.examples.SIGNED_TOKEN_SCOPED),
                         AUTH_TOKEN_SCOPED_CMS)

        tok = cms.cms_to_token(cms.token_to_cms(
            self.examples.SIGNED_TOKEN_SCOPED))
        self.assertEqual(tok, self.examples.SIGNED_TOKEN_SCOPED)

    def test_asn1_token(self):
        self.assertTrue(cms.is_asn1_token(self.examples.SIGNED_TOKEN_SCOPED))
        self.assertFalse(cms.is_asn1_token('FOOBAR'))

    def test_cms_sign_token_no_files(self):
        self.assertRaises(subprocess.CalledProcessError,
                          cms.cms_sign_token,
                          self.examples.TOKEN_SCOPED_DATA,
                          '/no/such/file', '/no/such/key')

    def test_cms_sign_token_no_files_pkiz(self):
        self.assertRaises(subprocess.CalledProcessError,
                          cms.pkiz_sign,
                          self.examples.TOKEN_SCOPED_DATA,
                          '/no/such/file', '/no/such/key')

    def test_cms_sign_token_success(self):
        self.assertTrue(
            cms.pkiz_sign(self.examples.TOKEN_SCOPED_DATA,
                          self.examples.SIGNING_CERT_FILE,
                          self.examples.SIGNING_KEY_FILE))

    def test_cms_verify_token_no_files(self):
        self.assertRaises(exceptions.CertificateConfigError,
                          cms.cms_verify,
                          self.examples.SIGNED_TOKEN_SCOPED,
                          '/no/such/file', '/no/such/key')

    def test_cms_verify_token_no_oserror(self):
        def raise_OSError(*args):
            e = OSError()
            e.errno = errno.EPIPE
            raise e

        with mock.patch('subprocess.Popen.communicate', new=raise_OSError):
            try:
                cms.cms_verify("x", '/no/such/file', '/no/such/key')
            except exceptions.CertificateConfigError as e:
                self.assertIn('/no/such/file', e.output)
                self.assertIn('Hit OSError ', e.output)
            else:
                self.fail('Expected exceptions.CertificateConfigError')

    def test_cms_verify_token_scoped(self):
        cms_content = cms.token_to_cms(self.examples.SIGNED_TOKEN_SCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       self.examples.SIGNING_CERT_FILE,
                                       self.examples.SIGNING_CA_FILE))

    def test_cms_verify_token_scoped_expired(self):
        cms_content = cms.token_to_cms(
            self.examples.SIGNED_TOKEN_SCOPED_EXPIRED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       self.examples.SIGNING_CERT_FILE,
                                       self.examples.SIGNING_CA_FILE))

    def test_cms_verify_token_unscoped(self):
        cms_content = cms.token_to_cms(self.examples.SIGNED_TOKEN_UNSCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       self.examples.SIGNING_CERT_FILE,
                                       self.examples.SIGNING_CA_FILE))

    def test_cms_verify_token_v3_scoped(self):
        cms_content = cms.token_to_cms(self.examples.SIGNED_v3_TOKEN_SCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       self.examples.SIGNING_CERT_FILE,
                                       self.examples.SIGNING_CA_FILE))

    def test_cms_hash_token_no_token_id(self):
        token_id = None
        self.assertThat(cms.cms_hash_token(token_id), matchers.Is(None))

    def test_cms_hash_token_not_pki(self):
        """If the token_id is not a PKI token then it returns the token_id."""
        token = 'something'
        self.assertFalse(cms.is_asn1_token(token))
        self.assertThat(cms.cms_hash_token(token), matchers.Is(token))

    def test_cms_hash_token_default_md5(self):
        """The default hash method is md5."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        token_id_default = cms.cms_hash_token(token)
        token_id_md5 = cms.cms_hash_token(token, mode='md5')
        self.assertThat(token_id_default, matchers.Equals(token_id_md5))
        # md5 hash is 32 chars.
        self.assertThat(token_id_default, matchers.HasLength(32))

    def test_cms_hash_token_sha256(self):
        """Can also hash with sha256."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        token_id = cms.cms_hash_token(token, mode='sha256')
        # sha256 hash is 64 chars.
        self.assertThat(token_id, matchers.HasLength(64))


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
