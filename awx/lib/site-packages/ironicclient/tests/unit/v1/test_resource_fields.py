# -*- coding: utf-8 -*-

#    Copyright (c) 2015 Intel Corporation
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

import testtools

from ironicclient.v1 import resource_fields


class ResourceFieldsTest(testtools.TestCase):

    def test_chassis_fields(self):
        self.assertEqual(
            len(resource_fields.CHASSIS_FIELDS),
            len(resource_fields.CHASSIS_FIELD_LABELS))

    def test_chassis_list_fields(self):
        self.assertEqual(
            len(resource_fields.CHASSIS_LIST_FIELDS),
            len(resource_fields.CHASSIS_LIST_FIELD_LABELS))

    def test_node_fields(self):
        self.assertEqual(
            len(resource_fields.NODE_FIELDS),
            len(resource_fields.NODE_FIELD_LABELS))

    def test_node_list_fields(self):
        self.assertEqual(
            len(resource_fields.NODE_LIST_FIELDS),
            len(resource_fields.NODE_LIST_FIELD_LABELS))

    def test_port_fields(self):
        self.assertEqual(
            len(resource_fields.PORT_FIELDS),
            len(resource_fields.PORT_FIELD_LABELS))

    def test_port_list_fields(self):
        self.assertEqual(
            len(resource_fields.PORT_LIST_FIELDS),
            len(resource_fields.PORT_LIST_FIELD_LABELS))
