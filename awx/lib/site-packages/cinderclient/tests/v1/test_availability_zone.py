# Copyright 2011-2013 OpenStack Foundation
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

import six

from cinderclient.v1 import availability_zones
from cinderclient.v1 import shell
from cinderclient.tests.fixture_data import client
from cinderclient.tests.fixture_data import availability_zones as azfixture
from cinderclient.tests import utils


class AvailabilityZoneTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = azfixture.Fixture

    def _assertZone(self, zone, name, status):
        self.assertEqual(name, zone.zoneName)
        self.assertEqual(status, zone.zoneState)

    def test_list_availability_zone(self):
        zones = self.cs.availability_zones.list(detailed=False)
        self.assert_called('GET', '/os-availability-zone')

        for zone in zones:
            self.assertIsInstance(zone,
                                  availability_zones.AvailabilityZone)

        self.assertEqual(2, len(zones))

        l0 = [six.u('zone-1'), six.u('available')]
        l1 = [six.u('zone-2'), six.u('not available')]

        z0 = shell._treeizeAvailabilityZone(zones[0])
        z1 = shell._treeizeAvailabilityZone(zones[1])

        self.assertEqual((1, 1), (len(z0), len(z1)))

        self._assertZone(z0[0], l0[0], l0[1])
        self._assertZone(z1[0], l1[0], l1[1])

    def test_detail_availability_zone(self):
        zones = self.cs.availability_zones.list(detailed=True)
        self.assert_called('GET', '/os-availability-zone/detail')

        for zone in zones:
            self.assertIsInstance(zone,
                                  availability_zones.AvailabilityZone)

        self.assertEqual(3, len(zones))

        l0 = [six.u('zone-1'), six.u('available')]
        l1 = [six.u('|- fake_host-1'), six.u('')]
        l2 = [six.u('| |- cinder-volume'),
              six.u('enabled :-) 2012-12-26 14:45:25')]
        l3 = [six.u('internal'), six.u('available')]
        l4 = [six.u('|- fake_host-1'), six.u('')]
        l5 = [six.u('| |- cinder-sched'),
              six.u('enabled :-) 2012-12-26 14:45:24')]
        l6 = [six.u('zone-2'), six.u('not available')]

        z0 = shell._treeizeAvailabilityZone(zones[0])
        z1 = shell._treeizeAvailabilityZone(zones[1])
        z2 = shell._treeizeAvailabilityZone(zones[2])

        self.assertEqual((3, 3, 1), (len(z0), len(z1), len(z2)))

        self._assertZone(z0[0], l0[0], l0[1])
        self._assertZone(z0[1], l1[0], l1[1])
        self._assertZone(z0[2], l2[0], l2[1])
        self._assertZone(z1[0], l3[0], l3[1])
        self._assertZone(z1[1], l4[0], l4[1])
        self._assertZone(z1[2], l5[0], l5[1])
        self._assertZone(z2[0], l6[0], l6[1])
