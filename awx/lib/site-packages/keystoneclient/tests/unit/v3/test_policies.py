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
from keystoneclient.v3 import policies


class PolicyTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(PolicyTests, self).setUp()
        self.key = 'policy'
        self.collection_key = 'policies'
        self.model = policies.Policy
        self.manager = self.client.policies

    def new_ref(self, **kwargs):
        kwargs = super(PolicyTests, self).new_ref(**kwargs)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('blob', uuid.uuid4().hex)
        return kwargs
