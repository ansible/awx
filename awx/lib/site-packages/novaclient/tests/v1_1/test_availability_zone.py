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

import six

from novaclient.v1_1 import availability_zones
from novaclient.v1_1 import shell
from novaclient.tests.v1_1 import fakes
from novaclient.tests import utils


cs = fakes.FakeClient()


class AvailabilityZoneTest(utils.TestCase):

    def _assertZone(self, zone, name, status):
        self.assertEqual(zone.zoneName, name)
        self.assertEqual(zone.zoneState, status)

    def test_list_availability_zone(self):
        zones = cs.availability_zones.list(detailed=False)
        cs.assert_called('GET', '/os-availability-zone')

        for zone in zones:
            self.assertTrue(isinstance(zone,
                                       availability_zones.AvailabilityZone))

        self.assertEqual(2, len(zones))

        l0 = [six.u('zone-1'), six.u('available')]
        l1 = [six.u('zone-2'), six.u('not available')]

        z0 = shell._treeizeAvailabilityZone(zones[0])
        z1 = shell._treeizeAvailabilityZone(zones[1])

        self.assertEqual((len(z0), len(z1)), (1, 1))

        self._assertZone(z0[0], l0[0], l0[1])
        self._assertZone(z1[0], l1[0], l1[1])

    def test_detail_availability_zone(self):
        zones = cs.availability_zones.list(detailed=True)
        cs.assert_called('GET', '/os-availability-zone/detail')

        for zone in zones:
            self.assertTrue(isinstance(zone,
                                       availability_zones.AvailabilityZone))

        self.assertEqual(3, len(zones))

        l0 = [six.u('zone-1'), six.u('available')]
        l1 = [six.u('|- fake_host-1'), six.u('')]
        l2 = [six.u('| |- nova-compute'),
             six.u('enabled :-) 2012-12-26 14:45:25')]
        l3 = [six.u('internal'), six.u('available')]
        l4 = [six.u('|- fake_host-1'), six.u('')]
        l5 = [six.u('| |- nova-sched'),
             six.u('enabled :-) 2012-12-26 14:45:25')]
        l6 = [six.u('|- fake_host-2'), six.u('')]
        l7 = [six.u('| |- nova-network'),
             six.u('enabled XXX 2012-12-26 14:45:24')]
        l8 = [six.u('zone-2'), six.u('not available')]

        z0 = shell._treeizeAvailabilityZone(zones[0])
        z1 = shell._treeizeAvailabilityZone(zones[1])
        z2 = shell._treeizeAvailabilityZone(zones[2])

        self.assertEqual((len(z0), len(z1), len(z2)), (3, 5, 1))

        self._assertZone(z0[0], l0[0], l0[1])
        self._assertZone(z0[1], l1[0], l1[1])
        self._assertZone(z0[2], l2[0], l2[1])
        self._assertZone(z1[0], l3[0], l3[1])
        self._assertZone(z1[1], l4[0], l4[1])
        self._assertZone(z1[2], l5[0], l5[1])
        self._assertZone(z1[3], l6[0], l6[1])
        self._assertZone(z1[4], l7[0], l7[1])
        self._assertZone(z2[0], l8[0], l8[1])
