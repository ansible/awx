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
from keystoneclient.v3 import domains


class DomainTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(DomainTests, self).setUp()
        self.key = 'domain'
        self.collection_key = 'domains'
        self.model = domains.Domain
        self.manager = self.client.domains

    def new_ref(self, **kwargs):
        kwargs = super(DomainTests, self).new_ref(**kwargs)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_list_filter_name(self):
        super(DomainTests, self).test_list(name='adomain123')

    def test_list_filter_enabled(self):
        super(DomainTests, self).test_list(enabled=True)

    def test_list_filter_disabled(self):
        # False is converted to '0' ref bug #1267530
        expected_query = {'enabled': '0'}
        super(DomainTests, self).test_list(expected_query=expected_query,
                                           enabled=False)

    def test_update_enabled_defaults_to_none(self):
        super(DomainTests, self).test_update(
            req_ref={'name': uuid.uuid4().hex})
