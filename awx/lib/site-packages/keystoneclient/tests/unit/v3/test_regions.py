# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import uuid


from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import regions


class RegionTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(RegionTests, self).setUp()
        self.key = 'region'
        self.collection_key = 'regions'
        self.model = regions.Region
        self.manager = self.client.regions

    def new_ref(self, **kwargs):
        kwargs = super(RegionTests, self).new_ref(**kwargs)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('id', uuid.uuid4().hex)
        return kwargs

    def test_update_enabled_defaults_to_none(self):
        super(RegionTests, self).test_update(
            req_ref={'description': uuid.uuid4().hex})
