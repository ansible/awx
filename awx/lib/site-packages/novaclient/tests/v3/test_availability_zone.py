# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from novaclient.tests.v1_1 import test_availability_zone
from novaclient.tests.v3 import fakes
from novaclient.v3 import availability_zones


class AvailabilityZoneTest(test_availability_zone.AvailabilityZoneTest):
    from novaclient.v3 import shell  # noqa

    def setUp(self):
        super(AvailabilityZoneTest, self).setUp()
        self.cs = self._get_fake_client()
        self.availability_zone_type = self._get_availability_zone_type()

    def _assertZone(self, zone, name, status):
        self.assertEqual(zone.zone_name, name)
        self.assertEqual(zone.zone_state, status)

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_availability_zone_type(self):
        return availability_zones.AvailabilityZone
