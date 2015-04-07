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


class VolumeBackupsTest(utils.TestCase):

    def test_create(self):
        cs.backups.create('2b695faf-b963-40c8-8464-274008fbcef4')
        cs.assert_called('POST', '/backups')

    def test_get(self):
        backup_id = '76a17945-3c6f-435c-975b-b5685db10b62'
        cs.backups.get(backup_id)
        cs.assert_called('GET', '/backups/%s' % backup_id)

    def test_list(self):
        cs.backups.list()
        cs.assert_called('GET', '/backups/detail')

    def test_delete(self):
        b = cs.backups.list()[0]
        b.delete()
        cs.assert_called('DELETE',
                         '/backups/76a17945-3c6f-435c-975b-b5685db10b62')
        cs.backups.delete('76a17945-3c6f-435c-975b-b5685db10b62')
        cs.assert_called('DELETE',
                         '/backups/76a17945-3c6f-435c-975b-b5685db10b62')
        cs.backups.delete(b)
        cs.assert_called('DELETE',
                         '/backups/76a17945-3c6f-435c-975b-b5685db10b62')

    def test_restore(self):
        backup_id = '76a17945-3c6f-435c-975b-b5685db10b62'
        cs.restores.restore(backup_id)
        cs.assert_called('POST', '/backups/%s/restore' % backup_id)
