# Copyright (C) 2013 Hewlett-Packard Development Company, L.P.
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
from cinderclient.tests.v1 import fakes


cs = fakes.FakeClient()


class VolumeTransfersTest(utils.TestCase):

    def test_create(self):
        cs.transfers.create('1234')
        cs.assert_called('POST', '/os-volume-transfer')

    def test_get(self):
        transfer_id = '5678'
        cs.transfers.get(transfer_id)
        cs.assert_called('GET', '/os-volume-transfer/%s' % transfer_id)

    def test_list(self):
        cs.transfers.list()
        cs.assert_called('GET', '/os-volume-transfer/detail')

    def test_delete(self):
        b = cs.transfers.list()[0]
        b.delete()
        cs.assert_called('DELETE', '/os-volume-transfer/5678')
        cs.transfers.delete('5678')
        cs.assert_called('DELETE', '/os-volume-transfer/5678')
        cs.transfers.delete(b)
        cs.assert_called('DELETE', '/os-volume-transfer/5678')

    def test_accept(self):
        transfer_id = '5678'
        auth_key = '12345'
        cs.transfers.accept(transfer_id, auth_key)
        cs.assert_called('POST', '/os-volume-transfer/%s/accept' % transfer_id)
