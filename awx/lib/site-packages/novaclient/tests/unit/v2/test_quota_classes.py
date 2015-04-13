# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
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

from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes


cs = fakes.FakeClient()


class QuotaClassSetsTest(utils.TestCase):

    def test_class_quotas_get(self):
        class_name = 'test'
        cs.quota_classes.get(class_name)
        cs.assert_called('GET', '/os-quota-class-sets/%s' % class_name)

    def test_update_quota(self):
        q = cs.quota_classes.get('test')
        q.update(cores=2)
        cs.assert_called('PUT', '/os-quota-class-sets/test')

    def test_refresh_quota(self):
        q = cs.quota_classes.get('test')
        q2 = cs.quota_classes.get('test')
        self.assertEqual(q.cores, q2.cores)
        q2.cores = 0
        self.assertNotEqual(q.cores, q2.cores)
        q2.get()
        self.assertEqual(q.cores, q2.cores)
