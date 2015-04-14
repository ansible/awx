# Copyright 2013 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

import mock
import testtools
import uuid

from troveclient.v1 import backups

"""
Unit tests for backups.py
"""


class BackupTest(testtools.TestCase):

    def setUp(self):
        super(BackupTest, self).setUp()
        self.backup_id = str(uuid.uuid4())
        self.info = {'name': 'my backup', 'id': self.backup_id}
        self.api = mock.Mock()
        self.manager = backups.Backups(self.api)
        self.backup = backups.Backup(self.manager, self.info)

    def tearDown(self):
        super(BackupTest, self).tearDown()

    def test___repr__(self):
        self.assertEqual('<Backup: my backup>', repr(self.backup))


class BackupManagerTest(testtools.TestCase):

    def setUp(self):
        super(BackupManagerTest, self).setUp()
        self.backups = backups.Backups(mock.Mock())
        self.instance_with_id = mock.Mock()
        self.instance_with_id.id = 215

    def tearDown(self):
        super(BackupManagerTest, self).tearDown()

    def test_create(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1'}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_description(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'description': 'foo'}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_with_instance_obj(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': self.instance_with_id.id}
        body = {'backup': args}
        self.backups.create('test_backup', self.instance_with_id)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_incremental(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'parent_id': 'foo'}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_copy(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'backup': '1'}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_list(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        self.backups.list(limit, marker)
        page_mock.assert_called_with("/backups", "backups", limit, marker, {})

    def test_list_by_datastore(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        datastore = "test-mysql"
        self.backups.list(limit, marker, datastore)
        page_mock.assert_called_with("/backups", "backups", limit, marker,
                                     {'datastore': datastore})

    def test_get(self):
        get_mock = mock.Mock()
        self.backups._get = get_mock
        self.backups.get(1)
        get_mock.assert_called_with('/backups/1', 'backup')

    def test_delete(self):
        resp = mock.Mock()
        resp.status_code = 200
        delete_mock = mock.Mock(return_value=(resp, None))
        self.backups.api.client.delete = delete_mock
        self.backups.delete('backup1')
        delete_mock.assert_called_with('/backups/backup1')

    def test_delete_500(self):
        resp = mock.Mock()
        resp.status_code = 500
        self.backups.api.client.delete = mock.Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.backups.delete, 'backup1')

    def test_delete_422(self):
        resp = mock.Mock()
        resp.status_code = 422
        self.backups.api.client.delete = mock.Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.backups.delete, 'backup1')
