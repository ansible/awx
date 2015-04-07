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

import uuid

from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import credentials


class CredentialTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(CredentialTests, self).setUp()
        self.key = 'credential'
        self.collection_key = 'credentials'
        self.model = credentials.Credential
        self.manager = self.client.credentials

    def new_ref(self, **kwargs):
        kwargs = super(CredentialTests, self).new_ref(**kwargs)
        kwargs.setdefault('blob', uuid.uuid4().hex)
        kwargs.setdefault('project_id', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('user_id', uuid.uuid4().hex)
        return kwargs

    @staticmethod
    def _ref_data_not_blob(ref):
        ret_ref = ref.copy()
        ret_ref['data'] = ref['blob']
        del ret_ref['blob']
        return ret_ref

    def test_create_data_not_blob(self):
        # Test create operation with previous, deprecated "data" argument,
        # which should be translated into "blob" at the API call level
        req_ref = self.new_ref()
        api_ref = self._ref_data_not_blob(req_ref)
        req_ref.pop('id')
        self.test_create(api_ref, req_ref)

    def test_update_data_not_blob(self):
        # Likewise test update operation with data instead of blob argument
        req_ref = self.new_ref()
        api_ref = self._ref_data_not_blob(req_ref)
        self.test_update(api_ref, req_ref)
