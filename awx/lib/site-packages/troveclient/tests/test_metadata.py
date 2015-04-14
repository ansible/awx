# Copyright 2014 Rackspace Hosting
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

import json
import mock
import testtools
from troveclient.v1 import metadata


class TestMetadata(testtools.TestCase):
    def setUp(self):
        super(TestMetadata, self).setUp()
        self.orig__init = metadata.Metadata.__init__
        metadata.Metadata.__init__ = mock.Mock(return_value=None)
        self.metadata = metadata.Metadata()
        self.metadata.manager = mock.Mock()
        self.metadata.api = mock.Mock()
        self.metadata.api.client = mock.Mock()

        self.instance_uuid = '3fbc8d6d-3f87-41d9-a4a1-060830dc6c4c'
        self.metadata_key = 'metakey'
        self.new_metadata_key = 'newmetakey'
        self.metadata_value = {'metavalue': [1, 2, 3]}

    def tearDown(self):
        super(TestMetadata, self).tearDown()
        metadata.Metadata.__init__ = self.orig__init

    def test_list(self):
        def side_effect_func(path, config):
            return path, config

        self.metadata._get = mock.Mock(side_effect=side_effect_func)
        path, config = self.metadata.list(self.instance_uuid)
        self.assertEqual('/instances/%s/metadata' % self.instance_uuid, path)
        self.assertEqual('metadata', config)

    def test_show(self):
        def side_effect_func(path, config):
            return path, config

        self.metadata._get = mock.Mock(side_effect=side_effect_func)
        path, config = self.metadata.show(self.instance_uuid,
                                          self.metadata_key)
        self.assertEqual('/instances/%s/metadata/%s' %
                         (self.instance_uuid, self.metadata_key), path)
        self.assertEqual('metadata', config)

    def test_create(self):
        def side_effect_func(path, body, config):
            return path, body, config

        create_body = {
            'metadata': {
                'value': self.metadata_value
            }
        }

        self.metadata._create = mock.Mock(side_effect=side_effect_func)
        path, body, config = self.metadata.create(self.instance_uuid,
                                                  self.metadata_key,
                                                  self.metadata_value)
        self.assertEqual('/instances/%s/metadata/%s' %
                         (self.instance_uuid, self.metadata_key), path)
        self.assertEqual(create_body, body)
        self.assertEqual('metadata', config)

    def test_edit(self):
        def side_effect_func(path, body):
            return path, body

        edit_body = {
            'metadata': {
                'value': self.metadata_value
            }
        }

        self.metadata._edit = mock.Mock(side_effect=side_effect_func)
        path, body = self.metadata.edit(self.instance_uuid,
                                        self.metadata_key,
                                        self.metadata_value)
        self.assertEqual('/instances/%s/metadata/%s' %
                         (self.instance_uuid, self.metadata_key), path)
        self.assertEqual(edit_body, body)

    def test_update(self):
        def side_effect_func(path, body):
            return path, body

        update_body = {
            'metadata': {
                'key': self.new_metadata_key,
                'value': self.metadata_value
            }
        }

        self.metadata._update = mock.Mock(side_effect=side_effect_func)
        path, body = self.metadata.update(self.instance_uuid,
                                          self.metadata_key,
                                          self.new_metadata_key,
                                          self.metadata_value)
        self.assertEqual('/instances/%s/metadata/%s' %
                         (self.instance_uuid, self.metadata_key), path)
        self.assertEqual(update_body, body)

    def test_delete(self):
        def side_effect_func(path):
            return path

        self.metadata._delete = mock.Mock(side_effect=side_effect_func)
        path = self.metadata.delete(self.instance_uuid, self.metadata_key)
        self.assertEqual('/instances/%s/metadata/%s' %
                         (self.instance_uuid, self.metadata_key), path)

    def test_parse_value_valid_json_in(self):
        value = {'one': [2, 3, 4]}
        ser_value = json.dumps(value)
        new_value = self.metadata._parse_value(ser_value)
        self.assertEqual(value, new_value)

    def test_parse_value_string_in(self):
        value = 'this is a string'
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_dict_in(self):
        value = {'one': [2, 3, 4]}
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_list_in(self):
        value = [2, 3, 4]
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_tuple_in(self):
        value = (2, 3, 4)
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_float_in(self):
        value = 1.32
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_int_in(self):
        value = 1
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)

    def test_parse_value_invalid_json_in(self):
        # NOTE(imsplitbit): it's worth mentioning here and in the code that
        # if you give _parse_value invalid json you get the string passed back
        # to you.
        value = "{'one': [2, 3, 4]}"
        new_value = self.metadata._parse_value(value)
        self.assertEqual(value, new_value)
