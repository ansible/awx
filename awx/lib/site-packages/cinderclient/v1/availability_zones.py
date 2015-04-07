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

"""Availability Zone interface (v1 extension)"""

from cinderclient import base


class AvailabilityZone(base.Resource):
    NAME_ATTR = 'display_name'

    def __repr__(self):
        return "<AvailabilityZone: %s>" % self.zoneName


class AvailabilityZoneManager(base.ManagerWithFind):
    """Manage :class:`AvailabilityZone` resources."""
    resource_class = AvailabilityZone

    def list(self, detailed=False):
        """Lists all availability zones.

        :rtype: list of :class:`AvailabilityZone`
        """
        if detailed is True:
            return self._list("/os-availability-zone/detail",
                              "availabilityZoneInfo")
        else:
            return self._list("/os-availability-zone", "availabilityZoneInfo")
