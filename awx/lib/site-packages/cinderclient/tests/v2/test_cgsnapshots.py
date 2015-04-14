# Copyright (C) 2012 - 2014 EMC Corporation.
#
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

from cinderclient.tests import utils
from cinderclient.tests.v2 import fakes


cs = fakes.FakeClient()


class cgsnapshotsTest(utils.TestCase):

    def test_delete_cgsnapshot(self):
        v = cs.cgsnapshots.list()[0]
        v.delete()
        cs.assert_called('DELETE', '/cgsnapshots/1234')
        cs.cgsnapshots.delete('1234')
        cs.assert_called('DELETE', '/cgsnapshots/1234')
        cs.cgsnapshots.delete(v)
        cs.assert_called('DELETE', '/cgsnapshots/1234')

    def test_create_cgsnapshot(self):
        cs.cgsnapshots.create('cgsnap')
        cs.assert_called('POST', '/cgsnapshots')

    def test_create_cgsnapshot_with_cg_id(self):
        cs.cgsnapshots.create('1234')
        expected = {'cgsnapshot': {'status': 'creating',
                                   'description': None,
                                   'user_id': None,
                                   'name': None,
                                   'consistencygroup_id': '1234',
                                   'project_id': None}}
        cs.assert_called('POST', '/cgsnapshots', body=expected)

    def test_list_cgsnapshot(self):
        cs.cgsnapshots.list()
        cs.assert_called('GET', '/cgsnapshots/detail')

    def test_get_cgsnapshot(self):
        cgsnapshot_id = '1234'
        cs.cgsnapshots.get(cgsnapshot_id)
        cs.assert_called('GET', '/cgsnapshots/%s' % cgsnapshot_id)
