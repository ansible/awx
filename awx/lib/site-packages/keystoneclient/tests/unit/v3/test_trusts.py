# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

from oslo_utils import timeutils

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3.contrib import trusts


class TrustTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(TrustTests, self).setUp()
        self.key = 'trust'
        self.collection_key = 'trusts'
        self.model = trusts.Trust
        self.manager = self.client.trusts
        self.path_prefix = 'OS-TRUST'

    def new_ref(self, **kwargs):
        kwargs = super(TrustTests, self).new_ref(**kwargs)
        kwargs.setdefault('project_id', uuid.uuid4().hex)
        return kwargs

    def test_create(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = False
        super(TrustTests, self).test_create(ref=ref)

    def test_create_limited_uses(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = False
        ref['remaining_uses'] = 5
        super(TrustTests, self).test_create(ref=ref)

    def test_create_roles(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = False
        req_ref = ref.copy()
        req_ref.pop('id')

        # Note the TrustManager takes a list of role_names, and converts
        # internally to the slightly odd list-of-dict API format, so we
        # have to pass the expected request data to allow correct stubbing
        ref['role_names'] = ['atestrole']
        req_ref['roles'] = [{'name': 'atestrole'}]
        super(TrustTests, self).test_create(ref=ref, req_ref=req_ref)

    def test_create_expires(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = False
        ref['expires_at'] = timeutils.parse_isotime(
            '2013-03-04T12:00:01.000000Z')
        req_ref = ref.copy()
        req_ref.pop('id')

        # Note the TrustManager takes a datetime.datetime object for
        # expires_at, and converts it internally into an iso format datestamp
        req_ref['expires_at'] = '2013-03-04T12:00:01.000000Z'
        super(TrustTests, self).test_create(ref=ref, req_ref=req_ref)

    def test_create_imp(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = True
        super(TrustTests, self).test_create(ref=ref)

    def test_create_roles_imp(self):
        ref = self.new_ref()
        ref['trustor_user_id'] = uuid.uuid4().hex
        ref['trustee_user_id'] = uuid.uuid4().hex
        ref['impersonation'] = True
        req_ref = ref.copy()
        req_ref.pop('id')
        ref['role_names'] = ['atestrole']
        req_ref['roles'] = [{'name': 'atestrole'}]
        super(TrustTests, self).test_create(ref=ref, req_ref=req_ref)

    def test_list_filter_trustor(self):
        expected_query = {'trustor_user_id': '12345'}
        super(TrustTests, self).test_list(expected_query=expected_query,
                                          trustor_user='12345')

    def test_list_filter_trustee(self):
        expected_query = {'trustee_user_id': '12345'}
        super(TrustTests, self).test_list(expected_query=expected_query,
                                          trustee_user='12345')

    def test_update(self):
        # Update not supported for the OS-TRUST API
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.update)
