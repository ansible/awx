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

"""
Availability Zone interface.
"""

from novaclient.v1_1 import availability_zones


class AvailabilityZone(availability_zones.AvailabilityZone):
    pass


class AvailabilityZoneManager(availability_zones.AvailabilityZoneManager):
    """
    Manage :class:`AvailabilityZone` resources.
    """
    resource_class = AvailabilityZone
    return_parameter_name = 'availability_zone_info'
