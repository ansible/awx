# Copyright (c) 2012 Intel Corporation.
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

import uuid

from oslotest import base as test_base

from oslo_utils import uuidutils


class UUIDUtilsTest(test_base.BaseTestCase):

    def test_generate_uuid(self):
        uuid_string = uuidutils.generate_uuid()
        self.assertTrue(isinstance(uuid_string, str))
        self.assertEqual(len(uuid_string), 36)
        # make sure there are 4 dashes
        self.assertEqual(len(uuid_string.replace('-', '')), 32)

    def test_is_uuid_like(self):
        self.assertTrue(uuidutils.is_uuid_like(str(uuid.uuid4())))
        self.assertTrue(uuidutils.is_uuid_like(
            '{12345678-1234-5678-1234-567812345678}'))
        self.assertTrue(uuidutils.is_uuid_like(
            '12345678123456781234567812345678'))
        self.assertTrue(uuidutils.is_uuid_like(
            'urn:uuid:12345678-1234-5678-1234-567812345678'))
        self.assertTrue(uuidutils.is_uuid_like(
            'urn:bbbaaaaa-aaaa-aaaa-aabb-bbbbbbbbbbbb'))
        self.assertTrue(uuidutils.is_uuid_like(
            'uuid:bbbaaaaa-aaaa-aaaa-aabb-bbbbbbbbbbbb'))
        self.assertTrue(uuidutils.is_uuid_like(
            '{}---bbb---aaa--aaa--aaa-----aaa---aaa--bbb-bbb---bbb-bbb-bb-{}'))

    def test_is_uuid_like_insensitive(self):
        self.assertTrue(uuidutils.is_uuid_like(str(uuid.uuid4()).upper()))

    def test_id_is_uuid_like(self):
        self.assertFalse(uuidutils.is_uuid_like(1234567))

    def test_name_is_uuid_like(self):
        self.assertFalse(uuidutils.is_uuid_like('zhongyueluo'))
