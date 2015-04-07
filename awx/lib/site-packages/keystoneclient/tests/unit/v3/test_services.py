# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import services


class ServiceTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ServiceTests, self).setUp()
        self.key = 'service'
        self.collection_key = 'services'
        self.model = services.Service
        self.manager = self.client.services

    def new_ref(self, **kwargs):
        kwargs = super(ServiceTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs

    def test_list_filter_name(self):
        filter_name = uuid.uuid4().hex
        expected_query = {'name': filter_name}
        super(ServiceTests, self).test_list(expected_query=expected_query,
                                            name=filter_name)

    def test_list_filter_type(self):
        filter_type = uuid.uuid4().hex
        expected_query = {'type': filter_type}
        super(ServiceTests, self).test_list(expected_query=expected_query,
                                            type=filter_type)
