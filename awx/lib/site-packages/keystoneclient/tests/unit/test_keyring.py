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

import datetime

import mock
from oslo_utils import timeutils

from keystoneclient import access
from keystoneclient import httpclient
from keystoneclient.tests.unit import utils
from keystoneclient.tests.unit.v2_0 import client_fixtures

try:
    import keyring  # noqa
    import pickle  # noqa
except ImportError:
    keyring = None


PROJECT_SCOPED_TOKEN = client_fixtures.project_scoped_token()

# These mirror values from PROJECT_SCOPED_TOKEN
USERNAME = 'exampleuser'
AUTH_URL = 'http://public.com:5000/v2.0'
TOKEN = '04c7d5ffaeef485f9dc69c06db285bdb'

PASSWORD = 'password'
TENANT = 'tenant'
TENANT_ID = 'tenant_id'


class KeyringTest(utils.TestCase):

    def setUp(self):
        if keyring is None:
            self.skipTest(
                'optional package keyring or pickle is not installed')

        class MemoryKeyring(keyring.backend.KeyringBackend):
            """A Simple testing keyring.

            This class supports stubbing an initial password to be returned by
            setting password, and allows easy password and key retrieval. Also
            records if a password was retrieved.
            """
            def __init__(self):
                self.key = None
                self.password = None
                self.fetched = False
                self.get_password_called = False
                self.set_password_called = False

            def supported(self):
                return 1

            def get_password(self, service, username):
                self.get_password_called = True
                key = username + '@' + service
                # make sure we don't get passwords crossed if one is enforced.
                if self.key and self.key != key:
                    return None
                if self.password:
                    self.fetched = True
                return self.password

            def set_password(self, service, username, password):
                self.set_password_called = True
                self.key = username + '@' + service
                self.password = password

        super(KeyringTest, self).setUp()
        self.memory_keyring = MemoryKeyring()
        keyring.set_keyring(self.memory_keyring)

    def test_no_keyring_key(self):
        """Ensure that if we don't have use_keyring set in the client that
        the keyring is never accessed.
        """
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL)

        # stub and check that a new token is received
        method = 'get_raw_token_from_identity_service'
        with mock.patch.object(cl, method) as meth:
            meth.return_value = (True, PROJECT_SCOPED_TOKEN)

            self.assertTrue(cl.authenticate())

            self.assertEqual(1, meth.call_count)

        # make sure that we never touched the keyring
        self.assertFalse(self.memory_keyring.get_password_called)
        self.assertFalse(self.memory_keyring.set_password_called)

    def test_build_keyring_key(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL)

        keyring_key = cl._build_keyring_key(auth_url=AUTH_URL,
                                            username=USERNAME,
                                            tenant_name=TENANT,
                                            tenant_id=TENANT_ID,
                                            token=TOKEN)

        self.assertEqual(keyring_key,
                         '%s/%s/%s/%s/%s' %
                         (AUTH_URL, TENANT_ID, TENANT, TOKEN, USERNAME))

    def test_set_and_get_keyring_expired(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL,
                                   use_keyring=True)

        # set an expired token into the keyring
        auth_ref = access.AccessInfo.factory(body=PROJECT_SCOPED_TOKEN)
        expired = timeutils.utcnow() - datetime.timedelta(minutes=30)
        auth_ref['token']['expires'] = timeutils.isotime(expired)
        self.memory_keyring.password = pickle.dumps(auth_ref)

        # stub and check that a new token is received, so not using expired
        method = 'get_raw_token_from_identity_service'
        with mock.patch.object(cl, method) as meth:
            meth.return_value = (True, PROJECT_SCOPED_TOKEN)

            self.assertTrue(cl.authenticate())

            self.assertEqual(1, meth.call_count)

        # check that a value was returned from the keyring
        self.assertTrue(self.memory_keyring.fetched)

        # check that the new token has been loaded into the keyring
        new_auth_ref = pickle.loads(self.memory_keyring.password)
        self.assertEqual(new_auth_ref['token']['expires'],
                         PROJECT_SCOPED_TOKEN['access']['token']['expires'])

    def test_get_keyring(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL,
                                   use_keyring=True)

        # set an token into the keyring
        auth_ref = access.AccessInfo.factory(body=PROJECT_SCOPED_TOKEN)
        future = timeutils.utcnow() + datetime.timedelta(minutes=30)
        auth_ref['token']['expires'] = timeutils.isotime(future)
        self.memory_keyring.password = pickle.dumps(auth_ref)

        # don't stub get_raw_token so will fail if authenticate happens

        self.assertTrue(cl.authenticate())
        self.assertTrue(self.memory_keyring.fetched)

    def test_set_keyring(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL,
                                   use_keyring=True)

        # stub and check that a new token is received
        method = 'get_raw_token_from_identity_service'
        with mock.patch.object(cl, method) as meth:
            meth.return_value = (True, PROJECT_SCOPED_TOKEN)

            self.assertTrue(cl.authenticate())

            self.assertEqual(1, meth.call_count)

        # we checked the keyring, but we didn't find anything
        self.assertTrue(self.memory_keyring.get_password_called)
        self.assertFalse(self.memory_keyring.fetched)

        # check that the new token has been loaded into the keyring
        self.assertTrue(self.memory_keyring.set_password_called)
        new_auth_ref = pickle.loads(self.memory_keyring.password)
        self.assertEqual(new_auth_ref.auth_token, TOKEN)
        self.assertEqual(new_auth_ref['token'],
                         PROJECT_SCOPED_TOKEN['access']['token'])
        self.assertEqual(new_auth_ref.username, USERNAME)
